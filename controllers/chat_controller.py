from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from dao.dao import SupabaseDAO
from services.gemini_service import GeminiService
from config import Config
from werkzeug.utils import secure_filename
import os

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
    """Endpoint para enviar mensagens para a IA"""
    if not Config.IA_STATUS:
        return jsonify({
            'error': True,
            'message': 'IA está temporariamente offline. Contate o administrador.'
        }), 503
    
    data = request.json
    message = data.get('message', '')
    chat_id = data.get('chat_id')
    usar_pesquisa = data.get('usar_pesquisa', True)  # Google Search ativado por padrão
    
    if not message:
        return jsonify({'error': True, 'message': 'Mensagem vazia'}), 400
    
    try:
        # Determina tipo de usuário
        if current_user.is_participante():
            tipo_usuario = 'participante'
        elif current_user.is_orientador():
            tipo_usuario = 'orientador'
        else:
            tipo_usuario = 'visitante'
        
        # Se não houver chat_id, cria novo chat
        if not chat_id:
            tipo_ia_id = 2 if current_user.is_participante() else \
                        3 if current_user.is_orientador() else 1
            
            # Gera título baseado na primeira mensagem
            from utils.helpers import generate_chat_title
            titulo = generate_chat_title(message)
            
            chat = dao.criar_chat(current_user.id, tipo_ia_id, titulo)
            chat_id = chat.id
        
        # Busca contexto de projetos do usuário
        projetos = dao.listar_projetos_por_usuario(current_user.id)
        contexto_projetos = ""
        
        if projetos:
            contexto_projetos = "\n\n=== PROJETOS DO USUÁRIO ===\n"
            for projeto in projetos:
                contexto_projetos += f"""
                Projeto: {projeto.nome}
                Categoria: {projeto.categoria}
                Status: {projeto.status}
                Resumo: {projeto.resumo or 'Não informado'}
                Objetivo Geral: {projeto.objetivo_geral or 'Não informado'}
                ---
                """
        
        # Carrega histórico do banco de dados (últimas 20 mensagens)
        mensagens_db = dao.obter_ultimas_n_mensagens(chat_id, n=20)
        
        # Converte para formato do Gemini
        history = []
        for msg in mensagens_db:
            history.append({
                'role': msg['role'],
                'parts': [msg['conteudo']]
            })
        
        # Monta mensagem com contexto
        message_com_contexto = f"{contexto_projetos}\n\nMENSAGEM DO USUÁRIO: {message}"
        
        # Envia para Gemini com Google Search
        response = gemini.chat(
            message_com_contexto, 
            tipo_usuario=tipo_usuario, 
            history=history,
            usar_pesquisa=usar_pesquisa
        )
        
        if response.get('error'):
            return jsonify({
                'error': True,
                'message': response['response']
            }), 500
        
        # Salva mensagem do usuário no banco
        dao.criar_mensagem(chat_id, 'user', message)
        
        # Salva resposta da IA no banco
        dao.criar_mensagem(chat_id, 'model', response['response'])
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'chat_id': chat_id,
            'search_used': usar_pesquisa
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao processar mensagem: {str(e)}'
        }), 500


@chat_bp.route('/load-history/<int:chat_id>', methods=['GET'])
@login_required
def load_history(chat_id):
    """Carrega histórico de mensagens de um chat"""
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
            'message': f'Erro ao carregar histórico: {str(e)}'
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
            'message': f'Erro ao criar chat: {str(e)}'
        }), 500


@chat_bp.route('/delete-chat/<int:chat_id>', methods=['DELETE'])
@login_required
def delete_chat(chat_id):
    """Deleta um chat (mensagens são deletadas automaticamente por CASCADE)"""
    try:
        chat = dao.buscar_chat_por_id(chat_id)
        
        if not chat or chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Chat não encontrado'}), 404
        
        dao.deletar_chat(chat_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao deletar chat: {str(e)}'
        }), 500


@chat_bp.route('/upload-file', methods=['POST'])
@login_required
def upload_file():
    """Upload de arquivo para análise da IA"""
    if not Config.IA_STATUS:
        return jsonify({'error': True, 'message': 'IA offline'}), 503
    
    if 'file' not in request.files:
        return jsonify({'error': True, 'message': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    message = request.form.get('message', 'Analise este arquivo')
    chat_id = request.form.get('chat_id')
    
    if file.filename == '':
        return jsonify({'error': True, 'message': 'Arquivo inválido'}), 400
    
    try:
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        tipo_usuario = 'participante' if current_user.is_participante() else \
                       'orientador' if current_user.is_orientador() else 'visitante'
        
        response = gemini.chat_with_file(message, filepath, tipo_usuario)
        
        os.remove(filepath)
        
        # Se houver chat_id, salva no histórico
        if chat_id:
            dao.criar_mensagem(chat_id, 'user', f'📎 {message} (arquivo: {filename})')
            dao.criar_mensagem(chat_id, 'model', response['response'])
        
        return jsonify({
            'success': True,
            'response': response['response']
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao processar arquivo: {str(e)}'
        }), 500