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
    """IA gera 4 ideias de projetos (uma por categoria)"""
    try:
        prompt = """
        Com base nas últimas 5 edições da Bragantec e nos projetos vencedores,
        crie UMA ideia de projeto inovador e com alto potencial de vitória para CADA uma das 4 categorias abaixo.
        
        Categorias:
        1. Ciências da Natureza e Exatas
        2. Informática
        3. Ciências Humanas e Linguagens
        4. Engenharias
        
        Para cada categoria, forneça:
        - Título atrativo e direto
        - Resumo executivo (máx 200 palavras)
        - 3 palavras-chave
        - Justificativa (por que tem potencial de ganhar)
        - Diferenciais em relação a projetos anteriores
        
        Baseie-se nos critérios de avaliação da Bragantec:
        - Inovação e criatividade
        - Relevância científica/social
        - Viabilidade de execução
        - Impacto potencial
        - Fundamentação teórica
        
        Retorne em formato JSON estruturado.
        """
        
        response = gemini.chat(prompt, tipo_usuario='participante')
        
        if response.get('error'):
            return jsonify({
                'error': True,
                'message': 'Erro ao gerar ideias'
            }), 500
        
        return jsonify({
            'success': True,
            'ideias': response['response']
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500

@project_bp.route('/autocompletar', methods=['POST'])
@login_required
def autocompletar():
    """IA preenche campos do projeto automaticamente"""
    try:
        data = request.json
        campos = data.get('campos', [])  # Lista de campos a preencher
        projeto_parcial = data.get('projeto', {})  # Dados já preenchidos
        
        if not campos:
            return jsonify({'error': True, 'message': 'Nenhum campo selecionado'}), 400
        
        # Monta prompt dinâmico baseado nos campos
        campos_str = ', '.join(campos)
        
        prompt = f"""
        Com base nas informações parciais do projeto abaixo, complete os seguintes campos: {campos_str}
        
        Dados do projeto:
        Título: {projeto_parcial.get('nome', 'Não informado')}
        Categoria: {projeto_parcial.get('categoria', 'Não informado')}
        Resumo: {projeto_parcial.get('resumo', 'Não informado')}
        
        Gere conteúdo profissional, acadêmico e adequado para a Bragantec.
        Retorne em formato JSON com os campos preenchidos.
        
        Exemplo de estrutura:
        {{
            "introducao": "texto da introdução...",
            "objetivo_geral": "texto do objetivo...",
            "metodologia": "texto da metodologia..."
        }}
        """
        
        response = gemini.chat(prompt, tipo_usuario='participante')
        
        if response.get('error'):
            return jsonify({'error': True, 'message': 'Erro ao autocompletar'}), 500
        
        # Tenta parsear resposta como JSON
        try:
            conteudo = json.loads(response['response'])
        except:
            conteudo = {'texto': response['response']}
        
        return jsonify({
            'success': True,
            'conteudo': conteudo
        })
        
    except Exception as e:
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