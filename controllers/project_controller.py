from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from dao.dao import SupabaseDAO
from services.gemini_service import GeminiService
from datetime import datetime
import json

project_bp = Blueprint('project', __name__, url_prefix='/projetos')
dao = SupabaseDAO()
gemini = GeminiService()

@project_bp.route('/')
@login_required
def index():
    """Lista todos os projetos do usuário"""
    projetos = dao.listar_projetos_por_usuario(current_user.id)
    return render_template('projetos/index.html', projetos=projetos)

@project_bp.route('/novo')
@login_required
def novo():
    """Página para criar novo projeto"""
    return render_template('projetos/criar.html')

@project_bp.route('/editar/<int:projeto_id>')
@login_required
def editar(projeto_id):
    """Página para editar projeto"""
    projeto = dao.buscar_projeto_por_id(projeto_id)
    
    if not projeto:
        return "Projeto não encontrado", 404
    
    # Verifica se o usuário tem permissão
    # TODO: Implementar verificação de permissão
    
    return render_template('projetos/editar.html', projeto=projeto)

@project_bp.route('/criar', methods=['POST'])
@login_required
def criar():
    """Cria um novo projeto"""
    try:
        data = request.json
        
        # Cria projeto no banco
        projeto = dao.criar_projeto_completo(
            nome=data.get('nome'),
            categoria=data.get('categoria'),
            resumo=data.get('resumo'),
            palavras_chave=data.get('palavras_chave'),
            introducao=data.get('introducao'),
            objetivo_geral=data.get('objetivo_geral'),
            objetivos_especificos=data.get('objetivos_especificos', []),
            metodologia=data.get('metodologia'),
            cronograma=data.get('cronograma'),
            resultados_esperados=data.get('resultados_esperados'),
            referencias_bibliograficas=data.get('referencias_bibliograficas'),
            eh_continuacao=data.get('eh_continuacao', False),
            projeto_anterior_titulo=data.get('projeto_anterior_titulo'),
            projeto_anterior_resumo=data.get('projeto_anterior_resumo'),
            projeto_anterior_inicio=data.get('projeto_anterior_inicio'),
            projeto_anterior_termino=data.get('projeto_anterior_termino'),
            status=data.get('status', 'rascunho'),
            ano_edicao=data.get('ano_edicao', datetime.now().year),
            gerado_por_ia=data.get('gerado_por_ia', False),
            prompt_ia_usado=data.get('prompt_ia_usado')
        )
        
        # Associa projeto ao participante
        dao.associar_participante_projeto(current_user.id, projeto.id)
        
        return jsonify({
            'success': True,
            'message': 'Projeto criado com sucesso!',
            'projeto': projeto.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao criar projeto: {str(e)}'
        }), 500

@project_bp.route('/atualizar/<int:projeto_id>', methods=['PUT'])
@login_required
def atualizar(projeto_id):
    """Atualiza projeto existente"""
    try:
        data = request.json
        
        projeto = dao.atualizar_projeto(projeto_id, **data)
        
        return jsonify({
            'success': True,
            'message': 'Projeto atualizado!',
            'projeto': projeto.to_dict() if projeto else None
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao atualizar: {str(e)}'
        }), 500

