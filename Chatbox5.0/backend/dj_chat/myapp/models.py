from django.db import models
from django.contrib.auth.models import User  # Django内置的用户模型
import base64  # 用于头像数据的base64编码

# Create your models here.
class UserProfile(models.Model):
    """用户档案模型
    存储用户的额外信息，如头像等
    与User模型是一对一关系
    """
    # OneToOneField创建一对一关系，CASCADE表示用户删除时档案也会被删除
    # related_name='profile'允许通过user.profile访问用户档案
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 标记是否为保留用户（如系统用户、管理员等）
    preserved = models.BooleanField(default=False, verbose_name='保留')
    
    # 存储头像的二进制数据，允许为空
    avatar_data = models.BinaryField(null=True, blank=True, verbose_name='头像数据')
    
    # 存储头像的MIME类型，如'image/jpeg'、'image/png'等
    avatar_type = models.CharField(max_length=50, null=True, blank=True, verbose_name='头像类型')
    
    class Meta:
        """模型的元数据类"""
        verbose_name = '用户资料'  # 在管理界面中显示的单数名称
        verbose_name_plural = '用户资料'  # 在管理界面中显示的复数名称

    def __str__(self):
        """返回模型的字符串表示"""
        return f"{self.user.username}的资料"

    def to_dict(self, request=None):
        """将用户档案转换为字典格式
        用于API响应和JSON序列化
        """
        data = {
            'preserved': self.preserved,
            'avatar_url': '/static/images/default-avatar.png'  # 默认头像路径
        }
        if self.avatar_data:
            # 如果存在头像数据，将其转换为base64格式的Data URL
            base64_data = base64.b64encode(self.avatar_data).decode('utf-8')
            data['avatar_url'] = f"data:{self.avatar_type};base64,{base64_data}"
        return data

class ChatMessage(models.Model):
    """聊天消息模型
    存储所有的聊天消息记录
    """
    # 消息类型的选项元组
    MESSAGE_TYPES = (
        ('user', '用户消息'),    # 普通用户发送的消息
        ('system', '系统消息'),  # 系统自动发送的消息
    )
    
    # UUID或其他唯一标识符，用于消息的唯一标识
    message_id = models.CharField(max_length=50, unique=True, verbose_name='消息ID')
    
    # 发送者的标识符（可以是用户名或其他ID）
    sender_id = models.CharField(max_length=50, verbose_name='发送者ID')
    
    # 消息的具体内容
    content = models.TextField(verbose_name='消息内容')
    
    # 消息类型，默认为用户消息
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='user', verbose_name='消息类型')
    
    # 消息创建时间，自动设置为当前时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='发送时间')

    class Meta:
        """消息模型的元数据"""
        ordering = ['created_at']  # 按时间顺序排序
        verbose_name = '聊天消息'
        verbose_name_plural = '聊天消息'
        indexes = [
            models.Index(fields=['created_at']),  # 创建时间索引，优化消息查询性能
            models.Index(fields=['sender_id']),   # 发送者索引，优化按用户查询性能
        ]

    def __str__(self):
        """返回消息的字符串表示"""
        return f"{self.sender_id} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

class UserSettings(models.Model):
    """用户设置模型
    存储用户的个性化偏好设置
    """
    # 与User模型的一对一关系
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # 是否启用暗色模式
    dark_mode = models.BooleanField(default=True)
    
    # 是否启用声音提醒
    sound_enabled = models.BooleanField(default=True)
    
    # 是否显示时间戳
    show_timestamps = models.BooleanField(default=True)
    
    # 是否启用自动滚动
    auto_scroll = models.BooleanField(default=True)
    
    # 记录创建时间
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 记录最后更新时间，每次保存时自动更新
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """设置模型的元数据"""
        db_table = 'user_settings'  # 指定数据库表名

    def to_dict(self):
        """将设置转换为字典格式
        用于API响应和JSON序列化
        """
        return {
            'dark_mode': self.dark_mode,
            'sound_enabled': self.sound_enabled,
            'show_timestamps': self.show_timestamps,
            'auto_scroll': self.auto_scroll,
        }
