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
            addMessageToChat(
                'assistant', 
                data.response, 
                data.thinking_process,
                data.search_used
            );
            
            // ✅ CORREÇÃO: Atualiza ID do chat se for novo SEM recarregar a página
            if (data.chat_id && !currentChatId) {
                currentChatId = data.chat_id;
                
                // Adiciona novo chat na sidebar dinamicamente
                addChatToSidebar(data.chat_id, message);
                
                // Mostra notificação
                APBIA.showNotification('Nova conversa iniciada!', 'success');
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

function addChatToSidebar(chatId, firstMessage) {
    /**
     * ✅ NOVA FUNÇÃO: Adiciona chat na sidebar sem recarregar página
     */
    const chatHistory = document.getElementById('chatHistory');
    
    // Remove mensagem "Nenhum chat anterior" se existir
    const emptyMessage = chatHistory.querySelector('p.text-muted');
    if (emptyMessage) {
        emptyMessage.remove();
    }
    
    // Cria elemento do chat
    const chatItem = document.createElement('div');
    chatItem.className = 'list-group-item chat-item active';
    chatItem.dataset.chatId = chatId;
    
    const now = new Date();
    const timeStr = now.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Gera título baseado na primeira mensagem
    const title = firstMessage.length > 40 ? 
        firstMessage.substring(0, 40) + '...' : 
        firstMessage;
    
    chatItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div class="flex-grow-1">
                <h6 class="mb-0">${title}</h6>
                <small class="text-muted">${timeStr}</small>
            </div>
            <button class="btn btn-sm btn-outline-danger delete-chat" 
                    data-chat-id="${chatId}"
                    title="Deletar conversa">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    
    // Adiciona no topo da lista
    chatHistory.insertBefore(chatItem, chatHistory.firstChild);
    
    // Adiciona handlers
    chatItem.addEventListener('click', function(e) {
        if (!e.target.classList.contains('delete-chat')) {
            loadChat(this.dataset.chatId);
        }
    });
    
    chatItem.querySelector('.delete-chat').addEventListener('click', function(e) {
        e.stopPropagation();
        deleteChat(this.dataset.chatId);
    });
    
    // Remove classe active de outros chats
    document.querySelectorAll('.chat-item').forEach(item => {
        if (item !== chatItem) {
            item.classList.remove('active');
        }
    });
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
    
    // Badge de thinking process
    if (role === 'assistant' && thinking) {
        const thinkingBadge = document.createElement('div');
        thinkingBadge.className = 'alert alert-light border mb-2';
        thinkingBadge.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-brain text-primary me-2"></i>
                <strong>Processo de Pensamento da IA:</strong>
                <button class="btn btn-sm btn-outline-primary ms-auto toggle-thinking">
                    <i class="fas fa-chevron-down"></i> Ver
                </button>
            </div>
            <div class="thinking-content" style="display: none; font-size: 0.9em; color: #666;">
                ${formatMessageContent(thinking)}
            </div>
        `;
        
        messageDiv.appendChild(thinkingBadge);
        
        // Toggle para mostrar/ocultar
        thinkingBadge.querySelector('.toggle-thinking').addEventListener('click', function() {
            const content = thinkingBadge.querySelector('.thinking-content');
            const icon = this.querySelector('i');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.className = 'fas fa-chevron-up';
                this.innerHTML = '<i class="fas fa-chevron-up"></i> Ocultar';
            } else {
                content.style.display = 'none';
                icon.className = 'fas fa-chevron-down';
                this.innerHTML = '<i class="fas fa-chevron-down"></i> Ver';
            }
        });
    }
    
    // Conteúdo principal
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = formatMessageContent(content);
    messageDiv.appendChild(contentDiv);
    
    // Badge de Google Search
    if (role === 'assistant' && searchUsed) {
        const searchBadge = document.createElement('div');
        searchBadge.className = 'mt-2';
        searchBadge.innerHTML = `
            <small class="badge bg-success">
                <i class="fas fa-search"></i> Consultou Google Search
            </small>
        `;
        messageDiv.appendChild(searchBadge);
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
    const div = document.createElement('div');
    div.textContent = content;
    let html = div.innerHTML;
    
    // Converte quebras de linha
    html = html.replace(/\n/g, '<br>');
    
    // Detecta e formata listas
    html = html.replace(/^- (.+)$/gm, '• $1');
    html = html.replace(/^\d+\. (.+)$/gm, '<strong>$&</strong>');
    
    // Formata código inline (entre ``)
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
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
            addChatToSidebar(data.chat.id, titulo);
            APBIA.showNotification('Nova conversa criada!', 'success');
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
            
            // Remove da sidebar
            const chatItem = document.querySelector(`[data-chat-id="${chatId}"]`);
            if (chatItem) {
                chatItem.remove();
            }
            
            // Se era o chat atual, limpa
            if (currentChatId === parseInt(chatId)) {
                currentChatId = null;
                clearChatMessages();
            }
            
            // Verifica se não há mais chats
            const chatHistory = document.getElementById('chatHistory');
            if (chatHistory.children.length === 0) {
                chatHistory.innerHTML = `
                    <p class="text-muted text-center px-3 py-3">
                        <i class="fas fa-inbox fa-2x mb-2 d-block"></i>
                        Nenhum chat anterior
                    </p>
                `;
            }
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
                addMessageToChat(msg.role, msg.conteudo, msg.thinking_process);
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
            addMessageToChat('assistant', data.response, data.thinking_process);
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