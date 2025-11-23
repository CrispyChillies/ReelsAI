"""
Text to Knowledge Graph processor.

This module handles the complete pipeline from text JSON
to Neo4j knowledge graph storage.
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from django.conf import settings
# Use LangChain's chat model import (install `langchain` + `openai`)
try:
    # Preferred import (newer LangChain)
    from langchain.chat_models import ChatOpenAI
except Exception:
    # Fallback for different packaging layouts
    try:
        from langchain.chat_models.openai import ChatOpenAI
    except Exception:
        ChatOpenAI = None

from .kg_constructor import run_knowledge_graph_pipeline
from .neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Processes text data and converts it to a Neo4j knowledge graph
    with automatic duplicate resolution.
    """
    
    def __init__(self, neo4j_client: Neo4jClient = None, llm=None, enable_resolution: bool = True):
        """
        Initialize the processor.
        
        Args:
            neo4j_client: Optional Neo4j client instance
            llm: Optional LLM instance for knowledge extraction
            enable_resolution: Whether to enable graph resolution for duplicates
        """
        # Initialize LLM first
        if llm:
            self.llm = llm
        else:
            if ChatOpenAI is None:
                raise ImportError("ChatOpenAI not available in installed langchain package")
            # Use explicit parameter names compatible with recent langchain versions
            self.llm = ChatOpenAI(
                model_name="gpt-4o-mini",
                openai_api_key=getattr(settings, 'OPENAI_API_KEY', ''),
                temperature=0.0,
            )
        
        # Initialize Neo4j client with LLM for resolution
        self.neo4j_client = neo4j_client or Neo4jClient(llm=self.llm if enable_resolution else None)
        self.enable_resolution = enable_resolution
        
        # Ensure indexes are created
        self.neo4j_client.create_indexes()
        
        logger.info(f"TextProcessor initialized with resolution: {enable_resolution}")
    
    def validate_payload(self, payload: Dict[str, Any]) -> bool:
        """
        Validate the incoming text payload.
        
        Args:
            payload: The text payload
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['user', 'post', 'topic', 'source', 'text']
        
        for field in required_fields:
            if field not in payload:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate user data
        user = payload.get('user', {})
        if not user.get('user_id'):
            logger.error("User must have user_id")
            return False
        
        # Validate post data
        post = payload.get('post', {})
        if not post.get('post_id'):
            logger.error("Post must have post_id")
            return False
        
        # Validate text
        if not payload.get('text', '').strip():
            logger.error("Text cannot be empty")
            return False
        
        return True
    
    def extract_knowledge_graph(self, topic: str, text: str) -> Dict[str, Any]:
        """
        Extract knowledge graph from text.
        
        Args:
            topic: The main topic/subject
            text: The text to extract knowledge from
            
        Returns:
            Knowledge graph result from pipeline
        """
        try:
            result = run_knowledge_graph_pipeline(
                topic=topic,
                raw_text=text,
                llm=self.llm
            )
            
            logger.info(f"Extracted {len(result['entities'])} entities and "
                       f"{len(result['resolved_relations'])} relations")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to extract knowledge graph: {e}")
            # Return empty result structure
            return {
                'entities': [],
                'resolved_relations': [],
                'graph': None,
                'validation': {}
            }
    
    def upsert_metadata_nodes(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Upsert metadata nodes (User, Post, Topic, Source) to Neo4j.
        
        Args:
            payload: The text payload
            
        Returns:
            Dictionary mapping node types to their IDs
        """
        node_ids = {}
        
        try:
            # Upsert User node
            user_data = payload['user'].copy()
            user_data.setdefault('name', f"User_{user_data['user_id']}")
            user_data.setdefault('email', '')
            user_data.setdefault('created_at', datetime.now().isoformat())
            
            node_ids['user'] = self.neo4j_client.upsert_user(user_data)
            logger.info(f"Upserted user: {node_ids['user']}")
            
            # Upsert Post node
            post_data = payload['post'].copy()
            post_data.setdefault('title', f"Post_{post_data['post_id']}")
            post_data.setdefault('description', '')
            post_data.setdefault('platform', '')
            post_data.setdefault('duration', 0)
            post_data.setdefault('upload_date', datetime.now().isoformat())
            post_data.setdefault('url', '')
            
            node_ids['post'] = self.neo4j_client.upsert_post(post_data)
            logger.info(f"Upserted post: {node_ids['post']}")
            
            # Upsert Topic node
            topic_data = payload['topic'].copy()
            if isinstance(topic_data, str):
                topic_data = {'name': topic_data}
            topic_data.setdefault('description', f"Topic about {topic_data['name']}")
            topic_data.setdefault('category', 'General')
            
            node_ids['topic'] = self.neo4j_client.upsert_topic(topic_data)
            logger.info(f"Upserted topic: {node_ids['topic']}")
            
            # Upsert Source node
            source_data = payload['source'].copy()
            if isinstance(source_data, str):
                source_data = {'name': source_data}
            source_data.setdefault('type', 'Unknown')
            source_data.setdefault('url', '')
            source_data.setdefault('description', f"Source: {source_data['name']}")
            
            node_ids['source'] = self.neo4j_client.upsert_source(source_data)
            logger.info(f"Upserted source: {node_ids['source']}")
            
        except Exception as e:
            logger.error(f"Failed to upsert metadata nodes: {e}")
            raise
        
        return node_ids
    
    def upsert_entities(self, entities: List[Dict[str, str]]) -> List[str]:
        """
        Upsert extracted entities to Neo4j.
        
        Args:
            entities: List of extracted entities
            
        Returns:
            List of entity names that were upserted
        """
        entity_names = []
        
        for entity in entities:
            try:
                # Ensure all required fields are present
                entity_data = {
                    'name': entity.get('name', ''),
                    'type': entity.get('type', 'Unknown'),
                    'description': entity.get('description', f"{entity.get('type', 'Unknown')}: {entity.get('name', '')}"),
                    'confidence': entity.get('confidence', 1.0)  # Default confidence
                }
                
                # Skip entities with empty names
                if not entity_data['name'].strip():
                    logger.warning(f"Skipping entity with empty name: {entity}")
                    continue
                
                entity_name = self.neo4j_client.upsert_entity(entity_data)
                entity_names.append(entity_name)
                
            except Exception as e:
                logger.error(f"Failed to upsert entity {entity}: {e}")
        
        logger.info(f"Upserted {len(entity_names)} entities")
        return entity_names
    
    def create_metadata_relationships(self, node_ids: Dict[str, str]):
        """
        Create relationships between metadata nodes.
        
        Args:
            node_ids: Dictionary mapping node types to their IDs
        """
        try:
            # User CARES post
            self.neo4j_client.create_user_cares_post_relationship(
                node_ids['user'], 
                node_ids['post'],
                {'relationship_type': 'engagement', 'weight': 1.0}
            )
            
            # Post ABOUT Topic
            self.neo4j_client.create_post_about_topic_relationship(
                node_ids['post'], 
                node_ids['topic'],
                {'relevance_score': 1.0}
            )
            
            # Post FROM Source
            self.neo4j_client.create_post_from_source_relationship(
                node_ids['post'], 
                node_ids['source'],
                {'original_source': True}
            )
            
            logger.info("Created metadata relationships")
            
        except Exception as e:
            logger.error(f"Failed to create metadata relationships: {e}")
            raise
    
    def create_entity_relationships(self, post_id: str, entities: List[Dict[str, str]], 
                                   relations: List[tuple]):
        """
        Create relationships between post and entities, and between entities.
        
        Args:
            post_id: Post identifier
            entities: List of extracted entities
            relations: List of relationships between entities (as tuples or dicts)
        """
        try:
            # Create Post MENTIONS Entity relationships
            for entity in entities:
                self.neo4j_client.create_post_mentions_entity_relationship(
                    post_id,
                    entity['name'],
                    {'entity_type': entity['type'], 'extraction_confidence': 1.0}
                )
                print(f"Linked post {post_id} to entity {entity['name']}")
            
            # Create relationships between entities
            entity_relations = []
            for relation in relations:
                if isinstance(relation, tuple) and len(relation) == 3:
                    entity_relations.append({
                        'subject': relation[0],
                        'relation': relation[1],
                        'object': relation[2]
                    })
                elif isinstance(relation, dict):
                    entity_relations.append(relation)
            
            if entity_relations:
                self.neo4j_client.create_entity_relationships(entity_relations, post_id)
            
            logger.info(f"Created {len(entities)} entity mentions and "
                       f"{len(entity_relations)} inter-entity relationships")
            
        except Exception as e:
            logger.error(f"Failed to create entity relationships: {e}")
            raise
    
    def _handle_existing_post_new_user(self, payload: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """
        Handle case where post exists but user is new.
        
        Args:
            payload: Text payload
            start_time: Processing start time
            
        Returns:
            Processing result
        """
        try:
            user_id = payload['user']['user_id']
            post_id = payload['post']['post_id']
            
            # Upsert user node
            user_data = payload['user'].copy()
            user_data.setdefault('name', f"User_{user_data['user_id']}")
            user_data.setdefault('email', '')
            user_data.setdefault('created_at', datetime.now().isoformat())
            
            user_node_id = self.neo4j_client.upsert_user(user_data)
            logger.info(f"Upserted user: {user_node_id}")
            
            # Create user-post relationship
            self.neo4j_client.create_user_cares_post_relationship(
                user_id,
                post_id,
                {'relationship_type': 'engagement', 'weight': 1.0, 'created_via': 'existing_post'}
            )
            
            # Get post details for response
            post_details = self.neo4j_client.get_post_details(post_id)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Get graph statistics for consistency
            graph_stats = self.neo4j_client.get_graph_stats()
            
            return {
                'status': 'success',
                'processing_type': 'existing_post_new_user',
                'message': 'Connected user to existing post',
                'processing_time_seconds': processing_time,
                'user_id': user_id,
                'post_id': post_id,
                'post_details': post_details,
                # Standardized fields for consistency
                'extracted_entities': 0,  # No new extraction for existing posts
                'extracted_relations': 0,
                'upserted_entities': 0,
                'node_ids': {'user': user_id, 'post': post_id},
                'graph_statistics': graph_stats,
                'kg_validation': {},
                'resolution_enabled': self.enable_resolution,
                'entities_count': len(post_details.get('entities', [])) if post_details else 0
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Failed to handle existing post for new user: {e}")
            return {
                'status': 'error',
                'processing_type': 'existing_post_new_user_failed',
                'error_message': str(e),
                'processing_time_seconds': processing_time,
                # Standardized error fields
                'extracted_entities': 0,
                'extracted_relations': 0,
                'upserted_entities': 0,
                'node_ids': {},
                'graph_statistics': {},
                'kg_validation': {},
                'resolution_enabled': self.enable_resolution
            }
    
    def _handle_new_post(self, payload: Dict[str, Any], start_time: datetime) -> Dict[str, Any]:
        """
        Handle case where post is completely new.
        
        Args:
            payload: Text payload
            start_time: Processing start time
            
        Returns:
            Processing result
        """
        try:
            topic_name = payload['topic']['name'] if isinstance(payload['topic'], dict) else payload['topic']
            text = payload['text']
            
            # Original full pipeline processing
            # Step 1: Extract knowledge graph from text
            kg_result = self.extract_knowledge_graph(topic_name, text)
            
            # Step 2: Upsert metadata nodes
            node_ids = self.upsert_metadata_nodes(payload)
            
            # Step 3: Upsert entities and relationships with resolution
            if self.enable_resolution:
                # Ensure entities have all required fields before resolution
                normalized_entities = []
                for entity in kg_result['entities']:
                    normalized_entity = {
                        'name': entity.get('name', ''),
                        'type': entity.get('type', 'Unknown'),
                        'description': entity.get('description', f"{entity.get('type', 'Unknown')}: {entity.get('name', '')}"),
                        'confidence': entity.get('confidence', 1.0)
                    }
                    # Skip entities with empty names
                    if normalized_entity['name'].strip():
                        normalized_entities.append(normalized_entity)
                
                # Convert relationship tuples to dictionaries for resolution
                relationship_dicts = []
                for rel_tuple in kg_result['resolved_relations']:
                    if isinstance(rel_tuple, tuple) and len(rel_tuple) == 3:
                        relationship_dicts.append({
                            'subject': rel_tuple[0],
                            'relation': rel_tuple[1],
                            'object': rel_tuple[2]
                        })
                    elif isinstance(rel_tuple, dict):
                        relationship_dicts.append(rel_tuple)
                
                # Use advanced upsert with graph resolution
                resolution_stats = self.neo4j_client.upsert_knowledge_graph_with_resolution(
                    post_id=node_ids['post'],
                    entities=normalized_entities,
                    relationships=relationship_dicts,
                    enable_resolution=True
                )
                entity_names = [
                    e['name'] for e in normalized_entities 
                    if e['name'] not in resolution_stats.get('entity_mappings', {})
                ]
            else:
                # Standard upsert without resolution
                entity_names = self.upsert_entities(kg_result['entities'])
                resolution_stats = {'resolution_disabled': True}
            
            # Step 4: Create metadata relationships
            self.create_metadata_relationships(node_ids)
            
            # Step 5: Create entity relationships (if not using resolution)
            if not self.enable_resolution:
                self.create_entity_relationships(
                    node_ids['post'], 
                    kg_result['entities'], 
                    kg_result['resolved_relations']
                )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Get final statistics
            graph_stats = self.neo4j_client.get_graph_stats()
            
            result = {
                'status': 'success',
                'processing_type': 'new_post_full_pipeline',
                'processing_time_seconds': processing_time,
                'extracted_entities': len(kg_result['entities']),
                'extracted_relations': len(kg_result['resolved_relations']),
                'upserted_entities': len(entity_names),
                'node_ids': node_ids,
                'graph_statistics': graph_stats,
                'kg_validation': kg_result['validation'],
                'resolution_enabled': self.enable_resolution,
            }
            
            # Add resolution statistics if available
            if 'resolution_stats' in locals():
                result['resolution_statistics'] = resolution_stats
                if 'entity_mappings' in resolution_stats:
                    result['resolved_entities_count'] = len(resolution_stats['entity_mappings'])
            
            logger.info(f"Successfully processed new post in {processing_time:.2f}s ")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_result = {
                'status': 'error',
                'processing_type': 'new_post_pipeline_failed',
                'error_message': str(e),
                'processing_time_seconds': processing_time,
                # Standardized error fields
                'extracted_entities': 0,
                'extracted_relations': 0,
                'upserted_entities': 0,
                'node_ids': {},
                'graph_statistics': {},
                'kg_validation': {},
                'resolution_enabled': self.enable_resolution
            }
            logger.error(f"Failed to process new post: {e}")
            return error_result
        
    def process_text(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete pipeline to process text and create knowledge graph.
        
        Args:
            payload: Text payload
            
        Returns:
            Processing result with statistics and status
        """
        start_time = datetime.now()
        
        try:
            # Validate payload
            if not self.validate_payload(payload):
                raise ValueError("Invalid payload structure")
            
            # Extract basic info
            user_id = payload['user']['user_id']
            post_id = payload['post']['post_id']
            topic_name = payload['topic']['name'] if isinstance(payload['topic'], dict) else payload['topic']
            text = payload['text']
            
            logger.info(f"Processing text for user: {user_id}, post: {post_id}")
            
            # Case 1: Check if user already has this post
            if self.neo4j_client.check_user_post_relationship(user_id, post_id):
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"User {user_id} already has relationship with post {post_id} - skipping processing")
                
                # Get graph statistics for consistency
                graph_stats = self.neo4j_client.get_graph_stats()
                
                return {
                    'status': 'success',
                    'processing_type': 'skipped_existing_relationship',
                    'message': 'User already has this post saved',
                    'processing_time_seconds': processing_time,
                    'user_id': user_id,
                    'post_id': post_id,
                    # Standardized fields for consistency
                    'extracted_entities': 0,  # No processing for existing relationships
                    'extracted_relations': 0,
                    'upserted_entities': 0,
                    'node_ids': {'user': user_id, 'post': post_id},
                    'graph_statistics': graph_stats,
                    'kg_validation': {},
                    'resolution_enabled': self.enable_resolution
                }
            
            # Case 2: Check if post exists but user doesn't have it
            post_exists = self.neo4j_client.check_post_exists(post_id)
            
            if post_exists:
                logger.info(f"Post {post_id} exists - creating user relationship only")
                return self._handle_existing_post_new_user(payload, start_time)
            else:
                logger.info(f"New post {post_id} - processing full pipeline")
                return self._handle_new_post(payload, start_time)
                
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_result = {
                'status': 'error',
                'error_message': str(e),
                'processing_time_seconds': processing_time,
                'processing_type': 'general_error',
                # Standardized error fields
                'extracted_entities': 0,
                'extracted_relations': 0,
                'upserted_entities': 0,
                'node_ids': {},
                'graph_statistics': {},
                'kg_validation': {},
                'resolution_enabled': self.enable_resolution
            }
            logger.error(f"Failed to process text: {e}")
            return error_result


def process_text_json(json_payload: str) -> Dict[str, Any]:
    """
    Convenience function to process text from JSON string.
    
    Args:
        json_payload: JSON string containing text data
        
    Returns:
        Processing result
    """
    try:
        payload = json.loads(json_payload)
    except json.JSONDecodeError as e:
        return {
            'status': 'error',
            'error_message': f"Invalid JSON: {e}"
        }
    
    processor = TextProcessor()
    return processor.process_text(payload)


def process_text_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to process text from dictionary.
    
    Args:
        payload: Dictionary containing text data
        
    Returns:
        Processing result
    """
    processor = TextProcessor()
    return processor.process_text(payload)


# Example payload structure for reference
EXAMPLE_PAYLOAD = {
    "user": {
        "user_id": "user_123",
        "name": "John Doe",
        "email": "john@example.com"
    },
    "post": {
        "post_id": "post_456",
        "title": "Introduction to Machine Learning",
        "platform": "Tiktok",
        "description": "A comprehensive guide to ML basics",
        "duration": 1800,  # seconds
        "upload_date": "2025-11-10T10:00:00Z",
        "url": "https://example.com/post/456"
    },
    "topic": {
        "name": "Machine Learning",
        "description": "Artificial intelligence and data science topic",
        "category": "Technology"
    },
    "source": {
        "name": "TechEd Platform",
        "type": "Educational Platform",
        "url": "https://teched.example.com",
        "description": "Online learning platform for technology courses"
    },
    "text": """
    Machine Learning is a subset of Artificial Intelligence that enables computers to learn 
    without being explicitly programmed. The video covers fundamental concepts including 
    supervised learning, unsupervised learning, and reinforcement learning. Popular algorithms 
    discussed include linear regression, decision trees, and neural networks. Companies like 
    Google and Microsoft use machine learning extensively in their products. Key programming 
    languages for ML include Python and R, with libraries such as TensorFlow and scikit-learn 
    being widely adopted.
    """
}