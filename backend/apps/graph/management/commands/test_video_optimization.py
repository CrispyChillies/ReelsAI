"""
Management command to test video processing optimization cases.
"""
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.agents.kg_constructor.text_processor import TextProcessor


class Command(BaseCommand):
    help = 'Test video processing optimization for duplicate detection and performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--enable-resolution',
            action='store_true',
            help='Enable LLM-based graph resolution',
        )
        parser.add_argument(
            '--clear-db',
            action='store_true',
            help='Clear the database before testing',
        )

    def handle(self, *args, **options):
        enable_resolution = options['enable_resolution']
        clear_db = options['clear_db']
        
        self.stdout.write(self.style.SUCCESS(
            f'Testing video processing optimization (resolution: {"enabled" if enable_resolution else "disabled"})'
        ))
        
        try:
            # Initialize processor with or without resolution
            processor = TextProcessor(enable_resolution=enable_resolution)
            
            if clear_db:
                self.stdout.write('Clearing database...')
                processor.neo4j_client.clear_database()
                processor.neo4j_client.create_indexes()
            
            # Sample payload for testing
            test_payload = {
                "user": {
                    "user_id": "user_alice",
                    "name": "Alice Johnson",
                    "email": "alice@example.com"
                },
                "video": {
                    "video_id": "video_test_123",
                    "title": "Test Video",
                    "description": "A test video for optimization",
                    "duration": 120,
                    "upload_date": "2025-01-15T10:00:00Z",
                    "url": "https://example.com/video/test_123"
                },
                "topic": {
                    "name": "Technology",
                    "description": "Technology-related content",
                    "category": "Education"
                },
                "source": {
                    "name": "TestChannel",
                    "type": "Educational Channel",
                    "url": "https://testchannel.example.com",
                    "description": "Educational content creator"
                },
                "summarization": """
                This test video discusses basic programming concepts including variables,
                functions, and data structures. Python is used as the primary language.
                The video covers loops, conditionals, and object-oriented programming.
                """
            }
            
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS("🧪 TESTING VIDEO PROCESSING OPTIMIZATION"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            
            # Test Case 1: First time processing (new video)
            self.stdout.write("\n📹 Case 1: Processing completely new video...")
            result1 = processor.process_video_summarization(test_payload)
            self.stdout.write(f"Status: {result1['status']}")
            self.stdout.write(f"Processing Type: {result1.get('processing_type', 'N/A')}")
            self.stdout.write(f"Processing Time: {result1['processing_time_seconds']:.2f}s")
            if 'extracted_entities' in result1:
                self.stdout.write(f"Extracted Entities: {result1['extracted_entities']}")
            
            if result1['status'] != 'success':
                self.stdout.write(self.style.ERROR(f"✗ Case 1 failed: {result1.get('error_message', 'Unknown error')}"))
                return
            
            # Test Case 2: Same user, same video (should skip)
            self.stdout.write("\n🔄 Case 2: Same user saving the same video again...")
            result2 = processor.process_video_summarization(test_payload)
            self.stdout.write(f"Status: {result2['status']}")
            self.stdout.write(f"Processing Type: {result2.get('processing_type', 'N/A')}")
            self.stdout.write(f"Message: {result2.get('message', 'N/A')}")
            self.stdout.write(f"Processing Time: {result2['processing_time_seconds']:.2f}s")
            
            # Test Case 3: Different user, same video (should only create relationship)
            self.stdout.write("\n👤 Case 3: Different user saving existing video...")
            test_payload_user2 = test_payload.copy()
            test_payload_user2['user'] = {
                "user_id": "user_bob",
                "name": "Bob Smith", 
                "email": "bob@example.com"
            }
            
            result3 = processor.process_video_summarization(test_payload_user2)
            self.stdout.write(f"Status: {result3['status']}")
            self.stdout.write(f"Processing Type: {result3.get('processing_type', 'N/A')}")
            self.stdout.write(f"Message: {result3.get('message', 'N/A')}")
            self.stdout.write(f"Processing Time: {result3['processing_time_seconds']:.2f}s")
            if 'entities_count' in result3:
                self.stdout.write(f"Existing Entities Found: {result3['entities_count']}")
            
            # Test Case 4: Bob tries to save the same video again (should skip)
            self.stdout.write("\n🔄 Case 4: Bob saving the same video again...")
            result4 = processor.process_video_summarization(test_payload_user2)
            self.stdout.write(f"Status: {result4['status']}")
            self.stdout.write(f"Processing Type: {result4.get('processing_type', 'N/A')}")
            self.stdout.write(f"Message: {result4.get('message', 'N/A')}")
            self.stdout.write(f"Processing Time: {result4['processing_time_seconds']:.2f}s")
            
            # Summary
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("📊 PERFORMANCE SUMMARY"))
            self.stdout.write("=" * 60)
            self.stdout.write(f"New Video Processing:      {result1['processing_time_seconds']:.2f}s")
            self.stdout.write(f"Same User Duplicate:       {result2['processing_time_seconds']:.2f}s")
            self.stdout.write(f"Different User Existing:   {result3['processing_time_seconds']:.2f}s")
            self.stdout.write(f"Same User Duplicate Again: {result4['processing_time_seconds']:.2f}s")
            
            # Calculate efficiency gains
            new_video_time = result1['processing_time_seconds']
            duplicate_time = result2['processing_time_seconds'] 
            existing_video_time = result3['processing_time_seconds']
            
            self.stdout.write(f"\n⚡ EFFICIENCY GAINS:")
            if duplicate_time > 0:
                self.stdout.write(f"Duplicate Detection Speedup: {new_video_time/duplicate_time:.1f}x faster")
            if existing_video_time > 0:
                self.stdout.write(f"Existing Video Speedup:      {new_video_time/existing_video_time:.1f}x faster")
            
            # Get final graph statistics  
            graph_stats = processor.neo4j_client.get_graph_stats()
            self.stdout.write('\nFinal Graph Statistics:')
            self.stdout.write(f"  - Total nodes: {graph_stats['total_nodes']}")
            self.stdout.write(f"  - Total relationships: {graph_stats['total_relationships']}")
            self.stdout.write(f"  - Total entities: {graph_stats.get('entities', 'N/A')}")
            self.stdout.write(f"  - Total videos: {graph_stats.get('videos', 'N/A')}")
            self.stdout.write(f"  - Total users: {graph_stats.get('users', 'N/A')}")
            
            # Close connections
            processor.neo4j_client.close()
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Video optimization test completed successfully!"))
            
            # Recommendations
            self.stdout.write(self.style.WARNING(f"\n💡 OPTIMIZATION RESULTS:"))
            if duplicate_time > 0 and new_video_time/duplicate_time > 50:
                self.stdout.write(self.style.SUCCESS(f"✅ Duplicate detection is highly optimized ({new_video_time/duplicate_time:.0f}x faster)"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Duplicate detection could be more optimized"))
            
            if existing_video_time > 0 and new_video_time/existing_video_time > 5:
                self.stdout.write(self.style.SUCCESS(f"✅ Existing video handling is well optimized ({new_video_time/existing_video_time:.0f}x faster)"))
            else:
                self.stdout.write(self.style.WARNING(f"⚠️  Existing video handling could be more optimized"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Test failed: {str(e)}'))
            raise e