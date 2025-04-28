// 确保全局变量在模块中可用
const protobuf = window.protobuf;
const pako = window.pako;

// 全局变量定义
let username = '';
const ws = new WebSocket('ws://localhost:8765');
let root = null;
let loginKey = null;

// 获取DOM元素引用
const messageArea = document.getElementById('messageArea');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const usernameModal = document.getElementById('usernameModal');
const usernameInput = document.getElementById('usernameInput');
const loginButton = document.getElementById('loginButton');
const loginMessage = document.getElementById('loginMessage');
const modalContent = document.querySelector('.modal-content');
const userList = document.getElementById('userList');

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

// 将登录处理函数移到全局作用域
function handleLogin(username, password) {
    try {
        // 生成加密密钥
        loginKey = window.wasmCrypto.generate_key();
        console.log('Login key:', loginKey);
        
        // 加密密码
        const encryptedPassword = window.wasmCrypto.encrypt(password, loginKey);
        console.log('Encrypted password:', encryptedPassword);
        
        // 解密测试
        const decryptedPassword = window.wasmCrypto.decrypt(encryptedPassword, loginKey);
        console.log('Decrypted password:', decryptedPassword);
        
        // 验证解密是否正确
        if (decryptedPassword === password) {
            console.log('Password encryption/decryption successful!');
        }
        
        showMessage('登录成功！', 'success');
        modalContent.classList.add('success');
        
        setTimeout(() => {
            usernameModal.style.display = 'none';
            // 发送用户名到服务器
            const message = WebSocketMessage.create({
                type: MessageType.values.USERNAME_SET,
                username: username
            });
            sendWebSocketMessage(message);
        }, 1000);
    } catch (error) {
        console.error('Encryption error:', error);
        showMessage('登录加密失败', 'error');
    }
}

// 登录按钮点击事件处理
loginButton.onclick = function() {
    const username = document.getElementById('usernameInput').value.trim();
    const password = document.getElementById('passwordInput').value;
    const secretKey = document.getElementById('secretKeyInput').value.trim();

    if (!username || !password) {
        showMessage('请输入用户名和密码', 'error');
        return;
    }

    if (!isLoginMode && !secretKey) {
        showMessage('请输入密钥', 'error');
        return;
    }

    // 这里添加实际的登录/注册逻辑
    if (isLoginMode) {
        // 登录逻辑
        handleLogin(username, password);
    } else {
        // 注册逻辑
        handleRegister(username, password, secretKey);
    }
};

// 切换登录/注册模式的事件监听
const authToggleButtons = document.querySelectorAll('.auth-toggle button');
const secretKeyGroup = document.querySelector('.secret-key');
const modalTitle = document.querySelector('.modal-content h3');
let isLoginMode = true;

authToggleButtons.forEach(button => {
    button.addEventListener('click', function() {
        const mode = this.dataset.mode;
        isLoginMode = mode === 'login';
        
        // 更新按钮状态
        authToggleButtons.forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');
        
        // 更新标题和按钮文本
        modalTitle.textContent = isLoginMode ? '登录聊天室' : '注册账号';
        loginButton.textContent = isLoginMode ? '登录' : '注册';
        
        // 显示/隐藏密钥输入框
        if (isLoginMode) {
            secretKeyGroup.style.display = 'none';
        } else {
            secretKeyGroup.style.display = 'block';
        }
    });
});

function handleRegister(username, password, secretKey) {
    // 模拟注册成功
    showMessage('注册成功！请登录', 'success');
    setTimeout(() => {
        // 切换回登录模式
        authToggleButtons[0].click();
        // 清空密码和密钥输入框
        document.getElementById('passwordInput').value = '';
        document.getElementById('secretKeyInput').value = '';
    }, 2000);
}

function showMessage(message, type) {
    loginMessage.textContent = message;
    loginMessage.className = 'login-message ' + type;
    
    // 5秒后自动隐藏消息
    setTimeout(() => {
        loginMessage.className = 'login-message';
    }, 5000);
}

