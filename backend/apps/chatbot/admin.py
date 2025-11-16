from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import ChatSession, ChatMessage


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_id_short', 'user_link', 'title_preview', 'message_count',
        'is_active', 'created_at', 'updated_at'
    ]
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['session_id', 'title', 'user__username', 'user__email']
    readonly_fields = ['session_id', 'created_at', 'updated_at', 'message_count']
    
    fieldsets = [
        ('Session Info', {
            'fields': ('session_id', 'user', 'title', 'is_active')
        }),
        ('Metadata', {
            'fields': ('context', 'message_count', 'total_tokens'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    ]
    
    def session_id_short(self, obj):
        return f"{obj.session_id[:20]}..."
    session_id_short.short_description = 'Session ID'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def title_preview(self, obj):
        if obj.title:
            return obj.title[:50] + ('...' if len(obj.title) > 50 else '')
        return f"Session {obj.session_id[:8]}"
    title_preview.short_description = 'Title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'session_link', 'role', 'content_preview', 'task_type',
        'user_intent', 'confidence', 'created_at'
    ]
    list_filter = ['role', 'task_type', 'user_intent', 'created_at']
    search_fields = ['content', 'session__session_id', 'session__user__username']
    readonly_fields = ['created_at', 'session', 'role', 'content']
    
    fieldsets = [
        ('Message Info', {
            'fields': ('session', 'role', 'content')
        }),
        ('Metadata', {
            'fields': ('message_data', 'task_type', 'user_intent', 'confidence'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('tokens_used', 'processing_time_ms'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    ]
    
    def session_link(self, obj):
        url = reverse('admin:chatbot_chatsession_change', args=[obj.session.pk])
        return format_html('<a href="{}">{}</a>', 
                          url, f"{obj.session.session_id[:15]}...")
    session_link.short_description = 'Session'
    
    def content_preview(self, obj):
        return obj.content[:100] + ('...' if len(obj.content) > 100 else '')
    content_preview.short_description = 'Content'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('session__user')
