"""
Enhanced SessionManager that integrates with database storage

This module provides utilities to bridge the in-memory session management
with persistent database storage for chat sessions and messages.
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from django.contrib.auth.models import User

from .models import ChatSession, ChatMessage, DatabaseSessionManager
from ..agents.chatbot.messages import ConversationState


class PersistentSessionManager:
    """
    Enhanced session manager that provides database persistence for chat sessions
    """
    
    @staticmethod
    def create_session_id(user_id: str) -> str:
        """Create a unique session ID"""
        return f"session_{user_id}_{int(time.time())}"
    
    @staticmethod
    def create_initial_state(user_message: str, user_id: str, session_id: str, 
                           user: User = None) -> ConversationState:
        """
        Create initial conversation state with database persistence
        
        Args:
            user_message: User's initial message
            user_id: User identifier
            session_id: Session identifier
            user: Django User instance (optional)
            
        Returns:
            ConversationState with loaded conversation history
        """
        # Load existing conversation history from database
        conversation_history = DatabaseSessionManager.load_conversation_history(
            session_id, limit=50
        )
        
        # Add the new user message
        new_message = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save user message to database if user is provided
        if user:
            DatabaseSessionManager.save_message(
                session_id=session_id,
                user=user,
                role="user",
                content=user_message
            )
        
        # Combine history with new message
        all_messages = conversation_history + [new_message]
        
        return ConversationState(
            messages=all_messages,
            session_id=session_id,
            user_id=user_id,
            context={}
        )
    
    @staticmethod
    def save_assistant_response(session_id: str, user: User, response_data: Dict[str, Any]):
        """
        Save assistant response to database
        
        Args:
            session_id: Session identifier
            user: Django User instance
            response_data: Response data including message, task, intent, etc.
        """
        DatabaseSessionManager.save_message(
            session_id=session_id,
            user=user,
            role="assistant",
            content=response_data.get("message", ""),
            message_data=response_data.get("data", {}),
            task_type=response_data.get("task"),
            user_intent=response_data.get("user_intent"),
            confidence=response_data.get("confidence"),
            processing_time_ms=response_data.get("processing_time_ms")
        )
    
    @staticmethod
    def get_session_info(session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information and metadata
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session info or None if not found
        """
        try:
            session = ChatSession.objects.get(session_id=session_id)
            return {
                "session_id": session.session_id,
                "user_id": session.user.id,
                "username": session.user.username,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": session.message_count,
                "is_active": session.is_active,
                "context": session.context
            }
        except ChatSession.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_session_list(user: User, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get list of user's chat sessions
        
        Args:
            user: Django User instance
            limit: Maximum number of sessions to return
            
        Returns:
            List of session dictionaries
        """
        sessions = DatabaseSessionManager.get_user_sessions(user, limit)
        
        return [
            {
                "session_id": session.session_id,
                "title": session.title or f"Session {session.session_id[:8]}",
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "message_count": session.message_count,
                "last_activity": session.get_last_activity().isoformat(),
                "is_active": session.is_active
            }
            for session in sessions
        ]
    
    @staticmethod
    def archive_session(session_id: str):
        """Archive a chat session"""
        DatabaseSessionManager.archive_session(session_id)
    
    @staticmethod
    def delete_session(session_id: str):
        """Permanently delete a chat session and all its messages"""
        try:
            session = ChatSession.objects.get(session_id=session_id)
            session.delete()
            return True
        except ChatSession.DoesNotExist:
            return False