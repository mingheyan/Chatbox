import logging
logger = logging.getLogger('myapp')

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
        logger.debug(f"生成新的密钥")
        return JsonResponse({'success': True, 'secret_key': key})
    return JsonResponse({'success': False, 'msg': '仅支持POST'})

@csrf_exempt
def register(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
        secret_key = data.get('secret_key')
        
        logger.debug(f"收到注册请求: username={username}")
        
        if not username or not password or not secret_key:
            logger.warning(f"注册失败: 缺少必要参数")
            return JsonResponse({'success': False, 'msg': '用户名、密码和密钥不能为空'})
            
        if SECRET_KEY_STORAGE['key'] is None:
            logger.error("注册失败: 系统密钥未生成")
            return JsonResponse({'success': False, 'msg': '密钥未生成，请联系管理员'})
            
        if secret_key != SECRET_KEY_STORAGE['key']:
            logger.warning(f"注册失败: 密钥错误 username={username}")
            return JsonResponse({'success': False, 'msg': '密钥错误'})
            
        if User.objects.filter(username=username).exists():
            logger.warning(f"注册失败: 用户名已存在 username={username}")
            return JsonResponse({'success': False, 'msg': '用户名已存在'})
            
        try:
            user = User.objects.create_user(username=username, password=password)
            profile = UserProfile.objects.create(user=user)
            settings = UserSettings.objects.create(user=user)
            user_settings = settings.to_dict()
            profile_data = profile.to_dict(request)
            user_settings.update(profile_data)
            
            logger.debug(f"用户注册成功: username={username}")
            return JsonResponse({
                'success': True,
                'msg': '注册成功',
                'data': {
                    'username': user.username,
                    'settings': user_settings
                }
            })
        except Exception as e:
            logger.error(f"用户注册异常: username={username}, error={str(e)}")
            return JsonResponse({'success': False, 'msg': f'注册失败: {str(e)}'})
            
    return JsonResponse({'success': False, 'msg': '仅支持POST'})

@csrf_exempt
def login(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
        
        logger.info(f"收到登录请求: username={username}")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            settings, _ = UserSettings.objects.get_or_create(user=user)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            
            user_settings = settings.to_dict()
            profile_data = profile.to_dict(request)
            user_settings.update(profile_data)
            
            logger.debug(f"用户登录成功: username={username}")
            return JsonResponse({
                'success': True,
                'msg': '登录成功',
                'data': {
                    'username': user.username,
                    'settings': user_settings
                }
            })
        else:
            logger.warning(f"登录失败: 用户名或密码错误 username={username}")
            return JsonResponse({'success': False, 'msg': '用户名或密码错误'})
    return JsonResponse({'success': False, 'msg': '仅支持POST'})

@csrf_exempt
def current_user(request):
    if request.user.is_authenticated:
        return JsonResponse({'success': True, 'username': request.user.username,'settings': request.user.settings.to_dict(),'profile': request.user.profile.to_dict(request)})
    else:
        return JsonResponse({'success': False, 'msg': '未登录'})

@csrf_exempt
def logout(request):
    if request.user.is_authenticated:
        username = request.user.username
        auth_logout(request)
        logger.debug(f"用户登出成功: username={username}")
        return JsonResponse({'success': True, 'msg': '已登出'})
    logger.debug("未登录用户尝试登出")
    return JsonResponse({'success': True, 'msg': '已登出'})

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """
    发送消息的接口
    POST /api/send_message/
    """
    try:
        logger.debug(f"收到发送消息请求: Content-Type={request.content_type}")
        
        if request.content_type != 'application/json':
            logger.warning("消息发送失败: Content-Type 不是 application/json")
            return JsonResponse({
                'success': False,
                'message': 'Content-Type must be application/json'
            }, status=400)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"消息发送失败: JSON解析错误 error={str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Invalid JSON: {str(e)}'
            }, status=400)

        required_fields = ['sender_id', 'content']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning(f"消息发送失败: 缺少必要字段 missing_fields={missing_fields}")
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
        
        logger.debug(f"消息发送成功: sender_id={data['sender_id']}, message_id={message.message_id}")
        return JsonResponse({
            'success': True,
            'message': '消息发送成功',
            'data': {
                'message_id': message.message_id,
                'timestamp': message.created_at.timestamp()
            }
        })
    except Exception as e:
        logger.error(f"消息发送异常: error={str(e)}")
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
    """
    try:
        before_timestamp = float(request.GET.get('before', time.time()))
        limit = int(request.GET.get('limit', 20))
        
        logger.debug(f"获取历史消息: before={before_timestamp}, limit={limit}")
        
        before_time = datetime.fromtimestamp(before_timestamp)
        messages = ChatMessage.objects.filter(
            created_at__lt=before_time
        ).order_by('-created_at')[:limit]
        
        message_list = [{
            'message_id': msg.message_id,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'message_type': msg.message_type,
            'timestamp': msg.created_at.timestamp()
        } for msg in reversed(messages)]
        
        logger.debug(f"成功获取历史消息: count={len(message_list)}")
        return JsonResponse({
            'success': True,
            'data': message_list
        })
    except Exception as e:
        logger.error(f"获取历史消息失败: error={str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'获取消息失败: {str(e)}'
        }, status=500)

@csrf_exempt
@login_required
def get_user_settings(request):
    """
    获取用户设置
    GET /api/settings/
    """
    try:
        settings, _ = UserSettings.objects.get_or_create(user=request.user)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        
        user_settings = settings.to_dict()
        profile_data = profile.to_dict(request)
        user_settings.update(profile_data)
        
        logger.debug(f"获取用户设置成功: username={request.user.username}")
        return JsonResponse({
            'success': True,
            'data': user_settings
        })
    except Exception as e:
        logger.error(f"获取用户设置失败: username={request.user.username}, error={str(e)}")
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
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            settings, _ = UserSettings.objects.get_or_create(user=request.user)
            
            # 更新设置
            for field in ['dark_mode', 'sound_enabled', 'show_timestamps', 'auto_scroll']:
                if field in data:
                    setattr(settings, field, data[field])
            
            settings.save()
            logger.debug(f"更新用户设置成功: username={request.user.username}")
            
            return JsonResponse({
                'success': True,
                'message': '设置已更新',
                'data': settings.to_dict()
            })
        except Exception as e:
            logger.error(f"更新用户设置失败: username={request.user.username}, error={str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'更新设置失败: {str(e)}'
            }, status=500)
    return JsonResponse({'success': False, 'message': '仅支持POST请求'})

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
            logger.warning(f"更新头像失败: 未找到头像文件 username={request.user.username}")
            return JsonResponse({'success': False, 'message': '未找到头像文件'})
        
        avatar_file = request.FILES['avatar']
        
        # 验证文件类型
        if not avatar_file.content_type.startswith('image/'):
            logger.warning(f"更新头像失败: 文件类型错误 username={request.user.username}, content_type={avatar_file.content_type}")
            return JsonResponse({'success': False, 'message': '仅支持图片文件'})
            
        # 验证文件大小（限制为5MB）
        if avatar_file.size > 5 * 1024 * 1024:
            logger.warning(f"更新头像失败: 文件过大 username={request.user.username}, size={avatar_file.size}")
            return JsonResponse({'success': False, 'message': '图片大小不能超过5MB'})
            
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # 读取图片数据
        avatar_data = avatar_file.read()
        
        # 保存图片数据和类型到数据库
        profile.avatar_data = avatar_data
        profile.avatar_type = avatar_file.content_type
        profile.save()
        
        logger.debug(f"更新头像成功: username={request.user.username}, size={len(avatar_data)}")
        
        # 使用to_dict方法获取完整的资料信息
        profile_data = profile.to_dict(request)
        
        return JsonResponse({
            'success': True,
            'message': '头像更新成功',
            'data': profile_data
        })
        
    except Exception as e:
        logger.error(f"更新头像异常: username={request.user.username}, error={str(e)}")
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
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile_data = profile.to_dict(request)
        
        logger.debug(f"获取用户资料成功: target_username={username}")
        return JsonResponse({
            'success': True,
            'data': profile_data
        })
    except User.DoesNotExist:
        logger.warning(f"获取用户资料失败: 用户不存在 username={username}")
        return JsonResponse({
            'success': False,
            'message': '用户不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"获取用户资料异常: username={username}, error={str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'获取用户资料失败: {str(e)}'
        }, status=500)
