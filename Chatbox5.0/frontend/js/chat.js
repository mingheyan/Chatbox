// 确保全局变量在模块中可用
const protobuf = window.protobuf;
const pako = window.pako;

// 全局变量定义
let username = '';
const ws = new WebSocket('ws://localhost:8765');
let root = null;
let loginKey = null;
let isLoginMode = true; // 新增：用于跟踪当前是登录还是注册模式

// 获取DOM元素引用
const messageArea = document.getElementById('messageArea');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const usernameModal = document.getElementById('usernameModal');
const usernameInput = document.getElementById('usernameInput');
const passwordInput = document.getElementById('passwordInput');
const secretKeyInput = document.getElementById('secretKeyInput');
const loginButton = document.getElementById('loginButton');
const loginMessage = document.getElementById('loginMessage');
const modalContent = document.querySelector('.modal-content');
const userList = document.getElementById('userList');
const authToggleButtons = document.querySelectorAll('.auth-toggle button');
const secretKeyGroup = document.querySelector('.secret-key');
const currentUserInfo = document.getElementById('currentUserInfo');
const loginBtn = document.getElementById('loginBtn');
const logoutBtn = document.getElementById('logoutBtn');

// 创建 protobuf 消息类型
const Root = protobuf.Root;
const Type = protobuf.Type;
const Field = protobuf.Field;
const Enum = protobuf.Enum;

// 创建消息类型
root = new Root();

// 创建枚举类型
const MessageType = new Enum("MessageType", {
    UNKNOWN: 0,
    CHAT_MESSAGE: 1,
    USER_JOIN: 2,
    USER_LEAVE: 3,
    USER_LIST: 4,
    USERNAME_SET: 5,
    PING: 6,
    PONG: 7,
    MESSAGE_ACK: 8
});
root.add(MessageType);

// 创建消息确认类型
const MessageAck = new Type("MessageAck")
    .add(new Field("message_id", 1, "string"))
    .add(new Field("sender", 2, "string"))
    .add(new Field("timestamp", 3, "int64"));
root.add(MessageAck);

const ChatMessage = new Type("ChatMessage")
    .add(new Field("sender", 1, "string"))
    .add(new Field("content", 2, "string"))
    .add(new Field("type", 3, "MessageType"))
    .add(new Field("timestamp", 4, "int64"))
    .add(new Field("message_id", 5, "string"));
root.add(ChatMessage);

const UserListMessage = new Type("UserListMessage")
    .add(new Field("users", 1, "string", "repeated"));
root.add(UserListMessage);

const WebSocketMessage = new Type("WebSocketMessage")
    .add(new Field("type", 1, "MessageType"))
    .add(new Field("chat_message", 2, "ChatMessage", "optional"))
    .add(new Field("user_list", 3, "UserListMessage", "optional"))
    .add(new Field("username", 4, "string", "optional"))
    .add(new Field("ack", 5, "MessageAck", "optional"))
    .add(new Field("timestamp", 6, "int64", "optional"));
root.add(WebSocketMessage);

ws.onopen = function() {
    appendMessage('系统', '连接成功！', 'system');
    
};

ws.onmessage = function(event) {
    handleWebSocketMessage(event);
};

ws.onclose = function() {
    appendMessage('系统', '连接已断开', 'system');
};

sendButton.onclick = sendMessage;
messageInput.onkeypress = function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
};

// 辅助函数
function sendWebSocketMessage(message) {
    const encoded = WebSocketMessage.encode(message).finish();
    const compressed = pako.gzip(encoded);
    ws.send(compressed);
}

function handleWebSocketMessage(event) {
    const reader = new FileReader();
    reader.onload = function() {
        try {
            const compressed = new Uint8Array(reader.result);
            const decompressed = pako.ungzip(compressed);
            const message = WebSocketMessage.decode(decompressed);
            
            switch(message.type) {
                case MessageType.values.PING:
                    handlePing();
                    break;
                case MessageType.values.USER_LIST:
                    updateUserList(message.user_list.users);
                    break;
                case MessageType.values.CHAT_MESSAGE:
                    handleChatMessage(message.chat_message);
                    break;
            }
        } catch (error) {
            console.error('Error decoding message:', error);
        }
    };
    reader.readAsArrayBuffer(event.data);
}

function handlePing() {
    const pong = WebSocketMessage.create({
        type: MessageType.values.PONG,
        timestamp: Date.now()
    });
    sendWebSocketMessage(pong);
}

function handleChatMessage(chatMessage) {
    if (chatMessage.message_id) {
        sendMessageAck(chatMessage.message_id);
    }
    
    appendMessage(
        chatMessage.sender,
        chatMessage.content,
        chatMessage.sender === '系统' ? 'system' :
        chatMessage.sender === username ? 'sent' : 'received'
    );
}

function sendMessageAck(messageId) {
    const ackMessage = WebSocketMessage.create({
        type: MessageType.values.MESSAGE_ACK,
        ack: {
            message_id: messageId,
            sender: username,
            timestamp: Date.now()
        }
    });
    sendWebSocketMessage(ackMessage);
}

