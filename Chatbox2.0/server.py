import asyncio          # 导入异步IO库，用于处理异步操作
import json            # 导入JSON库，用于处理JSON格式数据
import websockets      # 导入websockets库，用于WebSocket服务器功能
import aioconsole      # 需要安装: pip install aioconsole
import time
from chat_pb2 import WebSocketMessage, ChatMessage, UserListMessage, MessageType

# 使用字典存储所有连接的客户端和其用户名
# 键为WebSocket连接对象，值为用户名
CLIENTS = {}

async def handle_connection(websocket):
    try:
        async for message in websocket:
            try:
                data = WebSocketMessage()
                data.ParseFromString(message)
                
                if data.type == MessageType.USERNAME_SET:
                    CLIENTS[websocket] = data.username
                    print(f"New user joined: {data.username}")  # 添加调试信息
                    
                    # 创建欢迎消息
                    welcome_msg = WebSocketMessage()
                    welcome_msg.type = MessageType.CHAT_MESSAGE
                    welcome_msg.chat_message.sender = "系统"
                    welcome_msg.chat_message.content = f"欢迎 {data.username} 加入聊天室！"
                    welcome_msg.chat_message.type = MessageType.USER_JOIN
                    welcome_msg.chat_message.timestamp = int(time.time())
                    
                    await broadcast(welcome_msg.SerializeToString(), None)
                    await update_user_list()
                
                elif data.type == MessageType.CHAT_MESSAGE:
                    print(f"Received message from {CLIENTS[websocket]}")  # 添加调试信息
                    broadcast_msg = WebSocketMessage()
                    broadcast_msg.type = MessageType.CHAT_MESSAGE
                    broadcast_msg.chat_message.sender = CLIENTS[websocket]
                    broadcast_msg.chat_message.content = data.chat_message.content
                    broadcast_msg.chat_message.type = MessageType.CHAT_MESSAGE
                    broadcast_msg.chat_message.timestamp = int(time.time())
                    
                    await broadcast(broadcast_msg.SerializeToString(), websocket)
                
            except Exception as e:
                print(f"Error handling message: {e}")  # 添加错误处理
                
    except websockets.exceptions.ConnectionClosed:
        print("Client connection closed unexpectedly")
    finally:
        if websocket in CLIENTS:
            username = CLIENTS[websocket]
            print(f"User disconnected: {username}")  # 添加调试信息
            del CLIENTS[websocket]
            
            leave_msg = WebSocketMessage()
            leave_msg.type = MessageType.CHAT_MESSAGE
            leave_msg.chat_message.sender = "系统"
            leave_msg.chat_message.content = f"{username} 离开了聊天室"
            leave_msg.chat_message.type = MessageType.USER_LEAVE
            leave_msg.chat_message.timestamp = int(time.time())
            
            await broadcast(leave_msg.SerializeToString(), None)
            await update_user_list()

async def broadcast(message, sender):
    """
    广播消息给所有客户端
    参数：
        message: 要广播的消息
        sender: 消息发送者的WebSocket连接（可以为None）
    """
    if CLIENTS:  # 如果有连接的客户端
        # 使用asyncio.gather同时向所有客户端发送消息
        await asyncio.gather(
            *[client.send(message) for client in CLIENTS]
        )

async def update_user_list():
    """
    更新并发送在线用户列表给所有客户端
    """
    if CLIENTS:
        user_list_msg = WebSocketMessage()
        user_list_msg.type = MessageType.USER_LIST
        user_list_msg.user_list.users.extend(list(CLIENTS.values()))
        
        await asyncio.gather(
            *[client.send(user_list_msg.SerializeToString()) for client in CLIENTS]
        )

async def server_input():
    """
    处理服务器端的输入并广播消息
    """
    while True:
        try:
            # 异步读取控制台输入
            message = await aioconsole.ainput("服务器消息> ")
            if message.strip():
                server_msg = WebSocketMessage()
                server_msg.type = MessageType.CHAT_MESSAGE
                server_msg.chat_message.sender = "服务器管理员"
                server_msg.chat_message.content = message
                server_msg.chat_message.type = MessageType.CHAT_MESSAGE
                server_msg.chat_message.timestamp = int(time.time())
                
                await broadcast(server_msg.SerializeToString(), None)
        except Exception as e:
            print(f"发送消息时出错: {e}")

async def main():
    """
    主函数：启动WebSocket服务器
    """
    # 创建WebSocket服务器并开始监听
    async with websockets.serve(handle_connection, "localhost", 8765):
        print("聊天服务器已启动在 ws://localhost:8765")
        # 创建服务器输入任务
        input_task = asyncio.create_task(server_input())
        # 等待服务器运行
        await asyncio.Future()

# 程序入口点
if __name__ == "__main__":
    # 启动异步事件循环
    asyncio.run(main()) 