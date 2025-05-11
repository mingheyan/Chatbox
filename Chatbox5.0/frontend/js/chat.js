// 确保全局变量在模块中可用
const protobuf = window.protobuf;
const pako = window.pako;

// 全局变量定义
let username = '';
let ws = null;
let root = null;
let loginKey = null;
let isLoginMode = true; // 新增：用于跟踪当前是登录还是注册模式
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
const reconnectDelay = 3000; // 3秒

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

// 图片处理相关变量
let currentImageFile = null;

// 初始化图片上传区域
const pasteArea = document.getElementById('pasteArea');

// 处理粘贴事件
document.addEventListener('paste', async (e) => {
    const items = e.clipboardData.items;
    for (let item of items) {
        if (item.type.indexOf('image') !== -1) {
            const file = item.getAsFile();
            await handleImageFile(file);
            break;
        }
    }
});

// 处理拖放事件
pasteArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    pasteArea.classList.add('dragover');
});

pasteArea.addEventListener('dragleave', () => {
    pasteArea.classList.remove('dragover');
});

pasteArea.addEventListener('drop', async (e) => {
    e.preventDefault();
    pasteArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files[0] && files[0].type.startsWith('image/')) {
        await handleImageFile(files[0]);
    }
});

// 点击上传
pasteArea.addEventListener('click', () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e) => {
        if (e.target.files[0]) {
            await handleImageFile(e.target.files[0]);
        }
    };
    input.click();
});

// 处理图片文件
async function handleImageFile(file) {
    if (!file.type.startsWith('image/')) {
        console.error('不是有效的图片文件');
        return;
    }

    currentImageFile = file;
    
    // 创建预览
    const reader = new FileReader();
    reader.onload = (e) => {
        const placeholder = pasteArea.querySelector('.upload-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        // 移除旧的预览
        const oldPreview = pasteArea.querySelector('img');
        if (oldPreview) {
            oldPreview.remove();
        }
        
        // 添加新的预览
        const img = document.createElement('img');
        img.src = e.target.result;
        img.className = 'preview-image';
        pasteArea.appendChild(img);

        // 添加删除按钮
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-preview';
        deleteBtn.innerHTML = '×';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            clearImagePreview();
        };
        pasteArea.appendChild(deleteBtn);
    };
    reader.readAsDataURL(file);
}

// 清除图片预览
function clearImagePreview() {
    currentImageFile = null;
    const placeholder = pasteArea.querySelector('.upload-placeholder');
    if (placeholder) {
        placeholder.style.display = 'flex';
    }
    const preview = pasteArea.querySelector('.preview-image');
    if (preview) {
        preview.remove();
    }
    const deleteBtn = pasteArea.querySelector('.delete-preview');
    if (deleteBtn) {
        deleteBtn.remove();
    }
}

// 修改发送消息函数以支持图片
async function sendMessage() {
    const textContent = messageInput.value.trim();
    if (!currentImageFile && !textContent) {
        return;
    }

    try {
        // 如果有图片，先发送图片消息
        if (currentImageFile) {
            const imageContent = await new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.readAsDataURL(currentImageFile);
            });

            // 创建图片消息对象
            const imageMessage = ChatMessage.create({
                sender: username,
                content: imageContent,
                type: MessageType.values.CHAT_MESSAGE,
                timestamp: Date.now(),
                message_id: Math.random().toString(36).substring(2, 15)
            });

            const imageWebSocketMessage = WebSocketMessage.create({
                type: MessageType.values.CHAT_MESSAGE,
                chat_message: imageMessage
            });

            // 发送图片消息
            sendWebSocketMessage(imageWebSocketMessage);
        }

        // 如果有文本，发送文本消息
        if (textContent) {
            // 创建文本消息对象
            const textMessage = ChatMessage.create({
                sender: username,
                content: textContent,
                type: MessageType.values.CHAT_MESSAGE,
                timestamp: Date.now(),
                message_id: Math.random().toString(36).substring(2, 15)
            });

            const textWebSocketMessage = WebSocketMessage.create({
                type: MessageType.values.CHAT_MESSAGE,
                chat_message: textMessage
            });

            // 发送文本消息
            sendWebSocketMessage(textWebSocketMessage);
        }

        // 清空输入
        messageInput.value = '';
        if (currentImageFile) {
            clearImagePreview();
        }
    } catch (error) {
        console.error('Error sending message:', error);
        appendMessage('系统', '发送消息失败', 'system');
    }
}

