from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, Response
from flask_login import login_required, current_user
from functools import wraps
from dao.dao import SupabaseDAO
from config import Config
from services.gemini_stats import gemini_stats  
from utils.advanced_logger import logger
from datetime import datetime 
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
    Exporta estatísticas em JSON
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
    Testa conexão com Gemini API
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

@admin_bp.route('/gemini-stats-api')
@admin_required
def gemini_stats_api():
    """
    API JSON para estatísticas do Gemini em tempo real
    """
    try:
        from services.gemini_stats import gemini_stats
        
        # Pega estatísticas globais
        global_stats = gemini_stats.get_global_stats()
        
        # Pega informações de limites
        limits_info = gemini_stats.get_limits_info()
        
        # Calcula uso atual vs limites
        rpm_current = global_stats.get('requests_minute', 0)
        rpm_limit = limits_info['limits']['rpm']
        rpm_percent = int((rpm_current / rpm_limit) * 100)
        rpm_remaining = max(0, rpm_limit - rpm_current)
        
        tpm_current = global_stats.get('tokens_minute', 0)
        tpm_limit = limits_info['limits']['tpm']
        tpm_percent = int((tpm_current / tpm_limit) * 100)
        tpm_remaining = max(0, tpm_limit - tpm_current)
        
        rpd_current = global_stats.get('requests_today', 0)
        rpd_limit = limits_info['limits']['rpd']
        rpd_percent = int((rpd_current / rpd_limit) * 100)
        rpd_remaining = max(0, rpd_limit - rpd_current)
        
        search_current = global_stats.get('searches_today', 0)
        search_limit = limits_info['limits']['google_search_rpd']
        search_percent = int((search_current / search_limit) * 100)
        search_remaining = max(0, search_limit - search_current)
        
        return jsonify({
            'success': True,
            'global': {
                # RPM
                'requests_minute': rpm_current,
                'rpm_limit': rpm_limit,
                'rpm_percent': rpm_percent,
                'rpm_remaining': rpm_remaining,
                
                # TPM
                'tokens_minute': tpm_current,
                'tpm_limit': tpm_limit,
                'tpm_percent': tpm_percent,
                'tpm_remaining': tpm_remaining,
                
                # RPD
                'requests_today': rpd_current,
                'rpd_limit': rpd_limit,
                'rpd_percent': rpd_percent,
                'rpd_remaining': rpd_remaining,
                
                # Search
                'searches_today': search_current,
                'search_limit': search_limit,
                'search_percent': search_percent,
                'search_remaining': search_remaining,
                
                # Outros
                'unique_users_24h': global_stats.get('unique_users_24h', 0),
                'requests_24h': global_stats.get('requests_24h', 0),
                'tokens_24h': global_stats.get('tokens_24h', 0),
            },
            'limits': limits_info
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estatísticas Gemini: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': True,
            'message': str(e)
        }), 500
        
