const chatbox = document.getElementById('chatbox');
const input = document.getElementById('input');
const sidebar = document.getElementById('sidebar');

function toggleSidebar() {
    sidebar.classList.toggle('active');
}

function addMessage(message, isUser, sentiment = null) {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'message-container';
    if (isUser) {
        messageContainer.classList.add('user-message-container');
    }

    const messageElement = document.createElement('div');
    messageElement.innerText = message;
    messageElement.className = 'message';
    if (isUser) {
        messageElement.classList.add('user-message');
    }

    if (isUser && sentiment) {
        const sentimentElement = document.createElement('span');
        sentimentElement.innerText = `(Sentiment: ${sentiment})`;
        sentimentElement.className = `sentiment ${sentiment}`;
        messageElement.appendChild(sentimentElement);
    }

    if (isUser) {
        const userAvatar = document.createElement('img');
        userAvatar.src = USER_AVATAR_URL;
        userAvatar.className = 'avatar user-avatar';
        userAvatar.alt = 'User Avatar';
        messageContainer.appendChild(messageElement);
        messageContainer.appendChild(userAvatar);
    } else {
        const botAvatar = document.createElement('img');
        botAvatar.src = BOT_AVATAR_URL;
        botAvatar.className = 'avatar bot-avatar';
        botAvatar.alt = 'Bot Avatar';
        messageContainer.appendChild(botAvatar);
        messageContainer.appendChild(messageElement);
    }

    chatbox.appendChild(messageContainer);
    chatbox.scrollTop = chatbox.scrollHeight;
}

async function sendMessage() {
    const userMessage = input.value.trim();
    if (!userMessage) return;

    input.value = '';

    try {
        const response = await fetch('/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMessage })
        });
        const data = await response.json();
        addMessage(userMessage, true, data.sentiment);
        addMessage(data.response, false);
    } catch (error) {
        addMessage('Lỗi: Không thể kết nối với server.', false);
    }
}

async function startNewChat() {
    try {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const response = await fetch('/new_chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({})
        });
        const data = await response.json();
        if (data.status === 'success') {
            window.location.href = '/';
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error starting new chat. Please try again. Details: ' + error.message);
    }
}

function loadChatSession(sessionKey) {
    window.location.href = `/?session_key=${sessionKey}`;
}

input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

window.onload = function() {
    chatbox.scrollTop = chatbox.scrollHeight;
};
