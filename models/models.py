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
    def __init__(self, id, nome, categoria, resumo=None, palavras_chave=None,
                 introducao=None, objetivo_geral=None, objetivos_especificos=None,
                 metodologia=None, cronograma=None, resultados_esperados=None,
                 referencias_bibliograficas=None, eh_continuacao=False,
                 projeto_anterior_titulo=None, projeto_anterior_resumo=None,
                 projeto_anterior_inicio=None, projeto_anterior_termino=None,
                 status='rascunho', ano_edicao=None, data_criacao=None,
                 data_atualizacao=None, gerado_por_ia=False, prompt_ia_usado=None):
        self.id = id
        self.nome = nome
        self.categoria = categoria
        self.resumo = resumo
        self.palavras_chave = palavras_chave
        self.introducao = introducao
        self.objetivo_geral = objetivo_geral
        self.objetivos_especificos = objetivos_especificos or []
        self.metodologia = metodologia
        self.cronograma = cronograma
        self.resultados_esperados = resultados_esperados
        self.referencias_bibliograficas = referencias_bibliograficas
        self.eh_continuacao = eh_continuacao
        self.projeto_anterior_titulo = projeto_anterior_titulo
        self.projeto_anterior_resumo = projeto_anterior_resumo
        self.projeto_anterior_inicio = projeto_anterior_inicio
        self.projeto_anterior_termino = projeto_anterior_termino
        self.status = status
        self.ano_edicao = ano_edicao or datetime.now().year
        self.data_criacao = data_criacao or datetime.now()
        self.data_atualizacao = data_atualizacao or datetime.now()
        self.gerado_por_ia = gerado_por_ia
        self.prompt_ia_usado = prompt_ia_usado
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'categoria': self.categoria,
            'resumo': self.resumo,
            'palavras_chave': self.palavras_chave,
            'introducao': self.introducao,
            'objetivo_geral': self.objetivo_geral,
            'objetivos_especificos': self.objetivos_especificos,
            'metodologia': self.metodologia,
            'cronograma': self.cronograma,
            'resultados_esperados': self.resultados_esperados,
            'referencias_bibliograficas': self.referencias_bibliograficas,
            'eh_continuacao': self.eh_continuacao,
            'projeto_anterior_titulo': self.projeto_anterior_titulo,
            'projeto_anterior_resumo': self.projeto_anterior_resumo,
            'projeto_anterior_inicio': self.projeto_anterior_inicio.isoformat() if self.projeto_anterior_inicio else None,
            'projeto_anterior_termino': self.projeto_anterior_termino.isoformat() if self.projeto_anterior_termino else None,
            'status': self.status,
            'ano_edicao': self.ano_edicao,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'gerado_por_ia': self.gerado_por_ia,
            'prompt_ia_usado': self.prompt_ia_usado
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