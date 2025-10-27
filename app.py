from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from dao.dao import SupabaseDAO

# ✅ NOVO: Importa sistema de debug
from utils.advanced_logger import logger, setup_request_logging, log_startup_info

# Importa blueprints
from controllers.auth_controller import auth_bp
from controllers.chat_controller import chat_bp
from controllers.admin_controller import admin_bp
from controllers.project_controller import project_bp

# Inicializa aplicação
app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# ✅ NOVO: Configura logging avançado
setup_request_logging(app)

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
    logger.debug(f"🔍 Carregando usuário ID: {user_id}")
    user = dao.buscar_usuario_por_id(int(user_id))
    if user:
        logger.info(f"✅ Usuário carregado: {user.nome_completo} (ID: {user.id})")
    else:
        logger.warning(f"⚠️ Usuário não encontrado: ID {user_id}")
    return user

# Registra blueprints
logger.info("📦 Registrando blueprints...")
app.register_blueprint(auth_bp)
logger.debug("✅ auth_bp registrado")

app.register_blueprint(chat_bp, url_prefix='/chat')
logger.debug("✅ chat_bp registrado em /chat")

app.register_blueprint(admin_bp, url_prefix='/admin')
logger.debug("✅ admin_bp registrado em /admin")

app.register_blueprint(project_bp, url_prefix='/projetos')
logger.debug("✅ project_bp registrado em /projetos")

# Rota principal
@app.route('/')
def index():
    """Página inicial"""
    logger.debug("📄 Renderizando página inicial")
    return render_template('index.html')

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"❌ 404 - Página não encontrada: {error}")
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.critical(f"💥 500 - Erro interno do servidor: {error}")
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(error):
    logger.warning(f"🚫 403 - Acesso negado: {error}")
    return render_template('errors/403.html'), 403

# Context processor para variáveis globais nos templates
@app.context_processor
def inject_globals():
    return {
        'app_name': 'APBIA',
        'app_version': '1.0.0',
        'ia_status': Config.IA_STATUS
    }

# Filtros customizados para templates
@app.template_filter('format_date')
def format_date_filter(date_value):
    """Formata data para exibição"""
    if not date_value:
        return '-'
    
    from datetime import datetime
    
    if isinstance(date_value, datetime):
        return date_value.strftime('%d/%m/%Y')
    
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
    # ✅ NOVO: Log de inicialização detalhado
    log_startup_info(app)
    
    logger.info("🌐 Iniciando servidor Flask...")
    logger.info(f"🔗 Acesse: http://localhost:5000")
    logger.info(f"🔗 Acesse (rede local): http://0.0.0.0:5000")
    
    if Config.DEBUG:
        logger.warning("⚠️ MODO DEBUG ATIVADO - NÃO USE EM PRODUÇÃO!")
    
    try:
        app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        logger.info("⏹️ Servidor encerrado pelo usuário")
    except Exception as e:
        logger.critical(f"💥 Erro fatal ao iniciar servidor: {e}")
        raise