from django.urls import path
from . import views

urlpatterns = [
    # Core chat endpoints
    path('message/', views.chat_message, name='chat_message'),
    path('capabilities/', views.chat_capabilities, name='chat_capabilities'),
    path('session/reset/', views.chat_session_reset, name='chat_session_reset'),
    path('status/', views.system_status, name='system_status'),
    
    # Session management endpoints  
    path('sessions/', views.chat_sessions, name='chat_sessions'),
    path('sessions/new/', views.chat_new_session, name='chat_new_session'),
    path('sessions/<str:session_id>/history/', views.chat_session_history, name='chat_session_history'),
    path('sessions/<str:session_id>/', views.chat_archive_session, name='chat_archive_session'),
    
    # Future WebSocket info
    path('websocket/', views.chat_websocket_info, name='websocket_info'),
]