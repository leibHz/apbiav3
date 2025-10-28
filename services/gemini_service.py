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
from services.gemini_stats import gemini_stats


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
                max_output_tokens=65526,  # ✅ Limite correto: 65.536 tokens
                tools=tools if tools else None,
                safety_settings=self.safety_settings,
                # Thinking Mode com budget dinâmico
                # Ref: https://ai.google.dev/gemini-api/docs/thinking
                thinking_config=types.ThinkingConfig(
                    thinking_budget=24000,  # 24.000 tokens de budget
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
            try:
                if hasattr(response.candidates[0], 'grounding_metadata'):
                    grounding = response.candidates[0].grounding_metadata
                    if grounding and hasattr(grounding, 'web_search_queries'):
                            queries = grounding.web_search_queries
                            # Verifica múltiplas condições
                            if queries and isinstance(queries, (list, tuple)) and len(queries) > 0:
                                search_used = True
                                logger.info(f"🔍 Google Search usado: {len(queries)} queries")
                                gemini_stats.record_search(user_id)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao verificar Google Search: {e}")
    # Não falha, apenas não marca como usado
            
            # Registra estatísticas
            tokens_input = 0
            tokens_output = 0
            
            if hasattr(response, 'usage_metadata'):
                tokens_input = response.usage_metadata.prompt_token_count
                tokens_output = response.usage_metadata.candidates_token_count
                
                # Registra request
                gemini_stats.record_request(user_id, tokens_input, tokens_output)
                
                logger.info(f"📊 Tokens - Input: {tokens_input} | Output: {tokens_output}")
                
                if hasattr(response.usage_metadata, 'cached_content_token_count'):
                    cached = response.usage_metadata.cached_content_token_count
                    if cached is not None and cached > 0:  # ✅ Verifica None primeiro
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