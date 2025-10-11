from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from dao.dao import SupabaseDAO

auth_bp = Blueprint('auth', __name__)
dao = SupabaseDAO()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página e lógica de login"""
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        bp = request.form.get('bp', '').strip().upper()  # BP opcional no login
        
        if not email or not senha:
            flash('Por favor, preencha todos os campos obrigatórios', 'error')
            return render_template('login.html')
        
        # Busca usuário por email
        usuario = dao.buscar_usuario_por_email(email)
        
        if not usuario:
            flash('Usuário não encontrado', 'error')
            return render_template('login.html')
        
        # Se forneceu BP, valida
        if bp:
            from utils.helpers import format_bp
            bp_formatado = format_bp(bp)
            
            # Verifica se o BP corresponde ao usuário
            if usuario.numero_inscricao != bp_formatado:
                flash('BP não corresponde ao email fornecido', 'error')
                return render_template('login.html')
        
        # Para participantes e orientadores, BP é obrigatório no login
        if usuario.requer_bp() and not bp:
            flash('BP é obrigatório para participantes e orientadores', 'error')
            return render_template('login.html')
        
        # Verifica senha
        if not dao.verificar_senha(senha, usuario.senha_hash):
            flash('Senha incorreta', 'error')
            return render_template('login.html')
        
        # Faz login
        login_user(usuario)
        session['user_type'] = usuario.tipo_usuario_id
        session['user_name'] = usuario.nome_completo
        
        flash(f'Bem-vindo(a), {usuario.nome_completo}!', 'success')
        
        # Redireciona baseado no tipo de usuário
        if usuario.is_admin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('chat.index'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    logout_user()
    session.clear()
    flash('Você saiu da sua conta', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/verificar-bp', methods=['POST'])
def verificar_bp():
    """Endpoint AJAX para verificar se BP existe"""
    from utils.helpers import validate_bp, format_bp
    
    bp = request.json.get('bp', '').strip()
    
    if not bp:
        return {'exists': False, 'message': 'BP não fornecido'}
    
    if not validate_bp(bp):
        return {'exists': False, 'message': 'Formato inválido. Use: BP12345678X'}
    
    bp_formatado = format_bp(bp)
    usuario = dao.buscar_usuario_por_bp(bp_formatado)
    
    if usuario:
        return {
            'exists': True,
            'nome': usuario.nome_completo,
            'email': usuario.email,
            'tipo': usuario.tipo_usuario_id
        }
    
    return {'exists': False, 'message': 'BP não encontrado no sistema'}