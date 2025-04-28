import asyncio          # 导入异步IO库，用于处理异步操作
import json            # 导入JSON库，用于处理JSON格式数据
import websockets      # 导入websockets库，用于WebSocket服务器功能
import aioconsole      # 需要安装: pip install aioconsole
import time
import gzip  # 添加gzip导入
from chat_pb2 import WebSocketMessage, ChatMessage, UserListMessage, MessageType
import uuid  # 新增：用于生成消息ID

# 使用字典存储所有连接的客户端和其用户名
# 键为WebSocket连接对象，值为用户名
CLIENTS = {}

# 修改常量部分
PING_INTERVAL = 30  # 发送ping的间隔秒数
PING_TIMEOUT = 60   # 等待pong响应的超时秒数（1分钟）
LAST_PONG = {}     # 存储最后一次pong时间
PENDING_MESSAGES = {}  # 新增：存储待确认的消息

async def handle_connection(websocket):
    try:
        # 初始化最后一次pong时间为当前时间
        LAST_PONG[websocket] = time.time()  # 添加这行
        
        # 创建ping任务
        ping_task = asyncio.create_task(send_ping(websocket))
        
        async for message in websocket:
            try:
                # 解压接收到的数据
                decompressed_data = gzip.decompress(message)
                data = WebSocketMessage()
                data.ParseFromString(decompressed_data)
                
                if data.type == MessageType.PONG:
                    # 更新最后一次pong时间
                    LAST_PONG[websocket] = time.time()
                    continue
                    
                elif data.type == MessageType.MESSAGE_ACK:
                    # 处理消息确认
                    msg_id = data.ack.message_id
                    if msg_id in PENDING_MESSAGES:
                        print(f"Message {msg_id} acknowledged by {data.ack.sender}")
                        del PENDING_MESSAGES[msg_id]
                    continue
                    
                elif data.type == MessageType.USERNAME_SET:
                    CLIENTS[websocket] = data.username
                    print(f"New user joined: {data.username}")  # 添加调试信息
                    
                    # 创建欢迎消息
                    welcome_msg = WebSocketMessage()
                    welcome_msg.type = MessageType.CHAT_MESSAGE
                    welcome_msg.chat_message.sender = "系统"
                    welcome_msg.chat_message.content = f"欢迎 {data.username} 加入聊天室！"
                    welcome_msg.chat_message.type = MessageType.USER_JOIN
                    welcome_msg.chat_message.timestamp = int(time.time())
                    
                    # 压缩欢迎消息
                    compressed_welcome = gzip.compress(welcome_msg.SerializeToString())
                    await broadcast(compressed_welcome, None)
                    await update_user_list()
                
                elif data.type == MessageType.CHAT_MESSAGE:
                    # 生成消息ID
                    msg_id = str(uuid.uuid4())
                    print(f"Received message from {CLIENTS[websocket]}")  # 添加调试信息
                    broadcast_msg = WebSocketMessage()
                    broadcast_msg.type = MessageType.CHAT_MESSAGE
                    broadcast_msg.chat_message.message_id = msg_id  # 添加消息ID
                    broadcast_msg.chat_message.sender = CLIENTS[websocket]
                    broadcast_msg.chat_message.content = data.chat_message.content
                    broadcast_msg.chat_message.type = MessageType.CHAT_MESSAGE
                    broadcast_msg.chat_message.timestamp = int(time.time())
                    
                    # 存储待确认的消息
                    PENDING_MESSAGES[msg_id] = {
                        'message': broadcast_msg,
                        'timestamp': time.time(),
                        'retries': 0
                    }
                    
                    # 压缩并广播消息
                    compressed_broadcast = gzip.compress(broadcast_msg.SerializeToString())
                    await broadcast(compressed_broadcast, websocket)
                    
                    # 创建重试任务
                    asyncio.create_task(retry_message(msg_id, websocket))
                
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
            
            # 压缩离开消息
            compressed_leave = gzip.compress(leave_msg.SerializeToString())
            await broadcast(compressed_leave, None)
            await update_user_list()
            
            # 取消ping任务
            ping_task.cancel()

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
        
        # 压缩用户列表消息
        compressed_list = gzip.compress(user_list_msg.SerializeToString())
        await asyncio.gather(
            *[client.send(compressed_list) for client in CLIENTS]
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
                
                # 压缩服务器消息
                compressed_msg = gzip.compress(server_msg.SerializeToString())
                await broadcast(compressed_msg, None)
        except Exception as e:
            print(f"发送消息时出错: {e}")

async def send_ping(websocket):
    """定期发送ping消息"""
    try:
        while True:
            await asyncio.sleep(PING_INTERVAL)
            
            try:
                # 发送新的ping
                ping_msg = WebSocketMessage()
                ping_msg.type = MessageType.PING
                ping_msg.timestamp = int(time.time())
                
                compressed_ping = gzip.compress(ping_msg.SerializeToString())
                await websocket.send(compressed_ping)
                print(f"Sent ping to {CLIENTS.get(websocket, 'unknown')}")
                
                # 给客户端一些时间来响应
                await asyncio.sleep(5)  # 等待5秒
                
                # 然后再检查pong时间
                last_pong = LAST_PONG.get(websocket, 0)
                current_time = time.time()
                
                print(f"Last pong: {last_pong}, Current time: {current_time}, Diff: {current_time - last_pong}")
                
                if current_time - last_pong > PING_TIMEOUT:
                    print(f"Ping timeout for {CLIENTS.get(websocket, 'unknown')}")
                    await websocket.close()
                    break
                    
            except (websockets.exceptions.ConnectionClosed, ConnectionResetError):
                break
            except Exception as e:
                print(f"Error sending ping: {e}")
                break
                
    except asyncio.CancelledError:
        pass
    finally:
        if websocket in LAST_PONG:
            del LAST_PONG[websocket]

async def retry_message(msg_id, original_sender, max_retries=3, retry_delay=5):
    """
    重试发送未确认的消息
    参数：
        msg_id: 消息ID
        original_sender: 原始发送者
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）
    """
    while msg_id in PENDING_MESSAGES and PENDING_MESSAGES[msg_id]['retries'] < max_retries:
        await asyncio.sleep(retry_delay)
        
        if msg_id not in PENDING_MESSAGES:  # 消息已被确认
            break
            
        PENDING_MESSAGES[msg_id]['retries'] += 1
        print(f"Retrying message {msg_id}, attempt {PENDING_MESSAGES[msg_id]['retries']}")
        
        message = PENDING_MESSAGES[msg_id]['message']
        compressed_msg = gzip.compress(message.SerializeToString())
        await broadcast(compressed_msg, original_sender)
    
    if msg_id in PENDING_MESSAGES:
        print(f"Message {msg_id} failed after {max_retries} retries")
        del PENDING_MESSAGES[msg_id]

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