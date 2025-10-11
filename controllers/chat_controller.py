from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from dao.dao import SupabaseDAO
from services.gemini_service import GeminiService
from config import Config
import os

chat_bp = Blueprint('chat', __name__)
dao = SupabaseDAO()
gemini = GeminiService()

# Armazena histórico de chats em sessão (em produção, usar banco de dados)
chat_histories = {}

@chat_bp.route('/')
@login_required
def index():
    """Página principal do chat"""
    # Verifica se IA está ativa
    if not Config.IA_STATUS:
        return render_template('chat.html', ia_offline=True)
    
    # Busca chats anteriores do usuário
    chats = dao.listar_chats_por_usuario(current_user.id)
    
    # Determina tipo de usuário para personalizar IA
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
        
        # Recupera histórico se existir
        history = chat_histories.get(f"{current_user.id}_{chat_id}", []) if chat_id else []
        
        # Envia para Gemini
        response = gemini.chat(message, tipo_usuario=tipo_usuario, history=history)
        
        # Atualiza histórico
        if chat_id:
            history_key = f"{current_user.id}_{chat_id}"
            if history_key not in chat_histories:
                chat_histories[history_key] = []
            
            chat_histories[history_key].extend([
                {'role': 'user', 'parts': [message]},
                {'role': 'model', 'parts': [response['response']]}
            ])
        
        return jsonify({
            'success': True,
            'response': response['response'],
            'thinking_process': response.get('thinking_process'),
            'chat_id': chat_id
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao processar mensagem: {str(e)}'
        }), 500


@chat_bp.route('/new-chat', methods=['POST'])
@login_required
def new_chat():
    """Cria um novo chat"""
    data = request.json
    titulo = data.get('titulo', 'Nova conversa')
    
    try:
        # Define tipo de IA baseado no usuário
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
    """Deleta um chat"""
    try:
        chat = dao.buscar_chat_por_id(chat_id)
        
        # Verifica se chat pertence ao usuário
        if not chat or chat.usuario_id != current_user.id:
            return jsonify({'error': True, 'message': 'Chat não encontrado'}), 404
        
        dao.deletar_chat(chat_id)
        
        # Remove do histórico em memória
        history_key = f"{current_user.id}_{chat_id}"
        if history_key in chat_histories:
            del chat_histories[history_key]
        
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
    
    if file.filename == '':
        return jsonify({'error': True, 'message': 'Arquivo inválido'}), 400
    
    try:
        # Salva arquivo temporariamente
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Determina tipo de usuário
        tipo_usuario = 'participante' if current_user.is_participante() else \
                       'orientador' if current_user.is_orientador() else 'visitante'
        
        # Envia para Gemini
        response = gemini.chat_with_file(message, filepath, tipo_usuario)
        
        # Remove arquivo temporário
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'response': response['response']
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao processar arquivo: {str(e)}'
        }), 500


from werkzeug.utils import secure_filename