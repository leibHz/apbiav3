"""
Funções auxiliares para o APBIA
"""

import os
import re
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config


def allowed_file(filename):
    """
    Verifica se o arquivo tem extensão permitida
    
    Args:
        filename: Nome do arquivo
    
    Returns:
        bool: True se permitido, False caso contrário
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """
    Retorna a extensão do arquivo
    
    Args:
        filename: Nome do arquivo
    
    Returns:
        str: Extensão do arquivo
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def format_file_size(bytes):
    """
    Formata tamanho de arquivo para leitura humana
    
    Args:
        bytes: Tamanho em bytes
    
    Returns:
        str: Tamanho formatado (ex: "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0


def sanitize_filename(filename):
    """
    Sanitiza nome de arquivo removendo caracteres perigosos
    
    Args:
        filename: Nome do arquivo
    
    Returns:
        str: Nome sanitizado
    """
    # Remove caracteres especiais
    filename = secure_filename(filename)
    
    # Adiciona timestamp para evitar conflitos
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"{name}_{timestamp}{ext}"


def validate_email(email):
    """
    Valida formato de email
    
    Args:
        email: Email a validar
    
    Returns:
        bool: True se válido
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_bp(bp):
    """
    Valida número de inscrição (BP)
    Formato: BP12345678X onde:
    - Sempre começa com 'BP'
    - 1-8 dígitos numéricos
    - Letra opcional no final (A-Z)
    
    Args:
        bp: Número BP
    
    Returns:
        bool: True se válido
    """
    if not bp:
        return False
    
    # Converte para maiúscula e remove espaços
    bp = str(bp).strip().upper()
    
    # Padrão: BP + 1-8 dígitos + letra opcional
    pattern = r'^BP\d{1,8}[A-Z]?'


def truncate_text(text, max_length=100, suffix='...'):
    """
    Trunca texto se exceder tamanho máximo
    
    Args:
        text: Texto a truncar
        max_length: Tamanho máximo
        suffix: Sufixo a adicionar se truncado
    
    Returns:
        str: Texto truncado
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_datetime_br(dt):
    """
    Formata datetime para padrão brasileiro
    
    Args:
        dt: Objeto datetime
    
    Returns:
        str: Data formatada (dd/mm/yyyy HH:MM)
    """
    if not dt:
        return ''
    
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    
    return dt.strftime('%d/%m/%Y %H:%M')


def get_user_type_name(tipo_id):
    """
    Retorna nome do tipo de usuário
    
    Args:
        tipo_id: ID do tipo
    
    Returns:
        str: Nome do tipo
    """
    tipos = {
        1: 'Administrador',
        2: 'Participante',
        3: 'Orientador',
        4: 'Visitante'
    }
    return tipos.get(tipo_id, 'Desconhecido')


def get_user_type_badge(tipo_id):
    """
    Retorna classe CSS do badge para tipo de usuário
    
    Args:
        tipo_id: ID do tipo
    
    Returns:
        str: Classe Bootstrap
    """
    badges = {
        1: 'bg-danger',
        2: 'bg-success',
        3: 'bg-info',
        4: 'bg-secondary'
    }
    return badges.get(tipo_id, 'bg-secondary')


def calculate_time_ago(dt):
    """
    Calcula tempo decorrido de forma legível
    
    Args:
        dt: Objeto datetime
    
    Returns:
        str: Tempo decorrido (ex: "2 horas atrás")
    """
    if not dt:
        return ''
    
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'Agora mesmo'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minuto{"s" if minutes != 1 else ""} atrás'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hora{"s" if hours != 1 else ""} atrás'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} dia{"s" if days != 1 else ""} atrás'
    else:
        return format_datetime_br(dt)


def extract_keywords(text, max_keywords=5):
    """
    Extrai palavras-chave simples de um texto
    
    Args:
        text: Texto a analisar
        max_keywords: Número máximo de palavras
    
    Returns:
        list: Lista de palavras-chave
    """
    # Remove pontuação e converte para minúsculas
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Remove stopwords comuns (simplificado)
    stopwords = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'da', 'do', 'em', 
                 'para', 'com', 'por', 'e', 'é', 'que'}
    
    words = [word for word in text.split() 
             if len(word) > 3 and word not in stopwords]
    
    # Conta frequência
    from collections import Counter
    word_freq = Counter(words)
    
    return [word for word, _ in word_freq.most_common(max_keywords)]


def generate_chat_title(first_message, max_length=50):
    """
    Gera título para chat baseado na primeira mensagem
    
    Args:
        first_message: Primeira mensagem do chat
        max_length: Tamanho máximo do título
    
    Returns:
        str: Título gerado
    """
    # Trunca e limpa
    title = first_message.strip()
    title = re.sub(r'\s+', ' ', title)  # Remove espaços múltiplos
    
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0] + '...'
    
    return title or 'Nova conversa'
    
    return re.match(pattern, bp) is not None


def format_bp(bp):
    """
    Formata BP para o padrão correto (maiúsculo)
    
    Args:
        bp: BP a formatar
    
    Returns:
        str: BP formatado
    """
    if not bp:
        return None
    
    return str(bp).strip().upper()


def truncate_text(text, max_length=100, suffix='...'):
    """
    Trunca texto se exceder tamanho máximo
    
    Args:
        text: Texto a truncar
        max_length: Tamanho máximo
        suffix: Sufixo a adicionar se truncado
    
    Returns:
        str: Texto truncado
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_datetime_br(dt):
    """
    Formata datetime para padrão brasileiro
    
    Args:
        dt: Objeto datetime
    
    Returns:
        str: Data formatada (dd/mm/yyyy HH:MM)
    """
    if not dt:
        return ''
    
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    
    return dt.strftime('%d/%m/%Y %H:%M')


