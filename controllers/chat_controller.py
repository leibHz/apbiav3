from flask import Blueprint, render_template, request, jsonify, session, send_file
from flask_login import login_required, current_user
from dao.dao import SupabaseDAO
from services.gemini_service import GeminiService
from config import Config
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from utils.rate_limiter import rate_limiter
from utils.advanced_logger import logger

chat_bp = Blueprint('chat', __name__)
dao = SupabaseDAO()
gemini = GeminiService()

# ✅ Diretório para arquivos permanentes
CHAT_FILES_DIR = os.path.join(Config.UPLOAD_FOLDER, 'chat_files')
os.makedirs(CHAT_FILES_DIR, exist_ok=True)

def _save_chat_file_to_disk(file, user_id, chat_id):
    """Salva arquivo com proteção contra race conditions"""
    import time
    from threading import Lock
    
    # Lock global para evitar race conditions
    if not hasattr(_save_chat_file_to_disk, 'lock'):
        _save_chat_file_to_disk.lock = Lock()
    
    with _save_chat_file_to_disk.lock:
        user_dir = os.path.join(CHAT_FILES_DIR, str(user_id))
        chat_dir = os.path.join(user_dir, str(chat_id))
        os.makedirs(chat_dir, exist_ok=True)
        
        # Nome único COM timestamp + contador
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(time.time() * 1000)  # Milissegundos
        
        counter = 0
        while True:
            suffix = f"_{counter}" if counter > 0 else ""
            unique_filename = f"{unique_id}_{timestamp}{suffix}_{original_filename}"
            full_path = os.path.join(chat_dir, unique_filename)
            
            if not os.path.exists(full_path):
                break
            counter += 1
        
        file.save(full_path)
        
        # Caminho relativo (para salvar no banco)
        relative_path = os.path.join('chat_files', str(user_id), str(chat_id), unique_filename)
        
        # Tamanho do arquivo
        file_size = os.path.getsize(full_path)
        
        # MIME type
        mime_type = file.content_type or 'application/octet-stream'
        
        return {
            'filepath': relative_path,
            'filename': original_filename,
            'mime_type': mime_type,
            'size': file_size
        }


@chat_bp.route('/')
@login_required
def index():
    """Página principal do chat"""
    if not Config.IA_STATUS:
        return render_template('chat.html', ia_offline=True)
    
    chats = dao.listar_chats_por_usuario(current_user.id)
    
    tipo_usuario = 'participante' if current_user.is_participante() else \
                   'orientador' if current_user.is_orientador() else None
    
    return render_template('chat.html', 
                         chats=chats, 
                         tipo_usuario=tipo_usuario,
                         ia_offline=False)


@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Endpoint para enviar mensagens COM MODO BRAGANTEC"""
    if not Config.IA_STATUS:
        return jsonify({
            'error': True,
            'message': 'IA está temporariamente offline.'
        }), 503

    # Verifica rate limit
    can_proceed, error_msg = rate_limiter.check_limit(current_user.id)

    if not can_proceed:
        return jsonify({
            'error': True,
            'message': error_msg
        }), 429

    data = request.json
    message = data.get('message', '')
    chat_id = data.get('chat_id')
    usar_pesquisa = data.get('usar_pesquisa', True)
    usar_code_execution = data.get('usar_code_execution', True)
    analyze_url = data.get('url')
    usar_contexto_bragantec = data.get('usar_contexto_bragantec', False)

    if not message:
        return jsonify({'error': True, 'message': 'Mensagem vazia'}), 400

    try:
        tipo_usuario = None
        # Tipo de usuário
        if current_user.is_participante():
            tipo_usuario = 'participante'
        elif current_user.is_orientador():
            tipo_usuario = 'orientador'

        # Cria chat se não existir
        if not chat_id:
            tipo_ia_id = 2 if current_user.is_participante() else \
                        3 if current_user.is_orientador() else 1

            from utils.helpers import generate_chat_title
            titulo = generate_chat_title(message)

            chat = dao.criar_chat(current_user.id, tipo_ia_id, titulo)
            chat_id = chat.id

        # Contexto de projetos
        projetos = dao.listar_projetos_por_usuario(current_user.id)
        contexto_projetos = ""

        if projetos:
            contexto_projetos = "\n\n=== SEUS PROJETOS ===\n"
            for projeto in projetos:
                contexto_projetos += f"""