// 修改消息显示函数以支持图片
function appendMessage(sender, content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    let contentHtml = '';
    if (content.startsWith('data:image')) {
        // 处理图片消息
        contentHtml = `<img src="${content}" class="message-image" alt="发送的图片">`;
    } else {
        // 处理文本消息
        contentHtml = `<div class="message-content">${content}</div>`;
    }

    // 添加发送者和内容
    if (type === 'system') {
        messageDiv.innerHTML = contentHtml;
    } else {
        messageDiv.innerHTML = `
            <div class="message-sender">${sender}</div>
            ${contentHtml}
        `;
    }

    // 单独添加时间戳元素
    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'timestamp';
    timestampDiv.textContent = new Date().toLocaleTimeString();
    messageDiv.appendChild(timestampDiv);

    messageArea.appendChild(messageDiv);
    if (window.autoScroll) {
        scrollToBottom();
    }
}

// WebSocket连接函数
function connectWebSocket() {
    try {
        ws = new WebSocket('ws://localhost:8765');

        ws.onopen = function() {
            console.log('WebSocket连接成功');
            appendMessage('系统', '连接成功！', 'system');
            reconnectAttempts = 0; // 重置重连次数
            
            // 如果已登录，重新发送用户名
            if (username) {
                const message = WebSocketMessage.create({
                    type: MessageType.values.USERNAME_SET,
                    username: username
                });
                sendWebSocketMessage(message);
            }
        };

        ws.onmessage = function(event) {
            handleWebSocketMessage(event);
        };

        ws.onclose = function() {
            console.log('WebSocket连接断开');
            appendMessage('系统', '连接已断开，正在尝试重新连接...', 'system');
            
            // 尝试重新连接
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(connectWebSocket, reconnectDelay);
            } else {
                appendMessage('系统', '重连失败，请刷新页面重试', 'system');
            }
        };

        ws.onerror = function(error) {
            console.error('WebSocket错误:', error);
            appendMessage('系统', 'WebSocket连接错误', 'system');
        };
    } catch (error) {
        console.error('创建WebSocket连接失败:', error);
        appendMessage('系统', 'WebSocket连接失败', 'system');
    }
}

// 发送WebSocket消息的安全包装
function sendWebSocketMessage(message) {
    try {
        if (ws && ws.readyState === WebSocket.OPEN) {
            const encoded = WebSocketMessage.encode(message).finish();
            const compressed = pako.gzip(encoded);
            ws.send(compressed);
        } else {
            console.warn('WebSocket未连接，消息未发送');
            appendMessage('系统', '连接断开，消息发送失败', 'system');
        }
    } catch (error) {
        console.error('发送消息失败:', error);
        appendMessage('系统', '消息发送失败', 'system');
    }
}

// 初始化WebSocket连接
connectWebSocket();

