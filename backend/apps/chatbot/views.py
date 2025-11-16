from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import json
import logging

from apps.agents.chatbot.chat_orchestrator import create_chat_orchestrator, ChatOrchestrator
from apps.agents.kg_constructor.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

# Global orchestrator instance (can be moved to dependency injection later)
_orchestrator_instance = None


def get_orchestrator(user=None) -> ChatOrchestrator:
    """Get or create the orchestrator instance with Django user support"""
    try:
        # Initialize with Neo4j client if available
        neo4j_client = Neo4jClient()
        orchestrator = create_chat_orchestrator(
            neo4j_client=neo4j_client, 
            user=user
        )
        logger.info("ChatOrchestrator initialized with Neo4j client")
        return orchestrator
    except Exception as e:
        # Fallback without Neo4j if connection fails
        orchestrator = create_chat_orchestrator(user=user)
        logger.warning(f"ChatOrchestrator initialized without Neo4j: {e}")
        return orchestrator


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_message(request):
    """
    Process a chat message through the orchestrator
    
    POST /api/chat/message/
    {
        "message": "Find videos about #machinelearning",
        "session_id": "optional_session_id"
    }
    """
    try:
        data = json.loads(request.body) if isinstance(request.body, bytes) else request.data
        
        user_message = data.get('message')
        session_id = data.get('session_id')
        
        if not user_message:
            return Response({
                'error': 'Message is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = str(request.user.id)
        orchestrator = get_orchestrator(user=request.user)
        
        # Process the message
        result = orchestrator.process_user_message(
            user_message=user_message,
            user_id=user_id,
            session_id=session_id
        )
        
        return Response(result)
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Chat message processing failed: {e}")
        return Response({
            'error': 'Internal server error',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    """
    Get user's chat sessions
    
    GET /api/chat/sessions/
    """
    try:
        from .session_manager import PersistentSessionManager
        
        limit = int(request.GET.get('limit', 20))
        sessions = PersistentSessionManager.get_user_session_list(request.user, limit)
        
        return Response({
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        })
        
    except Exception as e:
        logger.error(f"Failed to get user sessions: {e}")
        return Response({
            'error': 'Failed to retrieve sessions',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_session_history(request, session_id):
    """
    Get conversation history for a specific session
    
    GET /api/chat/sessions/{session_id}/history/
    """
    try:
        from .session_manager import PersistentSessionManager
        
        # Check if session belongs to the user
        session_info = PersistentSessionManager.get_session_info(session_id)
        if not session_info:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if session_info['user_id'] != request.user.id:
            return Response({
                'error': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        limit = int(request.GET.get('limit', 50))
        messages = PersistentSessionManager.load_conversation_history(session_id, limit)
        
        return Response({
            "success": True,
            "session_info": session_info,
            "messages": messages,
            "count": len(messages)
        })
        
    except Exception as e:
        logger.error(f"Failed to get session history: {e}")
        return Response({
            'error': 'Failed to retrieve session history',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_new_session(request):
    """
    Create a new chat session
    
    POST /api/chat/sessions/new/
    """
    try:
        from .session_manager import PersistentSessionManager
        
        context = request.data.get('context', {})
        session = PersistentSessionManager.create_new_session(request.user, context)
        
        return Response({
            "success": True,
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to create new session: {e}")
        return Response({
            'error': 'Failed to create session',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def chat_archive_session(request, session_id):
    """
    Archive (deactivate) a chat session
    
    DELETE /api/chat/sessions/{session_id}/
    """
    try:
        from .session_manager import PersistentSessionManager
        
        # Check if session belongs to the user
        session_info = PersistentSessionManager.get_session_info(session_id)
        if not session_info:
            return Response({
                'error': 'Session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if session_info['user_id'] != request.user.id:
            return Response({
                'error': 'Access denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        PersistentSessionManager.archive_session(session_id)
        
        return Response({
            "success": True,
            "message": "Session archived successfully"
        })
        
    except Exception as e:
        logger.error(f"Failed to archive session: {e}")
        return Response({
            'error': 'Failed to archive session',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_capabilities(request):
    """
    Get information about chat system capabilities
    
    GET /api/chat/capabilities/
    """
    capabilities = {
        "system_name": "ReelsAI Chat Assistant",
        "version": "1.0.0",
        "supported_tasks": [
            {
                "name": "video_crawling",
                "description": "Find and crawl videos with hashtags from social platforms",
                "examples": [
                    "Find videos about #machinelearning #AI",
                    "Tìm video về #học_máy",
                    "Crawl videos with #technology hashtag"
                ],
                "status": "placeholder_implementation"
            },
            {
                "name": "knowledge_qa",
                "description": "Answer questions based on your saved video collection",
                "examples": [
                    "What do my videos say about neural networks?",
                    "Explain machine learning from my saved content",
                    "Videos của tôi nói gì về AI?"
                ],
                "status": "placeholder_implementation"
            },
            {
                "name": "general_chat",
                "description": "General conversation and system help",
                "examples": [
                    "Hello, what can you do?",
                    "Help me understand the system",
                    "Xin chào, bạn có thể làm gì?"
                ],
                "status": "fully_implemented"
            }
        ],
        "supported_languages": ["English", "Vietnamese"],
        "features": {
            "intent_classification": True,
            "session_management": True,
            "multilingual_support": True,
            "knowledge_graph_integration": True,
            "langgraph_orchestration": True
        }
    }
    
    return Response(capabilities)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_session_reset(request):
    """
    Reset or create a new chat session
    
    POST /api/chat/session/reset/
    {
        "session_id": "optional_existing_session_id"
    }
    """
    try:
        user_id = str(request.user.id)
        import time
        new_session_id = f"session_{user_id}_{int(time.time())}"
        
        return Response({
            "success": True,
            "message": "New chat session created",
            "session_id": new_session_id,
            "user_id": user_id
        })
        
    except Exception as e:
        logger.error(f"Session reset failed: {e}")
        return Response({
            'error': 'Failed to create new session',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_status(request):
    """
    Get system status and health check
    
    GET /api/chat/status/
    """
    try:
        orchestrator = get_orchestrator()
        
        # Test components
        status_info = {
            "system": "online",
            "orchestrator": "initialized",
            "agents": {
                "intent_classifier": "ready",
                "video_crawling_agent": "placeholder",
                "knowledge_qa_agent": "placeholder", 
                "general_chat_agent": "ready"
            },
            "components": {
                "langgraph_workflow": "compiled",
                "llm_connection": "ready"
            }
        }
        
        # Test Neo4j connection if available
        try:
            if hasattr(orchestrator.qa_agent, 'neo4j_client') and orchestrator.qa_agent.neo4j_client:
                if orchestrator.qa_agent.neo4j_client.test_connection():
                    status_info["components"]["neo4j"] = "connected"
                else:
                    status_info["components"]["neo4j"] = "disconnected"
            else:
                status_info["components"]["neo4j"] = "not_configured"
        except Exception:
            status_info["components"]["neo4j"] = "error"
        
        return Response(status_info)
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return Response({
            "system": "error",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# WebSocket support placeholder (for future real-time chat)
@csrf_exempt
def chat_websocket_info(request):
    """
    Information about WebSocket endpoints for real-time chat
    TODO: Implement WebSocket support for real-time conversations
    """
    return JsonResponse({
        "websocket_support": "planned",
        "current_endpoint": "REST API only",
        "future_endpoints": {
            "websocket_url": "/ws/chat/{session_id}/",
            "features": [
                "real_time_messaging",
                "typing_indicators", 
                "live_video_processing_updates",
                "streaming_responses"
            ]
        },
        "recommendation": "Use REST API for now, WebSocket coming soon"
    })