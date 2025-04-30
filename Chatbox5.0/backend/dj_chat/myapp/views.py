from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_http_methods
import json
import secrets
from .models import ChatMessage
import uuid
from datetime import datetime, timedelta
import time

# 存储密钥（实际生产建议存数据库或环境变量）
SECRET_KEY_STORAGE = {'key': None}

def is_superuser(user):
    return user.is_superuser

@csrf_exempt
@user_passes_test(is_superuser)
def generate_secret_key(request):
    if request.method == 'POST':
        # 生成一个32位的随机密钥
        key = secrets.token_urlsafe(32)
        SECRET_KEY_STORAGE['key'] = key
        return JsonResponse({'success': True, 'secret_key': key})
    return JsonResponse({'success': False, 'msg': '仅支持POST'})

@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
        secret_key = data.get('secret_key')
        if not username or not password or not secret_key:
            return JsonResponse({'success': False, 'msg': '用户名、密码和密钥不能为空'})
        if SECRET_KEY_STORAGE['key'] is None:
            return JsonResponse({'success': False, 'msg': '密钥未生成，请联系管理员'})
        if secret_key != SECRET_KEY_STORAGE['key']:
            return JsonResponse({'success': False, 'msg': '密钥错误'})
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'msg': '用户名已存在'})
        user = User.objects.create_user(username=username, password=password)
        return JsonResponse({'success': True, 'msg': '注册成功'})
    return JsonResponse({'success': False, 'msg': '仅支持POST'})

@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return JsonResponse({'success': True, 'msg': '登录成功'})
        else:
            return JsonResponse({'success': False, 'msg': '用户名或密码错误'})
    return JsonResponse({'success': False, 'msg': '仅支持POST'})

@csrf_exempt
def current_user(request):
    if request.user.is_authenticated:
        return JsonResponse({'success': True, 'username': request.user.username})
    else:
        return JsonResponse({'success': False, 'msg': '未登录'})

@csrf_exempt
def logout(request):
    auth_logout(request)
    return JsonResponse({'success': True, 'msg': '已登出'})

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """
    发送消息的接口
    POST /api/send_message/
    """
    try:
        # 打印请求信息以便调试
        print(f"Received request: Content-Type: {request.content_type}")
        print(f"Request body: {request.body.decode()}")
        
        if request.content_type != 'application/json':
            return JsonResponse({
                'success': False,
                'message': 'Content-Type must be application/json'
            }, status=400)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'message': f'Invalid JSON: {str(e)}'
            }, status=400)

        required_fields = ['sender_id', 'content']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return JsonResponse({
                'success': False,
                'message': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=400)

        message = ChatMessage.objects.create(
            message_id=str(uuid.uuid4()),
            sender_id=data['sender_id'],
            content=data['content'],
            message_type=data.get('message_type', 'user')
        )
        
        return JsonResponse({
            'success': True,
            'message': '消息发送成功',
            'data': {
                'message_id': message.message_id,
                'timestamp': message.created_at.timestamp()
            }
        })
    except Exception as e:
        print(f"Error in send_message view: {str(e)}")  # 添加服务器端错误日志
        return JsonResponse({
            'success': False,
            'message': f'消息发送失败: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_messages(request):
    """
    获取历史消息的接口
    GET /api/get_messages/?before=timestamp&limit=20
    参数:
    - before: 获取此时间戳之前的消息（Unix时间戳，秒）
    - limit: 最多获取多少条消息（默认20条）
    """
    try:
        # 获取参数
        before_timestamp = float(request.GET.get('before', time.time()))
        limit = int(request.GET.get('limit', 20))
        
        # 转换时间戳为datetime对象
        before_time = datetime.fromtimestamp(before_timestamp)
        
        # 查询消息
        messages = ChatMessage.objects.filter(
            created_at__lt=before_time  # 获取指定时间之前的消息
        ).order_by('-created_at')[:limit]  # 按时间倒序排序，并限制数量
        
        # 转换为列表并反转，使最早的消息在前
        message_list = [{
            'message_id': msg.message_id,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'message_type': msg.message_type,
            'timestamp': msg.created_at.timestamp()
        } for msg in reversed(messages)]
        
        return JsonResponse({
            'success': True,
            'data': message_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取消息失败: {str(e)}'
        }, status=400)
