from django.urls import path
from . import views

app_name = 'ai_chatbot_agent'

urlpatterns = [
    # Main chat interface
    path('', views.ChatbotView.as_view(), name='chat'),
    path('chat/', views.ChatbotView.as_view(), name='chat_interface'),
    
    # API endpoints
    path('api/chat/', views.chat_api_view, name='chat_api'),
    path('api/feedback/', views.feedback_view, name='feedback_api'),
    path('api/sync-products/', views.sync_products_view, name='sync_products'),
    path('api/health/', views.health_check_view, name='health_check'),
    
    # User interface views
    path('history/', views.chat_history_view, name='chat_history'),
    path('session/<str:session_id>/', views.session_detail_view, name='session_detail'),
    path('stats/', views.chatbot_stats_view, name='chatbot_stats'),
]
