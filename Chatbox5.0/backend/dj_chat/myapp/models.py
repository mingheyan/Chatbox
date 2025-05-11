from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preserved = models.BooleanField(default=False, verbose_name='保留')
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f"{self.user.username}的资料"

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
