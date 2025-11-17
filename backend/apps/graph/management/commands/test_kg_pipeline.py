from django.core.management.base import BaseCommand
from django.conf import settings
import json

from apps.agents.kg_constructor.video_summarization_processor import VideoSummarizationProcessor, EXAMPLE_PAYLOAD
from apps.graph.models import KnowledgeGraphStatistics
from apps.agents.kg_constructor.config import get_google_llm

class Command(BaseCommand):
    help = 'Test the video summarization to Neo4j knowledge graph pipeline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-db',
            action='store_true',
            help='Clear the Neo4j database before testing (WARNING: deletes all data)',
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Only test the Neo4j connection without processing',
        )
        parser.add_argument(
            '--custom-payload',
            type=str,
            help='Path to JSON file with custom payload',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing Video Summarization to Neo4j Pipeline'))
        self.stdout.write('=' * 80)

        try:
            processor = VideoSummarizationProcessor()
            
            # Test connection first
            if not processor.neo4j_client.test_connection():
                self.stdout.write(self.style.ERROR('❌ Cannot connect to Neo4j database'))
                self.stdout.write('Make sure Neo4j is running and credentials are correct:')
                self.stdout.write(f'  URI: {processor.neo4j_client.uri}')
                self.stdout.write(f'  Username: {processor.neo4j_client.username}')
                return

            self.stdout.write(self.style.SUCCESS('✅ Neo4j connection successful'))
            
            if options['test_connection']:
                self.stdout.write('Connection test completed.')
                return

            # Clear database if requested
            if options['clear_db']:
                self.stdout.write(self.style.WARNING('⚠️  Clearing Neo4j database...'))
                processor.neo4j_client.clear_database()
                self.stdout.write(self.style.SUCCESS('✅ Database cleared'))

            # Load payload
            if options['custom_payload']:
                try:
                    with open(options['custom_payload'], 'r') as f:
                        payload = json.load(f)
                    self.stdout.write(f"📄 Using custom payload from {options['custom_payload']}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Failed to load custom payload: {e}"))
                    return
            else:
                payload = EXAMPLE_PAYLOAD
                self.stdout.write("📄 Using example payload")

            # Display payload info
            self.stdout.write('\n📋 Payload Information:')
            self.stdout.write(f"  User ID: {payload['user']['user_id']}")
            self.stdout.write(f"  Video ID: {payload['video']['video_id']}")
            self.stdout.write(f"  Topic: {payload['topic']['name']}")
            self.stdout.write(f"  Source: {payload['source']['name']}")
            self.stdout.write(f"  Summarization length: {len(payload['summarization'])} chars")

            # Process the payload
            self.stdout.write('\n🔄 Processing video summarization...')
            result = processor.process_video_summarization(payload)

            # Display results
            self.stdout.write('\n📊 Processing Results:')
            self.stdout.write('=' * 50)
            
            if result['status'] == 'success':
                self.stdout.write(self.style.SUCCESS(f"✅ Status: {result['status']}"))
                self.stdout.write(f"⏱️  Processing time: {result.get('processing_time_seconds', 0):.2f} seconds")
                self.stdout.write(f"🔍 Extracted entities: {result.get('extracted_entities', 'N/A')}")
                self.stdout.write(f"🔗 Extracted relations: {result.get('extracted_relations', 'N/A')}")
                self.stdout.write(f"💾 Upserted entities: {result.get('upserted_entities', 'N/A')}")
                
                # Display node IDs
                if result.get('node_ids'):
                    self.stdout.write('\n🆔 Created/Updated Node IDs:')
                    for node_type, node_id in result['node_ids'].items():
                        self.stdout.write(f"  {node_type.capitalize()}: {node_id}")
                
                # Display graph statistics
                if result.get('graph_statistics'):
                    stats = result['graph_statistics']
                    self.stdout.write('\n📈 Graph Statistics:')
                    self.stdout.write(f"  Total nodes: {stats.get('total_nodes', 0)}")
                    self.stdout.write(f"  Total relationships: {stats.get('total_relationships', 0)}")
                    self.stdout.write(f"  Users: {stats.get('users', 0)}")
                    self.stdout.write(f"  Videos: {stats.get('videos', 0)}")
                    self.stdout.write(f"  Topics: {stats.get('topics', 0)}")
                    self.stdout.write(f"  Sources: {stats.get('sources', 0)}")
                    self.stdout.write(f"  Entities: {stats.get('entities', 0)}")
                    
                    # Create statistics record
                    KnowledgeGraphStatistics.create_from_neo4j_stats(stats)
                    self.stdout.write('📝 Statistics saved to Django database')

                # Display KG validation
                if result.get('kg_validation'):
                    validation = result['kg_validation']
                    self.stdout.write('\n🔍 Knowledge Graph Validation:')
                    self.stdout.write(f"  Nodes in KG: {validation.get('num_nodes', 0)}")
                    self.stdout.write(f"  Edges in KG: {validation.get('num_edges', 0)}")
                    self.stdout.write(f"  Is connected: {validation.get('is_connected', False)}")
                    self.stdout.write(f"  Has cycles: {validation.get('has_cycles', False)}")
                    self.stdout.write(f"  Density: {validation.get('density', 0):.3f}")
                    isolated = validation.get('isolated_nodes', [])
                    self.stdout.write(f"  Isolated nodes: {len(isolated)}")
                
            else:
                self.stdout.write(self.style.ERROR(f"❌ Status: {result.get('status', 'unknown')}"))
                self.stdout.write(self.style.ERROR(f"Error: {result.get('error_message', 'Unknown error')}"))
                self.stdout.write(f"⏱️  Processing time: {result.get('processing_time_seconds', 0):.2f} seconds")

            # Test search functionality
            self.stdout.write('\n🔎 Testing entity search...')
            try:
                search_results = processor.neo4j_client.search_entities("Machine Learning", limit=5)
                self.stdout.write(f"Found {len(search_results)} entities matching 'Machine Learning':")
                for entity in search_results:
                    self.stdout.write(f"  - {entity['name']} ({entity['type']})")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Search test failed: {e}"))

            # Test video knowledge graph retrieval
            self.stdout.write('\n📺 Testing video knowledge graph retrieval...')
            try:
                video_id = payload['video']['video_id']
                video_graph = processor.neo4j_client.get_video_knowledge_graph(video_id)
                self.stdout.write(f"Video KG for {video_id}:")
                self.stdout.write(f"  Nodes: {len(video_graph['nodes'])}")
                self.stdout.write(f"  Relationships: {len(video_graph['relationships'])}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Video KG test failed: {e}"))

            processor.neo4j_client.close()
            
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('✅ Pipeline test completed successfully!'))
            
            # Provide next steps
            self.stdout.write('\n💡 Next Steps:')
            self.stdout.write('1. Test the REST API endpoints:')
            self.stdout.write('   POST /api/graph/process-video-summarization/')
            self.stdout.write('   GET  /api/graph/statistics/')
            self.stdout.write('   GET  /api/graph/search/?q=machine+learning')
            self.stdout.write('2. Check the Django admin for VideoSummarizationRequest records')
            self.stdout.write('3. Explore the Neo4j browser at http://localhost:7474')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Unexpected error: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())