// Chat JavaScript - APBIA com Histórico Persistente e Google Search
let currentChatId = null;
let usarPesquisaGoogle = true; // Google Search ativado por padrão

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initializeChatHandlers();
    loadSearchPreference();
});

function initializeChatHandlers() {
    // Formulário de envio
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', handleSendMessage);
    }
    
    // Botão de nova conversa
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewChat);
    }
    
    // Botão de upload
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }
    
    // Upload de arquivo
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }
    
    // Toggle Google Search
    const searchToggle = document.getElementById('searchToggle');
    if (searchToggle) {
        searchToggle.checked = usarPesquisaGoogle;
        searchToggle.addEventListener('change', function() {
            usarPesquisaGoogle = this.checked;
            localStorage.setItem('apbia_usar_pesquisa', usarPesquisaGoogle);
            
            const msg = usarPesquisaGoogle ? 
                'Google Search ativado - IA pode buscar informações atualizadas' : 
                'Google Search desativado - IA usará apenas conhecimento base';
            APBIA.showNotification(msg, 'info');
        });
    }
    
    // Itens do histórico
    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', function(e) {
            if (!e.target.classList.contains('delete-chat')) {
                loadChat(this.dataset.chatId);
            }
        });
    });
    
    // Botões de deletar chat
    document.querySelectorAll('.delete-chat').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            deleteChat(this.dataset.chatId);
        });
    });
}

function loadSearchPreference() {
    // Carrega preferência de pesquisa do localStorage
    const saved = localStorage.getItem('apbia_usar_pesquisa');
    if (saved !== null) {
        usarPesquisaGoogle = saved === 'true';
        const toggle = document.getElementById('searchToggle');
        if (toggle) {
            toggle.checked = usarPesquisaGoogle;
        }
    }
}

async function handleSendMessage(e) {
    e.preventDefault();
    
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Adiciona mensagem do usuário
    addMessageToChat('user', message);
    
    // Limpa input
    input.value = '';
    
    // Mostra indicador de pensamento
    showThinking(true);
    
    try {
        const response = await fetch('/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                chat_id: currentChatId,
                usar_pesquisa: usarPesquisaGoogle
            })
        });
        
        const data = await response.json();
        
        showThinking(false);
        
        if (data.success) {
            // Adiciona resposta da IA
            addMessageToChat('assistant', data.response, data.thinking_process, data.search_used);
            
            // Atualiza ID do chat se for novo
            if (data.chat_id && !currentChatId) {
                currentChatId = data.chat_id;
                
                // Recarrega página para atualizar lista de chats
                setTimeout(() => {
                    location.reload();
                }, 1000);
            }
        } else {
            showError(data.message || 'Erro ao processar mensagem');
        }
        
    } catch (error) {
        showThinking(false);
        showError('Erro de conexão. Tente novamente.');
        console.error('Erro:', error);
    }
}

