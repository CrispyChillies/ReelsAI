"""
Neo4j client for Knowledge Graph integration.

This module provides functionality to connect to Neo4j and upsert knowledge graphs
from text data with graph resolution capabilities.
"""

import logging
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase, Driver
from django.conf import settings
import json
from .graph_resolution import GraphResolutionEngine, create_graph_resolution_indexes

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Neo4j database client for knowledge graph operations with resolution capabilities.
    """
    
    def __init__(self, uri: str = None, username: str = None, password: str = None, llm=None):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j URI (defaults to settings.NEO4J_URI)
            username: Neo4j username (defaults to settings.NEO4J_USERNAME)
            password: Neo4j password (defaults to settings.NEO4J_PASSWORD)
            llm: Language model for graph resolution
        """
        self.uri = uri or getattr(settings, 'NEO4J_URI', 'bolt://localhost:7687')
        self.username = username or getattr(settings, 'NEO4J_USERNAME', 'neo4j')
        self.password = password or getattr(settings, 'NEO4J_PASSWORD', 'password')
        
        self._driver: Optional[Driver] = None
        self._resolution_engine: Optional[GraphResolutionEngine] = None
        self._connect()
        
        # Initialize resolution engine if LLM is provided
        if llm:
            self._resolution_engine = GraphResolutionEngine(self._driver, llm)
            logger.info("Graph resolution engine initialized")
    
    def _connect(self):
        """Establish connection to Neo4j database."""
        try:
            self._driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            # Test connection
            with self._driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close the Neo4j connection."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def test_connection(self) -> bool:
        """
        Test if connection to Neo4j is working.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self._driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def clear_database(self):
        """
        Clear all nodes and relationships from the database.
        WARNING: This deletes all data!
        """
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.warning("Database cleared - all nodes and relationships deleted")
    
    def create_indexes(self):
        """Create necessary indexes for better performance."""
        indexes = [
            "CREATE INDEX user_id_index IF NOT EXISTS FOR (u:User) ON (u.user_id)",
            "CREATE INDEX post_id_index IF NOT EXISTS FOR (v:Post) ON (v.post_id)",
            "CREATE INDEX topic_name_index IF NOT EXISTS FOR (t:Topic) ON (t.name)",
            "CREATE INDEX source_name_index IF NOT EXISTS FOR (s:Source) ON (s.name)",
            "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
        ]
        
        with self._driver.session() as session:
            for index in indexes:
                try:
                    session.run(index)
                    logger.info(f"Created index: {index}")
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")
        
        # Create resolution-specific indexes
        create_graph_resolution_indexes(self._driver)
    
    def upsert_user(self, user_data: Dict[str, Any]) -> str:
        """
        Upsert a User node.
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            User ID
        """
        query = """
        MERGE (u:User {user_id: $user_id})
        SET u.name = $name,
            u.email = $email,
            u.created_at = $created_at,
            u.updated_at = datetime()
        RETURN u.user_id as user_id
        """
        
        with self._driver.session() as session:
            result = session.run(query, **user_data)
            return result.single()["user_id"]
    
    def upsert_post(self, post_data: Dict[str, Any]) -> str:
        """
        Upsert a Post node.
        
        Args:
            post_data: Dictionary containing post information
            
        Returns:
            Post ID
        """
        query = """
        MERGE (v:Post {post_id: $post_id})
        SET v.title = $title,
            v.description = $description,
            v.duration = $duration,
            v.upload_date = $upload_date,
            v.url = $url,
            v.updated_at = datetime()
        RETURN v.post_id as post_id
        """
        
        with self._driver.session() as session:
            result = session.run(query, **post_data)
            return result.single()["post_id"]
    
    def upsert_topic(self, topic_data: Dict[str, Any]) -> str:
        """
        Upsert a Topic node.
        
        Args:
            topic_data: Dictionary containing topic information
            
        Returns:
            Topic name
        """
        query = """
        MERGE (t:Topic {name: $name})
        SET t.description = $description,
            t.category = $category,
            t.updated_at = datetime()
        RETURN t.name as name
        """
        
        with self._driver.session() as session:
            result = session.run(query, **topic_data)
            return result.single()["name"]
    
    def upsert_source(self, source_data: Dict[str, Any]) -> str:
        """
        Upsert a Source node.
        
        Args:
            source_data: Dictionary containing source information
            
        Returns:
            Source name
        """
        query = """
        MERGE (s:Source {name: $name})
        SET s.type = $type,
            s.url = $url,
            s.description = $description,
            s.updated_at = datetime()
        RETURN s.name as name
        """
        
        with self._driver.session() as session:
            result = session.run(query, **source_data)
            return result.single()["name"]
    
    def upsert_entity(self, entity_data: Dict[str, Any], post_id: str = None) -> str:
        """
        Upsert an Entity node.
        
        Args:
            entity_data: Dictionary containing entity information
            post_id: Optional post ID for tracking entity source
            
        Returns:
            Entity name
        """
        query = """
        MERGE (e:Entity {name: $name})
        SET e.type = $type,
            e.description = $description,
            e.confidence = $confidence,
            e.updated_at = datetime()
        RETURN e.name as name
        """
        
        with self._driver.session() as session:
            # First upsert the entity
            result = session.run(query, **entity_data)
            entity_name = result.single()["name"]
            
            # Then create the MENTIONS relationship if post_id is provided
            if post_id:
                mention_query = """
                MATCH (v:Post {post_id: $post_id})
                MATCH (e:Entity {name: $entity_name})
                MERGE (v)-[r:MENTIONS]->(e)
                SET r.created_at = COALESCE(r.created_at, datetime())
                RETURN r
                """
                session.run(mention_query, post_id=post_id, entity_name=entity_name)
            
            return entity_name
        
    def upsert_relationship(self, relationship_data: Dict[str, Any], post_id: str = None):
        """
        Upsert a relationship between two entities.
        
        Args:
            relationship_data: Dictionary containing 'subject', 'relation', 'object'
            post_id: Optional post ID for tracking relationship source
        """
        query = """
        MATCH (e1:Entity {name: $subject})
        MATCH (e2:Entity {name: $object})
        CALL apoc.create.relationship(e1, $relation_type, {
            created_at: datetime(),
            source: 'kg_extraction',
            post_id: $post_id
        }, e2) YIELD rel
        RETURN rel
        """
        
        with self._driver.session() as session:
            try:
                session.run(query,
                           subject=relationship_data['subject'],
                           object=relationship_data['object'],
                           relation_type=relationship_data['relation'].upper(),
                           post_id=post_id)
            except Exception as e:
                # Fallback to creating a generic RELATED relationship if APOC is not available
                fallback_query = """
                MATCH (e1:Entity {name: $subject})
                MATCH (e2:Entity {name: $object})
                MERGE (e1)-[r:RELATED]->(e2)
                SET r.relation_type = $relation_type,
                    r.created_at = datetime(),
                    r.source = 'kg_extraction',
                    r.post_id = $post_id
                RETURN r
                """
                session.run(fallback_query,
                           subject=relationship_data['subject'],
                           object=relationship_data['object'],
                           relation_type=relationship_data['relation'],
                           post_id=post_id)
    
    def create_user_cares_post_relationship(self, user_id: str, post_id: str, 
                                           properties: Dict[str, Any] = None):
        """
        Create CARES relationship between User and Post.
        
        Args:
            user_id: User identifier
            post_id: Post identifier
            properties: Optional relationship properties
        """
        query = """
        MATCH (u:User {user_id: $user_id})
        MATCH (v:Post {post_id: $post_id})
        MERGE (u)-[r:CARES]->(v)
        SET r.created_at = datetime(),
            r += $properties
        RETURN r
        """
        
        with self._driver.session() as session:
            session.run(query, 
                       user_id=user_id, 
                       post_id=post_id, 
                       properties=properties or {})
    
    def create_post_about_topic_relationship(self, post_id: str, topic_name: str,
                                            properties: Dict[str, Any] = None):
        """
        Create ABOUT relationship between Post and Topic.
        
        Args:
            post_id: Post identifier
            topic_name: Topic name
            properties: Optional relationship properties
        """
        query = """
        MATCH (v:Post {post_id: $post_id})
        MATCH (t:Topic {name: $topic_name})
        MERGE (v)-[r:ABOUT]->(t)
        SET r.created_at = datetime(),
            r += $properties
        RETURN r
        """
        
        with self._driver.session() as session:
            session.run(query,
                       post_id=post_id,
                       topic_name=topic_name,
                       properties=properties or {})
    
    def create_post_mentions_entity_relationship(self, post_id: str, entity_name: str,
                                                properties: Dict[str, Any] = None):
        """
        Create MENTIONS relationship between Post and Entity.
        
        Args:
            post_id: Post identifier
            entity_name: Entity name
            properties: Optional relationship properties
        """
        query = """
        MATCH (v:Post {post_id: $post_id})
        MATCH (e:Entity {name: $entity_name})
        MERGE (v)-[r:MENTIONS]->(e)
        SET r.created_at = datetime(),
            r += $properties
        RETURN r
        """
        
        with self._driver.session() as session:
            session.run(query,
                       post_id=post_id,
                       entity_name=entity_name,
                       properties=properties or {})
    
    def create_post_from_source_relationship(self, post_id: str, source_name: str,
                                            properties: Dict[str, Any] = None):
        """
        Create FROM relationship between Post and Source.
        
        Args:
            post_id: Post identifier
            source_name: Source name
            properties: Optional relationship properties
        """
        query = """
        MATCH (v:Post {post_id: $post_id})
        MATCH (s:Source {name: $source_name})
        MERGE (v)-[r:FROM]->(s)
        SET r.created_at = datetime(),
            r += $properties
        RETURN r
        """
        
        with self._driver.session() as session:
            session.run(query,
                       post_id=post_id,
                       source_name=source_name,
                       properties=properties or {})

    def create_entity_relationships(self, relations: List[Dict[str, Any]], post_id: str = None):
        """
        Create relationships between entities based on extracted relations.
        
        Args:
            relations: List of relationship dictionaries with 'subject', 'relation', 'object'
            post_id: Optional post ID for tracking relationship source
        """
        for relation in relations:
            self.upsert_relationship(relation, post_id)
    
    def check_post_exists(self, post_id: str) -> bool:
        """
        Check if a post already exists in the graph.
        
        Args:
            post_id: Post identifier
            
        Returns:
            True if post exists, False otherwise
        """
        query = "MATCH (v:Post {post_id: $post_id}) RETURN v LIMIT 1"
        
        with self._driver.session() as session:
            result = session.run(query, post_id=post_id)
            return result.single() is not None
    
    def check_user_post_relationship(self, user_id: str, post_id: str) -> bool:
        """
        Check if a user already has a CARES relationship with a post.
        
        Args:
            user_id: User identifier
            post_id: Post identifier
            
        Returns:
            True if relationship exists, False otherwise
        """
        query = """
        MATCH (u:User {user_id: $user_id})-[r:CARES]->(v:Post {post_id: $post_id})
        RETURN r LIMIT 1
        """
        
        with self._driver.session() as session:
            result = session.run(query, user_id=user_id, post_id=post_id)
            return result.single() is not None
    
    def get_post_details(self, post_id: str) -> Dict[str, Any]:
        """
        Get detailed information about an existing post.
        
        Args:
            post_id: Post identifier
            
        Returns:
            Dictionary containing post details and related entities
        """
        query = """
        MATCH (v:Post {post_id: $post_id})
        OPTIONAL MATCH (v)-[:ABOUT]->(t:Topic)
        OPTIONAL MATCH (v)-[:FROM]->(s:Source)
        OPTIONAL MATCH (v)-[:MENTIONS]->(e:Entity)
        RETURN v, 
               collect(DISTINCT t) as topics,
               collect(DISTINCT s) as sources,
               collect(DISTINCT e) as entities
        """
        
        with self._driver.session() as session:
            result = session.run(query, post_id=post_id)
            record = result.single()
            
            if not record:
                return None
                
            return {
                'post': dict(record['v']),
                'topics': [dict(topic) for topic in record['topics'] if topic],
                'sources': [dict(source) for source in record['sources'] if source],
                'entities': [dict(entity) for entity in record['entities'] if entity]
            }

    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the graph database.
        
        Returns:
            Dictionary containing graph statistics
        """
        queries = {
            'total_nodes': "MATCH (n) RETURN count(n) as count",
            'total_relationships': "MATCH ()-[r]->() RETURN count(r) as count",
            'users': "MATCH (n:User) RETURN count(n) as count",
            'posts': "MATCH (n:Post) RETURN count(n) as count",
            'topics': "MATCH (n:Topic) RETURN count(n) as count",
            'sources': "MATCH (n:Source) RETURN count(n) as count",
            'entities': "MATCH (n:Entity) RETURN count(n) as count",
        }
        
        stats = {}
        with self._driver.session() as session:
            for stat_name, query in queries.items():
                result = session.run(query)
                stats[stat_name] = result.single()["count"]
        
        return stats
    
    def search_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for entities by name.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of entity dictionaries
        """
        search_query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($query)
        RETURN e.name as name, e.type as type, e.description as description
        ORDER BY e.name
        LIMIT $limit
        """
        
        with self._driver.session() as session:
            result = session.run(search_query, query=query, limit=limit)
            return [dict(record) for record in result]
    
    def get_post_knowledge_graph(self, post_id: str) -> Dict[str, Any]:
        """
        Get the complete knowledge graph for a specific post.
        
        Args:
            post_id: Post identifier
            
        Returns:
            Dictionary containing nodes and relationships
        """
        query = """
        MATCH (v:Post {post_id: $post_id})-[r]-(n)
        RETURN v, r, n
        """
        
        nodes = []
        relationships = []
        
        with self._driver.session() as session:
            result = session.run(query, post_id=post_id)
            
            for record in result:
                # Add post node
                post_node = dict(record["v"])
                post_node["labels"] = ["Post"]
                if post_node not in nodes:
                    nodes.append(post_node)
                
                # Add connected node
                connected_node = dict(record["n"])
                connected_node["labels"] = list(record["n"].labels)
                if connected_node not in nodes:
                    nodes.append(connected_node)
                
                # Add relationship
                rel = dict(record["r"])
                rel["type"] = record["r"].type
                rel["start"] = post_node
                rel["end"] = connected_node
                relationships.append(rel)
        
        return {
            "nodes": nodes,
            "relationships": relationships
        }
    
    # Graph Resolution Methods
    
    def upsert_knowledge_graph_with_resolution(self, post_id: str, entities: List[Dict[str, str]], 
                                              relationships: List[Dict[str, str]], 
                                              enable_resolution: bool = True) -> Dict[str, Any]:
        """
        Upsert knowledge graph with automatic resolution of duplicates.
        
        Args:
            post_id: Post identifier
            entities: List of entity dictionaries
            relationships: List of relationship dictionaries
            enable_resolution: Whether to use LLM-based resolution
            
        Returns:
            Dictionary with resolution statistics and mappings
        """
        if enable_resolution and self._resolution_engine:
            # Convert relationships to tuples for resolution
            relationship_tuples = [
                (rel['subject'], rel['relation'], rel['object'])
                for rel in relationships
            ]
            
            # Perform graph resolution
            resolution_stats = self._resolution_engine.resolve_and_merge_post_graph(
                post_id, entities, relationship_tuples
            )
            
            # Apply entity mappings to relationships
            entity_mappings = resolution_stats['entity_mappings']
            resolved_relationships = []
            
            for rel in relationships:
                resolved_rel = rel.copy()
                resolved_rel['subject'] = entity_mappings.get(rel['subject'], rel['subject'])
                resolved_rel['object'] = entity_mappings.get(rel['object'], rel['object'])
                resolved_relationships.append(resolved_rel)
            
            # Upsert only non-duplicate entities
            entities_to_upsert = [
                entity for entity in entities 
                if entity['name'] not in entity_mappings
            ]
            
        else:
            # Standard upsert without resolution
            entities_to_upsert = entities
            resolved_relationships = relationships
            resolution_stats = {'entity_mappings': {}, 'resolution_disabled': True}
        
        # Proceed with standard upsert for remaining entities
        for entity in entities_to_upsert:
            self.upsert_entity(entity, post_id)
        
        for relationship in resolved_relationships:
            self.upsert_relationship(relationship, post_id)
        
        return resolution_stats
    
    def get_resolution_statistics(self, post_id: str = None) -> Dict[str, Any]:
        """
        Get graph resolution statistics.
        
        Args:
            post_id: Optional specific post ID
            
        Returns:
            Dictionary containing resolution statistics
        """
        if not self._resolution_engine:
            return {"error": "Resolution engine not available"}
        
        from .graph_resolution import get_resolution_statistics
        return get_resolution_statistics(self._driver, post_id)
    
    def get_conflict_flags(self, status: str = 'pending_review') -> List[Dict[str, Any]]:
        """
        Get conflict flags that need manual review.
        
        Args:
            status: Conflict status to filter by
            
        Returns:
            List of conflict flag dictionaries
        """
        query = """
        MATCH (c:ConflictFlag)
        WHERE c.status = $status
        RETURN c.post_id as post_id,
               c.new_relationship as new_relationship,
               c.existing_relationship as existing_relationship,
               c.reason as reason,
               c.created_at as created_at
        ORDER BY c.created_at DESC
        """
        
        with self._driver.session() as session:
            result = session.run(query, status=status)
            return [dict(record) for record in result]
    
    def resolve_conflict(self, post_id: str, new_relationship: str, 
                        existing_relationship: str, resolution: str, 
                        resolved_by: str = None) -> bool:
        """
        Manually resolve a conflict flag.
        
        Args:
            post_id: Post ID where conflict occurred
            new_relationship: New relationship string
            existing_relationship: Existing relationship string
            resolution: Resolution decision ('keep_existing', 'use_new', 'merge')
            resolved_by: User who resolved the conflict
            
        Returns:
            True if resolution was successful
        """
        try:
            with self._driver.session() as session:
                # Update conflict flag
                session.run("""
                    MATCH (c:ConflictFlag {
                        post_id: $post_id,
                        new_relationship: $new_relationship,
                        existing_relationship: $existing_relationship
                    })
                    SET c.status = 'resolved',
                        c.resolution = $resolution,
                        c.resolved_by = $resolved_by,
                        c.resolved_at = datetime()
                    RETURN c
                """, 
                post_id=post_id,
                new_relationship=new_relationship,
                existing_relationship=existing_relationship,
                resolution=resolution,
                resolved_by=resolved_by)
                
                logger.info(f"Conflict resolved for post {post_id}: {resolution}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to resolve conflict: {e}")
            return False
    
    def enable_resolution_engine(self, llm):
        """
        Enable the graph resolution engine with an LLM.
        
        Args:
            llm: Language model for resolution decisions
        """
        self._resolution_engine = GraphResolutionEngine(self._driver, llm)
        logger.info("Graph resolution engine enabled")
    
    def disable_resolution_engine(self):
        """Disable the graph resolution engine."""
        self._resolution_engine = None
        logger.info("Graph resolution engine disabled")