import os
import json
import logging
from typing import List, Dict, Any, Optional
from langchain_huggingface import HuggingFaceEndpoint
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from django.conf import settings
from .vector_store import VectorStoreService

logger = logging.getLogger(__name__)

class ChatbotService:
    """Main chatbot service using LangChain and Qwen2-7B-Instruct"""
    
    def __init__(self):
        self.vector_store = VectorStoreService()
        self.llm = None
        self._initialize_llm()
        self.system_prompt = self._get_system_prompt()
    
    def _initialize_llm(self):
        """Initialize the Qwen2-7B-Instruct model via Hugging Face"""
        try:
            hf_token = getattr(settings, 'HUGGINGFACE_API_TOKEN', None)
            if not hf_token:
                logger.error("Hugging Face API token not found")
                return
            
            self.llm = HuggingFaceEndpoint(
                repo_id="Qwen/Qwen2-7B-Instruct",
                huggingfacehub_api_token=hf_token,
                temperature=0.7,
                max_new_tokens=500,
                top_p=0.9,
                repetition_penalty=1.1,
                timeout=60
            )
            logger.info("Successfully initialized Qwen2-7B-Instruct model")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            self.llm = None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the chatbot"""
        return """You are a helpful and knowledgeable e-commerce assistant for an online shopping platform. Your role is to:

1. Help customers find products they're looking for
2. Provide detailed product information, specifications, and recommendations
3. Assist with order inquiries, shipping information, and return policies
4. Answer questions about product availability, pricing, and promotions
5. Offer personalized shopping recommendations based on customer preferences
6. Provide excellent customer service with a friendly and professional tone

Guidelines:
- Always be helpful, polite, and professional
- If you don't know something, admit it and offer to help find the information
- When recommending products, explain why they might be suitable
- Include relevant product links when discussing specific items
- Keep responses concise but informative
- Ask clarifying questions when needed to better assist the customer

Remember: Your goal is to enhance the shopping experience and help customers make informed purchasing decisions."""
    
    def _create_chat_prompt(self, user_message: str, context: str = "") -> ChatPromptTemplate:
        """Create a chat prompt with system message and context"""
        messages = [
            SystemMessagePromptTemplate.from_template(self.system_prompt),
        ]
        
        if context:
            context_template = "Here's some relevant product information that might help answer the customer's question:\n\n{context}\n\nCustomer question: {user_message}"
            messages.append(HumanMessagePromptTemplate.from_template(context_template))
        else:
            messages.append(HumanMessagePromptTemplate.from_template("{user_message}"))
        
        return ChatPromptTemplate.from_messages(messages)
    
    def _search_relevant_products(self, query: str, top_k: int = 3) -> str:
        """Search for relevant products and format as context"""
        try:
            products = self.vector_store.search_products(query, top_k)
            if not products:
                return ""
            
            context_parts = []
            for product in products:
                context_part = f"""
