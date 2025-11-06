from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Response
from flask_login import login_required, current_user
from functools import wraps
from dao.dao import SupabaseDAO
from config import Config
from services.gemini_stats import gemini_stats  # ✅ CORREÇÃO
from utils.advanced_logger import logger  # ✅ ADICIONE ESTA LINHA
from datetime import datetime  # ✅ ADICIONE ESTA LINHA TAMBÉM (você usa no código)
import traceback  
import json


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
dao = SupabaseDAO()

# Decorator para verificar se usuário é admin
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Acesso negado. Apenas administradores.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard administrativo"""
    usuarios = dao.listar_usuarios()
    tipos_usuario = dao.listar_tipos_usuario()
    
    # Estatísticas
    stats = {
        'total_usuarios': len(usuarios),
        'participantes': len([u for u in usuarios if u.tipo_usuario_id == 2]),
        'orientadores': len([u for u in usuarios if u.tipo_usuario_id == 3]),
        'ia_status': Config.IA_STATUS
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats, 
                         usuarios=usuarios,
                         tipos_usuario=tipos_usuario)


@admin_bp.route('/usuarios')
@admin_required
def usuarios():
    """Lista de usuários"""
    usuarios = dao.listar_usuarios()
    tipos_usuario = dao.listar_tipos_usuario()
    
    return render_template('admin/usuarios.html', 
                         usuarios=usuarios,
                         tipos_usuario=tipos_usuario)


@admin_bp.route('/adicionar-usuario', methods=['POST'])
@admin_required
def adicionar_usuario():
    """Adiciona novo usuário"""
    try:
        from utils.helpers import validate_bp, format_bp
        
        data = request.json
        
        nome_completo = data.get('nome_completo')
        email = data.get('email')
        senha = data.get('senha')
        tipo_usuario_id = data.get('tipo_usuario_id')
        numero_inscricao = data.get('numero_inscricao', '').strip()
        
        if not all([nome_completo, email, senha, tipo_usuario_id]):
            return jsonify({
                'error': True, 
                'message': 'Todos os campos obrigatórios devem ser preenchidos'
            }), 400
        
        tipo_usuario_id = int(tipo_usuario_id)
        
        # Valida BP para participantes e orientadores
        if tipo_usuario_id in [2, 3]:
            if not numero_inscricao:
                return jsonify({
                    'error': True,
                    'message': 'BP é obrigatório para participantes e orientadores'
                }), 400
            
            if not validate_bp(numero_inscricao):
                return jsonify({
                    'error': True,
                    'message': 'BP inválido. Formato correto: BP12345678X (ex: BP123456A)'
                }), 400
            
            numero_inscricao = format_bp(numero_inscricao)
        else:
            numero_inscricao = format_bp(numero_inscricao) if numero_inscricao else None
        
        # Verifica se email já existe
        if dao.buscar_usuario_por_email(email):
            return jsonify({
                'error': True,
                'message': 'Email já cadastrado'
            }), 400
        
        # Verifica BP se fornecido
        if numero_inscricao and dao.buscar_usuario_por_bp(numero_inscricao):
            return jsonify({
                'error': True,
                'message': 'BP já cadastrado'
            }), 400
        
        # Cria usuário
        usuario = dao.criar_usuario(
            nome_completo=nome_completo,
            email=email,
            senha=senha,
            tipo_usuario_id=tipo_usuario_id,
            numero_inscricao=numero_inscricao
        )
        
        return jsonify({
            'success': True,
            'message': 'Usuário criado com sucesso',
            'usuario': usuario.to_dict()
        })
        
    except ValueError as ve:
        return jsonify({
            'error': True,
            'message': str(ve)
        }), 400
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao criar usuário: {str(e)}'
        }), 500


@admin_bp.route('/editar-usuario/<int:usuario_id>', methods=['PUT'])
@admin_required
def editar_usuario(usuario_id):
    """Edita dados do usuário"""
    try:
        data = request.json
        
        # Campos editáveis
        campos_permitidos = ['nome_completo', 'email', 'tipo_usuario_id', 'numero_inscricao']
        dados_atualizacao = {k: v for k, v in data.items() if k in campos_permitidos}
        
        if not dados_atualizacao:
            return jsonify({
                'error': True,
                'message': 'Nenhum campo para atualizar'
            }), 400
        
        dao.atualizar_usuario(usuario_id, **dados_atualizacao)
        
        return jsonify({
            'success': True,
            'message': 'Usuário atualizado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao atualizar usuário: {str(e)}'
        }), 500


@admin_bp.route('/deletar-usuario/<int:usuario_id>', methods=['DELETE'])
@admin_required
def deletar_usuario(usuario_id):
    """Deleta usuário"""
    try:
        # Não permite deletar a si mesmo
        if usuario_id == current_user.id:
            return jsonify({
                'error': True,
                'message': 'Você não pode deletar sua própria conta'
            }), 400
        
        dao.deletar_usuario(usuario_id)
        
        return jsonify({
            'success': True,
            'message': 'Usuário deletado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao deletar usuário: {str(e)}'
        }), 500


@admin_bp.route('/toggle-ia', methods=['POST'])
@admin_required
def toggle_ia():
    """Liga/desliga a IA"""
    try:
        Config.IA_STATUS = not Config.IA_STATUS
        status = "ativada" if Config.IA_STATUS else "desativada"
        
        return jsonify({
            'success': True,
            'message': f'IA {status} com sucesso',
            'ia_status': Config.IA_STATUS
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao alterar status da IA: {str(e)}'
        }), 500


@admin_bp.route('/configuracoes')
@admin_required
def configuracoes():
    """Página de configurações"""
    import os
    
    # Lista arquivos de contexto
    context_files = []
    context_path = Config.CONTEXT_FILES_PATH
    
    if os.path.exists(context_path):
        for filename in os.listdir(context_path):
            if filename.endswith('.txt'):
                filepath = os.path.join(context_path, filename)
                size = os.path.getsize(filepath)
                context_files.append({
                    'name': filename,
                    'size': f"{size / 1024:.2f} KB"
                })
    
    return render_template('admin/configuracoes.html', 
                         ia_status=Config.IA_STATUS,
                         context_files=context_files)


@admin_bp.route('/gemini-stats')
@admin_required
def gemini_stats_page():
    """
    Página de estatísticas do Gemini API
    """
    return render_template('admin/gemini_stats.html')


@admin_bp.route('/gemini-stats-export')
@admin_required
def gemini_stats_export():
    """
    Exporta estatísticas em JSON (CORRIGIDO)
    """
    try:
        # Obtém dados das estatísticas
        global_stats = gemini_stats.get_global_stats()
        all_users_stats = gemini_stats.get_all_users_stats()
        limits_info = gemini_stats.get_limits_info()
        
        # Monta estrutura JSON
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'global': global_stats,
            'limits': limits_info,
            'users': all_users_stats,
            'total_users': len(all_users_stats)
        }
        
        # Converte para JSON string
        json_string = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Gera nome do arquivo
        filename = f'gemini_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # ✅ CORREÇÃO PRINCIPAL: Retorna Response correto
        return Response(
            json_string,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'application/json; charset=utf-8',
                'Cache-Control': 'no-cache'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Erro ao exportar estatísticas: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': True,
            'message': f'Erro ao exportar: {str(e)}'
        }), 500


@admin_bp.route('/gemini-stats-user/<int:user_id>')
@admin_required
def gemini_stats_user(user_id):
    """
    Estatísticas de um usuário específico
    """
    try:
        user_stats = gemini_stats.get_user_stats(user_id)
        
        if user_stats is None:
            return jsonify({
                'error': True,
                'message': 'Usuário não encontrado ou sem estatísticas'
            }), 404
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'stats': user_stats
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        }), 500


@admin_bp.route('/gemini-stats-all-users')
@admin_required
def gemini_stats_all_users():
    """
    Estatísticas de todos os usuários
    """
    try:
        all_stats = gemini_stats.get_all_users_stats()
        
        return jsonify({
            'success': True,
            'users': all_stats,
            'total_users': len(all_stats)
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao obter estatísticas: {str(e)}'
        }), 500

@admin_bp.route('/gemini-stats-reset/<int:user_id>', methods=['POST'])
@admin_required
def gemini_stats_reset_user(user_id):
    """
    Reseta estatísticas de um usuário
    """
    try:
        gemini_stats.reset_user(user_id)
        
        return jsonify({
            'success': True,
            'message': f'Estatísticas do usuário {user_id} resetadas'
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao resetar estatísticas: {str(e)}'
        }), 500


# Importar datetime
from datetime import datetime

# ===== ADICIONAR ESTAS ROTAS NO FINAL DO admin_controller.py =====

@admin_bp.route('/orientacoes')
@admin_required
def orientacoes():
    """
    Página de gerenciamento de orientações
    """
    try:
        # Lista todos orientadores
        usuarios = dao.listar_usuarios()
        orientadores = [u for u in usuarios if u.is_orientador()]
        participantes = [u for u in usuarios if u.is_participante()]
        
        # Lista todos projetos
        projetos = dao.listar_todos_projetos()
        
        # Lista orientações ativas
        orientacoes = dao.listar_orientacoes_completas()
        
        return render_template('admin/orientacoes.html',
                             orientadores=orientadores,
                             participantes=participantes,
                             projetos=projetos,
                             orientacoes=orientacoes)
        
    except Exception as e:
        logger.error(f"Erro ao carregar orientações: {e}")
        flash('Erro ao carregar dados', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/projeto/<int:projeto_id>/participantes')
@admin_required
def projeto_participantes(projeto_id):
    """
    Retorna participantes de um projeto (JSON)
    """
    try:
        participantes = dao.listar_participantes_por_projeto(projeto_id)
        
        return jsonify({
            'success': True,
            'participantes': [p.to_dict() for p in participantes]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar participantes: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500


@admin_bp.route('/orientacoes/criar', methods=['POST'])
@admin_required
def criar_orientacao():
    """
    Cria associação orientador-projeto
    """
    try:
        data = request.json
        projeto_id = data.get('projeto_id')
        orientador_id = data.get('orientador_id')
        
        if not projeto_id or not orientador_id:
            return jsonify({
                'error': True,
                'message': 'Projeto e orientador são obrigatórios'
            }), 400
        
        # Verifica se já existe
        if dao.verificar_orientacao_existe(orientador_id, projeto_id):
            return jsonify({
                'error': True,
                'message': 'Esta orientação já existe'
            }), 400
        
        # Cria associação
        dao.criar_orientacao(orientador_id, projeto_id)
        
        logger.info(f"✅ Orientação criada: Orientador {orientador_id} -> Projeto {projeto_id}")
        
        return jsonify({
            'success': True,
            'message': 'Orientação criada com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar orientação: {e}")
        return jsonify({
            'error': True,
            'message': f'Erro: {str(e)}'
        }), 500


@admin_bp.route('/orientacoes/remover', methods=['DELETE'])
@admin_required
def remover_orientacao():
    """
    Remove associação orientador-projeto
    """
    try:
        data = request.json
        orientador_id = data.get('orientador_id')
        projeto_id = data.get('projeto_id')
        
        if not orientador_id or not projeto_id:
            return jsonify({
                'error': True,
                'message': 'Dados inválidos'
            }), 400
        
        dao.remover_orientacao(orientador_id, projeto_id)
        
        logger.info(f"🗑️ Orientação removida: Orientador {orientador_id} -> Projeto {projeto_id}")
        
        return jsonify({
            'success': True,
            'message': 'Orientação removida!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao remover orientação: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500
        
@admin_bp.route('/stats-api')
@admin_required
def stats_api():
    """
    API que retorna estatísticas do sistema em tempo real
    """
    try:
        # Conta conversas totais
        chats_result = dao.supabase.table('chats').select('id', count='exact').execute()
        total_chats = chats_result.count if hasattr(chats_result, 'count') else len(chats_result.data)
        
        # Conta mensagens totais
        msgs_result = dao.supabase.table('mensagens').select('id', count='exact').execute()
        total_mensagens = msgs_result.count if hasattr(msgs_result, 'count') else len(msgs_result.data)
        
        # Conta usuários ativos (com chats)
        usuarios_com_chats = dao.supabase.table('chats').select('usuario_id').execute()
        usuarios_unicos = len(set(row['usuario_id'] for row in usuarios_com_chats.data)) if usuarios_com_chats.data else 0
        
        # Conta projetos
        projetos_result = dao.supabase.table('projetos').select('id', count='exact').execute()
        total_projetos = projetos_result.count if hasattr(projetos_result, 'count') else len(projetos_result.data)
        
        # Estatísticas Gemini (últimas 24h)
        gemini_global = gemini_stats.get_global_stats()
        
        return jsonify({
            'success': True,
            'conversas': total_chats,
            'mensagens': total_mensagens,
            'usuarios_ativos': usuarios_unicos,
            'projetos': total_projetos,
            'gemini_requests_24h': gemini_global.get('requests_24h', 0),
            'gemini_tokens_24h': gemini_global.get('tokens_24h', 0),
            'gemini_unique_users': gemini_global.get('unique_users_24h', 0),
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': True,
            'message': str(e)
        }), 500



@admin_bp.route('/test-gemini')
@admin_required
def test_gemini():
    """
    Testa conexão com Gemini API (CORRIGIDO)
    """
    try:
        from services.gemini_service import GeminiService
        
        logger.info("🧪 Testando conexão com Gemini...")
        
        gemini = GeminiService()
        
        # Envia mensagem de teste simples
        response = gemini.chat(
            "Teste de conexão. Responda apenas: OK",
            tipo_usuario='participante',
            usar_contexto_bragantec=False,
            usar_pesquisa=False,
            usar_code_execution=False
        )
        
        if response.get('error'):
            logger.error(f"❌ Teste falhou: {response.get('response')}")
            return jsonify({
                'success': False,
                'message': response.get('response', 'Erro desconhecido')
            }), 500
        
        logger.info(f"✅ Teste bem-sucedido: {response.get('response')}")
        
        return jsonify({
            'success': True,
            'message': 'Gemini funcionando corretamente! ✓',
            'response': response.get('response', ''),
            'model': 'gemini-2.5-flash'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar Gemini: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500


@admin_bp.route('/test-db')
@admin_required
def test_db():
    """
    Testa conexão com banco de dados
    """
    try:
        # Tenta fazer uma query simples
        result = dao.supabase.table('usuarios').select('id').limit(1).execute()
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Banco de dados funcionando',
                'rows': len(result.data) if result.data else 0
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nenhum resultado retornado'
            })
        
    except Exception as e:
        logger.error(f"Erro ao testar DB: {e}")
        return jsonify({
            'success': False,
            'message': f'Erro: {str(e)}'
        }), 500