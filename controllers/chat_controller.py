"""
Chat Controller COMPLETO
Usa TODOS os recursos do Gemini 2.5 Flash
"""

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from dao.dao import SupabaseDAO
from services.gemini_service import GeminiService
from config import Config
from werkzeug.utils import secure_filename
import os
from utils.rate_limiter import rate_limiter

chat_bp = Blueprint('chat', __name__)
dao = SupabaseDAO()
gemini = GeminiService()

@chat_bp.route('/')
@login_required
def index():
    """Página principal do chat"""
    if not Config.IA_STATUS:
        return render_template('chat.html', ia_offline=True)
    
    chats = dao.listar_chats_por_usuario(current_user.id)
    
    tipo_usuario = 'participante' if current_user.is_participante() else \
                   'orientador' if current_user.is_orientador() else 'visitante'
    
    return render_template('chat.html', 
                         chats=chats, 
                         tipo_usuario=tipo_usuario,
                         ia_offline=False)


@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """
    Endpoint COMPLETO para enviar mensagens
    Suporta:
    - Google Search
    - Code Execution
    - URL Analysis
    - Thinking Mode
    - Context Caching
    - Rate Limiting
    """
    if not Config.IA_STATUS:
        return jsonify({
            'error': True,
            'message': 'IA está temporariamente offline.'
        }), 503
    
    # ✅ Verifica rate limit
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
    analyze_url = data.get('url')  # URL para analisar (opcional)
    
    if not message:
        return jsonify({'error': True, 'message': 'Mensagem vazia'}), 400
    
    try:
        # Tipo de usuário
        if current_user.is_participante():
            tipo_usuario = 'participante'
        elif current_user.is_orientador():
            tipo_usuario = 'orientador'
        else:
            tipo_usuario = 'visitante'
        
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
        
        # Carrega histórico (últimas 20 mensagens)
        mensagens_db = dao.obter_ultimas_n_mensagens(chat_id, n=20)
        
        history = []
        for msg in mensagens_db:
            history.append({
                'role': msg['role'],
                'parts': [msg['conteudo']]
            })
        
        # Mensagem com contexto
        message_com_contexto = f"{contexto_projetos}\n\n{message}"
        
        # Chama Gemini com TODOS os recursos
        print(f"🚀 Chamando Gemini com:")
        print(f"   - Google Search: {usar_pesquisa}")
        print(f"   - Code Execution: {usar_code_execution}")
        print(f"   - URL Analysis: {analyze_url}")
        
        response = gemini.chat(
            message_com_contexto, 
            tipo_usuario=tipo_usuario, 
            history=history,
            usar_pesquisa=usar_pesquisa,
            usar_code_execution=usar_code_execution,
            analyze_url=analyze_url,
            user_id=current_user.id
        )
        
        if response.get('error'):
            return jsonify({
                'error': True,
                'message': response['response']
            }), 500
        
        # Salva mensagem do usuário
        dao.criar_mensagem(chat_id, 'user', message)
        
        # Salva resposta da IA com thinking process
        dao.criar_mensagem(
            chat_id, 
            'model', 
            response['response'],
            thinking_process=response.get('thinking_process')
        )
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'chat_id': chat_id,
            'search_used': response.get('search_used', False),
            'code_executed': response.get('code_executed', False)
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
    Upload de arquivo MULTIMODAL
    Suporta: imagens, vídeos, áudio, documentos
    """
    if not Config.IA_STATUS:
        return jsonify({'error': True, 'message': 'IA offline'}), 503
    
    if 'file' not in request.files:
        return jsonify({'error': True, 'message': 'Nenhum arquivo'}), 400
    
    file = request.files['file']
    message = request.form.get('message', 'Analise este arquivo')
    chat_id = request.form.get('chat_id')
    analyze_as = request.form.get('analyze_as', 'auto')  # image/video/document/audio/auto
    
    if file.filename == '':
        return jsonify({'error': True, 'message': 'Arquivo inválido'}), 400
    
    try:
        # Salva arquivo temporariamente
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Tipo de usuário
        tipo_usuario = 'participante' if current_user.is_participante() else \
                       'orientador' if current_user.is_orientador() else 'visitante'
        
        # Processa arquivo com Gemini (MULTIMODAL)
        print(f"📁 Processando arquivo multimodal: {filename}")
        print(f"   Tipo de análise: {analyze_as}")
        
        response = gemini.chat_with_file(
            message, 
            filepath, 
            tipo_usuario,
            user_id=current_user.id
        )
        
        # Remove arquivo temporário
        os.remove(filepath)
        
        # Salva no histórico se houver chat_id
        if chat_id:
            dao.criar_mensagem(
                chat_id, 
                'user', 
                f'📎 {message} (arquivo: {filename}, tipo: {response.get("file_type", "auto")})'
            )
            dao.criar_mensagem(
                chat_id, 
                'model', 
                response['response'],
                thinking_process=response.get('thinking_process')
            )
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'file_type': response.get('file_type')
        })
        
    except Exception as e:
        import traceback
        print(f"❌ Erro: {traceback.format_exc()}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@chat_bp.route('/analyze-url', methods=['POST'])
@login_required
def analyze_url():
    """
    Analisa uma URL com URL Context
    Novo recurso!
    """
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
                       'orientador' if current_user.is_orientador() else 'visitante'
        
        # Chama Gemini com URL Context
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
    """
    Conta tokens de uma mensagem
    Útil para verificar limites
    """
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'tokens': 0})
    
    try:
        tokens = gemini.count_tokens(text)
        return jsonify({
            'success': True,
            'tokens': tokens,
            'within_limit': tokens <= 1000000  # 1M tokens input limit
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500


@chat_bp.route('/cache-status', methods=['GET'])
@login_required
def cache_status():
    """Verifica status do cache de contexto"""
    try:
        caches = gemini.list_cached_contents()
        return jsonify({
            'success': True,
            'caches': [
                {
                    'name': cache.name,
                    'expire_time': str(cache.expire_time),
                    'model': cache.model
                }
                for cache in caches
            ]
        })
    except Exception as e:
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500


@chat_bp.route('/load-history/<int:chat_id>', methods=['GET'])
@login_required
def load_history(chat_id):
    """Carrega histórico de mensagens"""
    try:
        chat = dao.buscar_chat_por_id(chat_id)
        
        if not chat or chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Chat não encontrado'}), 404
        
        mensagens = dao.listar_mensagens_por_chat(chat_id)
        
        return jsonify({
            'success': True,
            'mensagens': mensagens,
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
    """Deleta um chat"""
    try:
        chat = dao.buscar_chat_por_id(chat_id)
        
        if not chat or chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Chat não encontrado'}), 404
        
        dao.deletar_chat(chat_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500