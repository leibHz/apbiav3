from supabase import create_client, Client
from config import Config
from models.models import Usuario, Projeto, Chat, ArquivoChat, FerramentaChat, TipoUsuario, TipoIA
import bcrypt
from utils.advanced_logger import logger, log_database_operation  # ✅ NOVO: Importa logger

class SupabaseDAO:
    """Data Access Object para Supabase com Debug Avançado"""
    
    def __init__(self):
        logger.info("🗄️ Inicializando SupabaseDAO...")
        try:
            self.supabase: Client = create_client(
                Config.SUPABASE_URL, 
                Config.SUPABASE_KEY
            )
            logger.info(f"✅ Conectado ao Supabase: {Config.SUPABASE_URL}")
        except TypeError:
            logger.warning("⚠️ Tentando fallback para versão antiga do Supabase...")
            from supabase.client import ClientOptions
            self.supabase = create_client(
                Config.SUPABASE_URL,
                Config.SUPABASE_KEY,
                options=ClientOptions()
            )
            logger.info("✅ Conectado (modo compatibilidade)")
        except Exception as e:
            logger.critical(f"💥 ERRO ao conectar ao Supabase: {e}")
            raise
    
    # ============ USUÁRIOS ============
    
    def criar_usuario(self, nome_completo, email, senha, tipo_usuario_id, numero_inscricao=None):
        """Cria um novo usuário"""
        logger.info(f"👤 Criando usuário: {email} (Tipo: {tipo_usuario_id})")
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
        
        try:
            result = self.supabase.table('usuarios').insert(data).execute()
            log_database_operation('INSERT', 'usuarios', data={'email': email}, result='Success')
            logger.info(f"✅ Usuário criado com sucesso: {email}")
            return self._row_to_usuario(result.data[0]) if result.data else None
        except Exception as e:
            log_database_operation('INSERT', 'usuarios', data={'email': email}, result=f'Error: {e}')
            logger.error(f"❌ Erro ao criar usuário: {e}")
            raise

    def buscar_usuario_por_id(self, usuario_id):
        """Busca usuário por ID"""
        logger.debug(f"🔍 Buscando usuário ID: {usuario_id}")
        result = self.supabase.table('usuarios').select('*').eq('id', usuario_id).execute()
        log_database_operation('SELECT', 'usuarios', data={'id': usuario_id}, result='Found' if result.data else 'Not Found')
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
        """
        ✅ ATUALIZADO: Deleta um chat (CASCADE deleta mensagens e arquivos)
        """
        logger.info(f"🗑️ Deletando chat ID: {chat_id}")
        
        try:
            # ✅ 1. Deleta arquivos relacionados (CASCADE pode não funcionar para arquivos físicos)
            self.deletar_arquivos_por_chat(chat_id)
            
            # ✅ 2. Deleta chat (CASCADE deleta mensagens automaticamente)
            result = self.supabase.table('chats').delete().eq('id', chat_id).execute()
            
            log_database_operation('DELETE', 'chats', data={'id': chat_id}, result='Success')
            return bool(result.data)
            
        except Exception as e:
            log_database_operation('DELETE', 'chats', data={'id': chat_id}, result=f'Error: {e}')
            logger.error(f"❌ Erro ao deletar chat: {e}")
            return False

    # ============ ARQUIVOS DE CHAT ============

    def criar_arquivo_chat(self, chat_id, nome_arquivo, url_arquivo, tipo_arquivo=None, 
                           tamanho_bytes=None, gemini_file_uri=None):
        """
        ✅ NOVO: Cria registro de arquivo no banco
        """
        logger.info(f"📎 Salvando arquivo no banco: {nome_arquivo}")
        
        data = {
            'chat_id': chat_id,
            'nome_arquivo': nome_arquivo,
            'url_arquivo': url_arquivo,
            'tipo_arquivo': tipo_arquivo,
            'tamanho_bytes': tamanho_bytes
        }
        
        if gemini_file_uri:
            data['gemini_file_uri'] = gemini_file_uri
        
        try:
            result = self.supabase.table('arquivos_chat').insert(data).execute()
            log_database_operation('INSERT', 'arquivos_chat', data={'nome': nome_arquivo}, result='Success')
            
            if result.data:
                logger.info(f"✅ Arquivo salvo: ID {result.data[0]['id']}")
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            log_database_operation('INSERT', 'arquivos_chat', data={'nome': nome_arquivo}, result=f'Error: {e}')
            logger.error(f"❌ Erro ao salvar arquivo: {e}")
            raise

    def listar_arquivos_por_chat(self, chat_id):
        """
        ✅ NOVO: Lista todos os arquivos de um chat
        """
        logger.debug(f"📁 Buscando arquivos do chat {chat_id}")
        
        try:
            result = self.supabase.table('arquivos_chat')\
                .select('*')\
                .eq('chat_id', chat_id)\
                .order('data_upload', desc=False)\
                .execute()
            
            if result.data:
                logger.info(f"✅ {len(result.data)} arquivos encontrados")
                return result.data
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar arquivos: {e}")
            return []

    def buscar_arquivo_por_id(self, arquivo_id):
        """
        ✅ NOVO: Busca arquivo por ID
        """
        logger.debug(f"🔍 Buscando arquivo ID: {arquivo_id}")
        
        try:
            result = self.supabase.table('arquivos_chat')\
                .select('*')\
                .eq('id', arquivo_id)\
                .execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar arquivo: {e}")
            return None

    def deletar_arquivo(self, arquivo_id):
        """
        ✅ NOVO: Deleta arquivo do banco
        """
        logger.info(f"🗑️ Deletando arquivo ID: {arquivo_id}")
        
        try:
            result = self.supabase.table('arquivos_chat')\
                .delete()\
                .eq('id', arquivo_id)\
                .execute()
            
            log_database_operation('DELETE', 'arquivos_chat', data={'id': arquivo_id}, result='Success')
            return bool(result.data)
            
        except Exception as e:
            log_database_operation('DELETE', 'arquivos_chat', data={'id': arquivo_id}, result=f'Error: {e}')
            logger.error(f"❌ Erro ao deletar arquivo: {e}")
            return False

    def associar_arquivo_mensagem(self, arquivo_id, mensagem_id):
        """
        ✅ NOVO: Associa arquivo a uma mensagem específica
        """
        try:
            result = self.supabase.table('arquivos_chat')\
                .update({'mensagem_id': mensagem_id})\
                .eq('id', arquivo_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível associar arquivo à mensagem: {e}")
            logger.warning("💡 Considere adicionar coluna 'mensagem_id' em 'arquivos_chat'")
            return False

    def deletar_arquivos_por_chat(self, chat_id):
        """
        ✅ NOVO: Deleta todos os arquivos de um chat
        """
        logger.info(f"🗑️ Deletando todos os arquivos do chat {chat_id}")
        
        try:
            result = self.supabase.table('arquivos_chat')\
                .delete()\
                .eq('chat_id', chat_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"❌ Erro ao deletar arquivos: {e}")
            return False

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
        
        # Converte datas
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
        
        # Converte datas de projeto anterior
        projeto_anterior_inicio = None
        if row.get('projeto_anterior_inicio'):
            if isinstance(row['projeto_anterior_inicio'], str):
                try:
                    projeto_anterior_inicio = datetime.fromisoformat(row['projeto_anterior_inicio']).date()
                except:
                    projeto_anterior_inicio = None
        
        projeto_anterior_termino = None
        if row.get('projeto_anterior_termino'):
            if isinstance(row['projeto_anterior_termino'], str):
                try:
                    projeto_anterior_termino = datetime.fromisoformat(row['projeto_anterior_termino']).date()
                except:
                    projeto_anterior_termino = None
        
        return Projeto(
            id=row['id'],
            nome=row['nome'],
            categoria=row['categoria'],
            resumo=row.get('resumo'),
            palavras_chave=row.get('palavras_chave'),
            introducao=row.get('introducao'),
            objetivo_geral=row.get('objetivo_geral'),
            objetivos_especificos=row.get('objetivos_especificos', []),
            metodologia=row.get('metodologia'),
            cronograma=row.get('cronograma'),
            resultados_esperados=row.get('resultados_esperados'),
            referencias_bibliograficas=row.get('referencias_bibliograficas'),
            eh_continuacao=row.get('eh_continuacao', False),
            projeto_anterior_titulo=row.get('projeto_anterior_titulo'),
            projeto_anterior_resumo=row.get('projeto_anterior_resumo'),
            projeto_anterior_inicio=projeto_anterior_inicio,
            projeto_anterior_termino=projeto_anterior_termino,
            status=row.get('status', 'rascunho'),
            ano_edicao=row.get('ano_edicao'),
            data_criacao=data_criacao,
            data_atualizacao=data_atualizacao,
            gerado_por_ia=row.get('gerado_por_ia', False),
            prompt_ia_usado=row.get('prompt_ia_usado')
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
    
    # ============ MENSAGENS ============

    def criar_mensagem(self, chat_id, role, conteudo, thinking_process=None):
        """
        Cria uma nova mensagem no histórico do chat
        """
        logger.debug(f"💬 Salvando mensagem: Chat {chat_id} | Role: {role}")
        data = {
            'chat_id': chat_id,
            'role': role,
            'conteudo': conteudo
        }
        
        # Adiciona thinking_process se fornecido
        if thinking_process:
            data['thinking_process'] = thinking_process
        
        try:
            result = self.supabase.table('mensagens').insert(data).execute()
            log_database_operation('INSERT', 'mensagens', data={'chat_id': chat_id, 'role': role}, result='Success')
            logger.info(f"✅ Mensagem salva: Chat {chat_id}")
            return result.data[0] if result.data else None
        except Exception as e:
            log_database_operation('INSERT', 'mensagens', data={'chat_id': chat_id}, result=f'Error: {e}')
            logger.error(f"❌ Erro ao salvar mensagem: {e}")
            raise

    def listar_mensagens_por_chat(self, chat_id, limit=100):
        """
        Lista mensagens de um chat (ordenadas por data)
        
        Args:
            chat_id: ID do chat
            limit: Número máximo de mensagens a retornar
        
        Returns:
            list: Lista de mensagens
        """
        result = self.supabase.table('mensagens')\
            .select('*')\
            .eq('chat_id', chat_id)\
            .order('data_envio', desc=False)\
            .limit(limit)\
            .execute()
        
        return result.data if result.data else []

    def contar_mensagens_por_chat(self, chat_id):
        """
        Conta quantas mensagens existem em um chat
        
        Args:
            chat_id: ID do chat
        
        Returns:
            int: Número de mensagens
        """
        result = self.supabase.table('mensagens')\
            .select('id', count='exact')\
            .eq('chat_id', chat_id)\
            .execute()
        
        return result.count if hasattr(result, 'count') else 0

    def deletar_mensagens_por_chat(self, chat_id):
        """
        Deleta todas as mensagens de um chat (chamado automaticamente por CASCADE)
        
        Args:
            chat_id: ID do chat
        
        Returns:
            bool: True se sucesso
        """
        result = self.supabase.table('mensagens')\
            .delete()\
            .eq('chat_id', chat_id)\
            .execute()
        
        return bool(result.data)

    def obter_ultimas_n_mensagens(self, chat_id, n=10):
        """
        Obtém as últimas N mensagens de um chat
        Útil para contexto limitado
        
        Args:
            chat_id: ID do chat
            n: Número de mensagens
        
        Returns:
            list: Lista de mensagens
        """
        result = self.supabase.table('mensagens')\
            .select('*')\
            .eq('chat_id', chat_id)\
            .order('data_envio', desc=True)\
            .limit(n)\
            .execute()
        
        # Inverte para ordem cronológica correta
        return list(reversed(result.data)) if result.data else []

    def listar_projetos_por_usuario(self, usuario_id):
        """
        Lista projetos de um usuário (via tabela de associação)
        
        Args:
            usuario_id: ID do usuário
        
        Returns:
            list: Lista de projetos
        """
        # Busca IDs dos projetos do usuário
        result = self.supabase.table('participantes_projetos')\
            .select('projeto_id')\
            .eq('participante_id', usuario_id)\
            .execute()
        
        if not result.data:
            return []
        
        projeto_ids = [row['projeto_id'] for row in result.data]
        
        # Busca os projetos completos
        projetos_result = self.supabase.table('projetos')\
            .select('*')\
            .in_('id', projeto_ids)\
            .execute()
        
        return [self._row_to_projeto(row) for row in projetos_result.data] if projetos_result.data else []

    def buscar_projeto_por_id(self, projeto_id):
        """
        Busca projeto por ID
        
        Args:
            projeto_id: ID do projeto
        
        Returns:
            Projeto: Objeto Projeto ou None
        """
        result = self.supabase.table('projetos')\
            .select('*')\
            .eq('id', projeto_id)\
            .execute()
        
        return self._row_to_projeto(result.data[0]) if result.data else None