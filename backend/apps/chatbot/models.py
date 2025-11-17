from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class ChatSession(models.Model):
    """
    Represents a chat session between a user and the AI system
    """
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Session metadata
    title = models.CharField(max_length=500, blank=True, null=True, help_text="Auto-generated session title")
    context = models.JSONField(default=dict, blank=True, help_text="Session context and metadata")
    
    # Analytics
    message_count = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0, help_text="Estimated token usage")
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        title = self.title or f"Session {self.session_id[:8]}"
        return f"{self.user.username} - {title} ({self.message_count} messages)"
    
    def get_last_activity(self):
        """Get the timestamp of the last message in this session"""
        last_message = self.messages.order_by('-created_at').first()
        return last_message.created_at if last_message else self.created_at
    
    def update_message_count(self):
        """Update the cached message count"""
        self.message_count = self.messages.count()
        self.save(update_fields=['message_count', 'updated_at'])
    
    def generate_title(self):
        """Auto-generate a title based on the first few messages"""
        first_user_message = self.messages.filter(role='user').first()
        if first_user_message:
            content = first_user_message.content[:100]
            if len(first_user_message.content) > 100:
                content += "..."
            self.title = content
            self.save(update_fields=['title'])
        return self.title


class ChatMessage(models.Model):
    """
    Represents individual messages in a chat session
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    # Message metadata
    message_data = models.JSONField(default=dict, blank=True, help_text="Additional message data and metadata")
    task_type = models.CharField(max_length=50, blank=True, null=True, help_text="Task that generated this message")
    user_intent = models.CharField(max_length=50, blank=True, null=True, help_text="Classified user intent")
    confidence = models.FloatField(null=True, blank=True, help_text="Intent classification confidence")
    
    # Analytics
    tokens_used = models.PositiveIntegerField(default=0, help_text="Estimated tokens for this message")
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True, help_text="Processing time in milliseconds")
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"
        indexes = [
            models.Index(fields=['session', 'created_at']),
            models.Index(fields=['role', 'created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        preview = self.content[:50]
        if len(self.content) > 50:
            preview += "..."
        return f"{self.role.title()}: {preview}"
    
    def save(self, *args, **kwargs):
        # Update session message count and last activity when saving messages
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.session.update_message_count()
            
            # Auto-generate session title if this is the first user message
            if self.role == 'user' and not self.session.title:
                self.session.generate_title()


class DatabaseSessionManager:
    """
    Utility class for managing chat sessions and loading conversation history
    """
    
    @staticmethod
    def get_or_create_session(session_id: str, user: User) -> ChatSession:
        """
        Get existing session or create a new one
        
        Args:
            session_id: Session identifier
            user: Django User instance
            
        Returns:
            ChatSession instance
        """
        session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': user,
                'is_active': True
            }
        )
        return session
    
    @staticmethod
    def create_new_session(user: User, context: dict = None) -> ChatSession:
        """
        Create a new chat session with auto-generated ID
        
        Args:
            user: Django User instance
            context: Optional initial context data
            
        Returns:
            New ChatSession instance
        """
        import time
        session_id = f"session_{user.id}_{int(time.time())}"
        
        return ChatSession.objects.create(
            session_id=session_id,
            user=user,
            context=context or {},
            is_active=True
        )
    
    @staticmethod
    def load_conversation_history(session_id: str, limit: int = 50) -> list:
        """
        Load conversation history for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to load
            
        Returns:
            List of message dictionaries
        """
        try:
            session = ChatSession.objects.get(session_id=session_id)
            messages = session.messages.order_by('created_at')
            
            if limit:
                messages = messages[:limit]
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat(),
                    "data": msg.message_data,
                    "task_type": msg.task_type,
                    "user_intent": msg.user_intent,
                    "confidence": msg.confidence
                }
                for msg in messages
            ]
        except ChatSession.DoesNotExist:
            return []
    
    @staticmethod
    def save_message(session_id: str, user: User, role: str, content: str, 
                    message_data: dict = None, task_type: str = None,
                    user_intent: str = None, confidence: float = None,
                    tokens_used: int = 0, processing_time_ms: int = None) -> ChatMessage:
        """
        Save a message to the database
        
        Args:
            session_id: Session identifier
            user: Django User instance
            role: Message role ('user' or 'assistant')
            content: Message content
            message_data: Additional message metadata
            task_type: Task that generated this message
            user_intent: Classified user intent
            confidence: Intent classification confidence
            tokens_used: Estimated tokens used
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            Created ChatMessage instance
        """
        session = DatabaseSessionManager.get_or_create_session(session_id, user)
        
        message = ChatMessage.objects.create(
            session=session,
            role=role,
            content=content,
            message_data=message_data or {},
            task_type=task_type,
            user_intent=user_intent,
            confidence=confidence,
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms
        )
        
        return message
    
    @staticmethod
    def get_user_sessions(user: User, limit: int = 20) -> list:
        """
        Get recent chat sessions for a user
        
        Args:
            user: Django User instance
            limit: Maximum number of sessions to return
            
        Returns:
            List of ChatSession instances
        """
        return list(
            ChatSession.objects
            .filter(user=user)
            .order_by('-updated_at')[:limit]
        )
    
    @staticmethod
    def archive_session(session_id: str):
        """
        Archive (deactivate) a chat session
        
        Args:
            session_id: Session identifier
        """
        ChatSession.objects.filter(session_id=session_id).update(is_active=False)
