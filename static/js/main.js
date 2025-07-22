document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const clearChatButton = document.getElementById('clear-chat');
    
    const sessionId = 'session_' + Date.now();
    
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.scrollHeight > 120) {
            this.style.overflowY = 'auto';
        } else {
            this.style.overflowY = 'hidden';
        }
    });
    
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    sendButton.addEventListener('click', sendMessage);
    
    clearChatButton.addEventListener('click', clearChat);
    
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        addMessageToChat('user', message);
        
        userInput.value = '';
        userInput.style.height = 'auto';
        
        userInput.disabled = true;
        sendButton.disabled = true;
        
        showTypingIndicator();
        
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Erro na comunicação com o servidor');
            }
            return response.json();
        })
        .then(data => {
            removeTypingIndicator();
            
            addMessageToChat('bot', data.response, data.source);
            
            scrollToBottom();
        })
        .catch(error => {
            console.error('Erro:', error);
            
            removeTypingIndicator();
            
            addMessageToChat('bot', 'Desculpe, ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.', 'erro');
        })
        .finally(() => {
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        });
    }
    
    function addMessageToChat(role, content, source = '') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const formattedContent = formatMessage(content);
        
        const paragraph = document.createElement('p');
        paragraph.innerHTML = formattedContent;
        messageContent.appendChild(paragraph);
        
        if (role === 'bot' && source) {
            const messageInfo = document.createElement('div');
            messageInfo.className = 'message-info';
            
            const sourceSpan = document.createElement('span');
            sourceSpan.className = `message-source ${source}`;
            sourceSpan.textContent = source;
            messageInfo.appendChild(sourceSpan);
            
            messageContent.appendChild(messageInfo);
        }
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        scrollToBottom();
    }
    
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            typingDiv.appendChild(dot);
        }
        
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    }
    
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    function clearChat() {
        if (!confirm('Tem certeza que deseja limpar o histórico de conversa?')) {
            return;
        }
        
        chatMessages.innerHTML = '';
        
        addMessageToChat('bot', 'Olá! Sou o assistente virtual da Belas Artes. Como posso ajudar você hoje?', 'sistema');
        
        fetch('/api/clear-history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        })
        .catch(error => {
            console.error('Erro ao limpar histórico:', error);
        });
    }
    
    
    function formatMessage(text) {
        
        text = text.replace(/\n/g, '<br>');
        
        
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        
        text = text.replace(/`(.*?)`/g, '<code>$1</code>');
        
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        return text;
    }
});