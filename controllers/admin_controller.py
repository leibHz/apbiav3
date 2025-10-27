from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from dao.dao import SupabaseDAO
from config import Config
from services.gemini_stats import gemini_stats  # ✅ CORREÇÃO

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


@admin_bp.route('/gemini-stats-api')
@admin_required
def gemini_stats_api():
    """
    API JSON para retornar estatísticas do Gemini
    """
    try:
        stats = gemini_stats.get_stats()
        
        return jsonify({
            'success': True,
            'global': stats['global'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao obter estatísticas: {str(e)}'
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


@admin_bp.route('/gemini-stats-export')
@admin_required
def gemini_stats_export():
    """
    Exporta todas as estatísticas em JSON
    """
    try:
        export_data = gemini_stats.export_stats()
        
        from flask import Response
        import json
        
        # Gera arquivo JSON para download
        json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        return Response(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=gemini_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
        
    except Exception as e:
        return jsonify({
            'error': True,
            'message': f'Erro ao exportar estatísticas: {str(e)}'
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