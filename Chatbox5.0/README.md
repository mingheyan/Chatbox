# Chatbox 5.0

一个基于WebSocket的实时聊天应用，支持加密通信和消息确认机制。

## 项目结构

```
Chatbox5.0/
├── frontend/           # 前端文件
│   ├── html/          # HTML文件
│   ├── js/            # JavaScript文件
│   └── css/           # CSS样式文件
├── backend/           # 后端文件
│   ├── server.py      # WebSocket服务器
│   ├── file_server.py # 静态文件服务器
│   └── chat_pb2.py    # Protocol Buffer生成的Python代码
├── proto/             # Protocol Buffer定义
│   └── chat.proto     # 消息格式定义
└── wasm/             # WebAssembly相关文件
    └── wasm-crypto/   # 加密模块
        └── pkg/       # 编译后的WASM文件
```

## 功能特性

- 实时WebSocket通信
- 用户认证（登录/注册）
- 消息加密
- 消息确认机制
- 用户在线状态显示
- 服务器管理员消息
- 心跳检测（Ping/Pong）

## 安装和运行

1. 安装Python依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 启动静态文件服务器：
   ```bash
   cd backend
   python file_server.py
   ```

3. 启动WebSocket服务器：
   ```bash
   cd backend
   python server.py
   ```

4. 在浏览器中访问：
   ```
   http://localhost:8000/frontend/html/index.html
   ```

## 技术栈

- 前端：
  - 原生JavaScript
  - WebSocket API
  - WebAssembly
  - Protocol Buffers
  - CSS3

- 后端：
  - Python
  - websockets
  - Protocol Buffers
  - aioconsole

## 开发说明

- 使用Protocol Buffers进行消息序列化
- 使用WebAssembly进行客户端加密
- 支持消息压缩（gzip）
- 实现了消息重试机制
- 使用心跳检测保持连接活跃

## 注意事项

- 确保8000和8765端口未被占用
- WebAssembly模块需要现代浏览器支持
- 建议使用最新版本的Chrome或Firefox浏览器 