from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test, login_required
from django.views.decorators.http import require_http_methods
import json
import secrets
from .models import ChatMessage, UserSettings, UserProfile
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
        # 创建用户资料
        profile = UserProfile.objects.create(user=user)
        # 创建用户设置
        settings = UserSettings.objects.create(user=user)
        
        # 合并设置和资料信息
        user_settings = settings.to_dict()
        profile_data = profile.to_dict(request)
        user_settings.update(profile_data)
        
        return JsonResponse({
            'success': True,
            'msg': '注册成功',
            'data': {
                'username': user.username,
                'settings': user_settings
            }
        })
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
            # 确保用户有设置记录
            settings, _ = UserSettings.objects.get_or_create(user=user)
            # 确保用户有资料记录
            profile, _ = UserProfile.objects.get_or_create(user=user)
            
            # 合并设置和资料信息
            user_settings = settings.to_dict()
            profile_data = profile.to_dict(request)
            user_settings.update(profile_data)
            
            return JsonResponse({
                'success': True,
                'msg': '登录成功',
                'data': {
                    'username': user.username,
                    'settings': user_settings
                }
            })
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
        # print(f"Request body: {request.body.decode()}")
        
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

@csrf_exempt
@login_required
def get_user_settings(request):
    """
    获取用户设置
    GET /api/settings/
    """
    if request.method != 'GET':
        return JsonResponse({
            'success': False,
            'message': '仅支持GET请求'
        }, status=405)

    try:
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        return JsonResponse({
            'success': True,
            'data': settings.to_dict()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取设置失败: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
def update_user_settings(request):
    """
    更新用户设置
    POST /api/settings/update/
    """
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': '仅支持POST请求'
        }, status=405)

    try:
        data = json.loads(request.body)
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        
        # 更新设置
        if 'dark_mode' in data:
            settings.dark_mode = data['dark_mode']
        if 'sound_enabled' in data:
            settings.sound_enabled = data['sound_enabled']
        if 'show_timestamps' in data:
            settings.show_timestamps = data['show_timestamps']
        if 'auto_scroll' in data:
            settings.auto_scroll = data['auto_scroll']
        
        settings.save()
        
        return JsonResponse({
            'success': True,
            'message': '设置更新成功',
            'data': settings.to_dict()
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '无效的JSON数据'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新设置失败: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
def update_avatar(request):
    """
    更新用户头像
    POST /api/settings/update_avatar/
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': '仅支持POST请求'})
    
    try:
        if 'avatar' not in request.FILES:
            return JsonResponse({'success': False, 'message': '未找到头像文件'})
        
        avatar_file = request.FILES['avatar']
        
        # 验证文件类型
        if not avatar_file.content_type.startswith('image/'):
            return JsonResponse({'success': False, 'message': '仅支持图片文件'})
            
        # 验证文件大小（限制为5MB）
        if avatar_file.size > 5 * 1024 * 1024:
            return JsonResponse({'success': False, 'message': '图片大小不能超过5MB'})
            
        # 获取或创建用户资料
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # 读取图片数据
        avatar_data = avatar_file.read()
        
        # 保存图片数据和类型到数据库
        profile.avatar_data = avatar_data
        profile.avatar_type = avatar_file.content_type
        profile.save()
        
        # 使用to_dict方法获取完整的资料信息
        profile_data = profile.to_dict(request)
        
        return JsonResponse({
            'success': True,
            'message': '头像更新成功',
            'data': profile_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新头像失败: {str(e)}'
        }, status=500)

@csrf_exempt
def get_user_profile(request, username):
    """
    获取用户资料
    GET /api/user_profile/<username>/
    """
    try:
        user = User.objects.get(username=username)
        profile = UserProfile.objects.get(user=user)
        
        # 使用更新后的to_dict方法
        profile_data = profile.to_dict(request)
        
        return JsonResponse({
            'success': True,
            'data': profile_data
        })
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        return JsonResponse({
            'success': False,
            'message': '用户不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取用户资料失败: {str(e)}'
        }, status=500)
