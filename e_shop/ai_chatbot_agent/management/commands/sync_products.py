from django.core.management.base import BaseCommand
from django.db import transaction
from shop.models import Product, Category
from ai_chatbot_agent.models import ProductKnowledge, ChatbotConfig
from ai_chatbot_agent.services.vector_store import VectorStoreService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync products from shop app to AI chatbot vector database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force resync all products even if they already exist',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of products to process in each batch',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting product sync to vector database...'))
        
        vector_store = VectorStoreService()
        if not vector_store.index:
            self.stdout.write(
                self.style.ERROR('Vector store not initialized. Please check your Pinecone configuration.')
            )
            return

        force_sync = options['force']
        batch_size = options['batch_size']
        
        # Get all products
        products = Product.objects.select_related('category').all()
        total_products = products.count()
        
        if total_products == 0:
            self.stdout.write(self.style.WARNING('No products found in the shop app.'))
            return

        self.stdout.write(f'Found {total_products} products to sync.')
        
        synced_count = 0
        error_count = 0
        skipped_count = 0
        
        # Process products in batches
        for i in range(0, total_products, batch_size):
            batch_products = products[i:i + batch_size]
            
            with transaction.atomic():
                for product in batch_products:
                    try:
                        # Check if product already exists in knowledge base
                        existing_knowledge = ProductKnowledge.objects.filter(
                            product_id=str(product.id)
                        ).first()
                        
                        if existing_knowledge and not force_sync:
                            skipped_count += 1
                            continue
                        
                        # Prepare product data
                        product_data = self._prepare_product_data(product)
                        
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
                                    'features': product_data.get('features', []),
                                    'tags': product_data.get('tags', []),
                                    'embedding_id': str(product.id)
                                }
                            )
                            synced_count += 1
                            
                            if synced_count % 10 == 0:
                                self.stdout.write(f'Synced {synced_count}/{total_products} products...')
                        else:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'Failed to sync product: {product.name}')
                            )
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error syncing product {product.id}: {str(e)}")
                        self.stdout.write(
                            self.style.ERROR(f'Error syncing product {product.name}: {str(e)}')
                        )
        
        # Create default chatbot configuration if it doesn't exist
        self._create_default_config()
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('Product sync completed!'))
        self.stdout.write(f'Total products: {total_products}')
        self.stdout.write(self.style.SUCCESS(f'Successfully synced: {synced_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped (already exists): {skipped_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))

    def _prepare_product_data(self, product):
        """Prepare product data for vector store"""
        # Get category name
        category_name = 'General'
        if hasattr(product, 'category') and product.category:
            category_name = product.category.name
        
        # Check availability
        availability = True
        if hasattr(product, 'available'):
            availability = product.available
        elif hasattr(product, 'stock') and hasattr(product, 'stock_quantity'):
            availability = product.stock_quantity > 0
        
        # Enhanced feature extraction from description
        features = []
        tags = []
        
        if product.description:
            description_lower = product.description.lower()
            
            # Enhanced product features to look for
            feature_keywords = {
                'materials': ['cotton', 'bamboo', 'recycled', 'organic', 'eco-friendly', 'natural', 'sustainable'],
                'technology': ['solar-powered', 'led', 'wireless', 'bluetooth', 'smart', 'digital'],
                'quality': ['premium', 'professional', 'handmade', 'artisan', 'luxury', 'high-quality'],
                'size': ['compact', 'portable', 'lightweight', 'mini', 'large', 'small', 'medium'],
                'durability': ['durable', 'waterproof', 'weather-resistant', 'long-lasting'],
                'energy': ['energy-saving', 'rechargeable', 'battery-powered', 'efficient']
            }
            
            for category, keywords in feature_keywords.items():
                for keyword in keywords:
                    if keyword in description_lower:
                        features.append(keyword.title())
                        tags.append(category)
            
            # Extract color information
            colors = ['red', 'blue', 'green', 'black', 'white', 'yellow', 'orange', 'purple', 'pink', 'brown']
            for color in colors:
                if color in description_lower:
                    features.append(color.title())
                    tags.append('color')
        
        # Add category-specific features
        if 'clothing' in category_name.lower():
            tags.extend(['apparel', 'fashion', 'wear'])
        elif 'electronics' in category_name.lower():
            tags.extend(['tech', 'gadget', 'device'])
        elif 'home' in category_name.lower():
            tags.extend(['household', 'domestic', 'interior'])
        
        return {
            'name': product.name,
            'description': product.description or '',
            'category': category_name,
            'price': float(product.price),
            'availability': availability,
            'features': list(set(features)),  # Remove duplicates
            'tags': list(set(tags))  # Remove duplicates
        }

    def _create_default_config(self):
        """Create default chatbot configuration"""
        ChatbotConfig.objects.get_or_create(
            name='default',
            defaults={
                'model_name': 'Qwen/Qwen2-7B-Instruct',
                'temperature': 0.7,
                'max_tokens': 500,
                'system_prompt': """You are a helpful and knowledgeable e-commerce assistant for an online shopping platform. Your role is to:

1. Help customers find products they're looking for
2. Provide detailed product information, specifications, and recommendations
3. Assist with order inquiries, shipping information, and return policies
4. Answer questions about product availability, pricing, and promotions
5. Offer personalized shopping recommendations based on customer preferences

Guidelines:
- Always be helpful, polite, and professional
- If you don't know something, admit it and offer to help find the information
- When recommending products, explain why they might be suitable
- Include relevant product links when discussing specific items
- Keep responses concise but informative
- Ask clarifying questions when needed to better assist the customer

Remember: Your goal is to enhance the shopping experience and help customers make informed purchasing decisions.""",
                'is_active': True
            }
        )
