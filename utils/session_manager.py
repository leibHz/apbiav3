"""
Sistema de Sessão Única para APBIA
Impede que a mesma conta seja acessada simultaneamente de múltiplos dispositivos
"""

import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash, request
from flask_login import current_user, logout_user
from utils.advanced_logger import logger

class SessionManager:
    """Gerencia sessões únicas por usuário"""
    
    def __init__(self, dao):
        self.dao = dao
        self.session_timeout = timedelta(hours=12)  # Timeout de 12 horas
    
    def generate_session_token(self):
        """Gera token único de sessão"""
        return secrets.token_urlsafe(32)
    
    def create_session(self, user_id):
        """
        Cria nova sessão para usuário
        Invalida sessões anteriores
        """
        token = self.generate_session_token()
        now = datetime.now()
        
        # Atualiza token na tabela de usuários
        self.dao.supabase.table('usuarios').update({
            'session_token': token,
            'session_created_at': now.isoformat(),
            'last_activity': now.isoformat()
        }).eq('id', user_id).execute()
        
        # Armazena token na sessão Flask
        session['session_token'] = token
        session.permanent = True
        
        return token
    
    def validate_session(self, user_id):
        """
        Valida se sessão atual é a única ativa
        
        Returns:
            bool: True se válida, False se inválida
        """
        if not user_id:
            return False
        
        # Busca token atual da sessão
        current_token = session.get('session_token')
        
        if not current_token:
            return False
        
        # Busca token armazenado no banco
        result = self.dao.supabase.table('usuarios')\
            .select('session_token, session_created_at')\
            .eq('id', user_id)\
            .execute()
        
        if not result.data:
            return False
        
        user_data = result.data[0]
        stored_token = user_data.get('session_token')
        session_created = user_data.get('session_created_at')
        
        # Verifica se tokens coincidem
        if current_token != stored_token:
            return False
        
        # Verifica timeout (opcional)
        if session_created:
            created_at = datetime.fromisoformat(session_created.replace('Z', '+00:00'))
            if datetime.now() - created_at > self.session_timeout:
                return False
        
        # Atualiza última atividade
        self.update_activity(user_id)
        
        return True
    
    def update_activity(self, user_id):
        """Atualiza timestamp de última atividade"""
        self.dao.supabase.table('usuarios').update({
            'last_activity': datetime.now().isoformat()
        }).eq('id', user_id).execute()
    
    def invalidate_session(self, user_id):
        """Invalida sessão de um usuário"""
        self.dao.supabase.table('usuarios').update({
            'session_token': None,
            'session_created_at': None
        }).eq('id', user_id).execute()
        
        if 'session_token' in session:
            session.pop('session_token')


def require_valid_session(f):
    """
    Decorator que verifica validade da sessão
    Faz logout automático se sessão inválida
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return f(*args, **kwargs)
        
        # Importa aqui para evitar circular import
        from dao.dao import SupabaseDAO
        dao = SupabaseDAO()
        session_manager = SessionManager(dao)
        
        # Valida sessão
        if not session_manager.validate_session(current_user.id):
            logout_user()
            session.clear()
            flash('⚠️ Sua conta foi acessada de outro dispositivo. Faça login novamente.', 'warning')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


# Instância global
_session_manager = None

def get_session_manager():
    """Retorna instância global do SessionManager"""
    global _session_manager
    if _session_manager is None:
        from dao.dao import SupabaseDAO
        dao = SupabaseDAO()
        _session_manager = SessionManager(dao)
    return _session_manager