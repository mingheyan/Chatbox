from django.db import models
from django.contrib.auth.models import User
import base64

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preserved = models.BooleanField(default=False, verbose_name='保留')
    avatar_data = models.BinaryField(null=True, blank=True, verbose_name='头像数据')
    avatar_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='头像类型')
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f"{self.user.username}的资料"

    def to_dict(self, request=None):
        data = {
            'preserved': self.preserved,
            'avatar_url': '/static/images/default-avatar.png'  # 设置默认头像
        }
        if self.avatar_data:
            # 将二进制数据转换为base64字符串
            base64_data = base64.b64encode(self.avatar_data).decode('utf-8')
            data['avatar_url'] = f"data:{self.avatar_type};base64,{base64_data}"
        return data

class ChatMessage(models.Model):
    MESSAGE_TYPES = (
        ('user', '用户消息'),
        ('system', '系统消息'),
    )
    
    message_id = models.CharField(max_length=50, unique=True, verbose_name='消息ID')
    sender_id = models.CharField(max_length=50, verbose_name='发送者ID')
    content = models.TextField(verbose_name='消息内容')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='user', verbose_name='消息类型')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')

    class Meta:
        ordering = ['created_at']
        verbose_name = '聊天消息'
        verbose_name_plural = '聊天消息'
        indexes = [
            models.Index(fields=['created_at']),  # 添加时间索引以优化查询
            models.Index(fields=['sender_id']),   # 添加发送者索引
        ]

    def __str__(self):
        return f"{self.sender_id} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    dark_mode = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)
    show_timestamps = models.BooleanField(default=True)
    auto_scroll = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_settings'

    def to_dict(self):
        return {
            'dark_mode': self.dark_mode,
            'sound_enabled': self.sound_enabled,
            'show_timestamps': self.show_timestamps,
            'auto_scroll': self.auto_scroll,
        }
