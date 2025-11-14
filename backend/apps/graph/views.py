from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.conf import settings
import logging
import json

from .models import VideoSummarizationRequest, KnowledgeGraphStatistics
from ..agents.kg_constructor.video_summarization_processor import VideoSummarizationProcessor
from ..agents.kg_constructor.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_video_summarization(request):
    """
    Process video summarization and create knowledge graph.
    
    Expected payload:
    {
        "user": {
            "user_id": "user_123",
            "name": "John Doe",
            "email": "john@example.com"
        },
        "video": {
            "video_id": "video_456",
            "title": "Video Title",
            "description": "Video description",
            "duration": 1800,
            "upload_date": "2025-11-10T10:00:00Z",
            "url": "https://example.com/video/456"
        },
        "topic": {
            "name": "Machine Learning",
            "description": "Topic description",
            "category": "Technology"
        },
        "source": {
            "name": "Source Name",
            "type": "Educational Platform",
            "url": "https://source.example.com",
            "description": "Source description"
        },
        "summarization": "The video summarization text content..."
    }
    """
    try:
        payload = request.data
        
        # Validate basic payload structure
        if not payload:
            return Response({
                'error': 'Empty payload'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract basic information for tracking
        video_data = payload.get('video', {})
        topic_data = payload.get('topic', {})
        source_data = payload.get('source', {})
        
        video_id = video_data.get('video_id', '')
        topic_name = topic_data.get('name', '') if isinstance(topic_data, dict) else str(topic_data)
        source_name = source_data.get('name', '') if isinstance(source_data, dict) else str(source_data)
        
        if not video_id:
            return Response({
                'error': 'video_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create tracking record
        with transaction.atomic():
            summarization_request = VideoSummarizationRequest.objects.create(
                user=request.user,
                video_id=video_id,
                topic=topic_name,
                source=source_name,
                payload=payload,
                status='processing',
                processing_started_at=timezone.now()
            )
        
        try:
            # Process the video summarization
            processor = VideoSummarizationProcessor()
            result = processor.process_video_summarization(payload)
            
            # Update tracking record with results
            with transaction.atomic():
                summarization_request.processing_completed_at = timezone.now()
                summarization_request.processing_time_seconds = result.get('processing_time_seconds')
                summarization_request.processing_result = result
                
                if result.get('status') == 'success':
                    summarization_request.status = 'completed'
                else:
                    summarization_request.status = 'failed'
                    summarization_request.error_message = result.get('error_message', 'Unknown error')
                
                summarization_request.save()
            
            # Create statistics snapshot if successful
            if result.get('status') == 'success' and result.get('graph_statistics'):
                KnowledgeGraphStatistics.create_from_neo4j_stats(result['graph_statistics'])
            
            # Return success response
            return Response({
                'request_id': summarization_request.id,
                'status': result.get('status'),
                'processing_time_seconds': result.get('processing_time_seconds'),
                'extracted_entities': result.get('extracted_entities', 0),
                'extracted_relations': result.get('extracted_relations', 0),
                'upserted_entities': result.get('upserted_entities', 0),
                'graph_statistics': result.get('graph_statistics'),
                'node_ids': result.get('node_ids'),
                'message': 'Video summarization processed successfully' if result.get('status') == 'success' else result.get('error_message')
            }, status=status.HTTP_200_OK if result.get('status') == 'success' else status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.error(f"Error processing video summarization: {e}")
            
            # Update tracking record with error
            with transaction.atomic():
                summarization_request.status = 'failed'
                summarization_request.error_message = str(e)
                summarization_request.processing_completed_at = timezone.now()
                summarization_request.save()
            
            return Response({
                'request_id': summarization_request.id,
                'error': f'Processing failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Unexpected error in process_video_summarization: {e}")
        return Response({
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_processing_status(request, request_id):
    """
    Get the status of a video summarization processing request.
    """
    try:
        summarization_request = VideoSummarizationRequest.objects.get(
            id=request_id,
            user=request.user
        )
        
        return Response({
            'request_id': summarization_request.id,
            'status': summarization_request.status,
            'video_id': summarization_request.video_id,
            'topic': summarization_request.topic,
            'source': summarization_request.source,
            'created_at': summarization_request.created_at,
            'processing_started_at': summarization_request.processing_started_at,
            'processing_completed_at': summarization_request.processing_completed_at,
            'processing_time_seconds': summarization_request.processing_time_seconds,
            'extracted_entities_count': summarization_request.extracted_entities_count,
            'extracted_relations_count': summarization_request.extracted_relations_count,
            'error_message': summarization_request.error_message,
            'processing_result': summarization_request.processing_result
        }, status=status.HTTP_200_OK)
    
    except VideoSummarizationRequest.DoesNotExist:
        return Response({
            'error': 'Request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_requests(request):
    """
    List all video summarization requests for the authenticated user.
    """
    requests = VideoSummarizationRequest.objects.filter(user=request.user)
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    video_id_filter = request.GET.get('video_id')
    if video_id_filter:
        requests = requests.filter(video_id=video_id_filter)
    
    # Pagination
    page_size = min(int(request.GET.get('page_size', 20)), 100)
    page = int(request.GET.get('page', 1))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = requests.count()
    requests = requests[start:end]
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'requests': [
            {
                'request_id': req.id,
                'status': req.status,
                'video_id': req.video_id,
                'topic': req.topic,
                'source': req.source,
                'created_at': req.created_at,
                'processing_time_seconds': req.processing_time_seconds,
                'extracted_entities_count': req.extracted_entities_count,
                'extracted_relations_count': req.extracted_relations_count,
                'error_message': req.error_message if req.status == 'failed' else None
            } for req in requests
        ]
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_graph_statistics(request):
    """
    Get current knowledge graph statistics.
    """
    try:
        # Get from Neo4j
        neo4j_client = Neo4jClient()
        current_stats = neo4j_client.get_graph_stats()
        neo4j_client.close()
        
        # Get latest stored statistics
        try:
            latest_stored_stats = KnowledgeGraphStatistics.objects.latest()
        except KnowledgeGraphStatistics.DoesNotExist:
            latest_stored_stats = None
        
        return Response({
            'current_stats': current_stats,
            'latest_stored_stats': {
                'timestamp': latest_stored_stats.timestamp,
                'total_nodes': latest_stored_stats.total_nodes,
                'total_relationships': latest_stored_stats.total_relationships,
                'user_nodes': latest_stored_stats.user_nodes,
                'video_nodes': latest_stored_stats.video_nodes,
                'topic_nodes': latest_stored_stats.topic_nodes,
                'source_nodes': latest_stored_stats.source_nodes,
                'entity_nodes': latest_stored_stats.entity_nodes
            } if latest_stored_stats else None
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting graph statistics: {e}")
        return Response({
            'error': f'Failed to get statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_entities(request):
    """
    Search for entities in the knowledge graph.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return Response({
            'error': 'Query parameter "q" is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    limit = min(int(request.GET.get('limit', 10)), 100)
    
    try:
        neo4j_client = Neo4jClient()
        entities = neo4j_client.search_entities(query, limit)
        neo4j_client.close()
        
        return Response({
            'query': query,
            'entities': entities,
            'count': len(entities)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error searching entities: {e}")
        return Response({
            'error': f'Search failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_video_knowledge_graph(request, video_id):
    """
    Get the complete knowledge graph for a specific video.
    """
    try:
        neo4j_client = Neo4jClient()
        graph_data = neo4j_client.get_video_knowledge_graph(video_id)
        neo4j_client.close()
        
        return Response({
            'video_id': video_id,
            'nodes': graph_data['nodes'],
            'relationships': graph_data['relationships'],
            'summary': {
                'node_count': len(graph_data['nodes']),
                'relationship_count': len(graph_data['relationships'])
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting video knowledge graph: {e}")
        return Response({
            'error': f'Failed to get video knowledge graph: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_neo4j_connection(request):
    """
    Test Neo4j database connection.
    """
    try:
        neo4j_client = Neo4jClient()
        is_connected = neo4j_client.test_connection()
        neo4j_client.close()
        
        return Response({
            'connected': is_connected,
            'message': 'Connection successful' if is_connected else 'Connection failed'
        }, status=status.HTTP_200_OK if is_connected else status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        return Response({
            'connected': False,
            'message': f'Connection test failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resolution_statistics(request):
    """
    Get graph resolution statistics.
    
    Query parameters:
    - video_id: Optional specific video ID
    """
    try:
        video_id = request.GET.get('video_id', None)
        
        neo4j_client = Neo4jClient()
        stats = neo4j_client.get_resolution_statistics(video_id)
        neo4j_client.close()
        
        return Response({
            'resolution_statistics': stats,
            'video_id': video_id
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting resolution statistics: {e}")
        return Response({
            'error': f'Failed to get resolution statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conflict_flags(request):
    """
    Get conflict flags that need manual review.
    
    Query parameters:
    - status: Filter by conflict status (default: 'pending_review')
    """
    try:
        conflict_status = request.GET.get('status', 'pending_review')
        
        neo4j_client = Neo4jClient()
        conflicts = neo4j_client.get_conflict_flags(conflict_status)
        neo4j_client.close()
        
        return Response({
            'conflicts': conflicts,
            'count': len(conflicts),
            'status_filter': conflict_status
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting conflict flags: {e}")
        return Response({
            'error': f'Failed to get conflict flags: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_conflict(request):
    """
    Manually resolve a conflict flag.
    
    Expected payload:
    {
        "video_id": "video_123",
        "new_relationship": "[\"EntityA\", \"relates_to\", \"EntityB\"]",
        "existing_relationship": "[\"EntityA\", \"connects_to\", \"EntityB\"]",
        "resolution": "keep_existing",  # Options: "keep_existing", "use_new", "merge"
        "comment": "Optional resolution comment"
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['video_id', 'new_relationship', 'existing_relationship', 'resolution']
        for field in required_fields:
            if field not in data:
                return Response({
                    'error': f'Missing required field: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate resolution value
        valid_resolutions = ['keep_existing', 'use_new', 'merge']
        if data['resolution'] not in valid_resolutions:
            return Response({
                'error': f'Invalid resolution. Must be one of: {valid_resolutions}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        neo4j_client = Neo4jClient()
        success = neo4j_client.resolve_conflict(
            video_id=data['video_id'],
            new_relationship=data['new_relationship'],
            existing_relationship=data['existing_relationship'],
            resolution=data['resolution'],
            resolved_by=request.user.username if hasattr(request.user, 'username') else 'api_user'
        )
        neo4j_client.close()
        
        if success:
            return Response({
                'message': 'Conflict resolved successfully',
                'resolution': data['resolution']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Failed to resolve conflict'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error resolving conflict: {e}")
        return Response({
            'error': f'Failed to resolve conflict: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_resolution_engine(request):
    """
    Enable or disable the graph resolution engine.
    
    Expected payload:
    {
        "enable": true  // Boolean to enable/disable resolution
    }
    """
    try:
        data = request.data
        enable = data.get('enable', True)
        
        if enable:
            # Initialize processor with resolution enabled
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                api_key=getattr(settings, 'OPENAI_API_KEY', ''),
                model="gpt-4o-mini",
                temperature=0.0
            )
            processor = VideoSummarizationProcessor(enable_resolution=True, llm=llm)
            message = 'Graph resolution engine enabled'
        else:
            # Initialize processor without resolution
            processor = VideoSummarizationProcessor(enable_resolution=False)
            message = 'Graph resolution engine disabled'
        
        # Test that processor works
        processor.neo4j_client.test_connection()
        processor.neo4j_client.close()
        
        return Response({
            'message': message,
            'resolution_enabled': enable
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error toggling resolution engine: {e}")
        return Response({
            'error': f'Failed to toggle resolution engine: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
