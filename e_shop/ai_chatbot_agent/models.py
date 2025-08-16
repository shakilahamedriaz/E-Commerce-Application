from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class ChatSession(models.Model):
    """Chat session model to track conversations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Chat Session {self.session_id[:8]}..."

class ChatMessage(models.Model):
    """Individual chat messages within a session"""
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)  # Store additional info like products, links
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

class ProductKnowledge(models.Model):
    """Product knowledge base for RAG"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.CharField(max_length=255, unique=True)
    product_name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    availability = models.BooleanField(default=True)
    features = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    embedding_id = models.CharField(max_length=255, blank=True)  # Pinecone vector ID
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['product_name']
    
    def __str__(self):
        return self.product_name

class ChatbotConfig(models.Model):
    """Configuration for chatbot behavior"""
    name = models.CharField(max_length=100, unique=True)
    model_name = models.CharField(max_length=255, default="Qwen/Qwen2-7B-Instruct")
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=500)
    system_prompt = models.TextField(default="You are a helpful e-commerce assistant.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class UserFeedback(models.Model):
    """User feedback on chatbot responses"""
    FEEDBACK_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    feedback_type = models.CharField(max_length=10, choices=FEEDBACK_CHOICES)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.feedback_type} feedback for {self.message.id}"
