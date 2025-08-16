from django.core.management.base import BaseCommand
from ai_chatbot_agent.services.vector_store import VectorStoreService
from pinecone import Pinecone
import os
import time

class Command(BaseCommand):
    help = 'Fix Pinecone index dimensions by recreating with correct dimensions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force delete existing index and recreate',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('PINECONE_API_KEY')
        index_name = os.getenv('PINECONE_INDEX_NAME', 'ecommerce-chatbot')
        
        if not api_key:
            self.stdout.write(self.style.ERROR('PINECONE_API_KEY not found'))
            return
        
        try:
            pc = Pinecone(api_key=api_key)
            
            # Check existing indexes
            existing_indexes = pc.list_indexes().names()
            self.stdout.write(f"📋 Existing indexes: {existing_indexes}")
            
            if index_name in existing_indexes:
                index_info = pc.describe_index(index_name)
                self.stdout.write(f"📊 Current index '{index_name}' dimensions: {index_info.dimension}")
                
                if index_info.dimension == 384:
                    self.stdout.write(self.style.SUCCESS("✅ Index already has correct dimensions (384)"))
                    return
                
                if force:
                    self.stdout.write(f"🗑️ Deleting existing index '{index_name}'...")
                    pc.delete_index(index_name)
                    time.sleep(10)  # Wait for deletion
                else:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Index '{index_name}' has wrong dimensions ({index_info.dimension}). "
                        f"Use --force to delete and recreate."
                    ))
                    return
            
            # Create new index with correct dimensions
            self.stdout.write(f"🏗️ Creating index '{index_name}' with 384 dimensions...")
            
            pc.create_index(
                name=index_name,
                dimension=384,  # Correct dimension for all-MiniLM-L6-v2
                metric='cosine',
                spec={
                    'serverless': {
                        'cloud': 'aws',
                        'region': 'us-east-1'
                    }
                }
            )
            
            # Wait for index to be ready
            self.stdout.write("⏳ Waiting for index to be ready...")
            while not pc.describe_index(index_name).status['ready']:
                time.sleep(2)
                self.stdout.write(".", ending='')
            
            self.stdout.write()
            self.stdout.write(self.style.SUCCESS(f"✅ Index '{index_name}' created successfully with 384 dimensions!"))
            
            # Verify
            new_index_info = pc.describe_index(index_name)
            self.stdout.write(f"📊 New index dimensions: {new_index_info.dimension}")
            self.stdout.write(f"📊 New index status: {new_index_info.status}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