def get_user_type_name(tipo_id):
    """
    Retorna nome do tipo de usuário
    
    Args:
        tipo_id: ID do tipo
    
    Returns:
        str: Nome do tipo
    """
    tipos = {
        1: 'Administrador',
        2: 'Participante',
        3: 'Orientador',
        4: 'Visitante'
    }
    return tipos.get(tipo_id, 'Desconhecido')


def get_user_type_badge(tipo_id):
    """
    Retorna classe CSS do badge para tipo de usuário
    
    Args:
        tipo_id: ID do tipo
    
    Returns:
        str: Classe Bootstrap
    """
    badges = {
        1: 'bg-danger',
        2: 'bg-success',
        3: 'bg-info',
        4: 'bg-secondary'
    }
    return badges.get(tipo_id, 'bg-secondary')


def calculate_time_ago(dt):
    """
    Calcula tempo decorrido de forma legível
    
    Args:
        dt: Objeto datetime
    
    Returns:
        str: Tempo decorrido (ex: "2 horas atrás")
    """
    if not dt:
        return ''
    
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'Agora mesmo'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minuto{"s" if minutes != 1 else ""} atrás'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hora{"s" if hours != 1 else ""} atrás'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} dia{"s" if days != 1 else ""} atrás'
    else:
        return format_datetime_br(dt)


def extract_keywords(text, max_keywords=5):
    """
    Extrai palavras-chave simples de um texto
    
    Args:
        text: Texto a analisar
        max_keywords: Número máximo de palavras
    
    Returns:
        list: Lista de palavras-chave
    """
    # Remove pontuação e converte para minúsculas
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Remove stopwords comuns (simplificado)
    stopwords = {'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'da', 'do', 'em', 
                 'para', 'com', 'por', 'e', 'é', 'que'}
    
    words = [word for word in text.split() 
             if len(word) > 3 and word not in stopwords]
    
    # Conta frequência
    from collections import Counter
    word_freq = Counter(words)
    
    return [word for word, _ in word_freq.most_common(max_keywords)]


def generate_chat_title(first_message, max_length=50):
    """
    Gera título para chat baseado na primeira mensagem
    
    Args:
        first_message: Primeira mensagem do chat
        max_length: Tamanho máximo do título
    
    Returns:
        str: Título gerado
    """
    # Trunca e limpa
    title = first_message.strip()
    title = re.sub(r'\s+', ' ', title)  # Remove espaços múltiplos
    
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0] + '...'
    
    return title or 'Nova conversa'