@project_bp.route('/gerar-ideias', methods=['POST'])
@login_required
def gerar_ideias():
    """
    ✅ GERADOR DE IDEIAS COM MODO BRAGANTEC OBRIGATÓRIO
    
    Analisa projetos vencedores das edições anteriores da Bragantec
    para criar 4 novas ideias com ALTO POTENCIAL DE VITÓRIA
    """
    try:
        # ✅ Prompt AVANÇADO que analisa projetos vencedores
        prompt = """
        🎯 **MISSÃO CRÍTICA: CRIAR PROJETOS VENCEDORES PARA A BRAGANTEC 2025**

        Você tem acesso ao histórico COMPLETO das edições anteriores da Bragantec (feira de ciências do IFSP Bragança Paulista), incluindo cadernos de resumos com TODOS os projetos vencedores.

        **ANÁLISE OBRIGATÓRIA ANTES DE CRIAR:**
        
        1. **ESTUDE OS PROJETOS VENCEDORES** nos arquivos de contexto que você possui
        2. **IDENTIFIQUE PADRÕES DE SUCESSO:**
           - Que temas/abordagens venceram mais?
           - Quais características os projetos premiados têm em comum?
           - Que nível de complexidade/inovação foi valorizado?
           - Quais problemas reais foram abordados?
           - Que metodologias foram bem avaliadas?
        
        3. **EXTRAIA INSIGHTS DOS VENCEDORES:**
           - Títulos: Como eram formulados?
           - Relevância: Que impacto social/científico tinham?
           - Inovação: O que os diferenciava?
           - Viabilidade: Eram projetos executáveis por estudantes?
        
        4. **ENTENDA OS CRITÉRIOS DE AVALIAÇÃO:**
           - **Inovação e criatividade** (30 pontos)
           - **Relevância científica/social** (25 pontos)
           - **Fundamentação teórica** (20 pontos)
           - **Viabilidade de execução** (15 pontos)
           - **Impacto potencial** (10 pontos)

        ---

        **AGORA CRIE 4 IDEIAS DE PROJETOS (UMA POR CATEGORIA):**

        Com base na sua análise dos projetos vencedores das edições anteriores da Bragantec, crie UMA ideia de projeto para CADA uma das 4 categorias:

        1. **Ciências da Natureza e Exatas**
        2. **Informática**
        3. **Ciências Humanas e Linguagens**
        4. **Engenharias**

        **REQUISITOS PARA CADA PROJETO:**

        ✅ **DEVE SER INSPIRADO EM PROJETOS VENCEDORES ANTERIORES** (mas não cópia!)
        ✅ **DEVE ABORDAR PROBLEMAS REAIS E ATUAIS DE 2025**
        ✅ **DEVE SER INOVADOR** (trazer algo novo ou melhorado)
        ✅ **DEVE SER VIÁVEL** para estudantes de ensino médio/técnico executarem
        ✅ **DEVE TER IMPACTO** científico, social ou ambiental mensurável
        ✅ **DEVE TER FUNDAMENTAÇÃO TEÓRICA** sólida

        ---

        **PARA CADA CATEGORIA, FORNEÇA:**

        - **titulo**: Título atrativo, direto e científico (máx 80 caracteres)
          * Exemplo de títulos vencedores: específicos, técnicos, com termos científicos
        
        - **resumo**: Resumo executivo COMPLETO E PROFISSIONAL (200-250 palavras) contendo:
          * **Introdução**: Contexto e problema (2-3 frases)
          * **Objetivos**: O que o projeto pretende alcançar (1-2 frases)
          * **Metodologia**: Como será desenvolvido - materiais, métodos (3-4 frases)
          * **Resultados Esperados**: Impactos e conclusões esperadas (2-3 frases)
          * **Relevância**: Por que é importante (1-2 frases)
        
        - **palavras_chave**: Exatamente 3 palavras-chave técnicas/científicas separadas por vírgula
          * Use termos que projetos vencedores usaram
        
        - **inspiracao_vencedores**: Liste 2-3 características de projetos vencedores que inspiraram esta ideia
          * Exemplo: "Baseado no padrão de projetos premiados que abordam sustentabilidade com tecnologia IoT"
        
        - **diferenciais_competitivos**: O que torna este projeto um VENCEDOR POTENCIAL (máx 150 palavras)
          * Compare com projetos vencedores anteriores
          * Explique por que este seria bem avaliado pelos jurados
        
        - **viabilidade_tecnica**: Nível de dificuldade e recursos necessários (máx 100 palavras)
          * Seja realista sobre o que estudantes podem fazer

        ---

        **FORMATO DE SAÍDA (JSON ESTRITO):**

        Retorne APENAS um JSON válido (sem texto adicional) no formato:

        ```json
        {
          "Ciências da Natureza e Exatas": {
            "titulo": "...",
            "resumo": "...",
            "palavras_chave": "palavra1, palavra2, palavra3",
            "inspiracao_vencedores": "...",
            "diferenciais_competitivos": "...",
            "viabilidade_tecnica": "..."
          },
          "Informática": {
            "titulo": "...",
            "resumo": "...",
            "palavras_chave": "palavra1, palavra2, palavra3",
            "inspiracao_vencedores": "...",
            "diferenciais_competitivos": "...",
            "viabilidade_tecnica": "..."
          },
          "Ciências Humanas e Linguagens": {
            "titulo": "...",
            "resumo": "...",
            "palavras_chave": "palavra1, palavra2, palavra3",
            "inspiracao_vencedores": "...",
            "diferenciais_competitivos": "...",
            "viabilidade_tecnica": "..."
          },
          "Engenharias": {
            "titulo": "...",
            "resumo": "...",
            "palavras_chave": "palavra1, palavra2, palavra3",
            "inspiracao_vencedores": "...",
            "diferenciais_competitivos": "...",
            "viabilidade_tecnica": "..."
          }
        }
        ```

        **LEMBRE-SE:**
        - Você tem acesso aos cadernos de resumos das edições anteriores da Bragantec
        - USE esse conhecimento para criar projetos com padrões de sucesso comprovados
        - Não copie projetos, mas INSPIRE-SE nos elementos que fizeram eles vencerem
        - Pense como um jurado: O que ME impressionaria neste projeto?

        **NÃO ADICIONE TEXTO EXPLICATIVO. RETORNE APENAS O JSON.**
        """
        
        # ✅ MODO BRAGANTEC OBRIGATÓRIO - Usa conhecimento histórico completo
        print("🎯 Gerando ideias com análise COMPLETA dos projetos vencedores anteriores...")
        print("⚠️ Modo Bragantec FORÇADO (consome ~100k-200k tokens de input)")
        
        response = gemini.chat(
            prompt, 
            tipo_usuario='participante',
            usar_contexto_bragantec=True,  # ✅ OBRIGATÓRIO - Acessa histórico completo
            usar_pesquisa=False,  # Não precisa buscar na web, temos os arquivos
            usar_code_execution=False,  # Não precisa executar código
            user_id=current_user.id
        )
        
        if response.get('error'):
            return jsonify({
                'error': True,
                'message': 'Erro ao gerar ideias com IA'
            }), 500
        
        # ✅ Tenta parsear a resposta como JSON
        ideias_text = response['response']
        
        try:
            # Remove possíveis blocos de código markdown
            if '```json' in ideias_text:
                ideias_text = ideias_text.split('```json')[1].split('```')[0].strip()
            elif '```' in ideias_text:
                ideias_text = ideias_text.split('```')[1].split('```')[0].strip()
            
            # Parse JSON
            ideias = json.loads(ideias_text)
            
            # ✅ Valida estrutura e adiciona metadados
            categorias_esperadas = [
                "Ciências da Natureza e Exatas",
                "Informática",
                "Ciências Humanas e Linguagens",
                "Engenharias"
            ]
            
            for categoria in categorias_esperadas:
                if categoria not in ideias:
                    raise ValueError(f"Categoria '{categoria}' não encontrada")
                
                ideia = ideias[categoria]
                campos_obrigatorios = ['titulo', 'resumo', 'palavras_chave']
                
                for campo in campos_obrigatorios:
                    if campo not in ideia:
                        raise ValueError(f"Campo '{campo}' não encontrado em '{categoria}'")
                
                # ✅ Adiciona metadado de que foi gerado com análise de vencedores
                ideia['gerado_com_analise_vencedores'] = True
                ideia['ano_geracao'] = 2025
            
            # ✅ Retorna ideias estruturadas COM metadados
            return jsonify({
                'success': True,
                'ideias': ideias,
                'formato': 'json',
                'metadata': {
                    'analise_vencedores': True,
                    'modo_bragantec': True,
                    'contexto_usado': 'Cadernos de resumos das edições anteriores',
                    'aviso_tokens': 'Esta operação consumiu ~100k-200k tokens (contexto histórico completo)'
                }
            })
            
        except (json.JSONDecodeError, ValueError) as e:
            # ✅ Fallback: Se não conseguir parsear, retorna texto bruto
            print(f"⚠️ Erro ao parsear JSON: {e}")
            print(f"📄 Resposta bruta: {ideias_text[:500]}")
            
            return jsonify({
                'success': True,
                'ideias': ideias_text,
                'formato': 'texto',
                'aviso': 'A IA não retornou JSON estruturado. Exibindo texto bruto.'
            })
        
    except Exception as e:
        import traceback
        print(f"❌ Erro ao gerar ideias: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'error': True,
            'message': f'Erro ao gerar ideias: {str(e)}'
        }), 500

