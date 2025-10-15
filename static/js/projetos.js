// Helpers
function showLoading(message) {
    document.getElementById('loadingMessage').textContent = message;
    document.getElementById('loadingIA').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loadingIA').style.display = 'none';
}

// Contador de caracteres do resumo
document.getElementById('resumo')?.addEventListener('input', function() {
    const count = this.value.length;
    document.getElementById('resumo-count').textContent = `${count}/300`;
    
    if (count > 300) {
        this.classList.add('is-invalid');
    } else {
        this.classList.remove('is-invalid');
    }
});

// Toggle continuação de projeto
document.getElementById('eh_continuacao')?.addEventListener('change', function() {
    const fields = document.getElementById('continuacao-fields');
    fields.style.display = this.checked ? 'block' : 'none';
});

// Adicionar objetivo específico
document.getElementById('addObjetivo')?.addEventListener('click', function() {
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

function renumerarObjetivos() {
    const objetivos = document.querySelectorAll('#objetivos-especificos-container .input-group');
    objetivos.forEach((obj, index) => {
        obj.querySelector('.input-group-text').textContent = `${index + 1}.`;
    });
}

// Adicionar etapa no cronograma
document.getElementById('addEtapa')?.addEventListener('click', function() {
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

// Remove etapa
document.querySelectorAll('.remove-etapa').forEach(btn => {
    btn.addEventListener('click', function() {
        this.closest('tr').remove();
    });
});

// GERAR IDEIAS COM IA
document.getElementById('btnGerarIdeias')?.addEventListener('click', async function() {
    showLoading('Gerando 4 ideias inovadoras, uma para cada categoria...');
    
    try {
        const response = await fetch('/projetos/gerar-ideias', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            mostrarIdeias(data.ideias);
        } else {
            APBIA.showNotification('Erro ao gerar ideias', 'error');
        }
        
    } catch (error) {
        hideLoading();
        APBIA.showNotification('Erro ao conectar com IA', 'error');
    }
});

function mostrarIdeias(ideias) {
    // Parse se vier como string
    let ideiasObj;
    try {
        ideiasObj = typeof ideias === 'string' ? JSON.parse(ideias) : ideias;
    } catch {
        // Se não for JSON, mostra como texto
        document.getElementById('ideiasContent').innerHTML = `
            <div class="alert alert-info">
                <pre>${ideias}</pre>
            </div>
            <button class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
        `;
        new bootstrap.Modal(document.getElementById('modalIdeias')).show();
        return;
    }
    
    // Renderiza ideias estruturadas
    const html = `
        <div class="row g-3">
            ${Object.entries(ideiasObj).map(([categoria, ideia]) => `
                <div class="col-md-6">
                    <div class="card h-100">
                        <div class="card-header bg-primary text-white">
                            <strong>${categoria}</strong>
                        </div>
                        <div class="card-body">
                            <h5 class="card-title">${ideia.titulo || 'Sem título'}</h5>
                            <p class="card-text">${ideia.resumo || ideia.descricao || 'Sem descrição'}</p>
                            ${ideia.palavras_chave ? `
                                <p class="text-muted small">
                                    <strong>Palavras-chave:</strong> ${ideia.palavras_chave}
                                </p>
                            ` : ''}
                        </div>
                        <div class="card-footer">
                            <button class="btn btn-sm btn-success usar-ideia" 
                                    data-ideia='${JSON.stringify(ideia)}'
                                    data-categoria="${categoria}">
                                <i class="fas fa-check"></i> Usar Esta Ideia
                            </button>
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    document.getElementById('ideiasContent').innerHTML = html;
    
    // Adiciona handlers
    document.querySelectorAll('.usar-ideia').forEach(btn => {
        btn.addEventListener('click', function() {
            const ideia = JSON.parse(this.dataset.ideia);
            const categoria = this.dataset.categoria;
            preencherComIdeia(ideia, categoria);
            bootstrap.Modal.getInstance(document.getElementById('modalIdeias')).hide();
        });
    });
    
    new bootstrap.Modal(document.getElementById('modalIdeias')).show();
}

function preencherComIdeia(ideia, categoria) {
    document.getElementById('nome').value = ideia.titulo || '';
    document.getElementById('categoria').value = categoria || '';
    document.getElementById('resumo').value = ideia.resumo || ideia.descricao || '';
    document.getElementById('palavras_chave').value = ideia.palavras_chave || '';
    
    // Trigger contador
    document.getElementById('resumo').dispatchEvent(new Event('input'));
    
    APBIA.showNotification('Ideia aplicada! Complete os demais campos', 'success');
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
                APBIA.showNotification('Erro ao gerar conteúdo', 'error');
            }
            
        } catch (error) {
            hideLoading();
            APBIA.showNotification('Erro ao conectar com IA', 'error');
        }
    });
});

function coletarDadosParciais() {
    return {
        nome: document.getElementById('nome').value,
        categoria: document.getElementById('categoria').value,
        resumo: document.getElementById('resumo').value,
        palavras_chave: document.getElementById('palavras_chave').value
    };
}

function aplicarConteudoGerado(campo, conteudo) {
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
    }
}

// SALVAR PROJETO
document.getElementById('formProjeto')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = e.submitter;
    const status = submitBtn.dataset.status || 'rascunho';
    
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
            APBIA.showNotification('Erro: ' + data.message, 'error');
        }
        
    } catch (error) {
        hideLoading();
        APBIA.showNotification('Erro ao salvar projeto', 'error');
    }
});

function coletarDadosCompletos(status) {
    // Coleta objetivos específicos
    const objetivosEspecificos = Array.from(
        document.querySelectorAll('.objetivo-especifico')
    ).map(input => input.value).filter(v => v.trim());
    
    // Coleta cronograma
    const cronograma = [];
    document.querySelectorAll('#cronogramaBody tr').forEach(tr => {
        const etapa = tr.querySelector('input[type="text"]').value;
        const meses = Array.from(tr.querySelectorAll('input[type="checkbox"]'))
            .map((cb, idx) => cb.checked ? ['Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov'][idx] : null)
            .filter(m => m);
        
        if (etapa.trim()) {
            cronograma.push({ etapa, meses });
        }
    });
    
    return {
        nome: document.getElementById('nome').value,
        categoria: document.getElementById('categoria').value,
        ano_edicao: parseInt(document.getElementById('ano_edicao').value),
        resumo: document.getElementById('resumo').value,
        palavras_chave: document.getElementById('palavras_chave').value,
        introducao: document.getElementById('introducao').value,
        objetivo_geral: document.getElementById('objetivo_geral').value,
        objetivos_especificos: objetivosEspecificos,
        metodologia: document.getElementById('metodologia').value,
        cronograma: cronograma,
        resultados_esperados: document.getElementById('resultados_esperados').value,
        referencias_bibliograficas: document.getElementById('referencias_bibliograficas').value,
        eh_continuacao: document.getElementById('eh_continuacao').checked,
        projeto_anterior_titulo: document.getElementById('projeto_anterior_titulo').value,
        projeto_anterior_resumo: document.getElementById('projeto_anterior_resumo').value,
        projeto_anterior_inicio: document.getElementById('projeto_anterior_inicio').value,
        projeto_anterior_termino: document.getElementById('projeto_anterior_termino').value,
        status: status
    };
}

