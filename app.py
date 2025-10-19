from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from dao.dao import SupabaseDAO

# Importa blueprints
from controllers.auth_controller import auth_bp
from controllers.chat_controller import chat_bp
from controllers.admin_controller import admin_bp
from controllers.project_controller import project_bp  # ← JÁ ESTAVA IMPORTANDO

# Inicializa aplicação
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Inicializa Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# DAO para carregar usuários
dao = SupabaseDAO()

@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário para Flask-Login"""
    return dao.buscar_usuario_por_id(int(user_id))

# ✅ CORREÇÃO: REGISTRA TODOS os blueprints (FALTAVA project_bp!)
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp, url_prefix='/chat')
app.register_blueprint(admin_bp)
app.register_blueprint(project_bp, url_prefix='/projetos')  # ← ESTAVA FALTANDO!

# Rota principal
@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403

# Context processor para variáveis globais nos templates
@app.context_processor
def inject_globals():
    return {
        'app_name': 'APBIA',
        'app_version': '1.0.0',
        'ia_status': Config.IA_STATUS
    }

# Filtro customizado para formatar datas
@app.template_filter('format_date')
def format_date_filter(date_value):
    """Formata data para exibição"""
    if not date_value:
        return '-'
    
    from datetime import datetime
    
    # Se já for datetime, formata direto
    if isinstance(date_value, datetime):
        return date_value.strftime('%d/%m/%Y')
    
    # Se for string, converte primeiro
    if isinstance(date_value, str):
        try:
            dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y')
        except:
            return date_value
    
    return '-'

@app.template_filter('format_datetime')
def format_datetime_filter(date_value):
    """Formata data e hora para exibição"""
    if not date_value:
        return '-'
    
    from datetime import datetime
    
    if isinstance(date_value, datetime):
        return date_value.strftime('%d/%m/%Y %H:%M')
    
    if isinstance(date_value, str):
        try:
            dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M')
        except:
            return date_value
    
    return '-'

if __name__ == '__main__':
    print("="*60)
    print("🤖 APBIA - Assistente de Projetos para Bragantec")
    print("="*60)
    print(f"✅ Blueprint de Projetos registrado em: /projetos")
    print(f"✅ IA Status: {'ATIVA' if Config.IA_STATUS else 'OFFLINE'}")
    print(f"✅ Modelo: {Config.GEMINI_MODEL}")
    print("="*60)
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)