"""
Message-related classes and utilities for the chat orchestrator system

This module contains:
- Message state management
- Agent response formats
- Message processing utilities
- Session management
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel


class ConversationState(BaseModel):
    """State model for the conversation flow"""
    messages: List[Dict[str, Any]] = []
    current_task: Optional[str] = None
    user_intent: Optional[str] = None
    context: Dict[str, Any] = {}
    session_id: str = ""
    user_id: str = ""


@dataclass
class AgentResponse:
    """Standard response format for all agents"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    next_action: Optional[str] = None
    error: Optional[str] = None


class MessageFormatter:
    """Utility class for formatting different types of messages"""
    
    @staticmethod
    def format_success_response(message: str, data: Dict[str, Any] = None, 
                              next_action: str = None) -> AgentResponse:
        """Create a successful agent response"""
        return AgentResponse(
            success=True,
            message=message,
            data=data or {},
            next_action=next_action
        )
    
    @staticmethod
    def format_error_response(message: str, error: str = None) -> AgentResponse:
        """Create an error agent response"""
        return AgentResponse(
            success=False,
            message=message,
            error=error
        )
    
    @staticmethod
    def format_video_crawling_response(hashtags: List[str], topics: List[str], 
                                     found_videos: int = 15) -> AgentResponse:
        """Format response for video crawling requests"""
        mock_results = {
            "found_videos": found_videos,
            "hashtags_searched": hashtags,
            "topics_searched": topics,
            "processing_status": "queued",
            "estimated_completion": "5-10 minutes"
        }
        
        message = f"""🔍 Video Crawling Initiated!
        
I'm searching for videos with the following criteria:
📱 Hashtags: {', '.join(hashtags) if hashtags else 'None specified'}
📋 Topics: {', '.join(topics) if topics else 'Auto-detected from hashtags'}

📊 Preliminary Results:
• Found approximately {mock_results['found_videos']} matching videos
• Processing status: {mock_results['processing_status']}
• Estimated completion: {mock_results['estimated_completion']}

The videos will be processed through our analysis pipeline and added to your knowledge graph. You'll be notified when complete!

💡 While processing, you can ask me questions about your existing video knowledge."""
        
        return MessageFormatter.format_success_response(
            message=message,
            data=mock_results,
            next_action="monitor_crawling_progress"
        )
    
    @staticmethod
    def format_knowledge_qa_response(question: str, user_id: str, 
                                   relevant_videos: int = 3) -> AgentResponse:
        """Format response for knowledge Q&A requests"""
        mock_knowledge = {
            "relevant_videos": relevant_videos,
            "key_concepts": ["machine learning", "neural networks", "deep learning"],
            "confidence_score": 0.85,
            "sources": [
                {"video_id": "vid_123", "title": "Intro to ML", "timestamp": "2:30"},
                {"video_id": "vid_456", "title": "Neural Network Basics", "timestamp": "5:15"}
            ]
        }
        
        message = f"""🧠 Knowledge Answer:

Based on your saved video collection, here's what I found about your question:

**Question:** {question}

**Answer:** 
From your {mock_knowledge['relevant_videos']} relevant videos, I can tell you that machine learning is a subset of artificial intelligence that enables computers to learn patterns from data without being explicitly programmed.

**Key Related Concepts:**
{chr(10).join(f'• {concept}' for concept in mock_knowledge['key_concepts'])}

**Sources from your videos:**
{chr(10).join(f'📹 {source["title"]} (at {source["timestamp"]})' for source in mock_knowledge['sources'])}

**Confidence:** {mock_knowledge['confidence_score']:.0%}

💡 Want to explore this topic further? I can find more related videos or answer follow-up questions!"""
        
        return MessageFormatter.format_success_response(
            message=message,
            data=mock_knowledge,
            next_action="suggest_related_topics"
        )
    
    @staticmethod
    def format_greeting_response() -> AgentResponse:
        """Format greeting and capability overview response"""
        message = """👋 Hello! I'm your AI video knowledge assistant!

I can help you with:

🔍 **Video Discovery**
• Find and crawl videos with specific hashtags
• Search across multiple platforms (TikTok, YouTube, Instagram)
• Example: "Find videos about #machinelearning #AI"

🧠 **Knowledge Q&A**  
• Answer questions from your saved video collection
• Explain concepts and relationships between topics
• Example: "What did my videos say about neural networks?"

🌐 **Multilingual Support**
• Works in both English and Vietnamese
• Example: "Tìm video về #học_máy" or "Videos nói gì về AI?"

What would you like to explore today?"""
        
        return MessageFormatter.format_success_response(
            message=message,
            data={"chat_type": "greeting", "helpful": True}
        )
    
    @staticmethod
    def format_capabilities_response() -> AgentResponse:
        """Format system capabilities response"""
        message = """🚀 **My Capabilities**

**🎬 Video Management:**
• Crawl videos from social platforms using hashtags
• Process video content (transcription, summarization)
• Build knowledge graphs from video content
• Support both Vietnamese and English content

**💡 Knowledge Assistant:**
• Answer questions based on your video library
• Find connections between different topics
• Provide personalized insights from your content
• Multi-language support for global learning

**🔗 Smart Features:**
• Cross-reference information across videos
• Identify knowledge gaps in your collection
• Suggest related content and learning paths
• Cultural adaptation for Vietnamese vs English content

Try asking me to find videos or ask about your existing knowledge!"""
        
        return MessageFormatter.format_success_response(
            message=message,
            data={"chat_type": "capabilities", "helpful": True}
        )
    
    @staticmethod
    def format_generic_help_response() -> AgentResponse:
        """Format generic help response"""
        message = """I'm here to help with your video knowledge needs! 

You can:
• Ask me to find videos: "Find videos about #technology"
• Ask questions about your content: "What do my videos say about AI?"
• Get help: "What can you do?"

What would you like to explore?"""
        
        return MessageFormatter.format_success_response(
            message=message,
            data={"chat_type": "general", "helpful": True}
        )


