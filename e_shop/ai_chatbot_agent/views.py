import json
import uuid
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
from django.core.paginator import Paginator
from .models import ChatSession, ChatMessage, ProductKnowledge, ChatbotConfig
from .services.chatbot_service import ChatbotService
from .services.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def chat_api_view(request):
    """Handle chat API requests"""
    try:
        chatbot_service = ChatbotService()
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not user_message:
            return JsonResponse({'success': False, 'error': 'Message is required'}, status=400)
        
        # Get or create chat session
        chat_session, created = ChatSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user': request.user if request.user.is_authenticated else None
            }
        )
        
        # Save user message
        user_chat_message = ChatMessage.objects.create(
            session=chat_session,
            message_type='user',
            content=user_message
        )
        
        # Get session history for context
        session_history = list(
            ChatMessage.objects.filter(session=chat_session)
            .order_by('-timestamp')[:10]
            .values('message_type', 'content')
        )
        session_history.reverse()  # Chronological order
        
        # Generate bot response
        response_data = chatbot_service.generate_response(
            user_message, 
            session_history
        )
        
        # Save bot response
        bot_chat_message = ChatMessage.objects.create(
            session=chat_session,
            message_type='bot',
            content=response_data['response'],
            metadata={
                'intent': response_data['intent'],
                'products': response_data['products'],
                'metadata': response_data['metadata']
            }
        )
        
        return JsonResponse({
            'success': True,
            'response': response_data['response'],
            'session_id': session_id,
            'message_id': str(bot_chat_message.id),
            'intent': response_data['intent'],
            'products': response_data['products'],
            'metadata': response_data['metadata']
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in chat API: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)

class ChatbotView(View):
    """Main chatbot view for handling chat interactions"""
    
    def __init__(self):
        super().__init__()
        self.chatbot_service = ChatbotService()
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        """Render the chat interface"""
        return render(request, 'ai_chatbot_agent/chat.html')
    
    def post(self, request):
        """Handle chat message and return response"""
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            session_id = data.get('session_id', str(uuid.uuid4()))
            
            if not user_message:
                return JsonResponse({'error': 'Message is required'}, status=400)
            
            # Get or create chat session
            chat_session, created = ChatSession.objects.get_or_create(
                session_id=session_id,
                defaults={
                    'user': request.user if request.user.is_authenticated else None
                }
            )
            
            # Save user message
            user_chat_message = ChatMessage.objects.create(
                session=chat_session,
                message_type='user',
                content=user_message
            )
            
            # Get session history for context
            session_history = list(
                ChatMessage.objects.filter(session=chat_session)
                .order_by('-timestamp')[:10]
                .values('message_type', 'content')
            )
            session_history.reverse()  # Chronological order
            
            # Generate bot response
            response_data = self.chatbot_service.generate_response(
                user_message, 
                session_history
            )
            
            # Save bot response
            bot_chat_message = ChatMessage.objects.create(
                session=chat_session,
                message_type='bot',
                content=response_data['response'],
                metadata={
                    'intent': response_data['intent'],
                    'products': response_data['products'],
                    'metadata': response_data['metadata']
                }
            )
            
            return JsonResponse({
                'success': True,
                'response': response_data['response'],
                'session_id': session_id,
                'message_id': str(bot_chat_message.id),
                'intent': response_data['intent'],
                'products': response_data['products'],
                'metadata': response_data['metadata']
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error in chatbot view: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def feedback_view(request):
    """Handle user feedback on chatbot responses"""
    try:
        data = json.loads(request.body)
        message_id = data.get('message_id')
        feedback_type = data.get('feedback_type')
        comment = data.get('comment', '')
        
        if not message_id or not feedback_type:
            return JsonResponse({'error': 'message_id and feedback_type are required'}, status=400)
        
        # Get the message
        try:
            message = ChatMessage.objects.get(id=message_id)
        except ChatMessage.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
        
        # Create feedback
        from .models import UserFeedback
        UserFeedback.objects.create(
            message=message,
            user=request.user if request.user.is_authenticated else None,
            feedback_type=feedback_type,
            comment=comment
        )
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error in feedback view: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
def chat_history_view(request):
    """View chat history for authenticated users"""
    try:
        sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
        paginator = Paginator(sessions, 10)  # Show 10 sessions per page
        
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'ai_chatbot_agent/chat_history.html', {
            'page_obj': page_obj
        })
    except Exception as e:
        logger.error(f"Error in chat history view: {str(e)}")
        return render(request, 'ai_chatbot_agent/chat_history.html', {'error': 'Failed to load chat history'})

@login_required
def session_detail_view(request, session_id):
    """View detailed messages for a specific chat session"""
    try:
        session = ChatSession.objects.get(session_id=session_id, user=request.user)
        messages = session.messages.all().order_by('timestamp')
        
        return render(request, 'ai_chatbot_agent/session_detail.html', {
            'session': session,
            'messages': messages
        })
    except ChatSession.DoesNotExist:
        return render(request, 'ai_chatbot_agent/session_detail.html', {'error': 'Session not found'})
    except Exception as e:
        logger.error(f"Error in session detail view: {str(e)}")
        return render(request, 'ai_chatbot_agent/session_detail.html', {'error': 'Failed to load session'})

@csrf_exempt
@require_http_methods(["POST"])
def sync_products_view(request):
    """Sync products from shop app to vector database"""
    try:
        # Import shop models
        from shop.models import Product
        
        vector_store = VectorStoreService()
        synced_count = 0
        error_count = 0
        
        # Get all products from shop app
        products = Product.objects.all()
        
        for product in products:
            try:
                # Prepare product data
                product_data = {
                    'name': product.name,
                    'description': product.description,
                    'category': product.category.name if hasattr(product, 'category') else 'General',
                    'price': float(product.price),
                    'availability': product.available if hasattr(product, 'available') else True,
                    'features': []  # You can enhance this based on your product model
                }
                
                # Sync to vector store
                success = vector_store.upsert_product(str(product.id), product_data)
                
                if success:
                    # Update or create ProductKnowledge
                    ProductKnowledge.objects.update_or_create(
                        product_id=str(product.id),
                        defaults={
                            'product_name': product.name,
                            'description': product.description,
                            'category': product_data['category'],
                            'price': product.price,
                            'availability': product_data['availability'],
                            'embedding_id': str(product.id)
                        }
                    )
                    synced_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error syncing product {product.id}: {str(e)}")
                error_count += 1
        
        return JsonResponse({
            'success': True,
            'synced_count': synced_count,
            'error_count': error_count,
            'total_products': products.count()
        })
        
    except Exception as e:
        logger.error(f"Error in sync products view: {str(e)}")
        return JsonResponse({'error': 'Failed to sync products'}, status=500)

def chatbot_stats_view(request):
    """View chatbot statistics and analytics"""
    try:
        # Get basic stats
        total_sessions = ChatSession.objects.count()
        total_messages = ChatMessage.objects.count()
        active_sessions = ChatSession.objects.filter(is_active=True).count()
        
        # Get recent activity
        recent_sessions = ChatSession.objects.order_by('-created_at')[:5]
        
        # Get vector store stats
        vector_store = VectorStoreService()
        index_stats = vector_store.get_index_stats()
        
        context = {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'active_sessions': active_sessions,
            'recent_sessions': recent_sessions,
            'index_stats': index_stats
        }
        
        return render(request, 'ai_chatbot_agent/stats.html', context)
        
    except Exception as e:
        logger.error(f"Error in chatbot stats view: {str(e)}")
        return render(request, 'ai_chatbot_agent/stats.html', {'error': 'Failed to load stats'})

# API Views for external integrations
@csrf_exempt
@require_http_methods(["GET"])
def health_check_view(request):
    """Health check endpoint for the chatbot service"""
    try:
        chatbot_service = ChatbotService()
        vector_store = VectorStoreService()
        
        health_status = {
            'status': 'healthy',
            'llm_initialized': chatbot_service.llm is not None,
            'vector_store_initialized': vector_store.index is not None,
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)