Product: {product['name']}
Category: {product['category']}
Price: ${product['price']:.2f}
Availability: {'Available' if product['availability'] else 'Out of Stock'}
Relevance Score: {product['score']:.3f}
"""
                context_parts.append(context_part.strip())
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Failed to search relevant products: {str(e)}")
            return ""
    
    def _extract_intent(self, message: str) -> Dict[str, Any]:
        """Extract intent from user message with improved accuracy"""
        message_lower = message.lower()
        
        intent_data = {
            'intent': 'general',
            'entities': [],
            'confidence': 0.5
        }
        
        # Enhanced product search intents
        product_keywords = [
            'looking for', 'search', 'find', 'need', 'want', 'show me', 'do you have', 
            'any', 'sell', 'available', 'browse', 'see', 'get', 'buy'
        ]
        if any(keyword in message_lower for keyword in product_keywords):
            intent_data['intent'] = 'product_search'
            intent_data['confidence'] = 0.8
        
        # Enhanced price inquiry intents
        price_keywords = [
            'price', 'cost', 'how much', 'expensive', 'cheap', 'budget', 'affordable',
            'pricing', 'rate', 'fee', 'charge', 'value', 'money'
        ]
        if any(keyword in message_lower for keyword in price_keywords):
            intent_data['intent'] = 'price_inquiry'
            intent_data['confidence'] = 0.8
        
        # Enhanced availability inquiry intents
        availability_keywords = [
            'available', 'in stock', 'out of stock', 'when will', 'delivery',
            'shipping', 'can i get', 'do you have', 'sold out'
        ]
        if any(keyword in message_lower for keyword in availability_keywords):
            intent_data['intent'] = 'availability_inquiry'
            intent_data['confidence'] = 0.8
        
        # Enhanced recommendation intents
        recommendation_keywords = [
            'recommend', 'suggest', 'best', 'popular', 'top rated', 'good',
            'advice', 'help me choose', 'what should', 'which one'
        ]
        if any(keyword in message_lower for keyword in recommendation_keywords):
            intent_data['intent'] = 'recommendation'
            intent_data['confidence'] = 0.9
        
        # Extract entities (product types, categories, features)
        entities = []
        
        # Product categories
        categories = ['clothing', 'electronics', 'home', 'beauty', 'sports', 'books', 'toys']
        for category in categories:
            if category in message_lower:
                entities.append({'type': 'category', 'value': category})
        
        # Product types
        product_types = [
            'shirt', 't-shirt', 'tshirt', 'laptop', 'phone', 'notebook', 'book',
            'lamp', 'light', 'toothbrush', 'bulb', 'powder', 'protein'
        ]
        for product_type in product_types:
            if product_type in message_lower:
                entities.append({'type': 'product', 'value': product_type})
        
        # Colors
        colors = ['red', 'blue', 'green', 'black', 'white', 'yellow', 'orange', 'purple']
        for color in colors:
            if color in message_lower:
                entities.append({'type': 'color', 'value': color})
        
        # Price ranges
        import re
        price_patterns = [
            r'under \$?(\d+)',
            r'less than \$?(\d+)',
            r'below \$?(\d+)',
            r'around \$?(\d+)',
            r'about \$?(\d+)',
            r'\$(\d+)'
        ]
        for pattern in price_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                entities.append({'type': 'price_range', 'value': int(match)})
        
        intent_data['entities'] = entities
        return intent_data
    
    def generate_response(self, user_message: str, session_history: List[Dict] = None) -> Dict[str, Any]:
        """Generate chatbot response using RAG"""
        try:
            # Extract intent
            intent_data = self._extract_intent(user_message)
            
            # Search for relevant products
            context = ""
            relevant_products = []
            
            if intent_data['intent'] in ['product_search', 'price_inquiry', 'availability_inquiry', 'recommendation']:
                context = self._search_relevant_products(user_message)
                relevant_products = self.vector_store.search_products(user_message, top_k=5)
            
            # Generate response
            if self.llm:
                try:
                    # Create prompt
                    if context:
                        prompt = self._create_chat_prompt(user_message, context)
                        formatted_prompt = prompt.format(context=context, user_message=user_message)
                    else:
                        prompt = self._create_chat_prompt(user_message)
                        formatted_prompt = prompt.format(user_message=user_message)
                    
                    # Generate response using LLM
                    response = self.llm.invoke(formatted_prompt)
                    
                except Exception as e:
                    logger.error(f"LLM invocation failed: {str(e)}")
                    # Fallback to rule-based response
                    response = self._generate_fallback_response(user_message, relevant_products, intent_data)
            else:
                # Use fallback response system
                response = self._generate_fallback_response(user_message, relevant_products, intent_data)
            
            return {
                'response': response,
                'intent': intent_data['intent'],
                'products': relevant_products,
                'metadata': {
                    'context_used': bool(context),
                    'confidence': intent_data['confidence'],
                    'num_products_found': len(relevant_products),
                    'llm_used': self.llm is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}")
            return {
                'response': "I apologize, but I encountered an error while processing your request. Please try rephrasing your question.",
                'intent': 'error',
                'products': [],
                'metadata': {'error': str(e)}
            }
    
    def _generate_fallback_response(self, user_message: str, products: List[Dict], intent_data: Dict) -> str:
        """Generate enhanced fallback response when LLM is not available"""
        intent = intent_data['intent']
        entities = intent_data.get('entities', [])
        
        # Extract entity information
        price_filters = [e['value'] for e in entities if e['type'] == 'price_range']
        color_filters = [e['value'] for e in entities if e['type'] == 'color']
        category_filters = [e['value'] for e in entities if e['type'] == 'category']
        
        if intent == 'product_search' and products:
            response = f"I found {len(products)} products that match your search"
            
            # Add entity context
            if color_filters:
                response += f" for {', '.join(color_filters)} items"
            if category_filters:
                response += f" in {', '.join(category_filters)}"
            if price_filters:
                response += f" under ${max(price_filters)}"
            
            response += ":\n\n"
            
            for i, product in enumerate(products[:3], 1):
                response += f"**{i}. {product['name']}**\n"
                response += f"   💰 Price: ${product['price']:.2f}\n"
                response += f"   📂 Category: {product['category']}\n"
                response += f"   {'✅ Available' if product['availability'] else '❌ Out of Stock'}\n"
                response += f"   🎯 Match Score: {product.get('relevance_score', product['score']):.2f}\n\n"
            
            if len(products) > 3:
                response += f"...and {len(products) - 3} more products available!\n\n"
            
            response += "Would you like more details about any of these products?"
            return response
        
        elif intent == 'price_inquiry' and products:
            response = "Here are the prices for products matching your query:\n\n"
            for product in products[:5]:
                response += f"💰 **{product['name']}**: ${product['price']:.2f}\n"
                if not product['availability']:
                    response += "   ⚠️ Currently out of stock\n"
            
            # Price range analysis
            if products:
                prices = [p['price'] for p in products]
                response += f"\n📊 Price range: ${min(prices):.2f} - ${max(prices):.2f}\n"
                response += f"📈 Average price: ${sum(prices)/len(prices):.2f}"
            return response
        
        elif intent == 'availability_inquiry' and products:
            available_count = sum(1 for p in products if p['availability'])
            response = f"Availability status for {len(products)} products:\n\n"
            
            for product in products[:5]:
                status = "✅ Available" if product['availability'] else "❌ Out of Stock"
                response += f"{status} **{product['name']}** - ${product['price']:.2f}\n"
            
            response += f"\n📊 Summary: {available_count}/{len(products)} products are currently available."
            return response
        
        elif intent == 'recommendation':
            if products:
                # Get best match
                best_product = max(products, key=lambda x: x.get('relevance_score', x['score']))
                response = f"🎯 **Top Recommendation**: **{best_product['name']}**\n\n"
                response += f"💰 Price: ${best_product['price']:.2f}\n"
                response += f"📂 Category: {best_product['category']}\n"
                response += f"{'✅ Available now' if best_product['availability'] else '❌ Currently out of stock'}\n"
                response += f"🌟 Relevance Score: {best_product.get('relevance_score', best_product['score']):.2f}\n\n"
                
                if len(products) > 1:
                    response += "**Other great options:**\n"
                    for product in products[1:4]:
                        response += f"• {product['name']} - ${product['price']:.2f}\n"
                
                response += "\nWould you like more details about any of these recommendations?"
                return response
            else:
                response = "I'd be happy to recommend products! "
                if category_filters:
                    response += f"For {', '.join(category_filters)} items, "
                response += "could you tell me more about what you're looking for? For example:\n"
                response += "• Budget range\n• Specific features\n• Intended use\n• Preferred style or color"
                return response
        
        elif 'hello' in user_message.lower() or 'hi' in user_message.lower():
            return ("Hello! 👋 Welcome to our store! I'm your AI shopping assistant. "
                   "I can help you find products, check prices, and provide recommendations. "
                   "What are you looking for today?")
        
        elif 'thank' in user_message.lower():
            return "You're welcome! 😊 Is there anything else I can help you find today?"
        
        else:
            response = "I'm here to help you find the perfect products! You can ask me about:\n\n"
            response += "🔍 **Product searches** (e.g., 'show me t-shirts under $100')\n"
            response += "💰 **Pricing information** (e.g., 'how much is the organic cotton shirt?')\n"
            response += "📦 **Product availability** (e.g., 'is the desk lamp in stock?')\n"
            response += "🎯 **Recommendations** (e.g., 'recommend a good notebook')\n\n"
            response += "What would you like to know about our products?"
            return response
    
    def process_feedback(self, message_id: str, feedback_type: str, comment: str = "") -> bool:
        """Process user feedback for improving responses"""
        try:
            # Here you could implement feedback processing logic
            # For example, storing feedback for model fine-tuning
            logger.info(f"Received {feedback_type} feedback for message {message_id}: {comment}")
            return True
        except Exception as e:
            logger.error(f"Failed to process feedback: {str(e)}")
            return False
    
    def get_conversation_summary(self, session_history: List[Dict]) -> str:
        """Generate a summary of the conversation"""
        if not session_history or not self.llm:
            return ""
        
        try:
            # Create a summary prompt
            history_text = "\n".join([
                f"{'User' if msg['type'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in session_history[-10:]  # Last 10 messages
            ])
            
            summary_prompt = f"""Please provide a brief summary of this conversation:

{history_text}

Summary:"""
            
            summary = self.llm.invoke(summary_prompt)
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate conversation summary: {str(e)}")
            return ""