// 消息发送事件处理
sendButton.onclick = sendMessage;
messageInput.onkeypress = function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
};

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
                case MessageType.values.USER_JOIN:
                    appendMessage('系统', `${message.username} 加入了聊天室`, 'system');
                    break;
                case MessageType.values.USER_LEAVE:
                    appendMessage('系统', `${message.username} 离开了聊天室`, 'system');
                    break;
            }
        } catch (error) {
            console.error('Error decoding message:', error);
            appendMessage('系统', '接收消息时发生错误', 'system');
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
    try {
        // 如果不是自己发送的消息，且声音已启用，播放提示音
        if (chatMessage.sender !== username && window.soundEnabled) {
            playMessageSound();
        }
        
        // 检查是否是图片消息（base64格式）
        const isImage = chatMessage.content.startsWith('data:image');
        const messageType = chatMessage.sender === username ? 'sent' : 'received';

        // 创建消息容器
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${messageType}`;

        // 添加发送者信息
        if (chatMessage.sender !== '系统') {
            const senderDiv = document.createElement('div');
            senderDiv.className = 'message-sender';
            senderDiv.textContent = chatMessage.sender;
            messageDiv.appendChild(senderDiv);
        }

        // 添加消息内容
        if (isImage) {
            const img = document.createElement('img');
            img.src = chatMessage.content;
            img.className = 'message-image';
            img.alt = '图片消息';
            messageDiv.appendChild(img);
        } else {
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = chatMessage.content;
            messageDiv.appendChild(contentDiv);
        }

        // 添加时间戳
        const timestampDiv = document.createElement('div');
        timestampDiv.className = 'timestamp';
        const timestamp = new Date(chatMessage.timestamp || Date.now()).toLocaleTimeString();
        timestampDiv.textContent = timestamp;
        messageDiv.appendChild(timestampDiv);

        // 添加到消息区域
        messageArea.appendChild(messageDiv);
        
        // 根据自动滚动设置决定是否滚动
        if (window.autoScroll) {
            scrollToBottom();
        }

        // 发送消息确认
        if (chatMessage.message_id) {
            sendMessageAck(chatMessage.message_id);
        }
    } catch (error) {
        console.error('Error handling chat message:', error);
        appendMessage('系统', '消息显示出错', 'system');
    }
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
async function handleLogin(username, password) {
    try {
        const response = await fetch('/api/login/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
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
                
                // 直接应用服务器返回的用户设置
                if (data.data && data.data.settings) {
                    const settings = data.data.settings;
                    // 更新设置开关状态
                    darkModeToggle.checked = settings.dark_mode;
                    soundToggle.checked = settings.sound_enabled;
                    timestampToggle.checked = settings.show_timestamps;
                    autoScrollToggle.checked = settings.auto_scroll;
                    
                    // 应用深色模式
                    if (settings.dark_mode) {
                        document.body.classList.add('dark-mode');
                    } else {
                        document.body.classList.remove('dark-mode');
                    }
                    
                    // 应用保留用户特殊样式
                    if (settings.preserved) {
                        document.body.classList.add('preserved-user');
                    } else {
                        document.body.classList.remove('preserved-user');
                    }
                    
                    // 更新声音设置（使用全局变量）
                    window.soundEnabled = settings.sound_enabled;
                    
                    // 更新时间戳显示
                    if (settings.show_timestamps) {
                        document.body.classList.add('show-timestamps');
                    } else {
                        document.body.classList.remove('show-timestamps');
                    }
                    
                    // 更新自动滚动
                    window.autoScroll = settings.auto_scroll;
                }
            }, 1000);
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('登录请求失败', 'error');
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
        currentUserInfo.textContent = usernameValue;
        loginBtn.style.display = 'none';
        logoutBtn.style.display = '';
    } else {
        currentUserInfo.textContent = '';
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

// 修改登录状态检测逻辑，集成UI更新和设置加载
(async () => {
    try {
        const res = await fetch('/api/current_user/', { credentials: 'include' });
        const data = await res.json();
        if (data.success) {
            // 已登录，直接隐藏弹窗
            usernameModal.style.display = 'none';
            username = data.username;
            updateUserUI(true, username);
            
            // 加载用户设置
            const settingsRes = await fetch('/api/settings/', { 
                method: 'GET',
                credentials: 'include'
            });
            const settingsData = await settingsRes.json();
            
            if (settingsData.success) {
                const settings = settingsData.data;
                // 更新设置开关状态
                darkModeToggle.checked = settings.dark_mode;
                soundToggle.checked = settings.sound_enabled;
                timestampToggle.checked = settings.show_timestamps;
                autoScrollToggle.checked = settings.auto_scroll;
                
                // 应用深色模式
                if (settings.dark_mode) {
                    document.body.classList.add('dark-mode');
                } else {
                    document.body.classList.remove('dark-mode');
                }
                
                // 应用保留用户特殊样式
                if (settings.preserved) {
                    document.body.classList.add('preserved-user');
                } else {
                    document.body.classList.remove('preserved-user');
                }
                
                // 更新声音设置
                window.soundEnabled = settings.sound_enabled;
                
                // 更新时间戳显示
                if (settings.show_timestamps) {
                    document.body.classList.add('show-timestamps');
                } else {
                    document.body.classList.remove('show-timestamps');
                }
                
                // 更新自动滚动
                window.autoScroll = settings.auto_scroll;
            }
            
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
        console.error('检查登录状态失败:', e);
        usernameModal.style.display = '';
        updateUserUI(false, '');
    }
})();

// 设置相关的代码
const settingsBtn = document.getElementById('settingsBtn');
const settingsModal = document.getElementById('settingsModal');
const closeSettingsBtn = document.querySelector('.close-settings');
const darkModeToggle = document.getElementById('darkModeToggle');
const soundToggle = document.getElementById('soundToggle');
const timestampToggle = document.getElementById('timestampToggle');
const autoScrollToggle = document.getElementById('autoScrollToggle');

// 加载保存的设置
async function loadSettings() {
    try {
        const response = await fetch('/api/settings/', {
            method: 'GET',
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            const settings = data.data;
            darkModeToggle.checked = settings.dark_mode;
            soundToggle.checked = settings.sound_enabled;
            timestampToggle.checked = settings.show_timestamps;
            autoScrollToggle.checked = settings.auto_scroll;

            // 立即应用设置
            applySettings();
        }
    } catch (error) {
        console.error('加载设置失败:', error);
        // 如果加载失败，尝试从本地存储加载备份
        const savedSettings = localStorage.getItem('chatSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            darkModeToggle.checked = settings.dark_mode;
            soundToggle.checked = settings.sound_enabled;
            timestampToggle.checked = settings.show_timestamps;
            autoScrollToggle.checked = settings.auto_scroll;
            applySettings();
        }
    }
}

// 修改保存设置函数，使其在保存后立即应用
async function saveSettings() {
    try {
        const settings = {
            dark_mode: darkModeToggle.checked,
            sound_enabled: soundToggle.checked,
            show_timestamps: timestampToggle.checked,
            auto_scroll: autoScrollToggle.checked
        };

        const response = await fetch('/api/settings/update/', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });

        const data = await response.json();
        if (data.success) {
            // 更新全局声音设置
            window.soundEnabled = settings.sound_enabled;
            
            // 应用深色模式
            if (settings.dark_mode) {
                document.body.classList.add('dark-mode');
            } else {
                document.body.classList.remove('dark-mode');
            }
            
            // 更新时间戳显示
            if (settings.show_timestamps) {
                document.body.classList.add('show-timestamps');
            } else {
                document.body.classList.remove('show-timestamps');
            }
            
            // 更新自动滚动
            window.autoScroll = settings.auto_scroll;
            
            showToast('设置已保存');
            
            // 测试声音
            if (settings.sound_enabled) {
                playMessageSound();
            }
        } else {
            showToast('保存设置失败: ' + data.message);
        }
    } catch (error) {
        console.error('保存设置失败:', error);
        showToast('保存设置失败，请稍后重试');
    }
}

// 修改应用设置函数
function applySettings() {
    // 应用深色模式
    if (darkModeToggle.checked) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
    
    // 更新声音设置
    window.soundEnabled = soundToggle.checked;
    
    // 更新时间戳显示
    document.body.classList.toggle('show-timestamps', timestampToggle.checked);
    
    // 更新自动滚动
    window.autoScroll = autoScrollToggle.checked;
    if (autoScrollToggle.checked) {
        document.body.classList.add('auto-scroll');
        scrollToBottom();
    } else {
        document.body.classList.remove('auto-scroll');
    }

    // 保存设置到本地存储作为备份
    const settings = {
        dark_mode: darkModeToggle.checked,
        sound_enabled: soundToggle.checked,
        show_timestamps: timestampToggle.checked,
        auto_scroll: autoScrollToggle.checked
    };
    localStorage.setItem('chatSettings', JSON.stringify(settings));
}

// 显示提示消息
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    // 2秒后自动消失
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// 事件监听器
settingsBtn.addEventListener('click', () => {
    settingsModal.classList.add('show');
});

closeSettingsBtn.addEventListener('click', () => {
    settingsModal.classList.remove('show');
});

// 点击模态框外部关闭
settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) {
        settingsModal.classList.remove('show');
    }
});

// 设置改变时保存
[darkModeToggle, soundToggle, timestampToggle, autoScrollToggle].forEach(toggle => {
    toggle.addEventListener('change', saveSettings);
});

// 添加自动滚动指示器
function addScrollIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'auto-scroll-indicator';
    indicator.textContent = '点击返回底部';
    indicator.onclick = scrollToBottom;
    document.body.appendChild(indicator);
}

// 在页面加载时添加滚动指示器
document.addEventListener('DOMContentLoaded', addScrollIndicator);

// 优化滚动到底部函数
function scrollToBottom() {
    const lastMessage = messageArea.lastElementChild;
    if (lastMessage) {
        lastMessage.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
}

// 监听消息区域的滚动事件
messageArea.addEventListener('scroll', () => {
    const isNearBottom = messageArea.scrollHeight - messageArea.scrollTop - messageArea.clientHeight < 100;
    if (isNearBottom) {
        document.body.classList.add('auto-scroll');
    } else {
        document.body.classList.remove('auto-scroll');
    }
});

// 声音提醒功能
function playMessageSound() {
    if (window.soundEnabled) {  // 使用全局声音设置
        try {
            // 创建音频上下文
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // 创建振荡器和增益节点
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            // 连接节点
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            // 设置声音参数
            oscillator.type = 'sine';  // 使用正弦波
            oscillator.frequency.setValueAtTime(880, audioContext.currentTime); // 设置频率为 880Hz (A5音)
            
            // 设置音量包络
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.2, audioContext.currentTime + 0.01);
            gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 0.2);

            // 播放声音
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (e) {
            console.error('播放提示音失败:', e);
        }
    }
}

// 初始化加载设置
document.addEventListener('DOMContentLoaded', () => {
    // 默认启用深色模式
    document.body.classList.add('dark-mode');
    
    if (document.cookie.includes('sessionid')) {
        loadSettings();
    } else {
        // 未登录时使用默认设置
        darkModeToggle.checked = true;
        soundToggle.checked = true;
        timestampToggle.checked = true;
        autoScrollToggle.checked = true;
        
        // 应用默认设置
        applySettings();
    }
}); 