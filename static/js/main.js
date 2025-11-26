// APBIA - Main JavaScript

// Inicialização quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Auto-dismiss alerts após 5 segundos
    autoHideAlerts();
    
    // Confirmação de ações destrutivas
    confirmDestructiveActions();
    
    // Loading states em formulários
    handleFormSubmissions();
    
    // Detecção de conexão
    monitorConnection();
}

// Auto-hide alerts
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            alert.style.transition = 'all 0.3s ease';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
}

// Confirmação em botões de deletar
function confirmDestructiveActions() {
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 
                          'Tem certeza que deseja realizar esta ação?';
            
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        });
    });
}

// Loading state em formulários
function handleFormSubmissions() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('[type="submit"]');
            
            if (submitBtn && !submitBtn.disabled) {
                // Salva texto original
                const originalText = submitBtn.innerHTML;
                
                // Adiciona spinner
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </span>
                    Processando...
                `;
                
                // Restaura após 30 segundos (timeout)
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 30000);
            }
        });
    });
}

// Monitora conexão com internet
function monitorConnection() {
    window.addEventListener('online', () => {
        showNotification('Conexão restaurada!', 'success');
    });
    
    window.addEventListener('offline', () => {
        showNotification('Você está offline. Verifique sua conexão.', 'warning');
    });
}

// Mostra notificações toast
function showNotification(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const iconClass = {
        'success': 'fa-check-circle',
        'error': 'fa-exclamation-circle',
        'warning': 'fa-exclamation-triangle',
        'info': 'fa-info-circle'
    }[type] || 'fa-info-circle';
    
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';
    
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = 'toast align-items-center text-white ' + bgClass;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('data-autohide', 'true');
    toast.setAttribute('data-delay', '5000');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas ${iconClass} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    onclick="this.closest('.toast').remove()"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // ✅ CORRIGIDO: Usa setTimeout ao invés de Bootstrap Toast
    // Remove após 5 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }, 5000);
    
    // Mostra notificação no console também
    if (window.console) {
        const emoji = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }[type] || 'ℹ️';
        console.info(`${emoji} Notificação [${type}]: ${message}`);
    }
}

// Cria container de toasts se não existir
function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    return container;
}

// Debounce para otimizar eventos
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Formata data para pt-BR
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Copia texto para clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copiado para área de transferência!', 'success');
        }).catch(() => {
            showNotification('Erro ao copiar', 'error');
        });
    } else {
        // Fallback para navegadores antigos
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        
        try {
            document.execCommand('copy');
            showNotification('Copiado para área de transferência!', 'success');
        } catch (err) {
            showNotification('Erro ao copiar', 'error');
        }
        
        document.body.removeChild(textarea);
    }
}

// Valida email
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// Formata número de telefone
function formatPhone(phone) {
    const cleaned = ('' + phone).replace(/\D/g, '');
    const match = cleaned.match(/^(\d{2})(\d{5})(\d{4})$/);
    
    if (match) {
        return '(' + match[1] + ') ' + match[2] + '-' + match[3];
    }
    
    return phone;
}

// Loading overlay
function showLoadingOverlay(message = 'Carregando...') {
    let overlay = document.getElementById('loading-overlay');
    
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        
        overlay.innerHTML = `
            <div class="text-center text-white">
                <div class="spinner-border mb-3" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <h5 id="loading-message">${message}</h5>
            </div>
        `;
        
        document.body.appendChild(overlay);
    } else {
        document.getElementById('loading-message').textContent = message;
        overlay.style.display = 'flex';
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Exporta funções globais
window.APBIA = {
    showNotification,
    copyToClipboard,
    debounce,
    formatDate,
    isValidEmail,
    formatPhone,
    showLoadingOverlay,
    hideLoadingOverlay
};

// Log de boas-vindas
console.log('%c🤖 APBIA - Assistente de Projetos para Bragantec', 
    'color: #007bff; font-size: 20px; font-weight: bold;');
console.log('%cSistema desenvolvido com Flask + Gemini 2.5 Flash', 
    'color: #6c757d; font-size: 12px;');