from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from drf_spectacular.utils import (
    extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse
)
import logging
import json

from .models import TextProcessingRequest, KnowledgeGraphStatistics
from ..agents.kg_constructor.text_processor import TextProcessor
from ..agents.kg_constructor.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Process Text",
    description="Process text content to extract entities and relationships, then create knowledge graph nodes.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'user': {
                    'type': 'object',
                    'properties': {
                        'user_id': {'type': 'string'},
                        'name': {'type': 'string'},
                        'email': {'type': 'string'}
                    },
                    'required': ['user_id']
                },
                'post': {
                    'type': 'object',
                    'properties': {
                        'post_id': {'type': 'string'},
                        'title': {'type': 'string'},
                        'description': {'type': 'string'},
                        'duration': {'type': 'integer'},
                        'upload_date': {'type': 'string', 'format': 'date-time'},
                        'url': {'type': 'string'}
                    },
                    'required': ['post_id']
                },
                'topic': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'description': {'type': 'string'},
                        'category': {'type': 'string'}
                    }
                },
                'source': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'type': {'type': 'string'},
                        'url': {'type': 'string'},
                        'description': {'type': 'string'}
                    }
                },
                'text': {'type': 'string'}
            },
            'required': ['user', 'post', 'text']
        }
    },
    responses={
        200: OpenApiResponse(
            description="Post processed successfully",
            examples=[
                OpenApiExample(
                    "Success Response",
                    value={
                        "request_id": 123,
                        "status": "success",
                        "processing_time_seconds": 15.3,
                        "extracted_entities": 25,
                        "extracted_relations": 18,
                        "upserted_entities": 20,
                        "graph_statistics": {
                            "total_nodes": 1250,
                            "total_relationships": 890
                        },
                        "node_ids": ["node_1", "node_2"],
                        "message": "Post text processed successfully"
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="Bad request - missing required fields"),
        500: OpenApiResponse(description="Processing failed")
    },
    examples=[
        OpenApiExample(
            "Post Text Processing Request",
            value={
                "user": {
                    "user_id": "user_123",
                    "name": "John Doe",
                    "email": "john@example.com"
                },
                "post": {
                    "post_id": "post_456",
                    "title": "Machine Learning Basics",
                    "description": "Introduction to ML concepts",
                    "duration": 1800,
                    "upload_date": "2025-11-10T10:00:00Z",
                    "url": "https://example.com/post/456"
                },
                "topic": {
                    "name": "Machine Learning",
                    "description": "AI and ML concepts",
                    "category": "Technology"
                },
                "source": {
                    "name": "Educational Platform",
                    "type": "Online Course",
                    "url": "https://platform.example.com",
                    "description": "Online learning platform"
                },
                "text": "This post covers fundamental machine learning concepts including supervised learning, neural networks, and practical applications..."
            },
            request_only=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_post_text(request):
    """
    Process post text and create knowledge graph.
    
    Expected payload:
    {
        "user": {
            "user_id": "user_123",
            "name": "John Doe",
            "email": "john@example.com"
        },
        "post": {
            "post_id": "post_456",
            "title": "Post Title",
            "description": "Post description",
            "duration": 1800,
            "upload_date": "2025-11-10T10:00:00Z",
            "url": "https://example.com/post/456"
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
        "text": "The post text content..."
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
        post_data = payload.get('post', {})
        topic_data = payload.get('topic', {})
        source_data = payload.get('source', {})
        
        post_id = post_data.get('post_id', '')
        topic_name = topic_data.get('name', '') if isinstance(topic_data, dict) else str(topic_data)
        source_name = source_data.get('name', '') if isinstance(source_data, dict) else str(source_data)
        
        if not post_id:
            return Response({
                'error': 'post_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create tracking record
        with transaction.atomic():
            text_processing_request = TextProcessingRequest.objects.create(
                user=request.user,
                post_id=post_id,
                topic=topic_name,
                source=source_name,
                payload=payload,
                status='processing',
                processing_started_at=timezone.now()
            )
        
        try:
            # Process the post text
            processor = TextProcessor()
            result = processor.process_text(payload)
            
            # Update tracking record with results
            with transaction.atomic():
                text_processing_request.processing_completed_at = timezone.now()
                text_processing_request.processing_time_seconds = result.get('processing_time_seconds')
                text_processing_request.processing_result = result
                
                if result.get('status') == 'success':
                    text_processing_request.status = 'completed'
                else:
                    text_processing_request.status = 'failed'
                    text_processing_request.error_message = result.get('error_message', 'Unknown error')
                
                text_processing_request.save()
            
            # Create statistics snapshot if successful
            if result.get('status') == 'success' and result.get('graph_statistics'):
                KnowledgeGraphStatistics.create_from_neo4j_stats(result['graph_statistics'])
            
            # Return success response
            return Response({
                'request_id': text_processing_request.id,
                'status': result.get('status'),
                'processing_time_seconds': result.get('processing_time_seconds'),
                'extracted_entities': result.get('extracted_entities', 0),
                'extracted_relations': result.get('extracted_relations', 0),
                'upserted_entities': result.get('upserted_entities', 0),
                'graph_statistics': result.get('graph_statistics'),
                'node_ids': result.get('node_ids'),
                'message': 'Post text processed successfully' if result.get('status') == 'success' else result.get('error_message')
            }, status=status.HTTP_200_OK if result.get('status') == 'success' else status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            
            # Update tracking record with error
            with transaction.atomic():
                text_processing_request.status = 'failed'
                text_processing_request.error_message = str(e)
                text_processing_request.processing_completed_at = timezone.now()
                text_processing_request.save()
            
            return Response({
                'request_id': text_processing_request.id,
                'error': f'Processing failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Unexpected error in process_text: {e}")
        return Response({
            'error': f'Unexpected error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Get Processing Status",
    description="Retrieve the status and results of a text processing request.",
    parameters=[
        OpenApiParameter(
            name="request_id",
            description="ID of the processing request",
            required=True,
            type=int,
            location=OpenApiParameter.PATH
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Request status retrieved successfully",
            examples=[
                OpenApiExample(
                    "Processing Status",
                    value={
                        "request_id": 123,
                        "status": "completed",
                        "post_id": "post_456",
                        "topic": "Machine Learning",
                        "source": "Educational Platform",
                        "created_at": "2025-11-17T10:00:00Z",
                        "processing_started_at": "2025-11-17T10:00:05Z",
                        "processing_completed_at": "2025-11-17T10:00:20Z",
                        "processing_time_seconds": 15.3,
                        "extracted_entities_count": 25,
                        "extracted_relations_count": 18,
                        "error_message": None,
                        "processing_result": {
                            "status": "success",
                            "graph_statistics": {}
                        }
                    }
                )
            ]
        ),
        404: OpenApiResponse(description="Request not found")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_processing_status(request, request_id):
    """
    Get the status of a text processing request.
    """
    try:
        text_processing_request = TextProcessingRequest.objects.get(
            id=request_id,
            user=request.user
        )
        
        return Response({
            'request_id': text_processing_request.id,
            'status': text_processing_request.status,
            'post_id': text_processing_request.post_id,
            'topic': text_processing_request.topic,
            'source': text_processing_request.source,
            'created_at': text_processing_request.created_at,
            'processing_started_at': text_processing_request.processing_started_at,
            'processing_completed_at': text_processing_request.processing_completed_at,
            'processing_time_seconds': text_processing_request.processing_time_seconds,
            'extracted_entities_count': text_processing_request.extracted_entities_count,
            'extracted_relations_count': text_processing_request.extracted_relations_count,
            'error_message': text_processing_request.error_message,
            'processing_result': text_processing_request.processing_result
        }, status=status.HTTP_200_OK)
    
    except TextProcessingRequest.DoesNotExist:
        return Response({
            'error': 'Request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Knowledge Graph"],
    summary="List User Requests",
    description="Get a paginated list of text processing requests for the authenticated user.",
    parameters=[
        OpenApiParameter(
            name="status",
            description="Filter by request status",
            required=False,
            type=str,
            enum=["processing", "completed", "failed"]
        ),
        OpenApiParameter(
            name="post_id",
            description="Filter by post ID",
            required=False,
            type=str
        ),
        OpenApiParameter(
            name="page_size",
            description="Number of results per page (max 100)",
            required=False,
            type=int,
            default=20
        ),
        OpenApiParameter(
            name="page",
            description="Page number",
            required=False,
            type=int,
            default=1
        )
    ],
    responses={
        200: OpenApiResponse(
            description="User requests retrieved successfully",
            examples=[
                OpenApiExample(
                    "User Requests List",
                    value={
                        "count": 5,
                        "page": 1,
                        "page_size": 20,
                        "requests": [
                            {
                                "request_id": 123,
                                "status": "completed",
                                "post_id": "post_456",
                                "topic": "Machine Learning",
                                "source": "Educational Platform",
                                "created_at": "2025-11-17T10:00:00Z",
                                "processing_time_seconds": 15.3,
                                "extracted_entities_count": 25,
                                "extracted_relations_count": 18,
                                "error_message": None
                            }
                        ]
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_requests(request):
    """
    List all post text processing requests for the authenticated user.
    """
    requests = TextProcessingRequest.objects.filter(user=request.user)
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    post_id_filter = request.GET.get('post_id')
    if post_id_filter:
        requests = requests.filter(post_id=post_id_filter)
    
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
                'post_id': req.post_id,
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


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Get Graph Statistics",
    description="Retrieve current knowledge graph statistics including node and relationship counts.",
    responses={
        200: OpenApiResponse(
            description="Graph statistics retrieved successfully",
            examples=[
                OpenApiExample(
                    "Graph Statistics",
                    value={
                        "current_stats": {
                            "total_nodes": 1250,
                            "total_relationships": 890,
                            "user_nodes": 50,
                            "post_nodes": 200,
                            "topic_nodes": 100,
                            "source_nodes": 25,
                            "entity_nodes": 875
                        },
                        "latest_stored_stats": {
                            "timestamp": "2025-11-17T09:30:00Z",
                            "total_nodes": 1245,
                            "total_relationships": 885,
                            "user_nodes": 50,
                            "post_nodes": 199,
                            "topic_nodes": 100,
                            "source_nodes": 25,
                            "entity_nodes": 871
                        }
                    }
                )
            ]
        ),
        500: OpenApiResponse(description="Failed to retrieve statistics")
    }
)
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
                'post_nodes': latest_stored_stats.post_nodes,
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


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Search Entities",
    description="Search for entities in the knowledge graph by name or properties.",
    parameters=[
        OpenApiParameter(
            name="q",
            description="Search query",
            required=True,
            type=str
        ),
        OpenApiParameter(
            name="limit",
            description="Maximum number of results (max 100)",
            required=False,
            type=int,
            default=10
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Entities found",
            examples=[
                OpenApiExample(
                    "Search Results",
                    value={
                        "query": "machine learning",
                        "entities": [
                            {
                                "id": "entity_123",
                                "name": "Machine Learning",
                                "type": "Concept",
                                "properties": {
                                    "description": "AI technique for pattern recognition"
                                }
                            }
                        ],
                        "count": 1
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="Query parameter required"),
        500: OpenApiResponse(description="Search failed")
    }
)
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


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Get Post Knowledge Graph",
    description="Retrieve the complete knowledge graph for a specific post including all nodes and relationships.",
    parameters=[
        OpenApiParameter(
            name="post_id",
            description="ID of the post",
            required=True,
            type=str,
            location=OpenApiParameter.PATH
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Post knowledge graph retrieved",
            examples=[
                OpenApiExample(
                    "Post Graph",
                    value={
                        "post_id": "post_456",
                        "nodes": [
                            {
                                "id": "entity_123",
                                "name": "Machine Learning",
                                "type": "Concept",
                                "properties": {}
                            }
                        ],
                        "relationships": [
                            {
                                "id": "rel_456",
                                "source": "entity_123",
                                "target": "entity_789",
                                "type": "relates_to"
                            }
                        ],
                        "summary": {
                            "node_count": 25,
                            "relationship_count": 18
                        }
                    }
                )
            ]
        ),
        500: OpenApiResponse(description="Failed to retrieve graph")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_post_knowledge_graph(request, post_id):
    """
    Get the complete knowledge graph for a specific post.
    """
    try:
        neo4j_client = Neo4jClient()
        graph_data = neo4j_client.get_post_knowledge_graph(post_id)
        neo4j_client.close()
        
        return Response({
            'post_id': post_id,
            'nodes': graph_data['nodes'],
            'relationships': graph_data['relationships'],
            'summary': {
                'node_count': len(graph_data['nodes']),
                'relationship_count': len(graph_data['relationships'])
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting post knowledge graph: {e}")
        return Response({
            'error': f'Failed to get post knowledge graph: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Test Neo4j Connection",
    description="Test the connection to the Neo4j knowledge graph database.",
    responses={
        200: OpenApiResponse(
            description="Connection test completed",
            examples=[
                OpenApiExample(
                    "Connection Success",
                    value={
                        "connected": True,
                        "message": "Connection successful"
                    }
                ),
                OpenApiExample(
                    "Connection Failed",
                    value={
                        "connected": False,
                        "message": "Connection failed"
                    }
                )
            ]
        ),
        500: OpenApiResponse(description="Connection test failed")
    }
)
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


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Get Resolution Statistics",
    description="Retrieve graph resolution statistics for conflict detection and entity merging.",
    parameters=[
        OpenApiParameter(
            name="post_id",
            description="Optional specific post ID to filter statistics",
            required=False,
            type=str
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Resolution statistics retrieved",
            examples=[
                OpenApiExample(
                    "Resolution Stats",
                    value={
                        "resolution_statistics": {
                            "total_conflicts_detected": 15,
                            "conflicts_resolved": 12,
                            "pending_conflicts": 3,
                            "entities_merged": 8,
                            "relationships_updated": 20
                        },
                        "post_id": "post_456"
                    }
                )
            ]
        ),
        500: OpenApiResponse(description="Failed to get statistics")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resolution_statistics(request):
    """
    Get graph resolution statistics.
    
    Query parameters:
    - post_id: Optional specific post ID
    """
    try:
        post_id = request.GET.get('post_id', None)
        
        neo4j_client = Neo4jClient()
        stats = neo4j_client.get_resolution_statistics(post_id)
        neo4j_client.close()
        
        return Response({
            'resolution_statistics': stats,
            'post_id': post_id
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error getting resolution statistics: {e}")
        return Response({
            'error': f'Failed to get resolution statistics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Get Conflict Flags",
    description="Retrieve conflict flags that need manual review for entity and relationship conflicts.",
    parameters=[
        OpenApiParameter(
            name="status",
            description="Filter conflicts by status",
            required=False,
            type=str,
            default="pending_review",
            enum=["pending_review", "resolved", "ignored"]
        )
    ],
    responses={
        200: OpenApiResponse(
            description="Conflict flags retrieved",
            examples=[
                OpenApiExample(
                    "Conflict Flags",
                    value={
                        "conflicts": [
                            {
                                "conflict_id": "conf_123",
                                "post_id": "post_456",
                                "new_relationship": "[\"EntityA\", \"relates_to\", \"EntityB\"]",
                                "existing_relationship": "[\"EntityA\", \"connects_to\", \"EntityB\"]",
                                "confidence_new": 0.85,
                                "confidence_existing": 0.75,
                                "status": "pending_review",
                                "created_at": "2025-11-17T10:00:00Z"
                            }
                        ],
                        "count": 1,
                        "status_filter": "pending_review"
                    }
                )
            ]
        ),
        500: OpenApiResponse(description="Failed to get conflicts")
    }
)
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


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Resolve Conflict",
    description="Manually resolve a detected conflict between entities or relationships in the knowledge graph.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'post_id': {'type': 'string'},
                'new_relationship': {'type': 'string'},
                'existing_relationship': {'type': 'string'},
                'resolution': {
                    'type': 'string',
                    'enum': ['keep_existing', 'use_new', 'merge']
                },
                'comment': {'type': 'string'}
            },
            'required': ['post_id', 'new_relationship', 'existing_relationship', 'resolution']
        }
    },
    responses={
        200: OpenApiResponse(
            description="Conflict resolved successfully",
            examples=[
                OpenApiExample(
                    "Resolution Success",
                    value={
                        "message": "Conflict resolved successfully",
                        "resolution": "keep_existing"
                    }
                )
            ]
        ),
        400: OpenApiResponse(description="Invalid request data"),
        500: OpenApiResponse(description="Failed to resolve conflict")
    },
    examples=[
        OpenApiExample(
            "Resolve Conflict Request",
            value={
                "post_id": "post_456",
                "new_relationship": "[\"EntityA\", \"relates_to\", \"EntityB\"]",
                "existing_relationship": "[\"EntityA\", \"connects_to\", \"EntityB\"]",
                "resolution": "keep_existing",
                "comment": "Existing relationship is more accurate"
            },
            request_only=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_conflict(request):
    """
    Manually resolve a conflict flag.
    
    Expected payload:
    {
        "post_id": "post_123",
        "new_relationship": "[\"EntityA\", \"relates_to\", \"EntityB\"]",
        "existing_relationship": "[\"EntityA\", \"connects_to\", \"EntityB\"]",
        "resolution": "keep_existing",  # Options: "keep_existing", "use_new", "merge"
        "comment": "Optional resolution comment"
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['post_id', 'new_relationship', 'existing_relationship', 'resolution']
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
            post_id=data['post_id'],
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


@extend_schema(
    tags=["Knowledge Graph"],
    summary="Toggle Resolution Engine",
    description="Enable or disable the graph resolution engine for automatic conflict detection and resolution.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'enable': {
                    'type': 'boolean',
                    'description': 'Whether to enable or disable the resolution engine'
                }
            },
            'required': ['enable']
        }
    },
    responses={
        200: OpenApiResponse(
            description="Resolution engine toggled successfully",
            examples=[
                OpenApiExample(
                    "Engine Enabled",
                    value={
                        "message": "Graph resolution engine enabled",
                        "resolution_enabled": True
                    }
                ),
                OpenApiExample(
                    "Engine Disabled",
                    value={
                        "message": "Graph resolution engine disabled",
                        "resolution_enabled": False
                    }
                )
            ]
        ),
        500: OpenApiResponse(description="Failed to toggle resolution engine")
    },
    examples=[
        OpenApiExample(
            "Enable Resolution Engine",
            value={"enable": True},
            request_only=True
        ),
        OpenApiExample(
            "Disable Resolution Engine",
            value={"enable": False},
            request_only=True
        )
    ]
)
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
            processor = TextProcessor(enable_resolution=True, llm=llm)
            message = 'Graph resolution engine enabled'
        else:
            # Initialize processor without resolution
            processor = TextProcessor(enable_resolution=False)
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
