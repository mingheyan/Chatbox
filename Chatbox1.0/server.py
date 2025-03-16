import asyncio          # 导入异步IO库，用于处理异步操作
import json            # 导入JSON库，用于处理JSON格式数据
import websockets      # 导入websockets库，用于WebSocket服务器功能
import aioconsole      # 需要安装: pip install aioconsole

# 使用字典存储所有连接的客户端和其用户名
# 键为WebSocket连接对象，值为用户名
CLIENTS = {}

async def handle_connection(websocket):
    try:
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'username':
                CLIENTS[websocket] = data['username']
                welcome_message = json.dumps({
                    "sender": "系统",
                    "message": f"欢迎 {data['username']} 加入聊天室！",
                    "type": "message"
                })
                await broadcast(welcome_message, None)
                await update_user_list()
                break  # 用户名设置完成，退出第一阶段
        async for message in websocket:
            data = json.loads(message)
            if data['type'] == 'message':
                broadcast_message = json.dumps({
                    "sender": CLIENTS[websocket],
                    "message": data['message'],
                    "type": "message"
                })
                await broadcast(broadcast_message, websocket)
    finally:
        if websocket in CLIENTS:
            username = CLIENTS[websocket]
            del CLIENTS[websocket]
            leave_message = json.dumps({
                "sender": "系统",
                "message": f"{username} 离开了聊天室",
                "type": "message"
            })
            await broadcast(leave_message, None)
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
        # 创建用户列表消息
        user_list = json.dumps({
            "type": "userList",
            "users": list(CLIENTS.values())  # 获取所有在线用户名
        })
        # 广播用户列表给所有客户端
        await asyncio.gather(
            *[client.send(user_list) for client in CLIENTS]
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
                server_message = json.dumps({
                    "sender": "服务器管理员",
                    "message": message,
                    "type": "message"
                })
                await broadcast(server_message, None)
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