class SessionManager:
    """Utility class for managing chat sessions"""
    
    @staticmethod
    def create_session_id(user_id: str) -> str:
        """Generate a new session ID"""
        return f"session_{user_id}_{int(datetime.now().timestamp())}"
    
    @staticmethod
    def add_user_message(state: ConversationState, message: str) -> ConversationState:
        """Add a user message to the conversation state"""
        state.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        return state
    
    @staticmethod
    def add_assistant_message(state: ConversationState, response: AgentResponse) -> ConversationState:
        """Add an assistant message to the conversation state"""
        state.messages.append({
            "role": "assistant",
            "content": response.message,
            "data": response.data,
            "timestamp": datetime.now().isoformat()
        })
        return state
    
    @staticmethod
    def create_initial_state(user_message: str, user_id: str, session_id: str) -> ConversationState:
        """Create initial conversation state"""
        return ConversationState(
            messages=[{
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            }],
            session_id=session_id,
            user_id=user_id,
            context={}
        )


class MessageValidator:
    """Utility class for validating messages and inputs"""
    
    @staticmethod
    def validate_user_message(message: str) -> tuple[bool, str]:
        """
        Validate user input message
        
        Returns:
            (is_valid, error_message)
        """
        if not message:
            return False, "Message cannot be empty"
        
        if not isinstance(message, str):
            return False, "Message must be a string"
        
        if len(message.strip()) == 0:
            return False, "Message cannot be only whitespace"
        
        if len(message) > 5000:  # Reasonable limit
            return False, "Message is too long (max 5000 characters)"
        
        return True, ""
    
    @staticmethod
    def validate_session_data(user_id: str, session_id: str = None) -> tuple[bool, str]:
        """
        Validate session data
        
        Returns:
            (is_valid, error_message)
        """
        if not user_id:
            return False, "User ID is required"
        
        if not isinstance(user_id, str):
            return False, "User ID must be a string"
        
        if session_id and not isinstance(session_id, str):
            return False, "Session ID must be a string"
        
        return True, ""


# Message type constants
class MessageTypes:
    """Constants for different message types"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Intent constants
class IntentTypes:
    """Constants for different intent types"""
    VIDEO_CRAWLING = "VIDEO_CRAWLING"
    KNOWLEDGE_QA = "KNOWLEDGE_QA"
    GENERAL_CHAT = "GENERAL_CHAT"


# Task constants
class TaskTypes:
    """Constants for different task types"""
    VIDEO_CRAWLING = "video_crawling"
    KNOWLEDGE_QA = "knowledge_qa"
    GENERAL_CHAT = "general_chat"
    ERROR = "error"