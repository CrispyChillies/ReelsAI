"""
URL configuration for the chatbot application.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Chatbot message endpoints
    path('send-message/', views.send_message, name='chatbot_send_message'),
    path('sessions/', views.list_sessions, name='chatbot_list_sessions'),
    path('sessions/<str:session_id>/messages/', views.get_session_messages, name='chatbot_session_messages'),
    path('sessions/<str:session_id>/delete/', views.delete_session, name='chatbot_delete_session'),
    path('sessions/<str:session_id>/rename/', views.rename_session, name='chatbot_rename_session'),
]