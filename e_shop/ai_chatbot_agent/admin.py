from django.contrib import admin
from .models import ChatSession, ChatMessage, ProductKnowledge, ChatbotConfig, UserFeedback

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['session_id', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'message_type', 'content_preview', 'timestamp']
    list_filter = ['message_type', 'timestamp']
    search_fields = ['content', 'session__session_id']
    readonly_fields = ['id', 'timestamp']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(ProductKnowledge)
class ProductKnowledgeAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'category', 'price', 'availability', 'created_at']
    list_filter = ['category', 'availability', 'created_at']
    search_fields = ['product_name', 'description', 'category']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(ChatbotConfig)
class ChatbotConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_name', 'temperature', 'max_tokens', 'is_active']
    list_filter = ['is_active', 'model_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['message', 'user', 'feedback_type', 'timestamp']
    list_filter = ['feedback_type', 'timestamp']
    search_fields = ['comment', 'message__content']
    readonly_fields = ['id', 'timestamp']
