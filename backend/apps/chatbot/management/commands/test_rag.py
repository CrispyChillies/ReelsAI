"""
Management command to test the RAG retrieve_and_answer function.
"""

import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from apps.agents.chatbot.tools import retrieve_and_answer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to test RAG functionality"""
    
    help = "Test the RAG retrieve_and_answer function with sample queries"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            default=1,
            help='User ID to test RAG for (default: 1)'
        )
        parser.add_argument(
            '--queries',
            nargs='+',
            default=[
                "What content do I have saved?",
                "Show me my TikTok videos",
                "What are my recent posts about?",
                "Tell me about my Facebook content",
                "Do I have any content about technology?"
            ],
            help='List of test queries to run'
        )
        parser.add_argument(
            '--k',
            type=int,
            default=5,
            help='Number of results to retrieve per query (default: 5)'
        )
        parser.add_argument(
            '--insert-test-data',
            action='store_true',
            help='Insert sample test data before querying'
        )
    
    def handle(self, *args, **options):
        """Execute the test command"""
        user_id = str(options['user_id'])
        queries = options['queries']
        insert_test_data = options['insert_test_data']
        k = options.get('k', 5)
        
        # Verify user exists
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"Testing RAG for user: {user.username} (ID: {user.id})")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found"))
            return
        
        # Insert test data if requested
        if insert_test_data:
            self.stdout.write("\n" + "="*50)
            self.stdout.write("📝 INSERTING TEST DATA")
            self.stdout.write("="*50)
            
            try:
                from apps.agents.rag.utils import insert_item
                import time
                
                test_content = [
                    {
                        "content_id": f"tiktok_{user_id}_1",
                        "content_url": f"https://www.tiktok.com/@{user_id}/video/1",
                        "platform": "tiktok",
                        "summary": "A fun video about cooking Vietnamese pho with traditional ingredients and modern techniques. Shows step-by-step process.",
                        "timestamp": int(time.time() - 86400)  # 1 day ago
                    },
                    {
                        "content_id": f"tiktok_{user_id}_2",
                        "content_url": f"https://www.tiktok.com/@{user_id}/video/2",
                        "platform": "tiktok", 
                        "summary": "Technology review of the latest smartphone features including camera quality and battery life.",
                        "timestamp": int(time.time() - 172800)  # 2 days ago
                    },
                    {
                        "content_id": f"facebook_{user_id}_1",
                        "content_url": f"https://www.facebook.com/{user_id}/posts/1",
                        "platform": "facebook",
                        "summary": "Travel blog post about visiting Da Nang, Vietnam with beautiful beach photos and restaurant recommendations.",
                        "timestamp": int(time.time() - 259200)  # 3 days ago
                    },
                    {
                        "content_id": f"facebook_{user_id}_2",
                        "content_url": f"https://www.facebook.com/{user_id}/posts/2",
                        "platform": "facebook",
                        "summary": "Discussion about work-life balance in tech industry with personal experiences and tips for remote work.",
                        "timestamp": int(time.time() - 604800)  # 1 week ago
                    },
                    {
                        "content_id": f"tiktok_{user_id}_3",
                        "content_url": f"https://www.tiktok.com/@{user_id}/video/3",
                        "platform": "tiktok",
                        "summary": "Educational content about machine learning basics and artificial intelligence applications in everyday life.",
                        "timestamp": int(time.time() - 1209600)  # 2 weeks ago
                    }
                ]
                
                for content in test_content:
                    result = insert_item(
                        content_id=content["content_id"],
                        content_url=content["content_url"],
                        user_id=user_id,
                        platform=content["platform"],
                        summary=content["summary"],
                        timestamp=content["timestamp"]
                    )
                    self.stdout.write(f"✅ Inserted {content['platform']} content: {content['content_id']}")
                
                self.stdout.write(self.style.SUCCESS(f"✅ Inserted {len(test_content)} test items"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to insert test data: {e}"))
                return
        
        # Test RAG queries
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🔍 TESTING RAG QUERIES")
        self.stdout.write("="*50)
        
        for i, query in enumerate(queries, 1):
            self.stdout.write(f"\n📝 Query {i}/{len(queries)}: {query}")
            self.stdout.write("-" * 60)
            
            try:
                # Call the RAG function with the correct signature
                result = retrieve_and_answer.invoke({
                    "query": query, 
                    "user_id": user_id, 
                    "k": k
                })
                
                self.stdout.write("🤖 Response:")
                self.stdout.write(result)
                self.stdout.write(self.style.SUCCESS("✅ Query completed successfully"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Query failed: {e}"))
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 TEST SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"✅ RAG testing completed for user {user_id}")
        self.stdout.write(f"📝 Tested {len(queries)} queries")
        if insert_test_data:
            self.stdout.write("📦 Test data was inserted")
        self.stdout.write("\n💡 Tips:")
        self.stdout.write("  • Try different query phrasings")
        self.stdout.write("  • Use platform filters (TikTok, Facebook)")
        self.stdout.write("  • Ask about recent content or specific topics")
        self.stdout.write("  • The system works with Vietnamese content via vietnamese-sbert model")