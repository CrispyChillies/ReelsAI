"""
API views for the chatbot application.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer, 
    SendMessageSerializer, 
    SendMessageResponseSerializer,
    SessionListSerializer,
    ChatMessageSerializer,
    ErrorResponseSerializer,
    DeleteSessionResponseSerializer,
    GetSessionMessagesResponseSerializer,
    ListSessionsResponseSerializer
)
from ..agents.chatbot.chatbot import Chatbot, ChatRequest
# from ..agents.kg_constructor.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Chatbot'],
    summary='Send a message to the chatbot',
    description='''
    Send a message to the chatbot and receive an AI response. 
    If session_id is not provided, a new session will be created.
    The chatbot uses RAG (Retrieval-Augmented Generation) tools when appropriate.
    ''',
    request=SendMessageSerializer,
    responses={
        200: SendMessageResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        500: ErrorResponseSerializer
    },
    parameters=[
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Optional session ID to continue an existing conversation'
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    Send a message to the chatbot and get an AI response.
    """
    try:
        # Validate input
        serializer = SendMessageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid input', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')
        
        # Create or get session
        if session_id:
            try:
                chat_session = ChatSession.objects.get(
                    session_id=session_id, 
                    user=request.user
                )
            except ChatSession.DoesNotExist:
                return Response(
                    {'error': f'Session {session_id} not found for this user'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Create new session
            session_id = f"session_{request.user.id}_{uuid.uuid4().hex[:8]}"
            chat_session = ChatSession.objects.create(
                session_id=session_id,
                user=request.user,
                title=user_message[:50] + "..." if len(user_message) > 50 else user_message
            )
        
        # Initialize chatbot
        try:
            # neo4j_client = Neo4jClient()
            chatbot = Chatbot(
                # neo4j_client=neo4j_client,
                user=request.user
            )
        except Exception as e:
            logger.error(f"Failed to initialize chatbot: {e}")
            return Response(
                {'error': 'Chatbot service unavailable'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Create chat request
        chat_request = ChatRequest(
            user_message=user_message,
            user_id=str(request.user.id),
            session_id=session_id
        )
        
        # Process message with chatbot
        with transaction.atomic():
            # Save user message
            user_msg = ChatMessage.objects.create(
                session=chat_session,
                message_type='human',
                content=user_message,
                metadata={'source': 'api'}
            )
            
            # Get chatbot response
            chat_response = chatbot.process_message(chat_request)
            
            if not chat_response.success:
                # Save error message
                ai_msg = ChatMessage.objects.create(
                    session=chat_session,
                    message_type='ai',
                    content=chat_response.message,
                    confidence=chat_response.confidence,
                    task_type=chat_response.task,
                    metadata=chat_response.data or {}
                )
                
                return Response(
                    {
                        'success': False,
                        'message': chat_response.message,
                        'session_id': session_id,
                        'user_message_id': user_msg.id,
                        'ai_message_id': ai_msg.id,
                        'timestamp': chat_response.timestamp
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Save successful AI response
            ai_msg = ChatMessage.objects.create(
                session=chat_session,
                message_type='ai',
                content=chat_response.message,
                used_rag_tool=chat_response.data.get('used_rag_tool', False) if chat_response.data else False,
                tool_calls_made=chat_response.data.get('tool_calls_made', False) if chat_response.data else False,
                confidence=chat_response.confidence,
                task_type=chat_response.task,
                metadata=chat_response.data or {}
            )
            
            # Update session timestamp
            chat_session.save()
        
        # Prepare response
        response_data = {
            'success': chat_response.success,
            'message': chat_response.message,
            'session_id': session_id,
            'data': chat_response.data,
            'task': chat_response.task,
            'confidence': chat_response.confidence,
            'timestamp': chat_response.timestamp,
            'user_message_id': user_msg.id,
            'ai_message_id': ai_msg.id
        }
        
        logger.info(f"Successfully processed message for user {request.user.id} in session {session_id}")
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Chatbot'],
    summary='Get messages from a chat session',
    description='''
    Retrieve all messages from a specific chat session for UI display.
    Returns messages in chronological order with metadata.
    ''',
    responses={
        200: GetSessionMessagesResponseSerializer,
        401: ErrorResponseSerializer,
        404: ErrorResponseSerializer
    },
    parameters=[
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='The session ID to retrieve messages from'
        )
    ]
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_messages(request, session_id):
    """
    Get all messages from a specific chat session.
    """
    try:
        # Get session
        chat_session = get_object_or_404(
            ChatSession,
            session_id=session_id,
            user=request.user
        )
        
        # Get all messages for this session
        messages = ChatMessage.objects.filter(
            session=chat_session
        ).order_by('timestamp')
        
        # Serialize messages
        serializer = ChatMessageSerializer(messages, many=True)
        
        logger.info(f"Retrieved {messages.count()} messages for session {session_id}")
        return Response({
            'session_id': session_id,
            'message_count': messages.count(),
            'messages': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in get_session_messages: {e}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Chatbot'],
    summary='Delete a chat session and its messages',
    description='''
    Delete a chat session and all its associated messages.
    This action is irreversible.
    ''',
    responses={
        200: DeleteSessionResponseSerializer,
        401: ErrorResponseSerializer, 
        404: ErrorResponseSerializer
    },
    parameters=[
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='The session ID to delete'
        )
    ]
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_session(request, session_id):
    """
    Delete a chat session and all its messages.
    """
    try:
        # Get session
        chat_session = get_object_or_404(
            ChatSession,
            session_id=session_id,
            user=request.user
        )
        
        # Get message count before deletion
        message_count = chat_session.messages.count()
        
        # Delete session (messages will be deleted via CASCADE)
        with transaction.atomic():
            chat_session.delete()
        
        logger.info(f"Deleted session {session_id} with {message_count} messages for user {request.user.id}")
        return Response({
            'success': True,
            'message': f'Session {session_id} deleted successfully',
            'deleted_messages': message_count
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in delete_session: {e}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['Chatbot'],
    summary='List all chat sessions for the authenticated user',
    description='''
    Get a list of all chat sessions for the authenticated user.
    Includes session metadata and message previews.
    ''',
    responses={
        200: ListSessionsResponseSerializer,
        401: ErrorResponseSerializer
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_sessions(request):
    """
    Get all chat sessions for the authenticated user.
    """
    try:
        # Get all sessions for the user
        sessions = ChatSession.objects.filter(
            user=request.user
        ).prefetch_related('messages')
        
        # Serialize sessions
        serializer = SessionListSerializer(sessions, many=True)
        
        logger.info(f"Retrieved {sessions.count()} sessions for user {request.user.id}")
        return Response({
            'session_count': sessions.count(),
            'sessions': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in list_sessions: {e}")
        return Response(
            {'error': 'Internal server error', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
