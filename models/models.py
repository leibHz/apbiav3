from datetime import datetime
from flask_login import UserMixin

class TipoUsuario:
    """Modelo para tipos de usuário"""
    def __init__(self, id, nome):
        self.id = id
        self.nome = nome
    
    def to_dict(self):
        return {'id': self.id, 'nome': self.nome}


class TipoIA:
    """Modelo para tipos de IA"""
    def __init__(self, id, nome):
        self.id = id
        self.nome = nome
    
    def to_dict(self):
        return {'id': self.id, 'nome': self.nome}


class Usuario(UserMixin):
    """Modelo para usuários"""
    def __init__(self, id, nome_completo, email, senha_hash=None, 
                 tipo_usuario_id=None, numero_inscricao=None,
                 data_criacao=None, data_atualizacao=None):
        self.id = id
        self.nome_completo = nome_completo
        self.email = email
        self.senha_hash = senha_hash
        self.tipo_usuario_id = tipo_usuario_id
        self.numero_inscricao = numero_inscricao  # Formato: BP12345678X
        self.data_criacao = data_criacao or datetime.now()
        self.data_atualizacao = data_atualizacao or datetime.now()
    
    def get_id(self):
        """Necessário para Flask-Login"""
        return str(self.id)
    
    def is_admin(self):
        """Verifica se usuário é administrador"""
        return self.tipo_usuario_id == 1
    
    def is_participante(self):
        """Verifica se usuário é participante"""
        return self.tipo_usuario_id == 2
    
    def is_orientador(self):
        """Verifica se usuário é orientador"""
        return self.tipo_usuario_id == 3
    
    def requer_bp(self):
        """Verifica se o tipo de usuário requer BP obrigatório"""
        return self.tipo_usuario_id in [2, 3]  # Participante ou Orientador
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome_completo': self.nome_completo,
            'email': self.email,
            'tipo_usuario_id': self.tipo_usuario_id,
            'numero_inscricao': self.numero_inscricao,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }


class Projeto:
    """Modelo para projetos"""
    def __init__(self, id, nome, descricao, area_projeto, ano_edicao, data_criacao=None):
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.area_projeto = area_projeto
        self.ano_edicao = ano_edicao
        self.data_criacao = data_criacao or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'area_projeto': self.area_projeto,
            'ano_edicao': self.ano_edicao,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
        }


class Chat:
    """Modelo para chats"""
    def __init__(self, id, usuario_id, tipo_ia_id, titulo, data_criacao=None):
        self.id = id
        self.usuario_id = usuario_id
        self.tipo_ia_id = tipo_ia_id
        self.titulo = titulo
        self.data_criacao = data_criacao or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'tipo_ia_id': self.tipo_ia_id,
            'titulo': self.titulo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
        }


class ArquivoChat:
    """Modelo para arquivos do chat"""
    def __init__(self, id, chat_id, nome_arquivo, url_arquivo, 
                 tipo_arquivo=None, tamanho_bytes=None, data_upload=None):
        self.id = id
        self.chat_id = chat_id
        self.nome_arquivo = nome_arquivo
        self.url_arquivo = url_arquivo
        self.tipo_arquivo = tipo_arquivo
        self.tamanho_bytes = tamanho_bytes
        self.data_upload = data_upload or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'nome_arquivo': self.nome_arquivo,
            'url_arquivo': self.url_arquivo,
            'tipo_arquivo': self.tipo_arquivo,
            'tamanho_bytes': self.tamanho_bytes,
            'data_upload': self.data_upload.isoformat() if self.data_upload else None
        }


class FerramentaChat:
    """Modelo para ferramentas do chat"""
    def __init__(self, id, chat_id, nome_ferramenta):
        self.id = id
        self.chat_id = chat_id
        self.nome_ferramenta = nome_ferramenta
    
    def to_dict(self):
        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'nome_ferramenta': self.nome_ferramenta
        }