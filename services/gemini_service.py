"""
Serviço COMPLETO E CORRETO para integração com Google Gemini 2.5 Flash
Baseado na documentação oficial consultada em 26/10/2025
Implementa TODOS os recursos da API Gemini CORRETAMENTE:
- ✅ Thinking Mode (include_thoughts)
- ✅ Google Search (google_search)
- ✅ Code Execution (code_execution)
- ✅ Context Caching IMPLÍCITO (automático, FREE tier)
- ✅ Multimodal (Imagem, Vídeo, Documentos, Áudio)
- ✅ Safety Settings (DESABILITADO - BLOCK_NONE)
- ✅ Structured Output (types.Schema)
- ✅ File API NOVA (client.files.upload)
"""

from google import genai
from google.genai import types
import os
import time
from config import Config

class GeminiService:
    """
    Serviço Gemini usando google-genai (biblioteca nova, GA maio 2025)
    TODAS as funcionalidades baseadas na documentação oficial
    """
    
    def __init__(self):
        """Inicializa o cliente Gemini com todas as configurações corretas"""
        # Cliente usando biblioteca NOVA
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        self.model_name = 'gemini-2.5-flash'
        self.context_files = self._load_context_files()
        
        # Safety Settings DESABILITADOS (BLOCK_NONE em todas as categorias)
        # Documentação: https://ai.google.dev/gemini-api/docs/safety-settings
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
        
        print("="*60)
        print("✅ GeminiService inicializado (google-genai v1.11.0)")
        print(f"✅ Modelo: {self.model_name}")
        print(f"✅ Output limit: 65.536 tokens (CORRETO)")
        print(f"✅ Input limit: 1.048.576 tokens")
        print(f"✅ Safety: DESABILITADO (BLOCK_NONE)")
        print(f"✅ Rate Limits FREE:")
        print(f"   - 10 RPM (requests/minuto)")
        print(f"   - 250k TPM (tokens/minuto)")
        print(f"   - 250 RPD (requests/dia)")
        print(f"✅ Google Search: 500 RPD (grátis)")
        print(f"✅ Context Caching: IMPLÍCITO (automático, FREE)")
        print("="*60)
    
    def _load_context_files(self):
        """
        Carrega arquivos de contexto da Bragantec
        
        OTIMIZAÇÃO: Coloca contexto grande no INÍCIO para aproveitar
        cache implícito automático (Gemini 2.5 feature)
        """
        context_content = []
        context_path = Config.CONTEXT_FILES_PATH
        
        if not os.path.exists(context_path):
            print(f"⚠️ Pasta {context_path} não existe. Criando...")
            os.makedirs(context_path, exist_ok=True)
            return ""
        
        files_found = False
        for filename in os.listdir(context_path):
            if filename.endswith('.txt'):
                files_found = True
                filepath = os.path.join(context_path, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context_content.append(f"=== {filename} ===\n{content}\n")
                    print(f"✅ Contexto carregado: {filename}")
                except Exception as e:
                    print(f"❌ Erro ao carregar {filename}: {e}")
        
        if not files_found:
            print("⚠️ Nenhum arquivo .txt encontrado em context_files/")
        
        return "\n".join(context_content) if context_content else ""
    
    def _get_system_instruction(self, tipo_usuario):
        """Retorna instruções do sistema baseado no tipo de usuário"""
        base_instruction = (
            "Você é o APBIA (Assistente de Projetos para Bragantec Baseado em IA), "
            "um assistente virtual criado para ajudar estudantes e orientadores na Bragantec, "
            "uma feira de ciências do IFSP de Bragança Paulista.\n\n"
            
            "🎯 SUAS CAPACIDADES:\n"
            "- Buscar informações no Google (até 500 vezes por dia)\n"
            "- Executar código Python para validar soluções\n"
            "- Analisar imagens, vídeos, documentos e áudio\n"
            "- Pensar profundamente sobre problemas complexos\n"
            "- Gerar saídas estruturadas em JSON\n\n"
            
            "Sua personalidade:\n"
            "- Amigável e acessível\n"
            "- Encorajadora e positiva\n"
            "- Paciente e didática\n"
            "- Entusiasta por ciência\n\n"
            
            "Suas funções:\n"
            "- Auxiliar no desenvolvimento de projetos científicos\n"
            "- Sugerir ideias inovadoras\n"
            "- Ajudar no planejamento de projetos\n"
            "- Esclarecer dúvidas sobre a Bragantec\n"
        )
        
        if tipo_usuario == 'participante':
            return base_instruction + (
                "\n✨ PARTICIPANTE: Foque em ajudá-lo a desenvolver seu projeto "
                "e preparar sua apresentação. Seja encorajador!"
            )
        elif tipo_usuario == 'orientador':
            return base_instruction + (
                "\n👨‍🏫 ORIENTADOR: Forneça insights pedagógicos e estratégias "
                "para guiar múltiplos projetos."
            )
        else:
            return base_instruction
    
    def chat(self, message, tipo_usuario='participante', history=None, 
             usar_pesquisa=True, usar_code_execution=True):
        """
        Chat com TODOS os recursos do Gemini 2.5 Flash
        
        Documentação:
        - Thinking: https://ai.google.dev/gemini-api/docs/thinking
        - Google Search: https://ai.google.dev/gemini-api/docs/google-search
        - Code Execution: https://ai.google.dev/gemini-api/docs/code-execution
        
        Args:
            message: Mensagem do usuário
            tipo_usuario: Tipo (participante, orientador, visitante)
            history: Histórico de conversas (list de dicts com 'role' e 'parts')
            usar_pesquisa: Habilita Google Search (FREE: 500 RPD)
            usar_code_execution: Habilita execução de código Python
        
        Returns:
            dict: {
                'response': str,
                'thinking_process': str ou None,
                'search_used': bool,
                'code_executed': bool
            }
        """
        try:
            # System instruction + contexto da Bragantec
            system_instruction = self._get_system_instruction(tipo_usuario)
            
            # ✅ OTIMIZAÇÃO: Coloca conteúdo grande no INÍCIO
            # Isso aumenta chance de cache implícito (FREE tier)
            # Ref: https://ai.google.dev/gemini-api/docs/caching
            full_context = f"{system_instruction}\n\n{self.context_files}"
            full_message = f"{full_context}\n\n=== MENSAGEM DO USUÁRIO ===\n{message}"
            
            # Configuração de ferramentas
            tools = []
            
            if usar_pesquisa:
                # Documentação: https://ai.google.dev/gemini-api/docs/google-search
                tools.append(types.Tool(google_search=types.GoogleSearch()))
                print("🔍 Google Search habilitado (FREE: 500 RPD)")
            
            if usar_code_execution:
                # Documentação: https://ai.google.dev/gemini-api/docs/code-execution
                tools.append(types.Tool(code_execution=types.ToolCodeExecution()))
                print("🐍 Code Execution habilitado")
            
            # Configuração completa
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=65536,  # ✅ CORRETO: Gemini 2.5 Flash limit
                tools=tools if tools else None,
                safety_settings=self.safety_settings,
                # Thinking Mode com orçamento dinâmico
                # Ref: https://ai.google.dev/gemini-api/docs/thinking
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,  # -1 = dinâmico (recomendado)
                    include_thoughts=True  # Incluir resumos de pensamento
                )
            )
            
            # Prepara conteúdo (histórico + mensagem atual)
            contents = []
            
            # Adiciona histórico
            if history:
                for msg in history:
                    contents.append(msg['parts'][0])
            
            # Adiciona mensagem atual
            contents.append(full_message)
            
            # Gera resposta
            print("🚀 Gerando resposta com Thinking Mode...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # Extração de dados da resposta
            thinking_process = None
            response_text = ""
            code_executed = False
            
            # Processa todas as partes da resposta
            for part in response.candidates[0].content.parts:
                # Thinking process (processo de pensamento da IA)
                if part.thought:
                    thinking_process = part.text
                    print(f"💭 Thinking detectado: {len(thinking_process)} chars")
                
                # Código executado
                elif hasattr(part, 'executable_code'):
                    code_executed = True
                    print(f"🐍 Código executado: {part.executable_code.code[:100]}...")
                
                # Resultado de código
                elif hasattr(part, 'code_execution_result'):
                    print(f"✅ Resultado do código disponível")
                
                # Texto normal (resposta final)
                elif part.text and not part.thought:
                    response_text += part.text
            
            # Verifica se usou Google Search
            search_used = False
            if hasattr(response.candidates[0], 'grounding_metadata'):
                grounding = response.candidates[0].grounding_metadata
                if grounding and hasattr(grounding, 'web_search_queries'):
                    search_used = len(grounding.web_search_queries) > 0
                    if search_used:
                        print(f"🔍 Usou Google Search: {grounding.web_search_queries}")
            
            # Log de usage (incluindo cache implícito)
            if hasattr(response, 'usage_metadata'):
                print(f"📊 Tokens - Input: {response.usage_metadata.prompt_token_count}")
                print(f"📊 Tokens - Output: {response.usage_metadata.candidates_token_count}")
                
                # Cache implícito (automático no Gemini 2.5)
                if hasattr(response.usage_metadata, 'cached_content_token_count'):
                    cached = response.usage_metadata.cached_content_token_count
                    if cached > 0:
                        print(f"💾 Cache IMPLÍCITO usado: {cached} tokens economizados!")
            
            result = {
                'response': response_text or response.text,
                'thinking_process': thinking_process,
                'search_used': search_used,
                'code_executed': code_executed
            }
            
            print(f"✅ Resposta pronta: {len(result['response'])} chars")
            return result
            
        except Exception as e:
            print(f"❌ Erro no Gemini: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                'response': f"Erro ao processar mensagem: {str(e)}",
                'thinking_process': None,
                'error': True,
                'search_used': False,
                'code_executed': False
            }
    
    def upload_file(self, file_path):
        """
        Upload de arquivo usando File API NOVA
        
        Documentação: https://ai.google.dev/api/files
        
        Suporta: imagens, vídeos, áudio, documentos (PDF, TXT, etc)
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            File object ou None em caso de erro
        """
        try:
            print(f"📤 Fazendo upload: {file_path}")
            
            # ✅ API NOVA: client.files.upload (não genai.upload_file)
            with open(file_path, 'rb') as f:
                uploaded_file = self.client.files.upload(file=f)
            
            print(f"✅ Upload concluído: {uploaded_file.display_name}")
            print(f"   URI: {uploaded_file.uri}")
            print(f"   MIME: {uploaded_file.mime_type}")
            
            # Aguarda processamento (importante para vídeos)
            while uploaded_file.state.name == "PROCESSING":
                print("⏳ Processando arquivo...")
                time.sleep(2)
                uploaded_file = self.client.files.get(name=uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise ValueError(f"Falha no processamento: {uploaded_file.error}")
            
            print(f"✅ Arquivo pronto para uso!")
            return uploaded_file
            
        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            return None
    
    def chat_with_file(self, message, file_path, tipo_usuario='participante'):
        """
        Chat com arquivo anexado (multimodal)
        
        Suporta: imagens, vídeos, áudio, documentos (PDF, DOC, TXT, etc)
        
        Args:
            message: Mensagem do usuário
            file_path: Caminho do arquivo
            tipo_usuario: Tipo do usuário
        
        Returns:
            dict com response e thinking_process
        """
        try:
            # Upload do arquivo
            uploaded_file = self.upload_file(file_path)
            if not uploaded_file:
                return {'response': 'Erro ao fazer upload do arquivo', 'error': True}
            
            # Detecta tipo de arquivo
            mime = uploaded_file.mime_type.lower()
            if 'image' in mime:
                file_type = 'imagem'
            elif 'video' in mime:
                file_type = 'vídeo'
            elif 'audio' in mime:
                file_type = 'áudio'
            else:
                file_type = 'documento'
            
            print(f"🔍 Analisando {file_type}...")
            
            # System instruction
            system_instruction = self._get_system_instruction(tipo_usuario)
            full_message = f"{system_instruction}\n\n{self.context_files}\n\n{message}"
            
            # Configuração
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=65536,
                safety_settings=self.safety_settings,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,
                    include_thoughts=True
                )
            )
            
            # Gera resposta com arquivo
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[full_message, uploaded_file],
                config=config
            )
            
            # Extrai thinking e resposta
            thinking_process = None
            response_text = ""
            
            for part in response.candidates[0].content.parts:
                if part.thought:
                    thinking_process = part.text
                elif part.text:
                    response_text += part.text
            
            # Deleta arquivo temporário (economia de espaço)
            self.client.files.delete(name=uploaded_file.name)
            print("🗑️ Arquivo temporário deletado")
            
            return {
                'response': response_text or response.text,
                'thinking_process': thinking_process,
                'file_type': file_type
            }
            
        except Exception as e:
            print(f"❌ Erro ao processar arquivo: {e}")
            return {
                'response': f"Erro ao processar arquivo: {str(e)}",
                'error': True
            }
    
    def generate_structured_output(self, prompt, schema_dict):
        """
        Gera saída estruturada em JSON com schema
        
        Documentação: https://ai.google.dev/gemini-api/docs/structured-output
        
        Args:
            prompt: Prompt para IA
            schema_dict: Dict com schema (será convertido para types.Schema)
                Exemplo: {
                    'type': 'OBJECT',
                    'properties': {
                        'titulo': {'type': 'STRING'},
                        'categoria': {'type': 'STRING'}
                    },
                    'required': ['titulo']
                }
        
        Returns:
            dict: {'success': bool, 'data': dict ou 'error': str}
        """
        try:
            print("📋 Gerando JSON estruturado...")
            
            # Converte dict para types.Schema
            def dict_to_schema(d):
                if d['type'] == 'OBJECT':
                    props = {}
                    for key, value in d.get('properties', {}).items():
                        props[key] = dict_to_schema(value)
                    
                    return types.Schema(
                        type=types.Type.OBJECT,
                        properties=props,
                        required=d.get('required', [])
                    )
                elif d['type'] == 'STRING':
                    return types.Schema(type=types.Type.STRING)
                elif d['type'] == 'NUMBER':
                    return types.Schema(type=types.Type.NUMBER)
                elif d['type'] == 'INTEGER':
                    return types.Schema(type=types.Type.INTEGER)
                elif d['type'] == 'BOOLEAN':
                    return types.Schema(type=types.Type.BOOLEAN)
                elif d['type'] == 'ARRAY':
                    return types.Schema(
                        type=types.Type.ARRAY,
                        items=dict_to_schema(d.get('items', {'type': 'STRING'}))
                    )
                else:
                    return types.Schema(type=types.Type.STRING)
            
            schema = dict_to_schema(schema_dict)
            
            # Config
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                max_output_tokens=65536
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            # Parse JSON
            import json
            result = json.loads(response.text)
            print(f"✅ JSON gerado com sucesso")
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            print(f"❌ Erro em structured output: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def count_tokens(self, text):
        """
        Conta tokens de um texto
        
        Útil para verificar limites antes de enviar
        
        Args:
            text: Texto para contar
        
        Returns:
            int: Número de tokens (aproximado)
        """
        try:
            # Workaround: gera com output mínimo para pegar contagem
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=types.GenerateContentConfig(
                    max_output_tokens=1
                )
            )
            
            # Pega do usage_metadata
            if hasattr(response, 'usage_metadata'):
                return response.usage_metadata.prompt_token_count
            
            return 0
        except Exception as e:
            print(f"⚠️ Erro ao contar tokens: {e}")
            # Fallback: estimativa grosseira (1 token ≈ 4 caracteres)
            return len(text) // 4