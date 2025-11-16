from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import json
import os
from pathlib import Path

from apps.agents.video_pipeline import UnifiedVideoProcessor, EXAMPLE_VIDEO_PAYLOAD
from apps.graph.models import KnowledgeGraphStatistics
from apps.agents.kg_constructor.config import get_openai_llm


class Command(BaseCommand):
    help = 'Test the unified video processing pipeline (video analysis + knowledge graph construction)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--video-path',
            type=str,
            help='Path to video file to process',
        )
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
            '--use-whisper',
            action='store_true',
            help='Use OpenAI Whisper for audio transcription (requires video file)',
        )
        parser.add_argument(
            '--use-gemini',
            action='store_true',
            help='Use Gemini for video understanding (requires video file)',
        )
        parser.add_argument(
            '--custom-payload',
            type=str,
            help='Path to JSON file with custom payload (excluding video_file)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing Unified Video Processing Pipeline'))
        self.stdout.write('=' * 80)

        try:
            # Initialize processor with options
            use_gemini = options.get('use_gemini', True)
            use_whisper = options.get('use_whisper', True)

            processor = UnifiedVideoProcessor(
                use_gemini_for_video=use_gemini,
                use_whisper_for_audio=use_whisper,
                enable_kg_resolution=True,
                llm=get_openai_llm(model="gpt-4o-mini")
            )

            self.stdout.write(f'🔧 Processor Configuration:')
            self.stdout.write(f'  Gemini Video Analysis: {use_gemini}')
            self.stdout.write(f'  Whisper Audio Analysis: {use_whisper}')
            self.stdout.write(f'  KG Resolution: True')

            # Test Neo4j connection first
            if not processor.kg_processor.neo4j_client.test_connection():
                self.stdout.write(self.style.ERROR('❌ Cannot connect to Neo4j database'))
                self.stdout.write('Make sure Neo4j is running and credentials are correct:')
                self.stdout.write(f'  URI: {processor.kg_processor.neo4j_client.uri}')
                self.stdout.write(f'  Username: {processor.kg_processor.neo4j_client.username}')
                return

            self.stdout.write(self.style.SUCCESS('✅ Neo4j connection successful'))

            if options['test_connection']:
                self.stdout.write('Connection test completed.')
                return

            # Clear database if requested
            if options['clear_db']:
                self.stdout.write(self.style.WARNING('⚠️  Clearing Neo4j database...'))
                processor.kg_processor.neo4j_client.clear_database()
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
                payload = EXAMPLE_VIDEO_PAYLOAD.copy()
                self.stdout.write("📄 Using example payload")

            # Handle video file
            video_file = None
            video_path = options.get('video_path')

            if video_path:
                # Use provided video file
                if not os.path.exists(video_path):
                    self.stdout.write(self.style.ERROR(f"❌ Video file not found: {video_path}"))
                    return

                with open(video_path, 'rb') as f:
                    video_content = f.read()

                video_file = SimpleUploadedFile(
                    name=os.path.basename(video_path),
                    content=video_content,
                    content_type='video/mp4'
                )
                self.stdout.write(f"📹 Using video file: {video_path}")
            else:
                # Simulate mode without actual video processing
                self.stdout.write(self.style.WARNING('⚠️  No video file provided - simulation mode'))
                self.stdout.write('Use --video-path /path/to/video.mp4 to test with actual video')

                # Create mock analysis result for testing KG pipeline
                mock_analysis = {
                    'transcript': 'This is a mock transcript for testing purposes.',
                    'summary': 'This video discusses machine learning concepts including neural networks, data processing, and model training. It covers fundamental algorithms and their applications in real-world scenarios.',
                    'detected_language': 'en',
                    'analysis_method': 'mock_simulation',
                    'processing_time_seconds': 0.1,
                    'error': None
                }

                # Create KG payload directly
                payload['video']['video_id'] = 'mock_video_123'
                kg_payload = processor.create_kg_payload_from_analysis(payload, mock_analysis)

                self.stdout.write('\n🔄 Processing mock data through KG pipeline...')
                result = processor.kg_processor.process_video_summarization(kg_payload)

                # Display KG results
                self._display_kg_results(result, mock_analysis)
                return

            # Add video file to payload
            payload['video_file'] = video_file

            # Display payload info
            self.stdout.write('\n📋 Payload Information:')
            self.stdout.write(f"  User ID: {payload['user']['user_id']}")
            self.stdout.write(f"  Video File: {video_file.name if video_file else 'None'}")
            self.stdout.write(f"  Topic: {payload['topic']['name']}")
            self.stdout.write(f"  Source: {payload['source']['name']}")

            if video_file:
                self.stdout.write(f"  Video Size: {video_file.size / (1024*1024):.1f} MB")

            # Process through unified pipeline
            self.stdout.write('\n🔄 Processing video through unified pipeline...')
            result = processor.process_video_to_knowledge_graph(payload)

            # Display results
            self._display_unified_results(result)

            # Test additional functionality
            if result['status'] == 'success':
                self._test_additional_features(processor, result)

            processor.kg_processor.neo4j_client.close()

            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('✅ Unified pipeline test completed!'))

            # Provide next steps
            self._show_next_steps()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Unexpected error: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def _display_unified_results(self, result):
        """Display unified pipeline results."""
        self.stdout.write('\n📊 Unified Pipeline Results:')
        self.stdout.write('=' * 60)

        if result['status'] == 'success':
            self.stdout.write(self.style.SUCCESS(f"✅ Status: {result['status']}"))
            self.stdout.write(f"🔄 Pipeline Type: {result['pipeline_type']}")
            self.stdout.write(f"⏱️  Total Processing Time: {result['total_processing_time_seconds']:.2f} secondss")

            # Video analysis results
            if 'video_analysis' in result:
                va = result['video_analysis']
                self.stdout.write('\n🎬 Video Analysis Stage:')
                self.stdout.write(f"  Method: {va.get('analysis_method', 'N/A')}")
                self.stdout.write(f"  Language: {va.get('detected_language', 'N/A')}")
                self.stdout.write(f"  Has Transcript: {va.get('has_transcript', False)}")
                self.stdout.write(f"  Summary Length: {va.get('summary_length', 0)} chars")
                self.stdout.write(f"  Transcript Length: {va.get('transcript_length', 0)} chars")
                self.stdout.write(f"  Processing Time: {va.get('processing_time_seconds', 0):.2f} seconds")     

            # Knowledge graph results
            if 'knowledge_graph' in result:
                self._display_kg_results(result['knowledge_graph'], None, indent='  ')

            self.stdout.write('\n🆔 Final Results:')
            self.stdout.write(f"  Video ID: {result.get('video_id', 'N/A')}")
            self.stdout.write(f"  User ID: {result.get('user_id', 'N/A')}")

        else:
            self.stdout.write(self.style.ERROR(f"❌ Status: {result['status']}"))
            self.stdout.write(self.style.ERROR(f"Stage: {result.get('stage', 'Unknown')}"))
            self.stdout.write(self.style.ERROR(f"Error: {result.get('error_message', 'Unknown error')}"))       
            self.stdout.write(f"⏱️  Processing Time: {result.get('total_processing_time_seconds', 0):.2f} secondds")

    def _display_kg_results(self, kg_result, analysis_result=None, indent=''):
        """Display knowledge graph results."""
        self.stdout.write(f'\n{indent}🧠 Knowledge Graph Stage:')

        if kg_result.get('status') == 'success':
            self.stdout.write(f"{indent}  Status: ✅ {kg_result['status']}")
            self.stdout.write(f"{indent}  Processing Type: {kg_result.get('processing_type', 'N/A')}")
            self.stdout.write(f"{indent}  Processing Time: {kg_result.get('processing_time_seconds', 0):.2f} seconds")
            self.stdout.write(f"{indent}  Extracted Entities: {kg_result.get('extracted_entities', 0)}")        
            self.stdout.write(f"{indent}  Extracted Relations: {kg_result.get('extracted_relations', 0)}")      
            self.stdout.write(f"{indent}  Upserted Entities: {kg_result.get('upserted_entities', 0)}")
            self.stdout.write(f"{indent}  Resolution Enabled: {kg_result.get('resolution_enabled', False)}")    

            # Display node IDs
            if kg_result.get('node_ids'):
                self.stdout.write(f'\n{indent}🆔 Created/Updated Node IDs:')
                for node_type, node_id in kg_result['node_ids'].items():
                    self.stdout.write(f"{indent}  {node_type.capitalize()}: {node_id}")

            # Display graph statistics
            if kg_result.get('graph_statistics'):
                stats = kg_result['graph_statistics']
                self.stdout.write(f'\n{indent}📈 Graph Statistics:')
                self.stdout.write(f"{indent}  Total nodes: {stats.get('total_nodes', 0)}")
                self.stdout.write(f"{indent}  Total relationships: {stats.get('total_relationships', 0)}")      
                self.stdout.write(f"{indent}  Users: {stats.get('users', 0)}")
                self.stdout.write(f"{indent}  Videos: {stats.get('videos', 0)}")
                self.stdout.write(f"{indent}  Topics: {stats.get('topics', 0)}")
                self.stdout.write(f"{indent}  Sources: {stats.get('sources', 0)}")
                self.stdout.write(f"{indent}  Entities: {stats.get('entities', 0)}")
        else:
            self.stdout.write(self.style.ERROR(f"{indent}  Status: ❌ {kg_result.get('status', 'error')}"))     
            self.stdout.write(self.style.ERROR(f"{indent}  Error: {kg_result.get('error_message', 'Unknown error')}"))

    def _test_additional_features(self, processor, result):
        """Test additional pipeline features."""
        self.stdout.write('\n🔧 Testing Additional Features:')

        try:
            # Test entity search
            search_results = processor.kg_processor.neo4j_client.search_entities("learning", limit=3)
            self.stdout.write(f"  🔍 Entity Search ('learning'): {len(search_results)} results")

            # Test video knowledge graph retrieval
            if 'video_id' in result:
                video_graph = processor.kg_processor.neo4j_client.get_video_knowledge_graph(result['video_id']) 
                self.stdout.write(f"  📺 Video KG: {len(video_graph['nodes'])} nodes, {len(video_graph['relationships'])} relationships")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Additional tests failed: {e}"))

    def _show_next_steps(self):
        """Show next steps for the user."""
        self.stdout.write('\n💡 Next Steps:')
        self.stdout.write('1. Test with your own video files:')
        self.stdout.write('   python manage.py test_unified_pipeline --video-path /path/to/video.mp4')
        self.stdout.write('2. Configure analysis methods:')
        self.stdout.write('   --use-gemini (visual+audio) or --use-whisper (audio only)')
        self.stdout.write('3. Test the REST API endpoints:')
        self.stdout.write('   POST /api/video/process-video/')  # This would need to be created
        self.stdout.write('   GET  /api/graph/search/?q=machine+learning')
        self.stdout.write('4. Explore the Neo4j browser at http://localhost:7474')