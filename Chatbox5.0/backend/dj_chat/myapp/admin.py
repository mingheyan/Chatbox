from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import ChatMessage, UserProfile, UserSettings

# 取消注册默认的User管理器
admin.site.unregister(User)

# 创建UserProfile的内联管理器
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = '用户资料'
    verbose_name_plural = '用户资料'

# 创建UserSettings的内联管理器
class UserSettingsInline(admin.StackedInline):
    model = UserSettings
    can_delete = False
    verbose_name = '用户设置'
    verbose_name_plural = '用户设置'

# 自定义User管理器
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline, UserSettingsInline)
    list_display = ('username', 'email', 'is_staff', 'is_active', 'get_preserved', 'get_dark_mode', 'get_sound_enabled')
    
    def get_preserved(self, obj):
        try:
            return obj.profile.preserved
        except UserProfile.DoesNotExist:
            return False
    get_preserved.short_description = '保留'
    get_preserved.boolean = True

    def get_dark_mode(self, obj):
        try:
            return obj.settings.dark_mode
        except UserSettings.DoesNotExist:
            return False
    get_dark_mode.short_description = '深色模式'
    get_dark_mode.boolean = True

    def get_sound_enabled(self, obj):
        try:
            return obj.settings.sound_enabled
        except UserSettings.DoesNotExist:
            return True
    get_sound_enabled.short_description = '声音开启'
    get_sound_enabled.boolean = True

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
