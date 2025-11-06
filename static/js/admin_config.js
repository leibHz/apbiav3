// =============================================
// APBIA - Admin Configurações JavaScript
// =============================================

// Carrega estatísticas reais
async function loadStats() {
    try {
        const response = await fetch('/admin/stats-api');
        const data = await response.json();

        if (data.success) {
            // Estatísticas gerais
            document.getElementById('stat-conversas').textContent = data.conversas || 0;
            document.getElementById('stat-mensagens').textContent = data.mensagens || 0;
            document.getElementById('stat-usuarios').textContent = data.usuarios_ativos || 0;
            document.getElementById('stat-projetos').textContent = data.projetos || 0;

            // Estatísticas Gemini
            document.getElementById('stat-requests-24h').textContent = data.gemini_requests_24h || 0;
            document.getElementById('stat-tokens-24h').textContent = (data.gemini_tokens_24h || 0).toLocaleString('pt-BR');
            document.getElementById('stat-unique-users').textContent = data.gemini_unique_users || 0;
        }
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
        document.getElementById('stat-conversas').textContent = 'Erro';
    }
}

// Toggle IA Status
document.getElementById('toggleIABtn')?.addEventListener('click', async function() {
    if (!confirm('Deseja alterar o status da IA?')) return;
    
    APBIA.showLoadingOverlay('Alterando status da IA...');
    
    try {
        const response = await fetch('/admin/toggle-ia', { method: 'POST' });
        const data = await response.json();
        
        APBIA.hideLoadingOverlay();
        
        if (data.success) {
            APBIA.showNotification(data.message, 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            APBIA.showNotification('Erro: ' + data.message, 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('Erro ao alterar status da IA', 'error');
    }
});

// ✅ Exportar estatísticas (CORRIGIDO)
document.getElementById('btnExportStats')?.addEventListener('click', async function() {
    try {
        APBIA.showLoadingOverlay('Preparando exportação...');
        
        // Faz requisição e aguarda resposta
        const response = await fetch('/admin/gemini-stats-export');
        
        if (!response.ok) {
            throw new Error('Erro ao exportar');
        }
        
        // Obtém o blob (arquivo)
        const blob = await response.blob();
        
        // Extrai nome do arquivo dos headers
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'gemini_stats.json';
        
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        // Cria URL temporária e força download
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        
        document.body.appendChild(a);
        a.click();
        
        // Limpa
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('✅ Estatísticas exportadas com sucesso!', 'success');
        
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('❌ Erro ao exportar: ' + error.message, 'error');
        console.error('Erro completo:', error);
    }
});

// Testar Gemini
document.getElementById('btnTestGemini')?.addEventListener('click', async function() {
    APBIA.showLoadingOverlay('Testando conexão com Gemini...');
    
    try {
        const response = await fetch('/admin/test-gemini');
        const data = await response.json();
        
        APBIA.hideLoadingOverlay();

        if (data.success) {
            APBIA.showNotification('✅ Gemini funcionando corretamente!', 'success');
        } else {
            APBIA.showNotification('❌ Erro: ' + data.message, 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('❌ Erro de conexão', 'error');
    }
});

// Testar DB
document.getElementById('btnTestDB')?.addEventListener('click', async function() {
    APBIA.showLoadingOverlay('Testando conexão com banco...');
    
    try {
        const response = await fetch('/admin/test-db');
        const data = await response.json();
        
        APBIA.hideLoadingOverlay();

        if (data.success) {
            APBIA.showNotification('✅ Banco de dados funcionando!', 'success');
        } else {
            APBIA.showNotification('❌ Erro: ' + data.message, 'error');
        }
    } catch (error) {
        APBIA.hideLoadingOverlay();
        APBIA.showNotification('❌ Erro de conexão', 'error');
    }
});

// Botão refresh
document.getElementById('refreshStats')?.addEventListener('click', function() {
    APBIA.showNotification('Atualizando estatísticas...', 'info');
    loadStats();
});

// Carrega estatísticas ao iniciar
loadStats();

// Atualiza automaticamente a cada 30 segundos
setInterval(loadStats, 30000);

console.log('✅ admin_config.js carregado');