@project_bp.route('/autocompletar', methods=['POST'])
@login_required
def autocompletar():
    """
    ✅ CORRIGIDO: IA preenche campos do projeto automaticamente
    Retorna JSON estruturado com campos específicos
    """
    try:
        data = request.json
        campos = data.get('campos', [])  # Lista de campos a preencher
        projeto_parcial = data.get('projeto', {})  # Dados já preenchidos
        
        if not campos:
            return jsonify({'error': True, 'message': 'Nenhum campo selecionado'}), 400
        
        # ✅ Prepara dados do projeto para contexto
        nome = projeto_parcial.get('nome', 'Não informado')
        categoria = projeto_parcial.get('categoria', 'Não informado')
        resumo = projeto_parcial.get('resumo', 'Não informado')
        palavras_chave = projeto_parcial.get('palavras_chave', 'Não informado')
        
        # ✅ Monta prompt dinâmico baseado nos campos solicitados
        campos_str = ', '.join(campos)
        
        prompt = f"""
        Você é um especialista em projetos científicos para a Bragantec (feira de ciências do IFSP).

        Com base nas informações parciais do projeto abaixo, complete APENAS os seguintes campos: {campos_str}

        **INFORMAÇÕES DO PROJETO:**
        - Título: {nome}
        - Categoria: {categoria}
        - Resumo: {resumo}
        - Palavras-chave: {palavras_chave}

        **INSTRUÇÕES:**
        1. Gere conteúdo profissional, acadêmico e adequado para feira de ciências
        2. Use linguagem científica mas acessível para estudantes de ensino médio
        3. Baseie-se nos critérios de avaliação da Bragantec
        4. Retorne APENAS um JSON válido no formato:

        {{
          "introducao": "texto da introdução (se solicitado)...",
          "objetivo_geral": "texto do objetivo geral (se solicitado)...",
          "metodologia": "texto da metodologia (se solicitado)...",
          "resultados_esperados": "texto dos resultados (se solicitado)..."
        }}

        **IMPORTANTE**:
        - Inclua APENAS os campos que foram solicitados: {campos_str}
        - NÃO adicione texto explicativo antes ou depois do JSON
        - Retorne APENAS o JSON válido
        - Se o campo for "objetivos", inclua "objetivo_geral" no JSON

        **REFERÊNCIAS PARA CADA CAMPO**:

        - **introducao**: Apresente o tema, contextualize sua relevância, mencione a fundamentação teórica. Responda: Qual o problema? Por que é importante? O que já se sabe sobre o tema? (250-400 palavras)

        - **objetivo_geral**: Descreva a finalidade principal do projeto usando verbo no infinitivo (desenvolver, analisar, comparar, investigar, propor). Deve ser claro, específico e alcançável. (1-2 frases)

        - **metodologia**: Detalhe materiais, métodos, procedimentos experimentais, equipamentos, tipo de pesquisa, dados a coletar, como será desenvolvido. Seja específico mas didático. (300-500 palavras)

        - **resultados_esperados**: Descreva as expectativas científicas, técnicas ou sociais do projeto quando finalizado. Quais conclusões espera obter? Qual o impacto potencial? (200-300 palavras)
        """
        
        # Chama Gemini
        response = gemini.chat(
            prompt, 
            tipo_usuario='participante',
            user_id=current_user.id
        )
        
        if response.get('error'):
            return jsonify({'error': True, 'message': 'Erro ao autocompletar'}), 500
        
        # ✅ Tenta parsear resposta como JSON
        try:
            conteudo_text = response['response']
            
            # Remove blocos markdown
            if '```json' in conteudo_text:
                conteudo_text = conteudo_text.split('```json')[1].split('```')[0].strip()
            elif '```' in conteudo_text:
                conteudo_text = conteudo_text.split('```')[1].split('```')[0].strip()
            
            conteudo = json.loads(conteudo_text)
            
            return jsonify({
                'success': True,
                'conteudo': conteudo,
                'formato': 'json'
            })
            
        except json.JSONDecodeError:
            # Fallback: retorna texto bruto
            print(f"⚠️ Erro ao parsear JSON do autocompletar")
            
            return jsonify({
                'success': True,
                'conteudo': {'texto': response['response']},
                'formato': 'texto'
            })
        
    except Exception as e:
        import traceback
        print(f"❌ Erro ao autocompletar: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500

@project_bp.route('/gerar-pdf/<int:projeto_id>')
@login_required
def gerar_pdf(projeto_id):
    """Gera PDF do plano de pesquisa"""
    try:
        from services.pdf_service import BragantecPDFGenerator
        from flask import send_file
        
        projeto = dao.buscar_projeto_por_id(projeto_id)
        
        if not projeto:
            return "Projeto não encontrado", 404
        
        # Gera PDF
        pdf_generator = BragantecPDFGenerator(projeto, current_user)
        pdf_buffer = pdf_generator.gerar()
        
        # Nome do arquivo
        filename = f"Plano_Pesquisa_{projeto.nome.replace(' ', '_')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        import traceback
        print(f"❌ Erro ao gerar PDF: {e}")
        print(traceback.format_exc())
        
        return jsonify({
            'error': True,
            'message': f'Erro ao gerar PDF: {str(e)}'
        }), 500

@project_bp.route('/deletar/<int:projeto_id>', methods=['DELETE'])
@login_required
def deletar(projeto_id):
    """Deleta um projeto"""
    try:
        dao.deletar_projeto(projeto_id)
        
        return jsonify({
            'success': True,
            'message': 'Projeto deletado!'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500