"""
Decorators para controle de acesso e utilitários
"""

from functools import wraps
from flask import redirect, url_for, flash, request, jsonify
from flask_login import current_user

def login_required_json(f):
    """
    Decorator para rotas JSON que requerem autenticação
    Retorna JSON ao invés de redirecionar
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': True, 'message': 'Autenticação necessária'}), 401
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator que permite acesso apenas para administradores
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_admin():
            flash('Acesso negado. Apenas administradores.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


def participante_required(f):
    """
    Decorator que permite acesso apenas para participantes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_participante():
            flash('Acesso apenas para participantes.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


def orientador_required(f):
    """
    Decorator que permite acesso apenas para orientadores
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_orientador():
            flash('Acesso apenas para orientadores.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


def check_ia_status(f):
    """
    Decorator que verifica se a IA está ativa antes de processar
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from config import Config
        
        if not Config.IA_STATUS:
            if request.is_json:
                return jsonify({
                    'error': True,
                    'message': 'IA está temporariamente offline. Contate o administrador.'
                }), 503
            else:
                flash('A IA está temporariamente desativada.', 'warning')
                return redirect(url_for('chat.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(max_calls=10, period=60):
    """
    Decorator simples de rate limiting
    
    Args:
        max_calls: Número máximo de chamadas permitidas
        period: Período em segundos
    """
    from collections import defaultdict
    from time import time
    
    calls = defaultdict(list)
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return f(*args, **kwargs)
            
            user_id = current_user.id
            now = time()
            
            # Remove chamadas antigas
            calls[user_id] = [call_time for call_time in calls[user_id] 
                             if now - call_time < period]
            
            # Verifica limite
            if len(calls[user_id]) >= max_calls:
                if request.is_json:
                    return jsonify({
                        'error': True,
                        'message': 'Muitas requisições. Aguarde um momento.'
                    }), 429
                else:
                    flash('Muitas requisições. Por favor, aguarde.', 'warning')
                    return redirect(request.referrer or url_for('index'))
            
            # Adiciona nova chamada
            calls[user_id].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator