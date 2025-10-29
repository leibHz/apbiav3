// =========================================
// APBIA - JavaScript para Projetos
// COM GERADOR BASEADO EM VENCEDORES
// =========================================

// Helpers
function showLoading(message) {
    document.getElementById('loadingMessage').textContent = message;
    document.getElementById('loadingIA').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingIA').style.display = 'none';
}

// Contador de caracteres do resumo
const resumoInput = document.getElementById('resumo');
if (resumoInput) {
    resumoInput.addEventListener('input', function() {
        const count = this.value.length;
        document.getElementById('resumo-count').textContent = `${count}/300`;
        
        if (count > 300) {
            this.classList.add('is-invalid');
        } else {
            this.classList.remove('is-invalid');
        }
    });
}

// Toggle continuação de projeto
const ehContinuacaoCheckbox = document.getElementById('eh_continuacao');
if (ehContinuacaoCheckbox) {
    ehContinuacaoCheckbox.addEventListener('change', function() {
        const fields = document.getElementById('continuacao-fields');
        fields.style.display = this.checked ? 'block' : 'none';
    });
}

// Adicionar objetivo específico
const addObjetivoBtn = document.getElementById('addObjetivo');
if (addObjetivoBtn) {
    addObjetivoBtn.addEventListener('click', function() {
        const container = document.getElementById('objetivos-especificos-container');
        const count = container.children.length + 1;
        
        const div = document.createElement('div');
        div.className = 'input-group mb-2';
        div.innerHTML = `
            <span class="input-group-text">${count}.</span>
            <input type="text" class="form-control objetivo-especifico" 
                   placeholder="Objetivo específico ${count}...">
            <button type="button" class="btn btn-outline-danger remove-objetivo">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(div);
        
        // Add remove handler
        div.querySelector('.remove-objetivo').addEventListener('click', function() {
            div.remove();
            renumerarObjetivos();
        });
    });
}

function renumerarObjetivos() {
    const objetivos = document.querySelectorAll('#objetivos-especificos-container .input-group');
    objetivos.forEach((obj, index) => {
        obj.querySelector('.input-group-text').textContent = `${index + 1}.`;
    });
}

// Adicionar etapa no cronograma
const addEtapaBtn = document.getElementById('addEtapa');
if (addEtapaBtn) {
    addEtapaBtn.addEventListener('click', function() {
        const tbody = document.getElementById('cronogramaBody');
        const tr = document.createElement('tr');
        
        tr.innerHTML = `
            <td><input type="text" class="form-control form-control-sm" placeholder="Nova etapa"></td>
            <td><input type="checkbox" class="form-check-input"></td>
            <td><input type="checkbox" class="form-check-input"></td>
            <td><input type="checkbox" class="form-check-input"></td>
            <td><input type="checkbox" class="form-check-input"></td>
            <td><input type="checkbox" class="form-check-input"></td>
            <td><input type="checkbox" class="form-check-input"></td>
            <td><input type="checkbox" class="form-check-input"></td>
            <td><input type="checkbox" class="form-check-input"></td>
            <td><input type="checkbox" class="form-check-input"></td>
            <td>
                <button type="button" class="btn btn-sm btn-danger remove-etapa">
                    <i class="fas fa-times"></i>
                </button>
            </td>
        `;
        
        tbody.appendChild(tr);
        
        tr.querySelector('.remove-etapa').addEventListener('click', function() {
            tr.remove();
        });
    });
}

// Remove etapa (para etapas já existentes)
document.querySelectorAll('.remove-etapa').forEach(btn => {
    btn.addEventListener('click', function() {
        this.closest('tr').remove();
    });
});

// ✅ GERAR IDEIAS COM ANÁLISE DE VENCEDORES
const btnGerarIdeias = document.getElementById('btnGerarIdeias');
if (btnGerarIdeias) {
    btnGerarIdeias.addEventListener('click', async function() {
        // ✅ Aviso sobre Modo Bragantec automático
        const confirmacao = confirm(
            '🎯 MODO BRAGANTEC AUTOMÁTICO\n\n' +
            'A IA vai analisar TODOS os projetos vencedores das edições anteriores da Bragantec para criar 4 ideias com alto potencial de vitória.\n\n' +
            '⚠️ ATENÇÃO:\n' +
            '• Processo pode levar 20-40 segundos\n' +
            '• Consome ~100k-200k tokens (contexto histórico completo)\n' +
            '• Gera ideias baseadas em padrões de projetos premiados\n\n' +
            'Deseja continuar?'
        );
        
        if (!confirmacao) return;
        
        showLoading('🧠 Analisando projetos vencedores das edições anteriores...');
        
        try {
            const response = await fetch('/projetos/gerar-ideias', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            hideLoading();
            
            if (data.success) {
                // ✅ Mostra metadados sobre a análise
                if (data.metadata) {
                    console.log('📊 Metadados da geração:', data.metadata);
                    APBIA.showNotification(
                        '✅ Ideias geradas com análise completa de projetos vencedores!',
                        'success'
                    );
                }
                
                mostrarIdeias(data.ideias, data.metadata);
            } else {
                APBIA.showNotification('Erro ao gerar ideias: ' + (data.message || ''), 'error');
            }
            
        } catch (error) {
            hideLoading();
            APBIA.showNotification('Erro ao conectar com IA', 'error');
            console.error('Erro:', error);
        }
    });
}

function mostrarIdeias(ideias, metadata) {
    // Parse se vier como string
    let ideiasText = ideias;
    
    // Tenta parsear como JSON
    let ideiasObj = null;
    try {
        ideiasObj = typeof ideias === 'string' ? JSON.parse(ideias) : ideias;
    } catch (e) {
        console.log('Ideias não são JSON, mostrando como texto');
    }
    
    let html = '';
    
    // ✅ Adiciona banner informativo sobre análise de vencedores
    if (metadata && metadata.analise_vencedores) {
        html += `
            <div class="alert alert-success mb-4">
                <h5><i class="fas fa-trophy"></i> <strong>Análise Completa Realizada</strong></h5>
                <p class="mb-2">
                    <i class="fas fa-check-circle"></i> <strong>Modo Bragantec ativado:</strong> 
                    ${metadata.contexto_usado}
                </p>
                <small class="text-muted">
                    <i class="fas fa-info-circle"></i> ${metadata.aviso_tokens}
                </small>
            </div>
        `;
    }
    
    if (ideiasObj && typeof ideiasObj === 'object') {
        // Renderiza ideias estruturadas
        html += '<div class="row g-3">';
        
        for (const [categoria, ideia] of Object.entries(ideiasObj)) {
            const titulo = ideia.titulo || ideia.nome || 'Sem título';
            const resumo = ideia.resumo || ideia.descricao || 'Sem descrição';
            const palavrasChave = ideia.palavras_chave || ideia.keywords || '';
            
            // ✅ NOVO: Exibe análise de vencedores
            const inspiracao = ideia.inspiracao_vencedores || '';
            const diferenciais = ideia.diferenciais_competitivos || ideia.diferenciais || '';
            const viabilidade = ideia.viabilidade_tecnica || '';
            
            // Define cor do badge por categoria
            const badgeColor = 
                categoria === 'Informática' ? 'primary' :
                categoria === 'Engenharias' ? 'success' :
                categoria === 'Ciências da Natureza e Exatas' ? 'info' : 'warning';
            
            html += `
                <div class="col-md-6">
                    <div class="card h-100 shadow-sm">
                        <div class="card-header bg-${badgeColor} text-white">
                            <strong><i class="fas fa-trophy"></i> ${categoria}</strong>
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">${titulo}</h5>
                            
                            <div class="mb-3">
                                <strong class="text-muted">Resumo:</strong>
                                <p class="card-text">${resumo}</p>
                            </div>
                            
                            ${palavrasChave ? `
                                <div class="mb-2">
                                    <strong class="text-muted"><i class="fas fa-tags"></i> Palavras-chave:</strong>
                                    <p class="mb-0"><code>${palavrasChave}</code></p>
                                </div>
                            ` : ''}
                            
                            ${inspiracao ? `
                                <div class="alert alert-info py-2 mb-2">
                                    <strong><i class="fas fa-lightbulb"></i> Inspiração em Vencedores:</strong>
                                    <p class="mb-0 small">${inspiracao}</p>
                                </div>
                            ` : ''}
                            
                            ${diferenciais ? `
                                <div class="alert alert-success py-2 mb-2">
                                    <strong><i class="fas fa-star"></i> Diferenciais Competitivos:</strong>
                                    <p class="mb-0 small">${diferenciais}</p>
                                </div>
                            ` : ''}
                            
                            ${viabilidade ? `
                                <div class="alert alert-warning py-2 mb-2">
                                    <strong><i class="fas fa-tools"></i> Viabilidade Técnica:</strong>
                                    <p class="mb-0 small">${viabilidade}</p>
                                </div>
                            ` : ''}
                        </div>
                        <div class="card-footer bg-light">
                            <button class="btn btn-sm btn-success usar-ideia w-100" 
                                    data-ideia='${JSON.stringify(ideia).replace(/'/g, "&apos;")}'
                                    data-categoria="${categoria}">
                                <i class="fas fa-check-circle"></i> <strong>Usar Esta Ideia</strong>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
    } else {
        // Mostra como texto formatado
        html += `
            <div class="alert alert-info">
                <h5><i class="fas fa-lightbulb"></i> Ideias Geradas:</h5>
                <pre class="mb-0" style="white-space: pre-wrap; font-family: inherit;">${ideiasText}</pre>
            </div>
            <button class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
        `;
    }
    
    document.getElementById('ideiasContent').innerHTML = html;
    
    // Adiciona handlers para botões "usar ideia"
    document.querySelectorAll('.usar-ideia').forEach(btn => {
        btn.addEventListener('click', function() {
            try {
                const ideia = JSON.parse(this.dataset.ideia);
                const categoria = this.dataset.categoria;
                preencherComIdeia(ideia, categoria);
                bootstrap.Modal.getInstance(document.getElementById('modalIdeias')).hide();
            } catch (e) {
                console.error('Erro ao usar ideia:', e);
                APBIA.showNotification('Erro ao aplicar ideia', 'error');
            }
        });
    });
    
    // Mostra modal
    const modal = new bootstrap.Modal(document.getElementById('modalIdeias'));
    modal.show();
}

function preencherComIdeia(ideia, categoria) {
    const nomeInput = document.getElementById('nome');
    const categoriaSelect = document.getElementById('categoria');
    const resumoInput = document.getElementById('resumo');
    const palavrasChaveInput = document.getElementById('palavras_chave');
    
    if (nomeInput) nomeInput.value = ideia.titulo || ideia.nome || '';
    if (categoriaSelect) categoriaSelect.value = categoria || '';
    if (resumoInput) {
        resumoInput.value = ideia.resumo || ideia.descricao || '';
        // Trigger contador
        resumoInput.dispatchEvent(new Event('input'));
    }
    if (palavrasChaveInput) palavrasChaveInput.value = ideia.palavras_chave || ideia.keywords || '';
    
    // ✅ Mostra notificação com info sobre análise de vencedores
    let notificacaoMsg = '✅ Ideia aplicada! Esta ideia foi criada baseada em projetos vencedores.';
    
    if (ideia.inspiracao_vencedores) {
        notificacaoMsg += '\n\n📊 ' + ideia.inspiracao_vencedores;
    }
    
    APBIA.showNotification(notificacaoMsg, 'success');
    
    // Scroll para o topo do formulário
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// AUTOCOMPLETAR CAMPOS COM IA
document.querySelectorAll('.btn-ia-autocompletar').forEach(btn => {
    btn.addEventListener('click', async function() {
        const campo = this.dataset.campo;
        
        if (!confirm(`A IA vai gerar conteúdo para: ${campo}. Continuar?`)) return;
        
        showLoading(`Gerando ${campo}...`);
        
        try {
            const projetoParcial = coletarDadosParciais();
            
            const response = await fetch('/projetos/autocompletar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    campos: [campo],
                    projeto: projetoParcial
                })
            });
            
            const data = await response.json();
            
            hideLoading();
            
            if (data.success) {
                aplicarConteudoGerado(campo, data.conteudo);
                APBIA.showNotification('Conteúdo gerado! Revise e ajuste', 'success');
            } else {
                APBIA.showNotification('Erro ao gerar conteúdo: ' + (data.message || ''), 'error');
            }
            
        } catch (error) {
            hideLoading();
            APBIA.showNotification('Erro ao conectar com IA', 'error');
            console.error('Erro:', error);
        }
    });
});

function coletarDadosParciais() {
    return {
        nome: document.getElementById('nome')?.value || '',
        categoria: document.getElementById('categoria')?.value || '',
        resumo: document.getElementById('resumo')?.value || '',
        palavras_chave: document.getElementById('palavras_chave')?.value || ''
    };
}

function aplicarConteudoGerado(campo, conteudo) {
    // Se conteúdo for string, usa diretamente
    if (typeof conteudo === 'string') {
        const elemento = document.getElementById(campo);
        if (elemento) {
            elemento.value = conteudo;
            if (campo === 'resumo') {
                elemento.dispatchEvent(new Event('input'));
            }
        }
        return;
    }
    
    // Se for objeto, tenta mapear
    if (campo === 'resumo' && conteudo.resumo) {
        document.getElementById('resumo').value = conteudo.resumo;
        document.getElementById('resumo').dispatchEvent(new Event('input'));
    } else if (campo === 'introducao' && conteudo.introducao) {
        document.getElementById('introducao').value = conteudo.introducao;
    } else if (campo === 'objetivos') {
        if (conteudo.objetivo_geral) {
            document.getElementById('objetivo_geral').value = conteudo.objetivo_geral;
        }
    } else if (campo === 'metodologia' && conteudo.metodologia) {
        document.getElementById('metodologia').value = conteudo.metodologia;
    } else if (campo === 'resultados_esperados' && conteudo.resultados_esperados) {
        document.getElementById('resultados_esperados').value = conteudo.resultados_esperados;
    } else if (conteudo.texto) {
        // Fallback: usa campo "texto" genérico
        const elemento = document.getElementById(campo);
        if (elemento) {
            elemento.value = conteudo.texto;
        }
    }
}

// SALVAR PROJETO
const formProjeto = document.getElementById('formProjeto');
if (formProjeto) {
    formProjeto.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = e.submitter;
        const status = submitBtn?.dataset?.status || 'rascunho';
        
        const dados = coletarDadosCompletos(status);
        
        showLoading('Salvando projeto...');
        
        try {
            const response = await fetch('/projetos/criar', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });
            
            const data = await response.json();
            
            hideLoading();
            
            if (data.success) {
                APBIA.showNotification('Projeto salvo com sucesso!', 'success');
                setTimeout(() => {
                    window.location.href = '/projetos';
                }, 1500);
            } else {
                APBIA.showNotification('Erro: ' + (data.message || ''), 'error');
            }
            
        } catch (error) {
            hideLoading();
            APBIA.showNotification('Erro ao salvar projeto', 'error');
            console.error('Erro:', error);
        }
    });
}

function coletarDadosCompletos(status) {
    // Coleta objetivos específicos
    const objetivosEspecificos = Array.from(
        document.querySelectorAll('.objetivo-especifico')
    ).map(input => input.value).filter(v => v.trim());
    
    // Coleta cronograma
    const cronograma = [];
    const cronogramaRows = document.querySelectorAll('#cronogramaBody tr');
    
    cronogramaRows.forEach(tr => {
        const etapaInput = tr.querySelector('input[type="text"]');
        if (!etapaInput) return;
        
        const etapa = etapaInput.value.trim();
        if (!etapa) return;
        
        const checkboxes = tr.querySelectorAll('input[type="checkbox"]');
        const meses = ['Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov'];
        const mesesMarcados = [];
        
        checkboxes.forEach((cb, idx) => {
            if (cb.checked && idx < meses.length) {
                mesesMarcados.push(meses[idx]);
            }
        });
        
        if (etapa) {
            cronograma.push({ 
                etapa: etapa, 
                meses: mesesMarcados 
            });
        }
    });
    
    // Coleta continuação de projeto
    const ehContinuacao = document.getElementById('eh_continuacao')?.checked || false;
    
    return {
        nome: document.getElementById('nome')?.value || '',
        categoria: document.getElementById('categoria')?.value || '',
        ano_edicao: parseInt(document.getElementById('ano_edicao')?.value) || new Date().getFullYear(),
        resumo: document.getElementById('resumo')?.value || '',
        palavras_chave: document.getElementById('palavras_chave')?.value || '',
        introducao: document.getElementById('introducao')?.value || '',
        objetivo_geral: document.getElementById('objetivo_geral')?.value || '',
        objetivos_especificos: objetivosEspecificos,
        metodologia: document.getElementById('metodologia')?.value || '',
        cronograma: cronograma,
        resultados_esperados: document.getElementById('resultados_esperados')?.value || '',
        referencias_bibliograficas: document.getElementById('referencias_bibliograficas')?.value || '',
        eh_continuacao: ehContinuacao,
        projeto_anterior_titulo: document.getElementById('projeto_anterior_titulo')?.value || '',
        projeto_anterior_resumo: document.getElementById('projeto_anterior_resumo')?.value || '',
        projeto_anterior_inicio: document.getElementById('projeto_anterior_inicio')?.value || '',
        projeto_anterior_termino: document.getElementById('projeto_anterior_termino')?.value || '',
        status: status
    };
}

// Log de inicialização
console.log('✅ projetos.js carregado com sucesso - Modo Análise de Vencedores ativo');