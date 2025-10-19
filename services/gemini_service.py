"""
Serviço CORRIGIDO para integração com Google Gemini 2.5 Flash
- Google Search funcionando (google_search, não google_search_retrieval)
- Thinking Mode extraído corretamente
- Baseado na documentação oficial de 2025
"""

import google.generativeai as genai
from google.genai import types
from config import Config
import os

class GeminiService:
    """Serviço para integração com Google Gemini 2.5 Flash"""
    
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        # Usa a nova API do Gemini
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        
        self.model_name = Config.GEMINI_MODEL
        self.context_files = self._load_context_files()
    
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
            
            "Sua personalidade deve ser:\n"
            "- Amigável e acessível, como um colega experiente\n"
            "- Encorajadora e positiva\n"
            "- Paciente e didática\n"
            "- Entusiasta por ciência e inovação\n"
            "- Proativa em sugerir ideias e soluções\n\n"
            
            "Suas principais funções são:\n"
            "- Auxiliar no desenvolvimento de projetos científicos\n"
            "- Sugerir ideias inovadoras e viáveis\n"
            "- Ajudar no planejamento e organização de projetos\n"
            "- Esclarecer dúvidas sobre a Bragantec\n"
            "- Fornecer orientação metodológica\n"
            "- Usar Google Search quando precisar de informações atualizadas\n\n"
            
            "Importante:\n"
            "- Use uma linguagem acessível, mas técnica quando necessário\n"
            "- Seja criativo nas sugestões\n"
            "- Incentive o pensamento crítico\n"
            "- Faça perguntas que estimulem a reflexão\n"
            "- Use exemplos práticos sempre que possível\n"
            "- Quando usar Google Search, mencione que consultou fontes atualizadas\n"
        )
        
        if tipo_usuario == 'participante':
            return base_instruction + (
                "\n✨ Você está conversando com um PARTICIPANTE da Bragantec. "
                "Foque em ajudá-lo a desenvolver seu projeto, superar desafios práticos, "
                "e preparar sua apresentação. Seja especialmente encorajador!"
            )
        elif tipo_usuario == 'orientador':
            return base_instruction + (
                "\n👨‍🏫 Você está conversando com um ORIENTADOR. "
                "Forneça insights pedagógicos, estratégias de mentoria, "
                "e sugestões para guiar múltiplos projetos simultaneamente."
            )
        else:
            return base_instruction
    
    def chat(self, message, tipo_usuario='participante', history=None, usar_pesquisa=True):
        """
        Envia mensagem para o Gemini e retorna resposta
        
        ✅ CORRIGIDO: Google Search + Thinking Mode funcionando
        
        Args:
            message: Mensagem do usuário
            tipo_usuario: Tipo do usuário (participante, orientador, etc)
            history: Histórico de conversas no formato correto
            usar_pesquisa: Se True, habilita Google Search
        
        Returns:
            dict com 'response', 'thinking_process', 'search_used'
        """
        try:
            # System instruction
            system_instruction = self._get_system_instruction(tipo_usuario)
            
            # Monta mensagem com contexto
            full_message = f"""
{system_instruction}

===== CONTEXTO DA BRAGANTEC =====
{self.context_files}

===== MENSAGEM DO USUÁRIO =====
{message}
"""
            
            # ✅ CORREÇÃO 1: Google Search CORRETO para Gemini 2.5
            tools = None
            if usar_pesquisa:
                tools = [types.Tool(google_search=types.GoogleSearch())]
            
            # ✅ CORREÇÃO 2: Thinking Config CORRETO
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
                tools=tools,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=-1,  # Pensamento dinâmico
                    include_thoughts=True  # Retorna o processo de pensamento
                )
            )
            
            # Converte histórico para o formato correto se fornecido
            contents = []
            if history:
                for msg in history:
                    contents.append(types.Content(
                        role=msg['role'],
                        parts=[types.Part(text=msg['parts'][0])]
                    ))
            
            # Adiciona mensagem atual
            contents.append(types.Content(
                role='user',
                parts=[types.Part(text=full_message)]
            ))
            
            # ✅ CORREÇÃO 3: Usa a API correta
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            # ✅ CORREÇÃO 4: Extração CORRETA do thinking process
            thinking_process = None
            response_text = ""
            
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                for part in candidate.content.parts:
                    if not part.text:
                        continue
                    
                    # Identifica se é pensamento ou resposta
                    if part.thought:
                        thinking_process = part.text
                    else:
                        response_text += part.text
            
            # Verifica se usou Google Search analisando grounding_metadata
            search_actually_used = False
            if hasattr(response.candidates[0], 'grounding_metadata'):
                grounding = response.candidates[0].grounding_metadata
                if grounding and hasattr(grounding, 'web_search_queries'):
                    search_actually_used = len(grounding.web_search_queries) > 0
            
            result = {
                'response': response_text or response.text,
                'thinking_process': thinking_process,
                'search_used': search_actually_used,
                'grounding_metadata': response.candidates[0].grounding_metadata if hasattr(response.candidates[0], 'grounding_metadata') else None
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Erro no Gemini: {str(e)}")
            return {
                'response': f"Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.\n\nDetalhes técnicos: {str(e)}",
                'thinking_process': None,
                'error': True,
                'search_used': False
            }
    
    def upload_file(self, file_path):
        """
        Faz upload de arquivo para o Gemini processar
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            File object do Gemini
        """
        try:
            # ✅ USA A API CORRETA DE UPLOAD
            uploaded_file = genai.upload_file(file_path)
            print(f"✅ Arquivo enviado: {uploaded_file.display_name}")
            return uploaded_file
        except Exception as e:
            print(f"❌ Erro ao fazer upload: {e}")
            return None
    
    def chat_with_file(self, message, file_path, tipo_usuario='participante'):
        """
        Envia mensagem com arquivo anexado
        
        Args:
            message: Mensagem do usuário
            file_path: Caminho do arquivo
            tipo_usuario: Tipo do usuário
        
        Returns:
            dict com resposta
        """
        try:
            uploaded_file = self.upload_file(file_path)
            if not uploaded_file:
                return {'response': 'Erro ao processar arquivo', 'error': True}
            
            system_instruction = self._get_system_instruction(tipo_usuario)
            full_message = f"{system_instruction}\n\nCONTEXTO:\n{self.context_files}\n\nMENSAGEM:\n{message}"
            
            config = types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=8192,
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True
                )
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role='user',
                        parts=[
                            types.Part(text=full_message),
                            types.Part(file_data=uploaded_file)
                        ]
                    )
                ],
                config=config
            )
            
            # Extrai thinking process
            thinking_process = None
            response_text = ""
            
            for part in response.candidates[0].content.parts:
                if not part.text:
                    continue
                if part.thought:
                    thinking_process = part.text
                else:
                    response_text += part.text
            
            return {
                'response': response_text or response.text,
                'thinking_process': thinking_process
            }
            
        except Exception as e:
            return {
                'response': f"Erro ao processar arquivo: {str(e)}",
                'error': True
            }