@admin_bp.route('/tipos-ia')
@admin_required
def tipos_ia():
    """
    Página de gerenciamento de Tipos de IA
    """
    try:
        tipos = dao.listar_tipos_ia()
        
        # Conta quantos chats usam cada tipo
        stats = {}
        for tipo in tipos:
            result = dao.supabase.table('chats')\
                .select('id', count='exact')\
                .eq('tipo_ia_id', tipo.id)\
                .execute()
            
            stats[tipo.id] = result.count if hasattr(result, 'count') else len(result.data)
        
        return render_template('admin/tipos_ia.html',
                             tipos=tipos,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Erro ao carregar tipos de IA: {e}")
        flash('Erro ao carregar dados', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/tipos-ia/criar', methods=['POST'])
@admin_required
def criar_tipo_ia():
    """
    Cria novo tipo de IA
    """
    try:
        data = request.json
        nome = data.get('nome', '').strip()
        
        if not nome:
            return jsonify({
                'error': True,
                'message': 'Nome é obrigatório'
            }), 400
        
        # Verifica se já existe
        tipos_existentes = dao.listar_tipos_ia()
        if any(t.nome.lower() == nome.lower() for t in tipos_existentes):
            return jsonify({
                'error': True,
                'message': 'Já existe um tipo de IA com este nome'
            }), 400
        
        # Cria
        result = dao.supabase.table('tipos_ia')\
            .insert({'nome': nome})\
            .execute()
        
        logger.info(f"✅ Tipo de IA criado: {nome}")
        
        return jsonify({
            'success': True,
            'message': 'Tipo de IA criado com sucesso!',
            'tipo': result.data[0] if result.data else None
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar tipo de IA: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500


@admin_bp.route('/tipos-ia/editar/<int:tipo_id>', methods=['PUT'])
@admin_required
def editar_tipo_ia(tipo_id):
    """
    Edita tipo de IA existente
    """
    try:
        data = request.json
        nome = data.get('nome', '').strip()
        
        if not nome:
            return jsonify({
                'error': True,
                'message': 'Nome é obrigatório'
            }), 400
        
        result = dao.supabase.table('tipos_ia')\
            .update({'nome': nome})\
            .eq('id', tipo_id)\
            .execute()
        
        logger.info(f"✅ Tipo de IA atualizado: ID {tipo_id} -> {nome}")
        
        return jsonify({
            'success': True,
            'message': 'Tipo de IA atualizado!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao editar tipo de IA: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500


@admin_bp.route('/tipos-ia/deletar/<int:tipo_id>', methods=['DELETE'])
@admin_required
def deletar_tipo_ia(tipo_id):
    """
    Deleta tipo de IA (se não tiver chats usando)
    """
    try:
        # Verifica se tem chats usando este tipo
        chats_usando = dao.supabase.table('chats')\
            .select('id', count='exact')\
            .eq('tipo_ia_id', tipo_id)\
            .execute()
        
        count = chats_usando.count if hasattr(chats_usando, 'count') else len(chats_usando.data)
        
        if count > 0:
            return jsonify({
                'error': True,
                'message': f'Não é possível deletar. Existem {count} chats usando este tipo de IA.'
            }), 400
        
        # Deleta
        result = dao.supabase.table('tipos_ia')\
            .delete()\
            .eq('id', tipo_id)\
            .execute()
        
        logger.info(f"🗑️ Tipo de IA deletado: ID {tipo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Tipo de IA deletado!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao deletar tipo de IA: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500
        
# ===== ADICIONAR NO FINAL DO controllers/admin_controller.py =====

@admin_bp.route('/participantes-projetos')
@admin_required
def participantes_projetos():
    """
    Página para gerenciar participantes dos projetos
    """
    try:
        # Lista todos os projetos
        projetos = dao.listar_todos_projetos()
        
        # Lista todos os participantes
        usuarios = dao.listar_usuarios()
        participantes = [u for u in usuarios if u.is_participante()]
        
        # Para cada projeto, busca seus participantes
        projetos_com_participantes = []
        for projeto in projetos:
            participantes_do_projeto = dao.listar_participantes_por_projeto(projeto.id)
            projetos_com_participantes.append({
                'projeto': projeto,
                'participantes': participantes_do_projeto
            })
        
        return render_template('admin/participantes_projetos.html',
                             projetos=projetos,
                             participantes=participantes,
                             projetos_com_participantes=projetos_com_participantes)
        
    except Exception as e:
        logger.error(f"Erro ao carregar participantes_projetos: {e}")
        flash('Erro ao carregar dados', 'error')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/adicionar-participante-projeto', methods=['POST'])
@admin_required
def adicionar_participante_projeto():
    """
    Adiciona participante a um projeto
    """
    try:
        data = request.json
        projeto_id = data.get('projeto_id')
        participante_id = data.get('participante_id')
        
        if not projeto_id or not participante_id:
            return jsonify({
                'error': True,
                'message': 'Projeto e participante são obrigatórios'
            }), 400
        
        # Verifica se já existe
        result = dao.supabase.table('participantes_projetos')\
            .select('*')\
            .eq('projeto_id', projeto_id)\
            .eq('participante_id', participante_id)\
            .execute()
        
        if result.data:
            return jsonify({
                'error': True,
                'message': 'Participante já está neste projeto'
            }), 400
        
        # Adiciona
        dao.associar_participante_projeto(participante_id, projeto_id)
        
        logger.info(f"✅ Participante {participante_id} adicionado ao projeto {projeto_id}")
        
        return jsonify({
            'success': True,
            'message': 'Participante adicionado ao projeto!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao adicionar participante: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500


@admin_bp.route('/remover-participante-projeto', methods=['DELETE'])
@admin_required
def remover_participante_projeto():
    """
    Remove participante de um projeto
    """
    try:
        data = request.json
        projeto_id = data.get('projeto_id')
        participante_id = data.get('participante_id')
        
        if not projeto_id or not participante_id:
            return jsonify({
                'error': True,
                'message': 'Dados inválidos'
            }), 400
        
        # Remove
        dao.supabase.table('participantes_projetos')\
            .delete()\
            .eq('projeto_id', projeto_id)\
            .eq('participante_id', participante_id)\
            .execute()
        
        logger.info(f"🗑️ Participante {participante_id} removido do projeto {projeto_id}")
        
        return jsonify({
            'success': True,
            'message': 'Participante removido!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao remover participante: {e}")
        return jsonify({
            'error': True,
            'message': str(e)
        }), 500