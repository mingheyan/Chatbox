from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender_id', 'content', 'message_type', 'created_at')  # 列表显示的字段
    list_filter = ('message_type', 'created_at')  # 过滤器
    search_fields = ('sender_id', 'content')  # 搜索字段
    readonly_fields = ('created_at',)  # 只读字段
    ordering = ('-created_at',)  # 默认按创建时间倒序排序
    
    class Meta:
        verbose_name = '聊天消息'
        verbose_name_plural = '聊天消息'
