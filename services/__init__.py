"""
Módulo de Serviços do APBIA
Centraliza importações e instâncias globais
"""

# Importa estatísticas primeiro (para evitar circular import)
from services.gemini_stats import GeminiStats, gemini_stats

# Importa serviços
from services.gemini_service import GeminiService
from services.pdf_service import BragantecPDFGenerator

# Exporta para facilitar importações
__all__ = [
    'GeminiService',
    'GeminiStats',
    'gemini_stats',
    'BragantecPDFGenerator'
]