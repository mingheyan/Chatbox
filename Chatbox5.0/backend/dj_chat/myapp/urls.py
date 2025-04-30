from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('generate_secret_key/', views.generate_secret_key, name='generate_secret_key'),
    path('current_user/', views.current_user, name='current_user'),
    path('logout/', views.logout, name='logout'),
    path('send_message/', views.send_message, name='send_message'),
    path('get_messages/', views.get_messages, name='get_messages'),
] 