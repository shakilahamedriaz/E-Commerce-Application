import os
from typing import List, Dict, Any, Optional
import pinecone
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import numpy as np
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Service for managing Pinecone vector database operations"""
    
    def __init__(self):
        self.pc = None
        self.index = None
        # Use all-MiniLM-L6-v2 which produces 384 dimensions
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self.index_name = getattr(settings, 'PINECONE_INDEX_NAME', 'ecommerce-chatbot')
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone connection"""
        try:
            api_key = getattr(settings, 'PINECONE_API_KEY', None)
            if not api_key:
                logger.warning("Pinecone API key not found. Vector operations will be disabled.")
                return
                
            self.pc = Pinecone(api_key=api_key)
            
            # Check if index exists and has correct dimensions
            existing_indexes = self.pc.list_indexes().names()
            
            if self.index_name in existing_indexes:
                # Check if dimensions match
                index_info = self.pc.describe_index(self.index_name)
                if index_info.dimension != self.dimension:
                    logger.warning(f"Index {self.index_name} has {index_info.dimension} dimensions, expected {self.dimension}")
                    logger.warning("Please delete the existing index or use a different index name")
                    # For now, we'll try to use it anyway
                    self.index = self.pc.Index(self.index_name)
                    return
            else:
                # Create index with correct dimensions
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric='cosine',
                    spec={
                        'serverless': {
                            'cloud': 'aws',
                            'region': 'us-east-1'
                        }
                    }
                )
            
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Pinecone initialized successfully with index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            self.pc = None
            self.index = None
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for given text"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to create embedding: {str(e)}")
            return []
    
    def upsert_product(self, product_id: str, product_data: Dict[str, Any]) -> bool:
        """Upsert product data to vector store"""
        if not self.index:
            logger.warning("Pinecone not initialized. Cannot upsert product.")
            return False
            
        try:
            # Create combined text for embedding
            text_content = f"{product_data['name']} {product_data['description']} {product_data['category']}"
            if 'features' in product_data and product_data['features']:
                text_content += " " + " ".join(product_data['features'])
            
            # Create embedding
            embedding = self.create_embedding(text_content)
            if not embedding:
                return False
            
            # Prepare metadata
            metadata = {
                'product_id': product_id,
                'name': product_data['name'],
                'category': product_data['category'],
                'price': float(product_data['price']),
                'availability': product_data.get('availability', True)
            }
            
            # Upsert to Pinecone
            self.index.upsert(vectors=[(product_id, embedding, metadata)])
            logger.info(f"Successfully upserted product {product_id} to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert product {product_id}: {str(e)}")
            return False
    
    def search_products(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict[str, Any]]:
        """Search for products based on query with enhanced ranking"""
        if not self.index:
            logger.warning("Pinecone not initialized. Cannot search products.")
            return []
            
        try:
            # Create enhanced query embedding
            enhanced_query = self._enhance_query(query)
            query_embedding = self.create_embedding(enhanced_query)
            if not query_embedding:
                return []
            
            # Search in Pinecone with filters if provided
            search_params = {
                'vector': query_embedding,
                'top_k': min(top_k * 2, 20),  # Get more results for better ranking
                'include_metadata': True
            }
            
            if filters:
                search_params['filter'] = filters
            
            results = self.index.query(**search_params)
            
            products = []
            for match in results['matches']:
                product = {
                    'product_id': match['metadata']['product_id'],
                    'name': match['metadata']['name'],
                    'category': match['metadata']['category'],
                    'price': match['metadata']['price'],
                    'availability': match['metadata']['availability'],
                    'score': match['score'],
                    'relevance_score': self._calculate_relevance_score(query, match)
                }
                products.append(product)
            
            # Re-rank based on relevance score
            products.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Return top results
            final_products = products[:top_k]
            
            logger.info(f"Found {len(final_products)} products for query: {query}")
            return final_products
            
        except Exception as e:
            logger.error(f"Failed to search products: {str(e)}")
            return []
    
    def _enhance_query(self, query: str) -> str:
        """Enhance query with synonyms and related terms"""
        query_lower = query.lower()
        
        # Product synonyms
        synonyms = {
            'tshirt': 't-shirt shirt apparel clothing wear',
            't-shirt': 'tshirt shirt apparel clothing wear',
            'shirt': 't-shirt tshirt apparel clothing wear',
            'lamp': 'light lighting illumination desk table',
            'notebook': 'book journal diary writing pad',
            'toothbrush': 'dental hygiene oral care brush',
            'bulb': 'light lamp illumination led energy saving'
        }
        
        enhanced_terms = [query]
        for term, related in synonyms.items():
            if term in query_lower:
                enhanced_terms.extend(related.split())
        
        return ' '.join(enhanced_terms)
    
    def _calculate_relevance_score(self, query: str, match: Dict) -> float:
        """Calculate enhanced relevance score"""
        base_score = match['score']
        
        # Boost score based on exact matches
        query_lower = query.lower()
        name_lower = match['metadata']['name'].lower()
        
        # Exact name match boost
        if query_lower in name_lower or name_lower in query_lower:
            base_score += 0.3
        
        # Category relevance boost
        if 'category' in match['metadata']:
            category_lower = match['metadata']['category'].lower()
            if any(word in category_lower for word in query_lower.split()):
                base_score += 0.2
        
        # Availability boost
        if match['metadata'].get('availability', False):
            base_score += 0.1
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def delete_product(self, product_id: str) -> bool:
        """Delete product from vector store"""
        if not self.index:
            logger.warning("Pinecone not initialized. Cannot delete product.")
            return False
            
        try:
            self.index.delete(ids=[product_id])
            logger.info(f"Successfully deleted product {product_id} from vector store")
            return True
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {str(e)}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.index:
            return {}
            
        try:
            stats = self.index.describe_index_stats()
            return stats
        except Exception as e:
            logger.error(f"Failed to get index stats: {str(e)}")
            return {}
