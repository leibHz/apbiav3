"""
Serviço COMPLETO para Google Gemini 2.5 Flash
COM MODO BRAGANTEC OPCIONAL para reduzir consumo de tokens
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
    Serviço Gemini 2.5 Flash com MODO BRAGANTEC opcional
    """
    
    def __init__(self):
        """Inicializa cliente Gemini"""
        logger.info("🤖 Inicializando GeminiService...")
        
        try:
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            self.model_name = 'gemini-2.5-flash'
            
            # ✅ NOVO: Carrega contexto da Bragantec APENAS UMA VEZ
            self.context_files = self._load_context_files()
            
            # Safety Settings: BLOCK_NONE
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
            logger.info(f"   Context window: 1.048.576 tokens")
            logger.info(f"   Max output: 65.536 tokens")
            logger.info(f"   🎯 MODO BRAGANTEC: Opcional (controlado pelo usuário)")
            
        except Exception as e:
            logger.critical(f"💥 ERRO ao inicializar Gemini: {e}")
            raise
    
    def _load_context_files(self):
        """Carrega arquivos de contexto da Bragantec"""
        logger.debug("📂 Carregando arquivos de contexto...")
        context_content = []
        context_path = Config.CONTEXT_FILES_PATH
        
        if not os.path.exists(context_path):
            logger.warning(f"⚠️ Pasta {context_path} não existe")
            os.makedirs(context_path, exist_ok=True)
            return ""
        
        files_found = 0
        total_chars = 0
        
        for filename in os.listdir(context_path):
            if filename.endswith('.txt'):
                files_found += 1
                filepath = os.path.join(context_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        total_chars += len(content)
                        context_content.append(f"=== {filename} ===\n{content}\n")
                    logger.info(f"✅ Contexto carregado: {filename}")
                except Exception as e:
                    logger.error(f"❌ Erro ao carregar {filename}: {e}")
        
        if files_found == 0:
            logger.warning("⚠️ Nenhum arquivo .txt encontrado em context_files/")
        else:
            logger.info(f"✅ {files_found} arquivos carregados (~{total_chars:,} caracteres)")
        
        return "\n".join(context_content) if context_content else ""
    
    def _get_system_instruction(self, tipo_usuario, usar_contexto_bragantec=False):
        """
        System instructions OTIMIZADAS com/sem contexto Bragantec
        
        Args:
            tipo_usuario: 'participante', 'orientador' ou 'visitante'
            usar_contexto_bragantec: Se True, adiciona conhecimento da Bragantec
        """
        
        # ✅ PROMPT BASE (sem contexto pesado)
        base = f"""Você é o APBIA (Assistente de Projetos para Bragantec Baseado em IA), um assistente virtual especializado em ajudar estudantes e orientadores na Bragantec, a feira de ciências do IFSP Bragança Paulista.

🎯 SUAS CAPACIDADES:
- Buscar informações atualizadas no Google (SEMPRE cite as fontes com links)
- Executar código Python para validar soluções
- Analisar imagens, vídeos, documentos e áudio
- Pensar profundamente sobre problemas complexos
- Gerar saídas estruturadas em JSON

💡 SUA PERSONALIDADE:
- Amigável, acessível e encorajadora
- Paciente e didática
- Entusiasta por ciência e inovação
- Sempre cite fontes quando usar Google Search

📚 SUAS FUNÇÕES:
- Auxiliar no desenvolvimento de projetos científicos
- Sugerir ideias inovadoras
- Ajudar no planejamento de projetos
- Esclarecer dúvidas sobre metodologia científica

⚠️ CITAÇÕES OBRIGATÓRIAS:
Quando usar Google Search, SEMPRE:
1. Cite a fonte com o link completo
2. Exemplo: "Segundo [Nome da Fonte](link), ..."
3. Nunca invente informações sem fontes
"""
        
        # ✅ ADICIONA CONTEXTO BRAGANTEC SE ATIVADO
        if usar_contexto_bragantec:
            base += f"""

📖 CONHECIMENTO SOBRE A BRAGANTEC:
Você tem acesso ao histórico completo das edições anteriores da Bragantec, incluindo:
- Projetos vencedores e suas características
- Critérios de avaliação dos jurados
- Tendências e padrões de projetos premiados
- Categorias: Ciências da Natureza e Exatas, Informática, Ciências Humanas e Linguagens, Engenharias

Use este conhecimento para:
- Sugerir ideias alinhadas com projetos vencedores anteriores
- Orientar sobre o que os jurados valorizam
- Identificar oportunidades de inovação baseadas em edições passadas

⚠️ IMPORTANTE: Este conhecimento consome muitos tokens. Use-o com sabedoria.
"""
        else:
            base += """

ℹ️ MODO SEM CONTEXTO BRAGANTEC:
O usuário desativou o contexto histórico da Bragantec para economizar recursos.
Você ainda pode:
- Ajudar com metodologia científica geral
- Buscar informações atualizadas no Google
- Auxiliar no planejamento de projetos
- Sugerir ideias baseadas em conhecimento geral

💡 DICA: O usuário pode ativar o "Modo Bragantec" para ter acesso ao histórico completo de edições anteriores.
"""
        
        # ✅ PERSONALIZAÇÃO POR TIPO DE USUÁRIO
        if tipo_usuario == 'participante':
            base += """

✨ MODO PARTICIPANTE:
Foque em ajudá-lo a desenvolver seu projeto científico com entusiasmo e clareza.
Seja encorajador, explique conceitos de forma didática e ajude-o a brilhar na apresentação.
"""
        elif tipo_usuario == 'orientador':
            base += """

👨‍🏫 MODO ORIENTADOR:
Forneça insights pedagógicos e estratégias para guiar múltiplos projetos.
Ajude na orientação de estudantes com dicas profissionais e boas práticas.
"""
        
        return base
    
    def chat(self, message, tipo_usuario='participante', history=None, 
             usar_pesquisa=True, usar_code_execution=True, analyze_url=None, 
             usar_contexto_bragantec=False, user_id=None):
        """
        Chat com MODO BRAGANTEC opcional
        
        Args:
            message: Mensagem do usuário
            tipo_usuario: 'participante', 'orientador' ou 'visitante'
            history: Histórico de conversas
            usar_pesquisa: Habilita Google Search
            usar_code_execution: Habilita execução de código
            analyze_url: URL para análise
            usar_contexto_bragantec: 🆕 Se True, adiciona contexto da Bragantec
            user_id: ID do usuário
        """
        logger.info("🚀 Iniciando chat com Gemini")
        logger.debug(f"   Tipo usuário: {tipo_usuario}")
        logger.debug(f"   Google Search: {usar_pesquisa}")
        logger.debug(f"   Code Execution: {usar_code_execution}")
        logger.debug(f"   🎯 MODO BRAGANTEC: {usar_contexto_bragantec}")
        logger.debug(f"   Histórico: {len(history) if history else 0} mensagens")
        
        # Verifica limites
        can_proceed, error_msg = gemini_stats.check_limits(user_id)
        if not can_proceed:
            logger.warning(f"⚠️ Rate limit excedido: {error_msg}")
            return {
                'response': f"⚠️ {error_msg}",
                'thinking_process': None,
                'error': True,
                'search_used': False,
                'code_executed': False,
                'code_results': None
            }
        
        start_time = time.time()
        
        try:
            # ✅ System instruction OTIMIZADA
            system_instruction = self._get_system_instruction(
                tipo_usuario, 
                usar_contexto_bragantec
            )
            
            # ✅ ADICIONA CONTEXTO BRAGANTEC APENAS SE ATIVADO
            if usar_contexto_bragantec:
                full_message = f"{system_instruction}\n\n{self.context_files}\n\n=== MENSAGEM DO USUÁRIO ===\n{message}"
                logger.info("📚 Contexto Bragantec ADICIONADO (~{} chars)".format(len(self.context_files)))
            else:
                full_message = f"{system_instruction}\n\n=== MENSAGEM DO USUÁRIO ===\n{message}"
                logger.info("🚀 Contexto Bragantec DESABILITADO (economia de tokens)")
            
            # Ferramentas
            tools = []
            
            if usar_pesquisa:
                tools.append(types.Tool(google_search=types.GoogleSearch()))
                logger.info("🔍 Google Search habilitado")
            
            if usar_code_execution:
                tools.append(types.Tool(code_execution=types.ToolCodeExecution()))
                logger.info("🐍 Code Execution habilitado")
            
            # Configuração
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=65536,
                tools=tools if tools else None,
                safety_settings=self.safety_settings,
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
            code_results = []
            
            logger.debug(f"📦 Processando {len(response.candidates[0].content.parts)} parts")
            
            for i, part in enumerate(response.candidates[0].content.parts):
                logger.debug(f"   Part {i}: {type(part).__name__}")
                
                # Thinking process
                if part.thought:
                    thinking_process = part.text
                    logger.info(f"💭 Thinking: {len(thinking_process)} chars")
                
                # Code execution
                elif hasattr(part, 'executable_code') and part.executable_code:
                    code_executed = True
                    code_info = {
                        'language': part.executable_code.language if hasattr(part.executable_code, 'language') else 'python',
                        'code': part.executable_code.code if hasattr(part.executable_code, 'code') else str(part.executable_code)
                    }
                    logger.info(f"🐍 Código detectado: {code_info['language']}")
                    code_results.append(code_info)
                
                # Resultado da execução
                elif hasattr(part, 'code_execution_result') and part.code_execution_result:
                    result_info = {
                        'outcome': part.code_execution_result.outcome if hasattr(part.code_execution_result, 'outcome') else 'unknown',
                        'output': part.code_execution_result.output if hasattr(part.code_execution_result, 'output') else str(part.code_execution_result)
                    }
                    logger.info(f"✅ Resultado: {result_info['outcome']}")
                    
                    if code_results:
                        code_results[-1]['result'] = result_info
                
                # Texto normal
                elif part.text and not part.thought:
                    response_text += part.text
            
            # Verifica Google Search
            search_used = False
            try:
                if hasattr(response.candidates[0], 'grounding_metadata'):
                    grounding = response.candidates[0].grounding_metadata
                    if grounding and hasattr(grounding, 'web_search_queries'):
                        queries = grounding.web_search_queries
                        if queries and isinstance(queries, (list, tuple)) and len(queries) > 0:
                            search_used = True
                            logger.info(f"🔍 Google Search usado: {len(queries)} queries")
                            gemini_stats.record_search(user_id)
            except Exception as e:
                logger.warning(f"⚠️ Erro ao verificar Google Search: {e}")
            
            # Registra estatísticas
            tokens_input = 0
            tokens_output = 0
            
            if hasattr(response, 'usage_metadata'):
                tokens_input = response.usage_metadata.prompt_token_count
                tokens_output = response.usage_metadata.candidates_token_count
                
                gemini_stats.record_request(user_id, tokens_input, tokens_output)
                
                logger.info(f"📊 Tokens - Input: {tokens_input:,} | Output: {tokens_output:,}")
                
                # ✅ ALERTA se consumo alto
                if tokens_input > 100000:
                    logger.warning(f"⚠️ CONSUMO ALTO DE TOKENS INPUT: {tokens_input:,}")
                    logger.warning(f"💡 Considere desativar o Modo Bragantec para economizar")
                
                if hasattr(response.usage_metadata, 'cached_content_token_count'):
                    cached = response.usage_metadata.cached_content_token_count
                    if cached is not None and cached > 0:
                        logger.info(f"💾 Cache usado: {cached:,} tokens economizados!")
            
            duration = (time.time() - start_time) * 1000
            logger.info(f"✅ Resposta gerada em {duration:.2f}ms ({len(response_text)} chars)")
            
            # Log de uso
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
                'code_executed': code_executed,
                'code_results': code_results if code_results else None
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
                'code_executed': False,
                'code_results': None
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
    
    def chat_with_file(self, message, file_path, tipo_usuario='participante', user_id=None, keep_file_on_gemini=False):
        """
        ✅ ATUALIZADO: Chat com arquivo (multimodal) com opção de manter no Gemini
        
        Refs:
        - Imagem: https://ai.google.dev/gemini-api/docs/image-understanding
        - Vídeo: https://ai.google.dev/gemini-api/docs/video-understanding
        - Documentos: https://ai.google.dev/gemini-api/docs/document-processing
        
        Args:
            message: Mensagem
            file_path: Caminho do arquivo
            tipo_usuario: Tipo do usuário
            user_id: ID do usuário
            keep_file_on_gemini: Se True, mantém arquivo no Gemini por 48h para re-uso
        
        Returns:
            dict com:
                - response: Resposta da IA
                - thinking_process: Processo de pensamento
                - file_type: Tipo do arquivo
                - gemini_file_uri: URI do arquivo no Gemini (se keep_file_on_gemini=True)
        """
        # Verifica limites
        can_proceed, error_msg = gemini_stats.check_limits(user_id)
        if not can_proceed:
            return {'response': f"⚠️ {error_msg}", 'error': True}
        
        try:
            # ✅ 1. Faz upload do arquivo para o Gemini
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
            
            logger.info(f"🔍 Tipo: {file_type} | URI: {uploaded_file.uri}")
            
            # System instruction
            system_instruction = self._get_system_instruction(tipo_usuario)
            full_message = f"{system_instruction}\n\n{self.context_files}\n\n{message}"
            
            # Config
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=65536,
                safety_settings=self.safety_settings,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=20000,
                    include_thoughts=True
                )
            )
            
            # ✅ 2. Gera resposta
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
                logger.info(f"📊 Tokens - Input: {tokens_input:,} | Output: {tokens_output:,}")
            
            # ✅ 3. Decide se mantém ou deleta arquivo no Gemini
            gemini_file_uri = None
            
            if keep_file_on_gemini:
                # ✅ Mantém arquivo por 48h para re-uso
                gemini_file_uri = uploaded_file.uri
                logger.info(f"💾 Arquivo mantido no Gemini por 48h: {uploaded_file.name}")
                logger.info(f"   URI: {gemini_file_uri}")
                logger.info(f"   Expira em: {uploaded_file.expiration_time}")
            else:
                # ❌ Deleta arquivo imediatamente
                self.client.files.delete(name=uploaded_file.name)
                logger.info("🗑️ Arquivo deletado do Gemini")
            
            return {
                'response': response_text or response.text,
                'thinking_process': thinking_process,
                'file_type': file_type,
                'gemini_file_uri': gemini_file_uri,  # ✅ NOVO: URI para re-uso
                'gemini_file_name': uploaded_file.name if keep_file_on_gemini else None,
                'gemini_expiration': str(uploaded_file.expiration_time) if keep_file_on_gemini else None
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