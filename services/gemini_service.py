import google.generativeai as genai
from config import Config
import os

class GeminiService:
    """Serviço para integração com Google Gemini 2.5 Flash"""
    
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        self.context_files = self._load_context_files()
    
    def _load_context_files(self):
        """Carrega arquivos de contexto da Bragantec"""
        context_content = []
        context_path = Config.CONTEXT_FILES_PATH
        
        if os.path.exists(context_path):
            for filename in os.listdir(context_path):
                if filename.endswith('.txt'):
                    filepath = os.path.join(context_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            context_content.append(f"=== {filename} ===\n{content}\n")
                    except Exception as e:
                        print(f"Erro ao carregar {filename}: {e}")
        
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
                "\nVocê está conversando com um PARTICIPANTE da Bragantec. "
                "Foque em ajudá-lo a desenvolver seu projeto, superar desafios práticos, "
                "e preparar sua apresentação. Seja especialmente encorajador!"
            )
        elif tipo_usuario == 'orientador':
            return base_instruction + (
                "\nVocê está conversando com um ORIENTADOR. "
                "Forneça insights pedagógicos, estratégias de mentoria, "
                "e sugestões para guiar múltiplos projetos simultaneamente."
            )
        else:
            return base_instruction
    
    def chat(self, message, tipo_usuario='participante', history=None, usar_pesquisa=True):
        """
        Envia mensagem para o Gemini e retorna resposta
        
        Args:
            message: Mensagem do usuário
            tipo_usuario: Tipo do usuário (participante, orientador, etc)
            history: Histórico de conversas (lista de dicts com 'role' e 'parts')
            usar_pesquisa: Se True, habilita Google Search
        
        Returns:
            dict com 'response', 'thinking_process' e 'search_used'
        """
        try:
            # Prepara o contexto completo
            full_message = f"""
            CONTEXTO DA BRAGANTEC:
            {self.context_files}
            
            ===================================
            MENSAGEM DO USUÁRIO:
            {message}
            """
            
            # Configura generation config
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            # Configura ferramentas (Google Search)
            tools = None
            if usar_pesquisa:
                # Habilita Google Search conforme documentação
                tools = ["google_search_retrieval"]
            
            # Cria chat com histórico se fornecido
            if history:
                chat = self.model.start_chat(history=history)
                response = chat.send_message(
                    full_message,
                    generation_config=generation_config,
                    tools=tools
                )
            else:
                # Primeira mensagem com system instruction
                chat = self.model.start_chat()
                system_msg = self._get_system_instruction(tipo_usuario)
                response = chat.send_message(
                    f"{system_msg}\n\n{full_message}",
                    generation_config=generation_config,
                    tools=tools
                )
            
            # Extrai resposta
            result = {
                'response': response.text,
                'thinking_process': None,
                'search_used': usar_pesquisa
            }
            
            # Tenta extrair thinking process se disponível
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'thought') and part.thought:
                            result['thinking_process'] = part.thought
                            break
            
            return result
            
        except Exception as e:
            return {
                'response': f"Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente. Detalhes: {str(e)}",
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
            uploaded_file = genai.upload_file(file_path)
            return uploaded_file
        except Exception as e:
            print(f"Erro ao fazer upload: {e}")
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
            
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
            
            response = self.model.generate_content(
                [full_message, uploaded_file],
                generation_config=generation_config
            )
            
            return {
                'response': response.text,
                'thinking_process': None
            }
            
        except Exception as e:
            return {
                'response': f"Erro ao processar arquivo: {str(e)}",
                'error': True
            }