function addMessageToChat(role, content, thinking = null, searchUsed = false) {
    const messagesContainer = document.getElementById('chatMessages');
    
    // Remove mensagem de boas-vindas
    const welcome = document.getElementById('welcomeMessage');
    if (welcome) {
        welcome.remove();
    }
    
    // Cria elemento da mensagem
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role} fade-in`;
    
    // Conteúdo
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Formata o texto (mantém quebras de linha)
    contentDiv.innerHTML = formatMessageContent(content);
    messageDiv.appendChild(contentDiv);
    
    // Badge de Google Search usado
    if (role === 'assistant' && searchUsed) {
        const searchBadge = document.createElement('div');
        searchBadge.className = 'mt-2';
        searchBadge.innerHTML = '<small class="badge bg-info"><i class="fas fa-search"></i> Consultou Google Search</small>';
        messageDiv.appendChild(searchBadge);
    }
    
    // Se houver thinking process, adiciona
    if (thinking) {
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'alert alert-info mt-2 mb-0';
        thinkingDiv.innerHTML = `<small><strong><i class="fas fa-brain"></i> Processo de Pensamento:</strong><br>${thinking}</small>`;
        messageDiv.appendChild(thinkingDiv);
    }
    
    // Timestamp
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    timestamp.textContent = new Date().toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    messageDiv.appendChild(timestamp);
    
    messagesContainer.appendChild(messageDiv);
    
    // Scroll para o fim
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function formatMessageContent(content) {
    // Escapa HTML mas mantém formatação
    const div = document.createElement('div');
    div.textContent = content;
    let html = div.innerHTML;
    
    // Converte quebras de linha em <br>
    html = html.replace(/\n/g, '<br>');
    
    // Detecta e formata listas
    html = html.replace(/^- (.+)$/gm, '• $1');
    html = html.replace(/^\d+\. (.+)$/gm, '<strong>$&</strong>');
    
    return html;
}

function showThinking(show) {
    const indicator = document.getElementById('thinkingIndicator');
    if (indicator) {
        indicator.style.display = show ? 'block' : 'none';
    }
}

async function createNewChat() {
    const titulo = prompt('Nome da nova conversa:', 'Nova conversa');
    
    if (!titulo) return;
    
    try {
        const response = await fetch('/chat/new-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ titulo })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentChatId = data.chat.id;
            clearChatMessages();
            APBIA.showNotification('Nova conversa criada!', 'success');
            
            // Recarrega para atualizar histórico
            setTimeout(() => location.reload(), 1000);
        } else {
            showError(data.message || 'Erro ao criar chat');
        }
        
    } catch (error) {
        showError('Erro ao criar nova conversa');
        console.error('Erro:', error);
    }
}

async function deleteChat(chatId) {
    if (!confirm('Deseja realmente deletar esta conversa? O histórico será perdido permanentemente.')) return;
    
    try {
        const response = await fetch(`/chat/delete-chat/${chatId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            APBIA.showNotification('Conversa deletada', 'success');
            
            // Se era o chat atual, limpa
            if (currentChatId === parseInt(chatId)) {
                currentChatId = null;
                clearChatMessages();
            }
            
            setTimeout(() => location.reload(), 1000);
        } else {
            showError(data.message || 'Erro ao deletar chat');
        }
        
    } catch (error) {
        showError('Erro ao deletar conversa');
        console.error('Erro:', error);
    }
}

async function loadChat(chatId) {
    currentChatId = parseInt(chatId);
    
    APBIA.showLoadingOverlay('Carregando histórico...');
    
    try {
        const response = await fetch(`/chat/load-history/${chatId}`);
        const data = await response.json();
        
        APBIA.hideLoadingOverlay();
        
        if (data.success) {
            // Limpa mensagens atuais
            clearChatMessages();
            
            // Adiciona mensagens do histórico
            data.mensagens.forEach(msg => {
                addMessageToChat(msg.role, msg.conteudo);
            });
            
            // Marca chat como ativo na sidebar
            document.querySelectorAll('.chat-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[data-chat-id="${chatId}"]`)?.classList.add('active');
            
            APBIA.showNotification('Histórico carregado!', 'success');
        } else {
            showError(data.message || 'Erro ao carregar histórico');
        }
        
    } catch (error) {
        APBIA.hideLoadingOverlay();
        showError('Erro ao carregar histórico');
        console.error('Erro:', error);
    }
}

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('message', `Analise este arquivo`);
    formData.append('chat_id', currentChatId || '');
    
    showThinking(true);
    
    try {
        const response = await fetch('/chat/upload-file', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        showThinking(false);
        
        if (data.success) {
            addMessageToChat('user', `📎 Arquivo enviado: ${file.name}`);
            addMessageToChat('assistant', data.response);
        } else {
            showError(data.message || 'Erro ao processar arquivo');
        }
        
    } catch (error) {
        showThinking(false);
        showError('Erro ao enviar arquivo');
        console.error('Erro:', error);
    }
    
    // Limpa input
    e.target.value = '';
}

function clearChatMessages() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="text-center text-muted py-5" id="welcomeMessage">
            <i class="fas fa-robot fa-4x mb-3"></i>
            <h4>Continue sua conversa</h4>
            <p>Digite uma mensagem para continuar.</p>
        </div>
    `;
}

function showError(message) {
    APBIA.showNotification(message, 'error');
}

function showInfo(message) {
    APBIA.showNotification(message, 'info');
}

// Atalho de teclado - Ctrl+Enter para enviar
document.getElementById('chatInput')?.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        document.getElementById('chatForm').dispatchEvent(new Event('submit'));
    }
});