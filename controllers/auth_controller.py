from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
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
    # ✅ CORRIGIDO: url_for correto
    return redirect(url_for('index'))


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

@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    """
    Página de perfil do usuário
    Permite editar nome, email e APELIDO
    """
    if request.method == 'POST':
        try:
            data = request.json if request.is_json else request.form
            
            nome_completo = data.get('nome_completo', '').strip()
            email = data.get('email', '').strip()
            apelido = data.get('apelido', '').strip()
            
            if not nome_completo or not email:
                return jsonify({
                    'error': True,
                    'message': 'Nome e email são obrigatórios'
                }), 400
            
            # Atualiza dados
            dao.atualizar_usuario(
                current_user.id,
                nome_completo=nome_completo,
                email=email
            )
            
            # Atualiza apelido separadamente
            dao.atualizar_apelido(current_user.id, apelido if apelido else None)
            
            # Atualiza sessão
            current_user.nome_completo = nome_completo
            current_user.email = email
            current_user.apelido = apelido
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Perfil atualizado com sucesso!'
                })
            else:
                flash('Perfil atualizado com sucesso!', 'success')
                return redirect(url_for('auth.perfil'))
            
        except Exception as e:
            if request.is_json:
                return jsonify({
                    'error': True,
                    'message': f'Erro ao atualizar perfil: {str(e)}'
                }), 500
            else:
                flash(f'Erro ao atualizar: {str(e)}', 'error')
                return redirect(url_for('auth.perfil'))
    
    return render_template('perfil.html', usuario=current_user)


@auth_bp.route('/alterar-senha', methods=['POST'])
@login_required
def alterar_senha():
    """Altera senha do usuário"""
    try:
        data = request.json
        senha_atual = data.get('senha_atual', '')
        nova_senha = data.get('nova_senha', '')
        confirmar_senha = data.get('confirmar_senha', '')
        
        if not senha_atual or not nova_senha or not confirmar_senha:
            return jsonify({
                'error': True,
                'message': 'Preencha todos os campos'
            }), 400
        
        # Verifica senha atual
        if not dao.verificar_senha(senha_atual, current_user.senha_hash):
            return jsonify({
                'error': True,
                'message': 'Senha atual incorreta'
            }), 400
        
        # Verifica se senhas coincidem
        if nova_senha != confirmar_senha:
            return jsonify({
                'error': True,
                'message': 'As senhas não coincidem'
            }), 400
        
        # Valida tamanho
        if len(nova_senha) < 6:
            return jsonify({
                'error': True,
                'message': 'A senha deve ter pelo menos 6 caracteres'
            }), 400
        
        # Atualiza senha
        import bcrypt
        senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        dao.atualizar_usuario(current_user.id, senha_hash=senha_hash)
        
        return jsonify({
            'success': True,
            'message': 'Senha alterada com sucesso!'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500