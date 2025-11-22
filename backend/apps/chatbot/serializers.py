"""
Serializers for the chatbot application.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'message_type',
            'content',
            'timestamp',
            'used_rag_tool',
            'tool_calls_made',
            'confidence',
            'task_type',
            'metadata'
        ]
        read_only_fields = [
            'id',
            'timestamp',
            'used_rag_tool',
            'tool_calls_made',
            'confidence',
            'task_type',
            'metadata'
        ]


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'session_id',
            'created_at',
            'updated_at',
            'title',
            'message_count',
            'messages'
        ]
        read_only_fields = [
            'session_id',
            'created_at',
            'updated_at'
        ]
    
    def get_message_count(self, obj):
        """Get the number of messages in this session"""
        return obj.messages.count()


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a message to the chatbot"""
    message = serializers.CharField(max_length=5000, help_text="The message to send to the chatbot")
    session_id = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True,
        help_text="Session ID for the conversation. If not provided, a new session will be created."
    )


class SendMessageResponseSerializer(serializers.Serializer):
    """Serializer for the chatbot response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    session_id = serializers.CharField()
    data = serializers.JSONField(required=False)
    task = serializers.CharField(required=False)
    confidence = serializers.FloatField(required=False)
    timestamp = serializers.CharField()
    
    # Additional fields for the complete response
    user_message_id = serializers.UUIDField(required=False)
    ai_message_id = serializers.UUIDField(required=False)


class SessionListSerializer(serializers.ModelSerializer):
    """Serializer for listing chat sessions without messages"""
    message_count = serializers.SerializerMethodField()
    last_message_timestamp = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'session_id',
            'created_at',
            'updated_at',
            'title',
            'message_count',
            'last_message_timestamp',
            'last_message_preview'
        ]
    
    def get_message_count(self, obj) -> int:
        """Get the number of messages in this session"""
        return obj.messages.count()
    
    def get_last_message_timestamp(self, obj) -> str:
        """Get timestamp of the last message"""
        last_message = obj.messages.last()
        return last_message.timestamp.isoformat() if last_message else None
    
    def get_last_message_preview(self, obj) -> str:
        """Get a preview of the last message"""
        last_message = obj.messages.last()
        if last_message:
            content = last_message.content
            return content[:100] + "..." if len(content) > 100 else content
        return None


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses"""
    error = serializers.CharField()
    details = serializers.CharField(required=False)


class DeleteSessionResponseSerializer(serializers.Serializer):
    """Serializer for delete session response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    deleted_messages = serializers.IntegerField()


class GetSessionMessagesResponseSerializer(serializers.Serializer):
    """Serializer for get session messages response"""
    session_id = serializers.CharField()
    message_count = serializers.IntegerField()
    messages = ChatMessageSerializer(many=True)


class ListSessionsResponseSerializer(serializers.Serializer):
    """Serializer for list sessions response"""
    session_count = serializers.IntegerField()
    sessions = SessionListSerializer(many=True)

class RenameSessionSerializer(serializers.Serializer):
    """Serializer for renaming a chat session"""
    title = serializers.CharField(
        max_length=100,
        min_length=1,
        help_text="New title for the chat session (1-100 characters)"
    )


class RenameSessionResponseSerializer(serializers.Serializer):
    """Serializer for rename session response"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    session_id = serializers.CharField()
    old_title = serializers.CharField()
    new_title = serializers.CharField()
