from django.db import models

# Create your models here.
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