function sendMessage() {
    const messageText = messageInput.value.trim();
    if (messageText) {
        const chatMessage = ChatMessage.create({
            sender: username,
            content: messageText,
            type: MessageType.values.CHAT_MESSAGE,
            timestamp: Date.now()
        });

        const message = WebSocketMessage.create({
            type: MessageType.values.CHAT_MESSAGE,
            chat_message: chatMessage
        });
        
        sendWebSocketMessage(message);
        messageInput.value = '';
    }
}

function appendMessage(sender, message, type) {
    console.log('appendMessage:', { sender, username, type });
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    if (type === 'system') {
        messageDiv.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="timestamp">${timestamp}</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-sender">${sender}</div>
            <div class="message-content">${message}</div>
            <div class="timestamp">${timestamp}</div>
        `;
    }
    messageArea.appendChild(messageDiv);
    messageArea.scrollTop = messageArea.scrollHeight;
}

function updateUserList(users) {
    userList.innerHTML = '';
    users.forEach(user => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span class="user-status"></span>
            <span>${user}</span>
        `;
        userList.appendChild(li);
    });
}

// 添加模式切换事件处理
authToggleButtons.forEach(button => {
    button.addEventListener('click', () => {
        const mode = button.getAttribute('data-mode');
        isLoginMode = mode === 'login';
        
        // 更新按钮状态
        authToggleButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        // 更新界面
        loginButton.textContent = isLoginMode ? '登录' : '注册';
        if (isLoginMode) {
            secretKeyGroup.classList.remove('show');
        } else {
            secretKeyGroup.classList.add('show');
        }
        
        // 清空消息
        showMessage('', '');
    });
});

// 添加登录按钮点击事件
loginButton.onclick = function() {
    const usernameValue = usernameInput.value.trim();
    const passwordValue = passwordInput.value.trim();
    const secretKeyValue = secretKeyInput.value.trim();
    
    if (!usernameValue || !passwordValue) {
        showMessage('用户名和密码不能为空', 'error');
        return;
    }
    
    if (!isLoginMode && !secretKeyValue) {
        showMessage('注册需要提供密钥', 'error');
        return;
    }
    
    if (isLoginMode) {
        handleLogin(usernameValue, passwordValue);
    } else {
        handleRegister(usernameValue, passwordValue, secretKeyValue);
    }
};

// 将登录处理函数移到全局作用域
function handleLogin(username, password) {
    try {
        loginKey = window.wasmCrypto.generate_key();
        fetch('/api/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        })
        .then(res => res.json())
        .then(data => {
            showMessage(data.msg, data.success ? 'success' : 'error');
            if (data.success) {
                modalContent.classList.add('success');
                setTimeout(() => {
                    usernameModal.style.display = 'none';
                    updateUserUI(true, username);
                    const message = WebSocketMessage.create({
                        type: MessageType.values.USERNAME_SET,
                        username: username
                    });
                    sendWebSocketMessage(message);
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Login error:', error);
            showMessage('登录请求失败', 'error');
        });
    } catch (error) {
        console.error('Encryption error:', error);
        showMessage('登录加密失败', 'error');
    }
}

function handleRegister(username, password, secretKey) {
    try {
        fetch('/api/register/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, secret_key: secretKey })
        })
        .then(res => res.json())
        .then(data => {
            showMessage(data.msg, data.success ? 'success' : 'error');
            if (data.success) {
                modalContent.classList.add('success');
                loginKey = secretKey;
                setTimeout(() => {
                    usernameModal.style.display = 'none';
                    updateUserUI(true, username);
                    const message = WebSocketMessage.create({
                        type: MessageType.values.USERNAME_SET,
                        username: username
                    });
                    sendWebSocketMessage(message);
                }, 1000);
            }
        })
        .catch(error => {
            console.error('Register error:', error);
            showMessage('注册请求失败', 'error');
        });
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('注册失败：加密错误', 'error');
    }
}

function showMessage(message, type) {
    loginMessage.textContent = message;
    loginMessage.className = `login-message ${type}`;
}

function updateUserUI(isLoggedIn, usernameValue) {
    if (isLoggedIn) {
        currentUserInfo.textContent = `当前用户：${usernameValue}`;
        loginBtn.style.display = 'none';
        logoutBtn.style.display = '';
    } else {
        currentUserInfo.textContent = '未登录';
        loginBtn.style.display = '';
        logoutBtn.style.display = 'none';
    }
}

loginBtn.onclick = function() {
    usernameModal.style.display = '';
};

logoutBtn.onclick = async function() {
    await fetch('/api/logout/', { method: 'POST', credentials: 'include' });
    updateUserUI(false, '');
    usernameModal.style.display = '';
};

// 修改登录状态检测逻辑，集成UI更新
(async () => {
    try {
        const res = await fetch('/api/current_user/', { credentials: 'include' });
        const data = await res.json();
        if (data.success) {
            // 已登录，直接隐藏弹窗
            usernameModal.style.display = 'none';
            username = data.username;
            updateUserUI(true, username);
            // 发送用户名到服务器
            const message = WebSocketMessage.create({
                type: MessageType.values.USERNAME_SET,
                username: username
            });
            sendWebSocketMessage(message);
        } else {
            // 未登录，显示弹窗
            usernameModal.style.display = '';
            updateUserUI(false, '');
        }
    } catch (e) {
        usernameModal.style.display = '';
        updateUserUI(false, '');
    }
})(); 