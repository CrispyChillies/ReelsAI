"""
Graph Resolution System for Knowledge Graph Merging

This module provides functionality to resolve duplicates and conflicts when merging
new video knowledge graphs with the existing global knowledge graph.
"""

import logging
from typing import Dict, List, Any, Tuple
from neo4j import Driver
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .system_prompts import GRAPH_ENTITY_RESOLUTION_PROMPT, RELATIONSHIP_RESOLUTION_PROMPT

logger = logging.getLogger(__name__)


class GraphResolutionEngine:
    """
    Engine for resolving conflicts and duplicates when merging knowledge graphs.
    """
    
    def __init__(self, neo4j_driver: Driver, llm=None):
        """
        Initialize the resolution engine.
        
        Args:
            neo4j_driver: Neo4j database driver
            llm: Language model for resolution decisions
        """
        self.driver = neo4j_driver
        self.llm = llm
        
    def get_existing_entities(self, entity_types: List[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get existing entities from the global graph.
        
        Args:
            entity_types: Optional filter by entity types
            limit: Maximum number of entities to retrieve
            
        Returns:
            List of existing entity dictionaries
        """
        if entity_types:
            type_filter = "WHERE e.type IN $entity_types"
            params = {"entity_types": entity_types, "limit": limit}
        else:
            type_filter = ""
            params = {"limit": limit}
        
        query = f"""
        MATCH (e:Entity)
        {type_filter}
        RETURN e.name as name, e.type as type, e.description as description,
               e.confidence as confidence
        ORDER BY e.name
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]
    
    def get_existing_relationships(self, entity_names: List[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get existing relationships from the global graph.
        
        Args:
            entity_names: Optional filter by entity names involved
            limit: Maximum number of relationships to retrieve
            
        Returns:
            List of relationship dictionaries
        """
        if entity_names:
            entity_filter = "WHERE e1.name IN $entity_names OR e2.name IN $entity_names"
            params = {"entity_names": entity_names, "limit": limit}
        else:
            entity_filter = ""
            params = {"limit": limit}
        
        query = f"""
        MATCH (e1:Entity)-[r]->(e2:Entity)
        {entity_filter}
        RETURN e1.name as subject, type(r) as relation, e2.name as object,
               r.source as source, r.created_at as created_at
        ORDER BY e1.name, e2.name
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]
    
    def resolve_entities_with_llm(self, new_entities: List[Dict[str, str]], 
                                 existing_entities: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Use LLM to resolve entity duplicates between new and existing entities.
        
        Args:
            new_entities: Entities from new video
            existing_entities: Entities already in graph
            
        Returns:
            Resolution result from LLM
        """
        if not self.llm or not new_entities or not existing_entities:
            return {"resolutions": []}
        
        # Prepare entity lists for LLM
        new_entities_str = "\n".join([
            f"- {e['name']} (Type: {e['type']})" for e in new_entities
        ])
        
        existing_entities_str = "\n".join([
            f"- {e['name']} (Type: {e['type']})" for e in existing_entities[:100]  # Limit for context
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=GRAPH_ENTITY_RESOLUTION_PROMPT),
            HumanMessage(content=f"""NEW_ENTITIES:
                {new_entities_str}

                EXISTING_ENTITIES:
                {existing_entities_str}

                Identify which new entities should be merged with existing entities.""")
        ])
        
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        try:
            response = chain.invoke({})
            return response
        except Exception as e:
            logger.error(f"LLM entity resolution failed: {e}")
            return {"resolutions": []}
    
    def resolve_relationships_with_llm(self, new_relationships: List[Tuple[str, str, str]], 
                                     existing_relationships: List[Tuple[str, str, str]],
                                     entity_mappings: Dict[str, str]) -> Dict[str, Any]:
        """
        Use LLM to resolve relationship conflicts and duplicates.
        
        Args:
            new_relationships: Relationships from new video
            existing_relationships: Relationships already in graph
            entity_mappings: How new entities map to existing entities
            
        Returns:
            Resolution result from LLM
        """
        if not self.llm or not new_relationships:
            return {"duplicates": [], "conflicts": [], "updates": []}
        
        # Prepare relationship lists
        new_rels_str = "\n".join([
            f"- {subj} --[{rel}]--> {obj}" for subj, rel, obj in new_relationships
        ])
        
        existing_rels_str = "\n".join([
            f"- {subj} --[{rel}]--> {obj}" for subj, rel, obj in existing_relationships[:100]
        ])
        
        mappings_str = "\n".join([
            f"- {new_entity} → {existing_entity}" 
            for new_entity, existing_entity in entity_mappings.items()
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=RELATIONSHIP_RESOLUTION_PROMPT),
            HumanMessage(content=f"""NEW_RELATIONSHIPS:
                {new_rels_str}

                EXISTING_RELATIONSHIPS:
                {existing_rels_str}

                ENTITY_MAPPINGS:
                {mappings_str}

                Identify duplicates, conflicts, and required updates for these relationships.""")
        ])
        
        parser = JsonOutputParser()
        chain = prompt | self.llm | parser
        
        try:
            response = chain.invoke({})
            return response
        except Exception as e:
            logger.error(f"LLM relationship resolution failed: {e}")
            return {"duplicates": [], "conflicts": [], "updates": []}
    
    def apply_entity_resolutions(self, resolutions: List[Dict[str, Any]], 
                                video_id: str) -> Dict[str, str]:
        """
        Apply entity resolution decisions to the graph.
        
        Args:
            resolutions: List of entity resolution decisions
            video_id: ID of the video being processed
            
        Returns:
            Mapping of new entity names to canonical names
        """
        entity_mappings = {}
        
        for resolution in resolutions:
            new_entity = resolution['new_entity']
            existing_entity = resolution['existing_entity']
            confidence = resolution.get('confidence', 0.0)
            reason = resolution.get('reason', 'LLM resolution')
            
            if confidence >= 0.8:  # Only apply high-confidence resolutions
                entity_mappings[new_entity] = existing_entity
                
                # Update the existing entity with any new information
                query = """
                MATCH (e:Entity {name: $existing_entity})
                SET e.updated_at = datetime(),
                    e.last_seen_video = $video_id,
                    e.resolution_count = COALESCE(e.resolution_count, 0) + 1
                WITH e
                MATCH (v:Video {video_id: $video_id})
                MERGE (v)-[r:MENTIONS]->(e)
                SET r.resolution_applied = true,
                    r.original_name = $new_entity,
                    r.confidence = $confidence,
                    r.resolution_reason = $reason
                RETURN e.name
                """
                
                with self.driver.session() as session:
                    session.run(query,
                               existing_entity=existing_entity,
                               video_id=video_id,
                               new_entity=new_entity,
                               confidence=confidence,
                               reason=reason)
                
                logger.info(f"Resolved entity '{new_entity}' -> '{existing_entity}' (confidence: {confidence})")
        
        return entity_mappings
    
    def apply_relationship_resolutions(self, resolution_result: Dict[str, Any], 
                                     video_id: str, entity_mappings: Dict[str, str]):
        """
        Apply relationship resolution decisions to the graph.
        
        Args:
            resolution_result: LLM resolution result
            video_id: ID of the video being processed
            entity_mappings: Entity name mappings
        """
        # Handle duplicate relationships - merge them
        for duplicate in resolution_result.get('duplicates', []):
            new_rel = duplicate['new_relationship']
            existing_rel = duplicate['existing_relationship']
            
            # Update relationship weights/counts
            query = """
            MATCH (e1:Entity {name: $subject})-[r]->(e2:Entity {name: $object})
            WHERE type(r) = $relation
            SET r.mention_count = COALESCE(r.mention_count, 1) + 1,
                r.last_mentioned_video = $video_id,
                r.updated_at = datetime()
            RETURN r
            """
            
            with self.driver.session() as session:
                session.run(query,
                           subject=existing_rel[0],
                           relation=existing_rel[1],
                           object=existing_rel[2],
                           video_id=video_id)
        
        # Handle conflicts - flag for manual review
        for conflict in resolution_result.get('conflicts', []):
            query = """
            CREATE (c:ConflictFlag {
                video_id: $video_id,
                new_relationship: $new_rel,
                existing_relationship: $existing_rel,
                reason: $reason,
                created_at: datetime(),
                status: 'pending_review'
            })
            RETURN c
            """
            
            with self.driver.session() as session:
                session.run(query,
                           video_id=video_id,
                           new_rel=str(conflict['new_relationship']),
                           existing_rel=str(conflict['existing_relationship']),
                           reason=conflict['reason'])
        
        # Handle updates - apply entity name standardizations
        for update in resolution_result.get('updates', []):
            original_rel = update['original_relationship']
            updated_rel = update['updated_relationship']
            
            # This would involve updating existing relationships with new entity names
            # Implementation would depend on specific requirements
            logger.info(f"Relationship update suggested: {original_rel} -> {updated_rel}")
    
    def resolve_and_merge_video_graph(self, video_id: str, new_entities: List[Dict[str, str]], 
                                     new_relationships: List[Tuple[str, str, str]]) -> Dict[str, Any]:
        """
        Complete resolution and merging of a new video graph with the global graph.
        
        Args:
            video_id: Video identifier
            new_entities: Entities extracted from the video
            new_relationships: Relationships extracted from the video
            
        Returns:
            Resolution statistics and mappings
        """
        logger.info(f"Starting graph resolution for video {video_id}")
        
        # Get relevant existing entities (same types as new entities)
        new_entity_types = list(set(e['type'] for e in new_entities))
        existing_entities = self.get_existing_entities(entity_types=new_entity_types)
        
        # Resolve entity duplicates
        entity_resolution = self.resolve_entities_with_llm(new_entities, existing_entities)
        entity_mappings = self.apply_entity_resolutions(
            entity_resolution.get('resolutions', []), 
            video_id
        )
        
        # Get relevant existing relationships
        all_entity_names = [e['name'] for e in new_entities] + [e['name'] for e in existing_entities]
        existing_relationships = self.get_existing_relationships(entity_names=all_entity_names)
        existing_rel_tuples = [
            (rel['subject'], rel['relation'], rel['object']) 
            for rel in existing_relationships
        ]
        
        # Resolve relationship conflicts
        relationship_resolution = self.resolve_relationships_with_llm(
            new_relationships, existing_rel_tuples, entity_mappings
        )
        self.apply_relationship_resolutions(relationship_resolution, video_id, entity_mappings)
        
        # Calculate statistics
        resolution_stats = {
            'video_id': video_id,
            'new_entities_count': len(new_entities),
            'existing_entities_count': len(existing_entities),
            'entity_resolutions_count': len(entity_resolution.get('resolutions', [])),
            'entity_mappings': entity_mappings,
            'new_relationships_count': len(new_relationships),
            'relationship_duplicates': len(relationship_resolution.get('duplicates', [])),
            'relationship_conflicts': len(relationship_resolution.get('conflicts', [])),
            'relationship_updates': len(relationship_resolution.get('updates', []))
        }
        
        logger.info(f"Graph resolution completed for video {video_id}: "
                   f"{len(entity_mappings)} entities resolved, "
                   f"{len(relationship_resolution.get('duplicates', []))} relationships merged")
        
        return resolution_stats


def create_graph_resolution_indexes(driver: Driver):
    """
    Create indexes to optimize graph resolution queries.
    
    Args:
        driver: Neo4j database driver
    """
    indexes = [
        "CREATE INDEX entity_type_name_index IF NOT EXISTS FOR (e:Entity) ON (e.type, e.name)",
        "CREATE INDEX entity_resolution_index IF NOT EXISTS FOR (e:Entity) ON (e.resolution_count)",
        "CREATE INDEX video_mentions_index IF NOT EXISTS FOR ()-[r:MENTIONS]-() ON (r.resolution_applied)",
        "CREATE INDEX conflict_flag_index IF NOT EXISTS FOR (c:ConflictFlag) ON (c.status, c.created_at)"
    ]
    
    with driver.session() as session:
        for index_query in indexes:
            try:
                session.run(index_query)
                logger.info(f"Created resolution index: {index_query}")
            except Exception as e:
                logger.warning(f"Index creation failed (may already exist): {e}")


def get_resolution_statistics(driver: Driver, video_id: str = None) -> Dict[str, Any]:
    """
    Get statistics about graph resolution performance.
    
    Args:
        driver: Neo4j database driver
        video_id: Optional specific video ID
        
    Returns:
        Dictionary containing resolution statistics
    """
    video_filter = "WHERE c.video_id = $video_id" if video_id else ""
    params = {"video_id": video_id} if video_id else {}
    
    queries = {
        "total_resolutions": f"""
            MATCH (e:Entity)
            WHERE e.resolution_count > 0
            RETURN count(e) as count
        """,
        "total_conflicts": f"""
            MATCH (c:ConflictFlag)
            {video_filter}
            RETURN count(c) as count
        """,
        "pending_conflicts": f"""
            MATCH (c:ConflictFlag)
            WHERE c.status = 'pending_review'
            {video_filter and "AND " + video_filter.replace("WHERE", "")}
            RETURN count(c) as count
        """,
        "resolved_mentions": f"""
            MATCH ()-[r:MENTIONS]->()
            WHERE r.resolution_applied = true
            RETURN count(r) as count
        """
    }
    
    stats = {}
    with driver.session() as session:
        for stat_name, query in queries.items():
            result = session.run(query, **params)
            stats[stat_name] = result.single()["count"]
    
    return stats