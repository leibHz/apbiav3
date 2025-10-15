from supabase import create_client, Client
from config import Config
from models.models import Usuario, Projeto, Chat, ArquivoChat, FerramentaChat, TipoUsuario, TipoIA
import bcrypt

class SupabaseDAO:
    """Data Access Object para Supabase"""
    
    def __init__(self):
        try:
            # Tenta criar client com argumentos mínimos
            self.supabase: Client = create_client(
                Config.SUPABASE_URL, 
                Config.SUPABASE_KEY
            )
        except TypeError:
            # Fallback para versões mais antigas
            from supabase.client import ClientOptions
            self.supabase = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_KEY,
                options=ClientOptions()
            )
    
    # ============ USUÁRIOS ============
    
    def criar_usuario(self, nome_completo, email, senha, tipo_usuario_id, numero_inscricao=None):
        """Cria um novo usuário"""
        from utils.helpers import validate_bp, format_bp
        
        # Valida BP se for participante ou orientador
        if tipo_usuario_id in [2, 3]:  # Participante ou Orientador
            if not numero_inscricao:
                raise ValueError("BP é obrigatório para participantes e orientadores")
            
            if not validate_bp(numero_inscricao):
                raise ValueError("BP inválido. Formato correto: BP12345678X")
            
            numero_inscricao = format_bp(numero_inscricao)
        
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        data = {
            'nome_completo': nome_completo,
            'email': email,
            'senha_hash': senha_hash,
            'tipo_usuario_id': tipo_usuario_id,
            'numero_inscricao': numero_inscricao
        }
        
        result = self.supabase.table('usuarios').insert(data).execute()
        return self._row_to_usuario(result.data[0]) if result.data else None
    
    def buscar_usuario_por_id(self, usuario_id):
        """Busca usuário por ID"""
        result = self.supabase.table('usuarios').select('*').eq('id', usuario_id).execute()
        return self._row_to_usuario(result.data[0]) if result.data else None
    
    def buscar_usuario_por_email(self, email):
        """Busca usuário por email"""
        result = self.supabase.table('usuarios').select('*').eq('email', email).execute()
        return self._row_to_usuario(result.data[0]) if result.data else None
    
    def buscar_usuario_por_bp(self, numero_inscricao):
        """Busca usuário por número de inscrição (BP)"""
        from utils.helpers import format_bp
        
        numero_inscricao = format_bp(numero_inscricao)
        result = self.supabase.table('usuarios').select('*').eq('numero_inscricao', numero_inscricao).execute()
        return self._row_to_usuario(result.data[0]) if result.data else None
    
    def listar_usuarios(self):
        """Lista todos os usuários"""
        result = self.supabase.table('usuarios').select('*').execute()
        return [self._row_to_usuario(row) for row in result.data] if result.data else []
    
    def atualizar_usuario(self, usuario_id, **kwargs):
        """Atualiza dados do usuário"""
        result = self.supabase.table('usuarios').update(kwargs).eq('id', usuario_id).execute()
        return result.data[0] if result.data else None
    
    def deletar_usuario(self, usuario_id):
        """Deleta usuário"""
        result = self.supabase.table('usuarios').delete().eq('id', usuario_id).execute()
        return bool(result.data)
    
    def verificar_senha(self, senha, senha_hash):
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))
    
    # ============ PROJETOS ============
    
    def criar_projeto_completo(self, nome, categoria, **kwargs):
        """Cria um projeto completo com todos os campos"""
        from datetime import datetime
        
        data = {
            'nome': nome,
            'categoria': categoria,
            'resumo': kwargs.get('resumo'),
            'palavras_chave': kwargs.get('palavras_chave'),
            'introducao': kwargs.get('introducao'),
            'objetivo_geral': kwargs.get('objetivo_geral'),
            'objetivos_especificos': kwargs.get('objetivos_especificos', []),
            'metodologia': kwargs.get('metodologia'),
            'cronograma': kwargs.get('cronograma'),
            'resultados_esperados': kwargs.get('resultados_esperados'),
            'referencias_bibliograficas': kwargs.get('referencias_bibliograficas'),
            'eh_continuacao': kwargs.get('eh_continuacao', False),
            'projeto_anterior_titulo': kwargs.get('projeto_anterior_titulo'),
            'projeto_anterior_resumo': kwargs.get('projeto_anterior_resumo'),
            'projeto_anterior_inicio': kwargs.get('projeto_anterior_inicio'),
            'projeto_anterior_termino': kwargs.get('projeto_anterior_termino'),
            'status': kwargs.get('status', 'rascunho'),
            'ano_edicao': kwargs.get('ano_edicao', datetime.now().year),
            'gerado_por_ia': kwargs.get('gerado_por_ia', False),
            'prompt_ia_usado': kwargs.get('prompt_ia_usado')
        }
        
        result = self.supabase.table('projetos').insert(data).execute()
        return self._row_to_projeto(result.data[0]) if result.data else None
    
    def atualizar_projeto(self, projeto_id, **kwargs):
        """Atualiza campos de um projeto"""
        # Remove campos None para não sobrescrever
        data = {k: v for k, v in kwargs.items() if v is not None}
        
        if data:
            result = self.supabase.table('projetos').update(data).eq('id', projeto_id).execute()
            return self._row_to_projeto(result.data[0]) if result.data else None
        return None
    
    def deletar_projeto(self, projeto_id):
        """Deleta um projeto"""
        result = self.supabase.table('projetos').delete().eq('id', projeto_id).execute()
        return bool(result.data)
    
    def associar_participante_projeto(self, participante_id, projeto_id):
        """Associa participante a projeto"""
        data = {
            'participante_id': participante_id,
            'projeto_id': projeto_id
        }
        result = self.supabase.table('participantes_projetos').insert(data).execute()
        return bool(result.data)
    
    def associar_orientador_projeto(self, orientador_id, projeto_id):
        """Associa orientador a projeto"""
        data = {
            'orientador_id': orientador_id,
            'projeto_id': projeto_id
        }
        result = self.supabase.table('orientadores_projetos').insert(data).execute()
        return bool(result.data)
    
    # ============ CHATS ============
    
    def criar_chat(self, usuario_id, tipo_ia_id, titulo):
        """Cria um novo chat"""
        data = {
            'usuario_id': usuario_id,
            'tipo_ia_id': tipo_ia_id,
            'titulo': titulo
        }
        result = self.supabase.table('chats').insert(data).execute()
        return self._row_to_chat(result.data[0]) if result.data else None
    
    def buscar_chat_por_id(self, chat_id):
        """Busca chat por ID"""
        result = self.supabase.table('chats').select('*').eq('id', chat_id).execute()
        return self._row_to_chat(result.data[0]) if result.data else None
    
    def listar_chats_por_usuario(self, usuario_id):
        """Lista todos os chats de um usuário"""
        result = self.supabase.table('chats').select('*').eq('usuario_id', usuario_id).order('data_criacao', desc=True).execute()
        return [self._row_to_chat(row) for row in result.data] if result.data else []
    
    def deletar_chat(self, chat_id):
        """Deleta um chat"""
        result = self.supabase.table('chats').delete().eq('id', chat_id).execute()
        return bool(result.data)
    
    # ============ TIPOS ============
    
    def listar_tipos_usuario(self):
        """Lista todos os tipos de usuário"""
        result = self.supabase.table('tipos_usuario').select('*').execute()
        return [TipoUsuario(row['id'], row['nome']) for row in result.data] if result.data else []
    
    def listar_tipos_ia(self):
        """Lista todos os tipos de IA"""
        result = self.supabase.table('tipos_ia').select('*').execute()
        return [TipoIA(row['id'], row['nome']) for row in result.data] if result.data else []
    
    # ============ CONVERSORES ============
    
    def _row_to_usuario(self, row):
        """Converte linha do banco para objeto Usuario"""
        from datetime import datetime
        
        # Converte strings de data para datetime
        data_criacao = None
        if row.get('data_criacao'):
            if isinstance(row['data_criacao'], str):
                try:
                    data_criacao = datetime.fromisoformat(row['data_criacao'].replace('Z', '+00:00'))
                except:
                    data_criacao = None
            else:
                data_criacao = row['data_criacao']
        
        data_atualizacao = None
        if row.get('data_atualizacao'):
            if isinstance(row['data_atualizacao'], str):
                try:
                    data_atualizacao = datetime.fromisoformat(row['data_atualizacao'].replace('Z', '+00:00'))
                except:
                    data_atualizacao = None
            else:
                data_atualizacao = row['data_atualizacao']
        
        return Usuario(
            id=row['id'],
            nome_completo=row['nome_completo'],
            email=row['email'],
            senha_hash=row.get('senha_hash'),
            tipo_usuario_id=row['tipo_usuario_id'],
            numero_inscricao=row.get('numero_inscricao'),
            data_criacao=data_criacao,
            data_atualizacao=data_atualizacao
        )
    
    def _row_to_projeto(self, row):
        """Converte linha do banco para objeto Projeto"""
        from datetime import datetime
        
        data_criacao = None
        if row.get('data_criacao'):
            if isinstance(row['data_criacao'], str):
                try:
                    data_criacao = datetime.fromisoformat(row['data_criacao'].replace('Z', '+00:00'))
                except:
                    data_criacao = None
            else:
                data_criacao = row['data_criacao']
        
        return Projeto(
            id=row['id'],
            nome=row['nome'],
            descricao=row.get('descricao'),
            area_projeto=row['area_projeto'],
            ano_edicao=row['ano_edicao'],
            data_criacao=data_criacao
        )
    
    def _row_to_chat(self, row):
        """Converte linha do banco para objeto Chat"""
        from datetime import datetime
        
        data_criacao = None
        if row.get('data_criacao'):
            if isinstance(row['data_criacao'], str):
                try:
                    data_criacao = datetime.fromisoformat(row['data_criacao'].replace('Z', '+00:00'))
                except:
                    data_criacao = None
            else:
                data_criacao = row['data_criacao']
        
        return Chat(
            id=row['id'],
            usuario_id=row['usuario_id'],
            tipo_ia_id=row['tipo_ia_id'],
            titulo=row['titulo'],
            data_criacao=data_criacao
        )