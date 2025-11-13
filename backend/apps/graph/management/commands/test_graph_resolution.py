"""
Management command to test the graph resolution system.
"""
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from langchain_openai import ChatOpenAI
from apps.agents.kg_constructor.video_summarization_processor import VideoSummarizationProcessor


class Command(BaseCommand):
    help = 'Test the graph resolution system with sample data'

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
            f'Testing graph resolution system (resolution: {"enabled" if enable_resolution else "disabled"})'
        ))
        
        try:
            # Initialize processor with or without resolution
            processor = VideoSummarizationProcessor(enable_resolution=enable_resolution)
            
            if clear_db:
                self.stdout.write('Clearing database...')
                processor.neo4j_client.clear_database()
                processor.neo4j_client.create_indexes()
            
            # # Sample video 1 - Uses "AI" terminology
            # video1_payload = {
            #     "user": {
            #         "user_id": "user_123",
            #         "name": "Alice Johnson",
            #         "email": "alice@example.com"
            #     },
            #     "video": {
            #         "video_id": "video_ai_1",
            #         "title": "Introduction to AI",
            #         "description": "Basic concepts of AI and machine learning",
            #         "duration": 1800,
            #         "upload_date": "2025-01-15T10:00:00Z",
            #         "url": "https://example.com/video/ai_1"
            #     },
            #     "topic": {
            #         "name": "Artificial Intelligence",
            #         "description": "AI fundamentals and applications",
            #         "category": "Technology"
            #     },
            #     "source": {
            #         "name": "TechEd Platform",
            #         "type": "Educational Platform",
            #         "url": "https://teched.example.com",
            #         "description": "Technology education platform"
            #     },
            #     "summarization": """
            #     This video introduces AI (Artificial Intelligence) and its applications. 
            #     AI is transforming industries through machine learning and deep learning.
            #     Google is a leading company in AI research, developing tools like TensorFlow.
            #     AI systems can process natural language and understand human speech.
            #     Machine learning algorithms learn from data to make predictions.
            #     Neural networks are a key component of modern AI systems.
            #     """
            # }
            
            # Sample video 2 - Uses "Artificial Intelligence" terminology
            # video2_payload = {
            #     "user": {
            #         "user_id": "user_456", 
            #         "name": "Bob Smith",
            #         "email": "bob@example.com"
            #     },
            #     "video": {
            #         "video_id": "video_ml_2",
            #         "title": "Advanced Machine Learning",
            #         "description": "Deep dive into ML algorithms",
            #         "duration": 2400,
            #         "upload_date": "2025-01-16T14:00:00Z",
            #         "url": "https://example.com/video/ml_2"
            #     },
            #     "topic": {
            #         "name": "Machine Learning",
            #         "description": "Advanced ML techniques and algorithms",
            #         "category": "Technology"
            #     },
            #     "source": {
            #         "name": "ML Academy",
            #         "type": "Online Course",
            #         "url": "https://mlacademy.example.com",
            #         "description": "Machine learning education platform"
            #     },
            #     "summarization": """
            #     Advanced machine learning covers deep learning and neural networks.
            #     Artificial Intelligence encompasses various ML techniques and algorithms.
            #     Google Inc. has developed sophisticated AI frameworks and tools.
            #     Deep learning uses neural networks with multiple layers for pattern recognition.
            #     Natural Language Processing enables machines to understand human language.
            #     ML models require large datasets for training and validation.
            #     TensorFlow is a popular framework for building machine learning models.
            #     """
            # }

            video2_payload = {
                "user": {
                    "user_id": "demo_user_001",
                    "name": "Demo User",
                    "email": "demo@example.com"
                },
                "video": {
                    "video_id": "ai_tutorial_2024",
                    "title": "Artificial Intelligence Tutorial: From Basics to Advanced",
                    "description": "Comprehensive AI tutorial covering machine learning, neural networks, and practical applications",
                    "duration": 3600,
                    "upload_date": "2024-11-10T10:00:00Z",
                    "url": "https://example.com/videos/ai_tutorial_2024"
                },
                "topic": {
                    "name": "Artificial Intelligence",
                    "description": "Introduction to AI concepts and applications",
                    "category": "Technology"
                },
                "source": {
                    "name": "AI Academy",
                    "type": "Educational Platform",
                    "url": "https://aiacademy.example.com",
                    "description": "Premier online platform for AI education"
                },
                "summarization": "This comprehensive tutorial introduces Artificial Intelligence and its core concepts.\nThe video begins with Machine Learning fundamentals, explaining how algorithms can learn from data without explicit programming. Key algorithms discussed include Linear Regression for predictive modeling, Decision Trees for classification, and Neural Networks for complex pattern recognition.\n\nDeep Learning is covered as a subset of Machine Learning, focusing on neural networks with multiple layers. Popular frameworks like TensorFlow and PyTorch are demonstrated for building AI models. The instructor, Dr. Sarah Chen, shows practical examples using Python programming language.\n\nReal-world applications are explored, including Natural Language Processing for chatbots, Computer Vision for image recognition, and Autonomous Vehicles for self-driving cars. Companies like Google, Microsoft, and Tesla are mentioned as leaders in AI innovation.\n\nThe tutorial covers ethical considerations in AI, including bias detection and responsible AI development. Data Privacy and Algorithm Transparency are highlighted as crucial factors.\n\nTools and libraries demonstrated include Jupyter Notebooks for development, scikit-learn for traditional ML, and Keras for neural network development. The importance of Data Preprocessing and Feature Engineering is emphasized throughout.    "
            }
            
            # self.stdout.write('Processing first video (AI terminology)...')
            # result1 = processor.process_video_summarization(video1_payload)
            
            # if result1['status'] == 'success':
            #     self.stdout.write(self.style.SUCCESS(f'✓ Video 1 processed successfully'))
            #     self.stdout.write(f"  - Entities extracted: {result1['extracted_entities']}")
            #     self.stdout.write(f"  - Relations extracted: {result1['extracted_relations']}")
            #     if 'resolution_statistics' in result1:
            #         self.stdout.write(f"  - Entity resolutions: {result1['resolution_statistics'].get('entity_resolutions_count', 0)}")
            # else:
            #     self.stdout.write(self.style.ERROR(f'✗ Video 1 failed: {result1["error_message"]}'))
            #     return
            
            self.stdout.write('Processing second video (Artificial Intelligence terminology)...')
            result2 = processor.process_video_summarization(video2_payload)
            
            if result2['status'] == 'success':
                self.stdout.write(self.style.SUCCESS(f'✓ Video 2 processed successfully'))
                self.stdout.write(f"  - Entities extracted: {result2['extracted_entities']}")
                self.stdout.write(f"  - Relations extracted: {result2['extracted_relations']}")
                if 'resolution_statistics' in result2:
                    stats = result2['resolution_statistics']
                    self.stdout.write(f"  - Entity resolutions: {stats.get('entity_resolutions_count', 0)}")
                    self.stdout.write(f"  - Relationship duplicates: {stats.get('relationship_duplicates', 0)}")
                    self.stdout.write(f"  - Relationship conflicts: {stats.get('relationship_conflicts', 0)}")
                    
                    if 'entity_mappings' in stats and stats['entity_mappings']:
                        self.stdout.write('  - Entity mappings applied:')
                        for new_entity, existing_entity in stats['entity_mappings'].items():
                            self.stdout.write(f"    • {new_entity} → {existing_entity}")
            else:
                self.stdout.write(self.style.ERROR(f'✗ Video 2 failed: {result2["error_message"]}'))
                return
            
            # Get resolution statistics
            if enable_resolution:
                self.stdout.write('\nGetting resolution statistics...')
                resolution_stats = processor.neo4j_client.get_resolution_statistics()
                self.stdout.write(f"Total resolved entities: {resolution_stats.get('total_resolutions', 0)}")
                self.stdout.write(f"Total conflicts detected: {resolution_stats.get('total_conflicts', 0)}")
                self.stdout.write(f"Pending conflicts: {resolution_stats.get('pending_conflicts', 0)}")
                
                # Get conflict flags
                conflicts = processor.neo4j_client.get_conflict_flags()
                if conflicts:
                    self.stdout.write(f'\nConflicts needing review ({len(conflicts)}):')
                    for conflict in conflicts:
                        self.stdout.write(f"  - Video {conflict['video_id']}: {conflict['reason']}")
            
            # Get final graph statistics  
            graph_stats = processor.neo4j_client.get_graph_stats()
            self.stdout.write('\nFinal Graph Statistics:')
            self.stdout.write(f"  - Total nodes: {graph_stats['total_nodes']}")
            self.stdout.write(f"  - Total relationships: {graph_stats['total_relationships']}")
            self.stdout.write(f"  - Total entities: {graph_stats.get('total_entities', 'N/A')}")
            self.stdout.write(f"  - Total videos: {graph_stats.get('total_videos', 'N/A')}")
            
            processor.neo4j_client.close()
            
            self.stdout.write(self.style.SUCCESS('\n✓ Graph resolution test completed successfully!'))
            
            if enable_resolution:
                self.stdout.write(self.style.WARNING(
                    '\nNote: With resolution enabled, duplicate entities should be merged automatically.'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    '\nNote: With resolution disabled, duplicate entities will exist as separate nodes.'
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Test failed: {str(e)}'))
            raise e