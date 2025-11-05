import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    """Configurações da aplicação Flask"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui-mude-isso')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://bqgxmgoxirxmuvokzfkz.supabase.co')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')  # NUNCA COMITAR A KEY REAL!
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
    
    # ===================================================================
    # Google Gemini - Configurações Verificadas (27/10/2025)
    # Ref: https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash
    # ===================================================================
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')  # NUNCA COMITAR A KEY REAL!
    
    # Limites do Modelo Gemini 2.5 Flash
    # Ref: https://ai.google.dev/gemini-api/docs/models?hl=pt-br#gemini-2.5-flash
    # ===================================================================
    # Rate Limits do FREE Tier
    # Ref: https://ai.google.dev/gemini-api/docs/rate-limits?hl=pt-br
    # ===================================================================
    
    # Google Search (FREE)
    # Ref: https://ai.google.dev/gemini-api/docs/google-search?hl=pt-br
    
    # ===================================================================
    # Pricing: FREE (Sem custos)
    # Ref: https://ai.google.dev/gemini-api/docs/pricing?hl=pt-br#standard_1
    # ===================================================================
    # ✅ Tudo grátis no FREE tier:
    # - Input: $0.00
    # - Output: $0.00
    # - Google Search: $0.00 (incluído)
    # - Context Caching: Implícito (grátis)
    
    # Upload de arquivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # Contexto da IA
    CONTEXT_FILES_PATH = 'context_files'
    
    # Sistema
    IA_STATUS = True  # IA ativa por padrão
    
    @staticmethod
    def init_app(app):
        """Inicializa configurações adicionais"""
        # Cria pastas necessárias se não existirem
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.CONTEXT_FILES_PATH, exist_ok=True)
        
        # Log de configurações importantes
        print("\n" + "="*70)
        print("🤖 APBIA - Configurações inicializadas")
        print("="*70)