"""
Serviço CORRETO para Gemini 2.5 Flash
Usa a biblioteca NOVA: google-genai (GA desde maio 2025)
Baseado na documentação oficial de outubro 2025
"""

from google import genai
from google.genai import types
import os
from config import Config

class GeminiService:
    """Serviço Gemini usando a API NOVA e CORRETA"""
    
    def __init__(self):
        """Inicializa o cliente Gemini"""
        # Cliente usando a NOVA API
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        self.model_name = 'gemini-2.5-flash'
        self.context_files = self._load_context_files()
        
        # Safety Settings DESABILITADOS (como solicitado)
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
        print("✅ GeminiService iniciado (biblioteca google-genai)")
        print(f"✅ Modelo: {self.model_name}")
        print(f"✅ Safety: DESABILITADO (BLOCK_NONE)")
        print(f"✅ Rate Limits FREE: 10 RPM, 250k TPM, 250 RPD")
        print(f"✅ Output Limit: 65.536 tokens")
        print("="*60)
    
    def _load_context_files(self):
        """Carrega arquivos de contexto da Bragantec"""
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
            "- Analisar imagens, vídeos e documentos\n"
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
        
        Args:
            message: Mensagem do usuário
            tipo_usuario: Tipo (participante, orientador, visitante)
            history: Histórico de conversas
            usar_pesquisa: Habilita Google Search (FREE: 500 RPD)
            usar_code_execution: Habilita execução de código Python
        
        Returns:
            dict com response, thinking_process, search_used, code_executed
        """
        try:
            # System instruction
            system_instruction = self._get_system_instruction(tipo_usuario)
            full_context = f"{system_instruction}\n\n{self.context_files}"
            
            # Monta mensagem com contexto
            full_message = f"{full_context}\n\n=== MENSAGEM DO USUÁRIO ===\n{message}"
            
            # Configuração de ferramentas
            tools = []
            if usar_pesquisa:
                tools.append('google_search_retrieval')
                print("🔍 Google Search habilitado (FREE: 500 RPD)")
            
            if usar_code_execution:
                tools.append('code_execution')
                print("🐍 Code Execution habilitado")
            
            # Configuração completa
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=65536,  # ✅ CORRETO: 65.536
                tools=tools if tools else None,
                safety_settings=self.safety_settings,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True  # Sempre incluir pensamentos
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
            print("🚀 Gerando resposta com Thinking Mode...")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # Extração de dados
            thinking_process = None
            response_text = ""
            code_executed = False
            
            for part in response.candidates[0].content.parts:
                # Thinking process
                if part.thought:
                    thinking_process = part.text
                    print(f"💭 Thinking detectado: {len(thinking_process)} chars")
                
                # Código executado
                elif hasattr(part, 'executable_code'):
                    code_executed = True
                    print(f"🐍 Código executado")
                
                # Resultado de código
                elif hasattr(part, 'code_execution_result'):
                    print(f"✅ Resultado do código disponível")
                
                # Texto normal
                elif part.text and not part.thought:
                    response_text += part.text
            
            # Verifica Google Search
            search_used = False
            if hasattr(response.candidates[0], 'grounding_metadata'):
                grounding = response.candidates[0].grounding_metadata
                if grounding and hasattr(grounding, 'web_search_queries'):
                    search_used = len(grounding.web_search_queries) > 0
                    if search_used:
                        print(f"🔍 Usou Google Search: {grounding.web_search_queries}")
            
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
                'response': f"Erro: {str(e)}",
                'thinking_process': None,
                'error': True,
                'search_used': False,
                'code_executed': False
            }
    
    def upload_file(self, file_path):
        """
        Upload de arquivo usando File API
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            File object
        """
        try:
            print(f"📤 Fazendo upload: {file_path}")
            
            # Upload usando NOVA API
            with open(file_path, 'rb') as f:
                uploaded_file = self.client.files.upload(file=f)
            
            print(f"✅ Upload concluído: {uploaded_file.display_name}")
            
            # Aguarda processamento (importante para vídeos)
            import time
            while uploaded_file.state.name == "PROCESSING":
                print("⏳ Processando arquivo...")
                time.sleep(2)
                uploaded_file = self.client.files.get(name=uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise ValueError(f"Falha: {uploaded_file.error}")
            
            print(f"✅ Arquivo pronto!")
            return uploaded_file
            
        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            return None
    
    def chat_with_file(self, message, file_path, tipo_usuario='participante'):
        """
        Chat com arquivo anexado (multimodal)
        
        Args:
            message: Mensagem do usuário
            file_path: Caminho do arquivo
            tipo_usuario: Tipo do usuário
        
        Returns:
            dict com response
        """
        try:
            # Upload do arquivo
            uploaded_file = self.upload_file(file_path)
            if not uploaded_file:
                return {'response': 'Erro ao fazer upload', 'error': True}
            
            # System instruction
            system_instruction = self._get_system_instruction(tipo_usuario)
            full_message = f"{system_instruction}\n\n{self.context_files}\n\n{message}"
            
            # Configuração
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=65536,
                safety_settings=self.safety_settings,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True
                )
            )
            
            # Gera resposta com arquivo
            print(f"🎬 Processando arquivo multimodal...")
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
            
            # Deleta arquivo temporário
            self.client.files.delete(name=uploaded_file.name)
            print("🗑️ Arquivo temporário deletado")
            
            return {
                'response': response_text or response.text,
                'thinking_process': thinking_process
            }
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return {
                'response': f"Erro: {str(e)}",
                'error': True
            }
    
    def generate_structured_output(self, prompt, schema_dict):
        """
        Gera saída estruturada em JSON
        
        Args:
            prompt: Prompt para IA
            schema_dict: Dict com schema (será convertido para types.Schema)
        
        Returns:
            dict parseado
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
            print(f"✅ JSON gerado: {len(result)} items")
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def count_tokens(self, text):
        """
        Conta tokens de um texto
        
        Args:
            text: Texto para contar
        
        Returns:
            int: Número de tokens
        """
        try:
            # Nova API não tem método direto para count tokens
            # Workaround: usar o modelo
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=text,
                config=types.GenerateContentConfig(
                    max_output_tokens=1  # Mínimo para apenas contar
                )
            )
            
            # Pega do usage_metadata
            if hasattr(response, 'usage_metadata'):
                return response.usage_metadata.prompt_token_count
            
            return 0
        except Exception as e:
            print(f"⚠️ Erro ao contar tokens: {e}")
            return 0