"""
Serviço COMPLETO para Google Gemini 2.5 Flash
Baseado na documentação oficial (Outubro 2025)
Implementa TODOS os recursos com estatísticas integradas
"""

from google import genai
from google.genai import types
import os
import time
from config import Config
from utils.advanced_logger import logger, log_ai_usage
from collections import defaultdict
from datetime import datetime, timedelta

"""
Módulo de Estatísticas do Gemini API
Rastreia uso de RPM, TPM, RPD e Google Search
Baseado nos limites FREE tier do Gemini 2.5 Flash
"""

from collections import defaultdict
from datetime import datetime, date
import time
from utils.advanced_logger import logger


class GeminiStats:
    """
    Rastreador de estatísticas do Gemini API
    
    Limites FREE tier (Gemini 2.5 Flash):
    - 10 RPM (requests per minute)
    - 250k TPM (tokens per minute)  
    - 250 RPD (requests per day)
    - 500 Google Search per day (grátis)
    
    Ref: https://ai.google.dev/gemini-api/docs/rate-limits
    """
    
    def __init__(self):
        # Limites FREE tier
        self.RPM_LIMIT = 10          
        self.TPM_LIMIT = 250000      
        self.RPD_LIMIT = 250         
        self.SEARCH_RPD_LIMIT = 500  
        
        # Contadores globais
        self.requests_minute = defaultdict(list)  # {timestamp_minute: [request_times]}
        self.tokens_minute = defaultdict(int)     # {timestamp_minute: token_count}
        self.requests_day = defaultdict(int)      # {date: request_count}
        self.search_day = defaultdict(int)        # {date: search_count}
        
        # Estatísticas por usuário
        self.user_stats = defaultdict(lambda: {
            'requests_today': 0,
            'tokens_today': 0,
            'searches_today': 0,
            'total_requests': 0,
            'total_tokens_input': 0,
            'total_tokens_output': 0,
            'last_reset': datetime.now().date(),
            'first_request': None,
            'last_request': None
        })
        
        logger.info("📊 GeminiStats inicializado")
    
    def _reset_if_needed(self, user_id):
        """Reset diário de estatísticas do usuário"""
        today = datetime.now().date()
        user_stat = self.user_stats[user_id]
        
        if user_stat['last_reset'] != today:
            logger.debug(f"🔄 Reset diário para usuário {user_id}")
            user_stat['requests_today'] = 0
            user_stat['tokens_today'] = 0
            user_stat['searches_today'] = 0
            user_stat['last_reset'] = today
    
    def _clean_old_data(self):
        """Remove dados antigos dos contadores"""
        now = time.time()
        current_minute = int(now / 60)
        
        # Remove requests de mais de 1 minuto atrás
        old_minutes = [
            minute for minute in self.requests_minute.keys()
            if minute < current_minute - 1
        ]
        for minute in old_minutes:
            del self.requests_minute[minute]
            if minute in self.tokens_minute:
                del self.tokens_minute[minute]
        
        # Limpa requests_day de mais de 7 dias atrás
        week_ago = datetime.now().date() - datetime.timedelta(days=7)
        old_days = [
            day for day in self.requests_day.keys()
            if day < week_ago
        ]
        for day in old_days:
            if day in self.requests_day:
                del self.requests_day[day]
            if day in self.search_day:
                del self.search_day[day]
    
    def check_limits(self, user_id=None):
        """
        Verifica se pode fazer uma requisição
        
        Args:
            user_id: ID do usuário (opcional)
        
        Returns:
            tuple: (bool, str) - (pode_fazer, mensagem_erro)
        """
        self._clean_old_data()
        
        now = time.time()
        current_minute = int(now / 60)
        today = datetime.now().date()
        
        # Verifica RPM (requests per minute)
        requests_last_minute = sum(
            len(reqs) for minute, reqs in self.requests_minute.items()
            if minute >= current_minute - 1
        )
        
        if requests_last_minute >= self.RPM_LIMIT:
            logger.warning(f"⚠️ RPM excedido: {requests_last_minute}/{self.RPM_LIMIT}")
            return False, f"Limite de {self.RPM_LIMIT} requests/minuto excedido. Aguarde 60 segundos."
        
        # Verifica RPD (requests per day)
        requests_today = self.requests_day.get(today, 0)
        
        if requests_today >= self.RPD_LIMIT:
            logger.warning(f"⚠️ RPD excedido: {requests_today}/{self.RPD_LIMIT}")
            return False, f"Limite diário de {self.RPD_LIMIT} requests excedido. Volte amanhã às 00:00 PT (Pacific Time)."
        
        # Verifica TPM (tokens per minute)
        tokens_last_minute = sum(
            tokens for minute, tokens in self.tokens_minute.items()
            if minute >= current_minute - 1
        )
        
        if tokens_last_minute >= self.TPM_LIMIT:
            logger.warning(f"⚠️ TPM excedido: {tokens_last_minute}/{self.TPM_LIMIT}")
            return False, f"Limite de {self.TPM_LIMIT} tokens/minuto excedido. Aguarde 60 segundos."
        
        # Verifica limites por usuário
        if user_id:
            self._reset_if_needed(user_id)
            user_stat = self.user_stats[user_id]
            
            if user_stat['requests_today'] >= self.RPD_LIMIT:
                logger.warning(f"⚠️ Usuário {user_id} excedeu RPD pessoal")
                return False, f"Você excedeu seu limite diário de {self.RPD_LIMIT} requests. Volte amanhã."
        
        return True, ""
    
    def record_request(self, user_id=None, tokens_input=0, tokens_output=0):
        """
        Registra uma requisição
        
        Args:
            user_id: ID do usuário
            tokens_input: Tokens de entrada
            tokens_output: Tokens de saída
        """
        now = time.time()
        current_minute = int(now / 60)
        today = datetime.now().date()
        
        # Registra request global
        self.requests_minute[current_minute].append(now)
        self.requests_day[today] = self.requests_day.get(today, 0) + 1
        
        # Registra tokens globais
        total_tokens = tokens_input + tokens_output
        self.tokens_minute[current_minute] = self.tokens_minute.get(current_minute, 0) + total_tokens
        
        # Registra por usuário
        if user_id:
            self._reset_if_needed(user_id)
            user_stat = self.user_stats[user_id]
            
            user_stat['requests_today'] += 1
            user_stat['tokens_today'] += total_tokens
            user_stat['total_requests'] += 1
            user_stat['total_tokens_input'] += tokens_input
            user_stat['total_tokens_output'] += tokens_output
            
            if user_stat['first_request'] is None:
                user_stat['first_request'] = datetime.now()
            user_stat['last_request'] = datetime.now()
        
        # Log de estatísticas
        requests_now = len(self.requests_minute[current_minute])
        logger.info(
            f"📊 Request registrada | "
            f"RPM: {requests_now}/{self.RPM_LIMIT} | "
            f"RPD: {self.requests_day[today]}/{self.RPD_LIMIT} | "
            f"Tokens: {tokens_input}+{tokens_output}={total_tokens}"
        )
    
    def record_search(self, user_id=None):
        """
        Registra uso do Google Search
        
        Args:
            user_id: ID do usuário
        """
        today = datetime.now().date()
        self.search_day[today] = self.search_day.get(today, 0) + 1
        
        if user_id:
            self._reset_if_needed(user_id)
            self.user_stats[user_id]['searches_today'] += 1
        
        searches_today = self.search_day[today]
        logger.info(
            f"🔍 Google Search usado | "
            f"Total hoje: {searches_today}/{self.SEARCH_RPD_LIMIT}"
        )
        
        # Aviso se próximo do limite
        if searches_today >= self.SEARCH_RPD_LIMIT * 0.9:
            logger.warning(
                f"⚠️ Próximo do limite de Google Search: "
                f"{searches_today}/{self.SEARCH_RPD_LIMIT}"
            )
    
    def get_stats(self, user_id=None):
        """
        Retorna estatísticas atuais
        
        Args:
            user_id: ID do usuário (opcional)
        
        Returns:
            dict: Estatísticas
        """
        now = time.time()
        current_minute = int(now / 60)
        today = datetime.now().date()
        
        # Stats globais
        requests_last_minute = sum(
            len(reqs) for minute, reqs in self.requests_minute.items()
            if minute >= current_minute - 1
        )
        
        tokens_last_minute = sum(
            tokens for minute, tokens in self.tokens_minute.items()
            if minute >= current_minute - 1
        )
        
        stats = {
            'global': {
                'requests_minute': requests_last_minute,
                'rpm_limit': self.RPM_LIMIT,
                'rpm_remaining': max(0, self.RPM_LIMIT - requests_last_minute),
                
                'requests_today': self.requests_day.get(today, 0),
                'rpd_limit': self.RPD_LIMIT,
                'rpd_remaining': max(0, self.RPD_LIMIT - self.requests_day.get(today, 0)),
                
                'tokens_minute': tokens_last_minute,
                'tpm_limit': self.TPM_LIMIT,
                'tpm_remaining': max(0, self.TPM_LIMIT - tokens_last_minute),
                
                'searches_today': self.search_day.get(today, 0),
                'search_limit': self.SEARCH_RPD_LIMIT,
                'search_remaining': max(0, self.SEARCH_RPD_LIMIT - self.search_day.get(today, 0)),
            }
        }
        
        # Stats por usuário
        if user_id and user_id in self.user_stats:
            self._reset_if_needed(user_id)
            user_stat = self.user_stats[user_id]
            
            stats['user'] = {
                'requests_today': user_stat['requests_today'],
                'tokens_today': user_stat['tokens_today'],
                'searches_today': user_stat['searches_today'],
                
                'total_requests': user_stat['total_requests'],
                'total_tokens_input': user_stat['total_tokens_input'],
                'total_tokens_output': user_stat['total_tokens_output'],
                'total_tokens': user_stat['total_tokens_input'] + user_stat['total_tokens_output'],
                
                'first_request': user_stat['first_request'].isoformat() if user_stat['first_request'] else None,
                'last_request': user_stat['last_request'].isoformat() if user_stat['last_request'] else None,
                
                'avg_tokens_per_request': (
                    (user_stat['total_tokens_input'] + user_stat['total_tokens_output']) / user_stat['total_requests']
                    if user_stat['total_requests'] > 0 else 0
                ),
            }
        
        return stats
    
    def get_user_stats(self, user_id):
        """
        Retorna estatísticas de um usuário específico
        
        Args:
            user_id: ID do usuário
        
        Returns:
            dict: Estatísticas do usuário
        """
        if user_id not in self.user_stats:
            return None
        
        self._reset_if_needed(user_id)
        return self.get_stats(user_id).get('user')
    
    def get_all_users_stats(self):
        """
        Retorna estatísticas de todos os usuários
        
        Returns:
            dict: {user_id: stats}
        """
        all_stats = {}
        
        for user_id in self.user_stats.keys():
            all_stats[user_id] = self.get_user_stats(user_id)
        
        return all_stats
    
    def reset_user(self, user_id):
        """
        Reseta estatísticas de um usuário
        
        Args:
            user_id: ID do usuário
        """
        if user_id in self.user_stats:
            del self.user_stats[user_id]
            logger.info(f"🔄 Estatísticas do usuário {user_id} resetadas")
    
    def export_stats(self):
        """
        Exporta estatísticas completas
        
        Returns:
            dict: Estatísticas completas
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'global': self.get_stats()['global'],
            'users': self.get_all_users_stats()
        }


# Instância global
gemini_stats = GeminiStats()


class GeminiService:
    """
    Serviço Gemini 2.5 Flash com TODOS os recursos
    Documentação: https://ai.google.dev/gemini-api/docs
    """
    
    def __init__(self):
        """Inicializa cliente Gemini com configurações oficiais"""
        logger.info("🤖 Inicializando GeminiService...")
        
        try:
            # Cliente oficial google-genai
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            
            # Modelo: gemini-2.5-flash (FREE tier)
            self.model_name = 'gemini-2.5-flash'
            
            # Carrega contexto da Bragantec
            self.context_files = self._load_context_files()
            
            # Safety Settings: DESABILITADO (BLOCK_NONE)
            # Ref: https://ai.google.dev/gemini-api/docs/safety-settings
            self.safety_settings = [
                types.SafetySetting(
                    category='HARM_CATEGORY_HATE_SPEECH',
                    threshold='BLOCK_NONE'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_HARASSMENT',
                    threshold='BLOCK_NONE'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                    threshold='BLOCK_NONE'
                ),
                types.SafetySetting(
                    category='HARM_CATEGORY_DANGEROUS_CONTENT',
                    threshold='BLOCK_NONE'
                )
            ]
            
            logger.info("✅ GeminiService inicializado")
            logger.info(f"   Modelo: {self.model_name}")
            logger.info(f"   Context window: 1.048.576 tokens (1M)")
            logger.info(f"   Max output: 65.536 tokens")
            logger.info(f"   Safety: DESABILITADO (BLOCK_NONE)")
            logger.info(f"   FREE tier limits:")
            logger.info(f"     - 10 RPM (requests/minuto)")
            logger.info(f"     - 250k TPM (tokens/minuto)")
            logger.info(f"     - 250 RPD (requests/dia)")
            logger.info(f"     - 500 Google Search/dia (grátis)")
            logger.info("="*60)
            
        except Exception as e:
            logger.critical(f"💥 ERRO ao inicializar Gemini: {e}")
            raise
    
    def _load_context_files(self):
        """Carrega arquivos de contexto da Bragantec"""
        logger.debug("📂 Carregando arquivos de contexto...")
        context_content = []
        context_path = Config.CONTEXT_FILES_PATH
        
        if not os.path.exists(context_path):
            logger.warning(f"⚠️ Pasta {context_path} não existe. Criando...")
            os.makedirs(context_path, exist_ok=True)
            return ""
        
        files_found = 0
        for filename in os.listdir(context_path):
            if filename.endswith('.txt'):
                files_found += 1
                filepath = os.path.join(context_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context_content.append(f"=== {filename} ===\n{content}\n")
                    logger.info(f"✅ Contexto carregado: {filename}")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar {filename}: {e}")
        
        if files_found == 0:
            logger.warning("⚠️ Nenhum arquivo .txt encontrado em context_files/")
        else:
            logger.info(f"✅ {files_found} arquivos de contexto carregados")
        
        return "\n".join(context_content) if context_content else ""
    
    def _get_system_instruction(self, tipo_usuario):
        """Instruções do sistema por tipo de usuário"""
        base = (
            "Você é o APBIA (Assistente de Projetos para Bragantec Baseado em IA), "
            "um assistente virtual especializado em ajudar estudantes e orientadores "
            "na Bragantec, feira de ciências do IFSP Bragança Paulista.\n\n"
            
            "🎯 SUAS CAPACIDADES:\n"
            "- Buscar informações atualizadas no Google\n"
            "- Executar código Python para validar soluções\n"
            "- Analisar imagens, vídeos, documentos e áudio\n"
            "- Pensar profundamente sobre problemas complexos\n"
            "- Gerar saídas estruturadas em JSON\n\n"
            
            "💡 SUA PERSONALIDADE:\n"
            "- Amigável e acessível\n"
            "- Encorajadora e positiva\n"
            "- Paciente e didática\n"
            "- Entusiasta por ciência\n\n"
            
            "📚 SUAS FUNÇÕES:\n"
            "- Auxiliar no desenvolvimento de projetos científicos\n"
            "- Sugerir ideias inovadoras\n"
            "- Ajudar no planejamento de projetos\n"
            "- Esclarecer dúvidas sobre a Bragantec\n"
        )
        
        if tipo_usuario == 'participante':
            return base + (
                "\n✨ MODO PARTICIPANTE:\n"
                "Foque em ajudá-lo a desenvolver seu projeto e preparar sua apresentação. "
                "Seja encorajador e explique conceitos de forma clara."
            )
        elif tipo_usuario == 'orientador':
            return base + (
                "\n👨‍🏫 MODO ORIENTADOR:\n"
                "Forneça insights pedagógicos e estratégias para guiar múltiplos projetos. "
                "Ajude na orientação de estudantes."
            )
        else:
            return base
    
    def chat(self, message, tipo_usuario='participante', history=None, 
             usar_pesquisa=True, usar_code_execution=True, analyze_url=None, 
             user_id=None):
        """
        Chat com TODOS os recursos do Gemini 2.5 Flash
        
        Refs:
        - Thinking: https://ai.google.dev/gemini-api/docs/thinking
        - Google Search: https://ai.google.dev/gemini-api/docs/google-search
        - Code Execution: https://ai.google.dev/gemini-api/docs/code-execution
        - URL Context: https://ai.google.dev/gemini-api/docs/url-context
        
        Args:
            message: Mensagem do usuário
            tipo_usuario: 'participante', 'orientador' ou 'visitante'
            history: Histórico de conversas
            usar_pesquisa: Habilita Google Search (500 RPD grátis)
            usar_code_execution: Habilita execução de código Python
            analyze_url: URL para análise de contexto
            user_id: ID do usuário (para estatísticas)
        
        Returns:
            dict: {
                'response': str,
                'thinking_process': str ou None,
                'search_used': bool,
                'code_executed': bool
            }
        """
        logger.info("🚀 Iniciando chat com Gemini")
        logger.debug(f"   Tipo usuário: {tipo_usuario}")
        logger.debug(f"   Google Search: {usar_pesquisa}")
        logger.debug(f"   Code Execution: {usar_code_execution}")
        logger.debug(f"   Histórico: {len(history) if history else 0} mensagens")
        
        # Verifica limites ANTES de fazer request
        can_proceed, error_msg = gemini_stats.check_limits(user_id)
        if not can_proceed:
            logger.warning(f"⚠️ Rate limit excedido: {error_msg}")
            return {
                'response': f"⚠️ {error_msg}",
                'thinking_process': None,
                'error': True,
                'search_used': False,
                'code_executed': False
            }
        
        start_time = time.time()
        
        try:
            # System instruction + contexto
            system_instruction = self._get_system_instruction(tipo_usuario)
            full_context = f"{system_instruction}\n\n{self.context_files}"
            full_message = f"{full_context}\n\n=== MENSAGEM DO USUÁRIO ===\n{message}"
            
            # Ferramentas
            tools = []
            
            if usar_pesquisa:
                # Google Search (500 RPD grátis)
                # Ref: https://ai.google.dev/gemini-api/docs/google-search
                tools.append(types.Tool(google_search=types.GoogleSearch()))
                logger.info("🔍 Google Search habilitado")
            
            if usar_code_execution:
                # Code Execution
                # Ref: https://ai.google.dev/gemini-api/docs/code-execution
                tools.append(types.Tool(code_execution=types.ToolCodeExecution()))
                logger.info("🐍 Code Execution habilitado")
            
            # Configuração completa
            # Ref: https://ai.google.dev/api/generate-content
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=65536,  # ✅ Limite correto: 65.536 tokens
                tools=tools if tools else None,
                safety_settings=self.safety_settings,
                # Thinking Mode com budget dinâmico
                # Ref: https://ai.google.dev/gemini-api/docs/thinking
                thinking_config=types.ThinkingConfig(
                    thinking_budget=24000,  
                    include_thoughts=True
                )
            )
            
            # Prepara conteúdo
            contents = []
            
            # Adiciona histórico
            if history:
                for msg in history:
                    contents.append(msg['parts'][0])
            
            # Adiciona mensagem atual
            contents.append(full_message)
            
            # Gera resposta
            logger.debug("📤 Enviando requisição...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # Extrai dados
            thinking_process = None
            response_text = ""
            code_executed = False
            
            for part in response.candidates[0].content.parts:
                if part.thought:
                    thinking_process = part.text
                    logger.info(f"💭 Thinking: {len(thinking_process)} chars")
                elif hasattr(part, 'executable_code'):
                    code_executed = True
                    logger.info(f"🐍 Código executado")
                elif part.text and not part.thought:
                    response_text += part.text
            
            # Verifica Google Search
            search_used = False
            if hasattr(response.candidates[0], 'grounding_metadata'):
                grounding = response.candidates[0].grounding_metadata
                if grounding and hasattr(grounding, 'web_search_queries'):
                    search_used = len(grounding.web_search_queries) > 0
                    if search_used:
                        logger.info(f"🔍 Google Search usado")
                        gemini_stats.record_search(user_id)
            
            # Registra estatísticas
            tokens_input = 0
            tokens_output = 0
            
            if hasattr(response, 'usage_metadata'):
                tokens_input = response.usage_metadata.prompt_token_count
                tokens_output = response.usage_metadata.candidates_token_count
                
                # Registra request
                gemini_stats.record_request(user_id, tokens_input, tokens_output)
                
                logger.info(f"📊 Tokens - Input: {tokens_input} | Output: {tokens_output}")
                
                # Cache usado?
                if hasattr(response.usage_metadata, 'cached_content_token_count'):
                    cached = response.usage_metadata.cached_content_token_count
                    if cached > 0:
                        logger.info(f"💾 Cache usado: {cached} tokens economizados!")
            
            duration = (time.time() - start_time) * 1000
            logger.info(f"✅ Resposta gerada em {duration:.2f}ms ({len(response_text)} chars)")
            
            # Log de uso da IA
            log_ai_usage(
                self.model_name,
                'CHAT',
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                thinking=bool(thinking_process),
                search=search_used
            )
            
            return {
                'response': response_text or response.text,
                'thinking_process': thinking_process,
                'search_used': search_used,
                'code_executed': code_executed
            }
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            logger.error(f"❌ Erro após {duration:.2f}ms: {str(e)}")
            import traceback
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            
            return {
                'response': f"Erro ao processar mensagem: {str(e)}",
                'thinking_process': None,
                'error': True,
                'search_used': False,
                'code_executed': False
            }
    
    def upload_file(self, file_path):
        """
        Upload de arquivo multimodal
        
        Ref: https://ai.google.dev/api/files
        Suporta: imagens, vídeos, áudio, documentos
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            File object ou None
        """
        try:
            logger.info(f"📤 Upload: {file_path}")
            
            with open(file_path, 'rb') as f:
                uploaded_file = self.client.files.upload(file=f)
            
            logger.info(f"✅ Upload concluído: {uploaded_file.display_name}")
            logger.info(f"   URI: {uploaded_file.uri}")
            logger.info(f"   MIME: {uploaded_file.mime_type}")
            
            # Aguarda processamento (para vídeos)
            while uploaded_file.state.name == "PROCESSING":
                logger.info("⏳ Processando...")
                time.sleep(2)
                uploaded_file = self.client.files.get(name=uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise ValueError(f"Falha no processamento: {uploaded_file.error}")
            
            logger.info("✅ Arquivo pronto!")
            return uploaded_file
            
        except Exception as e:
            logger.error(f"❌ Erro no upload: {e}")
            return None
    
    def chat_with_file(self, message, file_path, tipo_usuario='participante', user_id=None):
        """
        Chat com arquivo (multimodal)
        
        Refs:
        - Imagem: https://ai.google.dev/gemini-api/docs/image-understanding
        - Vídeo: https://ai.google.dev/gemini-api/docs/video-understanding
        - Documentos: https://ai.google.dev/gemini-api/docs/document-processing
        
        Args:
            message: Mensagem
            file_path: Caminho do arquivo
            tipo_usuario: Tipo do usuário
            user_id: ID do usuário
        
        Returns:
            dict com response e thinking_process
        """
        # Verifica limites
        can_proceed, error_msg = gemini_stats.check_limits(user_id)
        if not can_proceed:
            return {'response': f"⚠️ {error_msg}", 'error': True}
        
        try:
            uploaded_file = self.upload_file(file_path)
            if not uploaded_file:
                return {'response': 'Erro ao fazer upload', 'error': True}
            
            # Detecta tipo
            mime = uploaded_file.mime_type.lower()
            if 'image' in mime:
                file_type = 'imagem'
            elif 'video' in mime:
                file_type = 'vídeo'
            elif 'audio' in mime:
                file_type = 'áudio'
            else:
                file_type = 'documento'
            
            logger.info(f"🔍 Tipo: {file_type}")
            
            # System instruction
            system_instruction = self._get_system_instruction(tipo_usuario)
            full_message = f"{system_instruction}\n\n{self.context_files}\n\n{message}"
            
            # Config
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=65536,
                safety_settings=self.safety_settings,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,
                    include_thoughts=True
                )
            )
            
            # Gera resposta
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[full_message, uploaded_file],
                config=config
            )
            
            # Extrai dados
            thinking_process = None
            response_text = ""
            
            for part in response.candidates[0].content.parts:
                if part.thought:
                    thinking_process = part.text
                elif part.text:
                    response_text += part.text
            
            # Registra estatísticas
            if hasattr(response, 'usage_metadata'):
                tokens_input = response.usage_metadata.prompt_token_count
                tokens_output = response.usage_metadata.candidates_token_count
                gemini_stats.record_request(user_id, tokens_input, tokens_output)
            
            # Deleta arquivo temporário
            self.client.files.delete(name=uploaded_file.name)
            logger.info("🗑️ Arquivo temporário deletado")
            
            return {
                'response': response_text or response.text,
                'thinking_process': thinking_process,
                'file_type': file_type
            }
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            return {'response': f"Erro: {str(e)}", 'error': True}
    
    def count_tokens(self, text):
        """
        Conta tokens
        
        Ref: https://ai.google.dev/api/tokens
        
        Args:
            text: Texto
        
        Returns:
            int: Número de tokens
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=types.GenerateContentConfig(max_output_tokens=1)
            )
            
            if hasattr(response, 'usage_metadata'):
                return response.usage_metadata.prompt_token_count
            
            return 0
        except Exception as e:
            logger.warning(f"⚠️ Erro ao contar tokens: {e}")
            # Fallback: 1 token ≈ 4 caracteres
            return len(text) // 4
    
    def get_stats(self):
        """Retorna estatísticas atuais"""
        return gemini_stats.get_stats()