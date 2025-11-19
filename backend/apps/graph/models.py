from django.db import models
from django.contrib.auth.models import User
import json


class TextProcessingRequest(models.Model):
    """
    Model to track text processing requests.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='text_processing_requests')
    post_id = models.CharField(max_length=255, db_index=True)
    topic = models.CharField(max_length=500)
    source = models.CharField(max_length=255)
    
    # Processing status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Request data
    payload = models.JSONField(help_text="Original text processing payload")
    
    # Processing results
    processing_result = models.JSONField(null=True, blank=True, help_text="Processing result from pipeline")
    error_message = models.TextField(blank=True, help_text="Error message if processing failed")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    processing_completed_at = models.DateTimeField(null=True, blank=True)
    processing_time_seconds = models.FloatField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post_id', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"TextProcessingRequest({self.post_id}) - {self.status}"
    
    @property
    def extracted_entities_count(self):
        """Get count of extracted entities from processing result."""
        if self.processing_result:
            return self.processing_result.get('extracted_entities', 0)
        return 0
    
    @property
    def extracted_relations_count(self):
        """Get count of extracted relations from processing result."""
        if self.processing_result:
            return self.processing_result.get('extracted_relations', 0)
        return 0


class KnowledgeGraphStatistics(models.Model):
    """
    Model to store periodic snapshots of knowledge graph statistics.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Node counts
    total_nodes = models.IntegerField(default=0)
    total_relationships = models.IntegerField(default=0)
    user_nodes = models.IntegerField(default=0)
    post_nodes = models.IntegerField(default=0)
    topic_nodes = models.IntegerField(default=0)
    source_nodes = models.IntegerField(default=0)
    entity_nodes = models.IntegerField(default=0)
    
    # Additional statistics
    statistics_data = models.JSONField(default=dict, help_text="Additional graph statistics")
    
    class Meta:
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'
    
    def __str__(self):
        return f"KGStats({self.timestamp}) - {self.total_nodes} nodes, {self.total_relationships} rels"
    
    @classmethod
    def create_from_neo4j_stats(cls, stats: dict):
        """
        Create a statistics record from Neo4j stats.
        
        Args:
            stats: Statistics dictionary from Neo4j
        """
        return cls.objects.create(
            total_nodes=stats.get('total_nodes', 0),
            total_relationships=stats.get('total_relationships', 0),
            user_nodes=stats.get('users', 0),
            post_nodes=stats.get('posts', 0),
            topic_nodes=stats.get('topics', 0),
            source_nodes=stats.get('sources', 0),
            entity_nodes=stats.get('entities', 0),
            statistics_data=stats
        )
