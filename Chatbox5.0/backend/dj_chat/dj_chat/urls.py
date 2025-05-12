from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.shortcuts import redirect
from pathlib import Path

# 添加根URL重定向函数
def redirect_to_frontend(request):
    return redirect('/frontend/html/index.html')

urlpatterns = [
    path('', redirect_to_frontend),  # 添加根URL重定向
    path("admin/", admin.site.urls),
    path('api/', include('myapp.urls')),  # 新增：包含myapp的API路由
]

# 让开发环境下可以访问静态文件
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 让开发环境下可以访问媒体文件
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 修正：让 /frontend/ 路径可以访问 Chatbox5.0/frontend 目录下的所有文件
urlpatterns += [
    re_path(r'^frontend/(?P<path>.*)$', serve, {'document_root': str(settings.BASE_DIR.parent.parent / 'frontend')}),
]


urlpatterns += [
    re_path(r'^wasm/(?P<path>.*)$', serve, {'document_root': str(settings.BASE_DIR.parent.parent / 'wasm')}),
]

# 添加静态文件服务
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]