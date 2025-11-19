from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import TextProcessingRequest, KnowledgeGraphStatistics


@admin.register(TextProcessingRequest)
class TextProcessingRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'post_id', 'topic', 'status', 
        'extracted_entities_count', 'extracted_relations_count',
        'processing_time_seconds', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'processing_started_at']
    search_fields = ['post_id', 'topic', 'source', 'user__username']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'processing_started_at', 
        'processing_completed_at', 'processing_time_seconds',
        'extracted_entities_count', 'extracted_relations_count'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'post_id', 'topic', 'source', 'status')
        }),
        ('Processing Details', {
            'fields': (
                'processing_started_at', 'processing_completed_at', 
                'processing_time_seconds', 'error_message'
            )
        }),
        ('Results', {
            'fields': (
                'extracted_entities_count', 'extracted_relations_count',
                'processing_result'
            )
        }),
        ('Raw Data', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    def colored_status(self, obj):
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    colored_status.short_description = 'Status'
    
    def view_user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    view_user_link.short_description = 'User'


@admin.register(KnowledgeGraphStatistics)
class KnowledgeGraphStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'total_nodes', 'total_relationships',
        'user_nodes', 'post_nodes', 'topic_nodes', 
        'source_nodes', 'entity_nodes'
    ]
    list_filter = ['timestamp']
    readonly_fields = [
        'timestamp', 'total_nodes', 'total_relationships',
        'user_nodes', 'post_nodes', 'topic_nodes', 
        'source_nodes', 'entity_nodes', 'statistics_data'
    ]
    
    def has_add_permission(self, request):
        # Prevent manual addition - these should be created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Make read-only
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Allow deletion for cleanup
        return True
