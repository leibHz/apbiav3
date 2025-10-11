// Chat JavaScript - APBIA
let currentChatId = null;

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initializeChatHandlers();
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
                chat_id: currentChatId
            })
        });
        
        const data = await response.json();
        
        showThinking(false);
        
        if (data.success) {
            // Adiciona resposta da IA
            addMessageToChat('assistant', data.response, data.thinking_process);
            
            // Atualiza ID do chat se for novo
            if (data.chat_id && !currentChatId) {
                currentChatId = data.chat_id;
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

function addMessageToChat(role, content, thinking = null) {
    const messagesContainer = document.getElementById('chatMessages');
    
    // Remove mensagem de boas-vindas
    const welcome = document.getElementById('welcomeMessage');
    if (welcome) {
        welcome.remove();
    }
    
    // Cria elemento da mensagem
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    // Conteúdo
    const contentDiv = document.createElement('div');
    contentDiv.textContent = content;
    messageDiv.appendChild(contentDiv);
    
    // Se houver thinking process, adiciona
    if (thinking) {
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'alert alert-info mt-2';
        thinkingDiv.innerHTML = `<small><strong>Processo de Pensamento:</strong><br>${thinking}</small>`;
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
            location.reload(); // Recarrega para atualizar histórico
        } else {
            showError(data.message || 'Erro ao criar chat');
        }
        
    } catch (error) {
        showError('Erro ao criar nova conversa');
        console.error('Erro:', error);
    }
}

async function deleteChat(chatId) {
    if (!confirm('Deseja realmente deletar esta conversa?')) return;
    
    try {
        const response = await fetch(`/chat/delete-chat/${chatId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            location.reload();
        } else {
            showError(data.message || 'Erro ao deletar chat');
        }
        
    } catch (error) {
        showError('Erro ao deletar conversa');
        console.error('Erro:', error);
    }
}

function loadChat(chatId) {
    currentChatId = chatId;
    clearChatMessages();
    
    // TODO: Carregar mensagens do chat do banco de dados
    // Por enquanto apenas limpa e define o ID
    
    showInfo('Chat carregado. Continue sua conversa!');
}

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('message', `Analise este arquivo: ${file.name}`);
    
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
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show';
    alert.innerHTML = `
        <i class="fas fa-exclamation-circle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('main').insertBefore(alert, document.querySelector('main').firstChild);
    
    setTimeout(() => alert.remove(), 5000);
}

function showInfo(message) {
    const alert = document.createElement('div');
    alert.className = 'alert alert-info alert-dismissible fade show';
    alert.innerHTML = `
        <i class="fas fa-info-circle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('main').insertBefore(alert, document.querySelector('main').firstChild);
    
    setTimeout(() => alert.remove(), 3000);
}