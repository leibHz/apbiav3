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
    GEMINI_MODEL = 'gemini-2.5-flash'
    
    # Limites do Modelo Gemini 2.5 Flash
    # Ref: https://ai.google.dev/gemini-api/docs/models?hl=pt-br#gemini-2.5-flash
    GEMINI_MAX_INPUT_TOKENS = 1_048_576   # 1M tokens (1.048.576)
    GEMINI_MAX_OUTPUT_TOKENS = 65_536     # 64K tokens (65.536) ✅ MÁXIMO
    GEMINI_DEFAULT_OUTPUT_TOKENS = 8_192  # 8K tokens (padrão)
    
    # ===================================================================
    # Rate Limits do FREE Tier
    # Ref: https://ai.google.dev/gemini-api/docs/rate-limits?hl=pt-br
    # ===================================================================
    GEMINI_RPM_LIMIT = 10           # Requests Per Minute
    GEMINI_TPM_LIMIT = 250_000    # Tokens Per Minute (250K)
    GEMINI_RPD_LIMIT = 250        # Requests Per Day
    GEMINI_TPD_LIMIT = None         # Tokens Per Day (Unlimited no FREE)
    
    # Google Search (FREE)
    # Ref: https://ai.google.dev/gemini-api/docs/google-search?hl=pt-br
    GEMINI_SEARCH_RPD = 450         # Google Search Requests Per Day
    
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
        print("🤖 APBIA - Configurações do Gemini 2.5 Flash")
        print("="*70)
        print(f"Modelo: {Config.GEMINI_MODEL}")
        print(f"Input Máximo: {Config.GEMINI_MAX_INPUT_TOKENS:,} tokens".replace(',', '.'))
        print(f"Output Máximo: {Config.GEMINI_MAX_OUTPUT_TOKENS:,} tokens".replace(',', '.'))
        print(f"\nRate Limits (FREE Tier):")
        print(f"  - RPM: {Config.GEMINI_RPM_LIMIT} req/min")
        print(f"  - TPM: {Config.GEMINI_TPM_LIMIT:,} tokens/min".replace(',', '.'))
        print(f"  - RPD: {Config.GEMINI_RPD_LIMIT:,} req/dia".replace(',', '.'))
        print(f"  - TPD: Ilimitado")
        print(f"  - Google Search: {Config.GEMINI_SEARCH_RPD} buscas/dia")
        print(f"\n💰 Custo: FREE (sem cobranças)")
        print("="*70 + "\n")