Projeto: {projeto.nome}
Categoria: {projeto.categoria}
Status: {projeto.status}
Resumo: {projeto.resumo or 'Não informado'}
---
"""

        # ✅ Carrega histórico COM ARQUIVOS
        mensagens_db = dao.obter_ultimas_n_mensagens(chat_id, n=20)
        arquivos_db = dao.listar_arquivos_por_chat(chat_id)  # ✅ NOVO

        history = []
        
        # ✅ Monta histórico incluindo arquivos
        for msg in mensagens_db:
            history.append({
                'role': msg['role'],
                'parts': [msg['conteudo']]
            })
            
            # ✅ Se mensagem tiver arquivo associado, adiciona ao histórico
            # (A API do Gemini mantém arquivos por 48h, então podemos referenciar)
            msg_id = msg.get('id')
            arquivo_msg = next(
                (arq for arq in arquivos_db if arq.get('mensagem_id') == msg_id),
                None
            )
            
            if arquivo_msg:
                # ✅ Arquivo ainda disponível no Gemini? (48h)
                # Por enquanto, apenas logamos. Futuramente, fazer re-upload se necessário
                print(f"📎 Mensagem {msg_id} tem arquivo: {arquivo_msg['nome_arquivo']}")

        # Mensagem com contexto
        message_com_contexto = f"{contexto_projetos}\n\n{message}"
        
        apelido = current_user.apelido if hasattr(current_user, 'apelido') else None

        # Chama Gemini COM MODO BRAGANTEC
        response = gemini.chat(
            message_com_contexto,
            tipo_usuario=tipo_usuario,
            history=history,
            usar_pesquisa=usar_pesquisa,
            usar_code_execution=usar_code_execution,
            analyze_url=analyze_url,
            usar_contexto_bragantec=usar_contexto_bragantec,
            user_id=current_user.id,
            apelido=apelido  # ✅ NOVO
        )

        # ✅ NOVO: Extrai contagem de tokens se disponível
        tokens_input = response.get('tokens_input', 0)
        tokens_output = response.get('tokens_output', 0)

        # Log de consumo
        if tokens_input or tokens_output:
            logger.info(f"📊 Tokens - Input: {tokens_input:,} | Output: {tokens_output:,}")
            
            # ✅ Alerta se consumo muito alto
            if tokens_input > 100000:
                logger.warning(f"⚠️ ALTO CONSUMO DE INPUT: {tokens_input:,} tokens!")
                logger.warning(f"💡 Usuário {current_user.id} - Modo Bragantec: {usar_contexto_bragantec}")

        if response.get('error'):
            return jsonify({
                'error': True,
                'message': response['response']
            }), 500

        # Salva mensagem do usuário
        dao.criar_mensagem(chat_id, 'user', message)

        # Salva resposta da IA
        msg_assistant_id = dao.criar_mensagem(
            chat_id,
            'model',
            response['response'],
            thinking_process=response.get('thinking_process')
        )

        # ✅ NOVO: Salva informações sobre ferramentas usadas
        if msg_assistant_id:
            ferramentas_usadas = {
                'google_search': response.get('search_used', False),
                'contexto_bragantec': usar_contexto_bragantec,
                'code_execution': response.get('code_executed', False),
                'url_context': bool(analyze_url)
            }
            
            dao.salvar_ferramenta_usada(msg_assistant_id['id'], ferramentas_usadas)
            logger.info(f"🔧 Ferramentas usadas: {ferramentas_usadas}")

        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'chat_id': chat_id,
            'search_used': response.get('search_used', False),
            'code_executed': response.get('code_executed', False),
            'code_results': response.get('code_results'),
            # ✅ NOVO: Retorna contagem de tokens
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'total_tokens': tokens_input + tokens_output
        })

    except Exception as e:
        import traceback
        print(f"❌ Erro: {traceback.format_exc()}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@chat_bp.route('/upload-file', methods=['POST'])
@login_required
def upload_file():
    """
    ✅ CORRIGIDO: Upload de arquivo MULTIMODAL com salvamento persistente
    """
    if not Config.IA_STATUS:
        return jsonify({'error': True, 'message': 'IA offline'}), 503
    
    if 'file' not in request.files:
        return jsonify({'error': True, 'message': 'Nenhum arquivo'}), 400
    
    file = request.files['file']
    message = request.form.get('message', 'Analise este arquivo')
    chat_id = request.form.get('chat_id')
    
    if file.filename == '':
        return jsonify({'error': True, 'message': 'Arquivo inválido'}), 400
    
    # ✅ Validação de tamanho
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > Config.MAX_CONTENT_LENGTH:
            return jsonify({
                'error': True,
                'message': f'Arquivo muito grande. Máximo: {Config.MAX_CONTENT_LENGTH/(1024*1024):.0f}MB'
            }), 400
    
    # ✅ Validação de tipo
    from utils.helpers import allowed_file
    if not allowed_file(file.filename):
        return jsonify({
            'error': True,
            'message': 'Tipo de arquivo não permitido'
        }), 400
    
    try:
        # ✅ 1. Salva arquivo TEMPORÁRIO para processar
        temp_filename = secure_filename(file.filename)
        temp_path = os.path.join(Config.UPLOAD_FOLDER, f"temp_{uuid.uuid4()}_{temp_filename}")
        file.save(temp_path)
        
        tipo_usuario = 'participante' if current_user.is_participante() else \
                       'orientador' if current_user.is_orientador() else None
        
        # ✅ 2. Processa arquivo com Gemini
        print(f"📁 Processando arquivo: {temp_filename}")
        
        response = gemini.chat_with_file(
            message, 
            temp_path, 
            tipo_usuario,
            user_id=current_user.id,
            keep_file_on_gemini=True  # ✅ NOVO: Mantém arquivo no Gemini por 48h
        )
        
        gemini_file_uri = response.get('gemini_file_uri')  # ✅ URI do arquivo no Gemini
        
        # ✅ 3. Salva arquivo PERMANENTEMENTE no disco
        file.seek(0)  # Reset file pointer
        file_info = _save_chat_file_to_disk(file, current_user.id, chat_id or 0)
        
        # ✅ 4. Remove arquivo temporário
        try:
            os.remove(temp_path)
        except:
            pass
        
        # ✅ 5. Salva no banco de dados (tabela arquivos_chat)
        if chat_id:
            arquivo_id = dao.criar_arquivo_chat(
                chat_id=int(chat_id),
                nome_arquivo=file_info['filename'],
                url_arquivo=file_info['filepath'],
                tipo_arquivo=file_info['mime_type'],
                tamanho_bytes=file_info['size'],
                gemini_file_uri=gemini_file_uri  # ✅ URI para re-uso
            )
            
            # ✅ 6. Salva mensagens no histórico
            msg_user = dao.criar_mensagem(
                chat_id, 
                'user', 
                f'📎 {message} (arquivo: {file_info["filename"]})'
            )
            
            msg_assistant = dao.criar_mensagem(
                chat_id, 
                'model', 
                response['response'],
                thinking_process=response.get('thinking_process')
            )
            
            # ✅ 7. Associa arquivo à mensagem do usuário
            dao.associar_arquivo_mensagem(arquivo_id, msg_user['id'])
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'file_type': response.get('file_type'),
            'file_info': {
                'name': file_info['filename'],
                'size': file_info['size'],
                'type': file_info['mime_type'],
                'url': f"/chat/file/{arquivo_id}" if chat_id else None
            }
        })
        
    except Exception as e:
        import traceback
        print(f"❌ Erro: {traceback.format_exc()}")
        
        # Limpa arquivo temporário em caso de erro
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@chat_bp.route('/file/<int:arquivo_id>')
@login_required
def serve_file(arquivo_id):
    """
    ✅ NOVO: Serve arquivo salvo do chat
    """
    try:
        arquivo = dao.buscar_arquivo_por_id(arquivo_id)
        
        if not arquivo:
            return jsonify({'error': True, 'message': 'Arquivo não encontrado'}), 404
        
        # Verifica permissão (apenas dono do chat pode acessar)
        chat = dao.buscar_chat_por_id(arquivo['chat_id'])
        if chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Acesso negado'}), 403
        
        # Caminho completo do arquivo
        file_path = os.path.join(Config.UPLOAD_FOLDER, arquivo['url_arquivo'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': True, 'message': 'Arquivo físico não encontrado'}), 404
        
        return send_file(
            file_path,
            mimetype=arquivo['tipo_arquivo'],
            as_attachment=False,
            download_name=arquivo['nome_arquivo']
        )
        
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}), 500


@chat_bp.route('/load-history/<int:chat_id>', methods=['GET'])
@login_required
def load_history(chat_id):
    """
    ✅ CORRIGIDO: Carrega histórico COM ARQUIVOS
    """
    try:
        chat = dao.buscar_chat_por_id(chat_id)
        
        if not chat or chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Chat não encontrado'}), 404
        
        # ✅ Carrega mensagens
        mensagens = dao.listar_mensagens_por_chat(chat_id)
        
        # ✅ Carrega arquivos do chat
        arquivos = dao.listar_arquivos_por_chat(chat_id)
        
        # ✅ Enriquece mensagens com informações de arquivos
        for msg in mensagens:
            msg_id = msg.get('id')
            
            # Procura arquivo associado a esta mensagem
            arquivo = next(
                (arq for arq in arquivos if arq.get('mensagem_id') == msg_id),
                None
            )
            
            if arquivo:
                msg['arquivo'] = {
                    'id': arquivo['id'],
                    'nome': arquivo['nome_arquivo'],
                    'tipo': arquivo['tipo_arquivo'],
                    'tamanho': arquivo['tamanho_bytes'],
                    'url': f"/chat/file/{arquivo['id']}"
                }
        
        return jsonify({
            'success': True,
            'mensagens': mensagens,
            'arquivos': arquivos,
            'chat': chat.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@chat_bp.route('/new-chat', methods=['POST'])
@login_required
def new_chat():
    """Cria um novo chat"""
    data = request.json
    titulo = data.get('titulo', 'Nova conversa')
    
    try:
        tipo_ia_id = 2 if current_user.is_participante() else \
                     3 if current_user.is_orientador() else 1
        
        chat = dao.criar_chat(current_user.id, tipo_ia_id, titulo)
        
        return jsonify({
            'success': True,
            'chat': chat.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@chat_bp.route('/delete-chat/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    """
    ✅ CORRIGIDO: Deleta chat E seus arquivos
    """
    try:
        chat = dao.buscar_chat_por_id(chat_id)
        
        if not chat or chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Chat não encontrado'}), 404
        
        # ✅ 1. Busca arquivos do chat
        arquivos = dao.listar_arquivos_por_chat(chat_id)
        
        # ✅ 2. Deleta arquivos físicos
        for arquivo in arquivos:
            file_path = os.path.join(Config.UPLOAD_FOLDER, arquivo['url_arquivo'])
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"🗑️ Arquivo deletado: {file_path}")
                except Exception as e:
                    print(f"⚠️ Erro ao deletar arquivo: {e}")
        
        # ✅ 3. Deleta chat do banco (CASCADE deleta mensagens e arquivos_chat)
        dao.deletar_chat(chat_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


# Rotas de análise de URL e contagem de tokens mantidas iguais...
@chat_bp.route('/analyze-url', methods=['POST'])
@login_required
def analyze_url():
    """Analisa uma URL com URL Context"""
    if not Config.IA_STATUS:
        return jsonify({'error': True, 'message': 'IA offline'}), 503
    
    data = request.json
    url = data.get('url')
    message = data.get('message', 'Analise esta URL')
    chat_id = data.get('chat_id')
    
    if not url:
        return jsonify({'error': True, 'message': 'URL não fornecida'}), 400
    
    try:
        tipo_usuario = 'participante' if current_user.is_participante() else \
                       'orientador' if current_user.is_orientador() else None
        
        print(f"🌐 Analisando URL: {url}")
        
        response = gemini.chat(
            message,
            tipo_usuario=tipo_usuario,
            analyze_url=url,
            user_id=current_user.id
        )
        
        if chat_id:
            dao.criar_mensagem(chat_id, 'user', f'🔗 {message} (URL: {url})')
            dao.criar_mensagem(
                chat_id, 
                'model', 
                response['response'],
                thinking_process=response.get('thinking_process')
            )
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process')
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@chat_bp.route('/count-tokens', methods=['POST'])
@login_required
def count_tokens():
    """Conta tokens de uma mensagem"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'tokens': 0})
    
    try:
        tokens = gemini.count_tokens(text)
        return jsonify({
            'success': True,
            'tokens': tokens,
            'within_limit': tokens <= 1000000
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500