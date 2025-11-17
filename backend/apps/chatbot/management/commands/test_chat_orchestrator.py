from django.core.management.base import BaseCommand
from django.conf import settings
import json

from apps.agents.chatbot.chat_orchestrator import create_chat_orchestrator


class Command(BaseCommand):
    help = 'Test the chat orchestrator system with sample conversations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Run in interactive mode for live chat testing',
        )
        parser.add_argument(
            '--user-id',
            type=str,
            default='test_user_123',
            help='User ID for testing (default: test_user_123)',
        )
        parser.add_argument(
            '--message',
            type=str,
            help='Single message to test (non-interactive mode)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing Chat Orchestrator System'))
        self.stdout.write('=' * 80)

        try:
            # Initialize orchestrator
            self.stdout.write('🔧 Initializing ChatOrchestrator...')
            orchestrator = create_chat_orchestrator()
            self.stdout.write(self.style.SUCCESS('✅ ChatOrchestrator initialized'))
            
            user_id = options['user_id']
            
            if options['interactive']:
                self._run_interactive_mode(orchestrator, user_id)
            elif options['message']:
                self._test_single_message(orchestrator, user_id, options['message'])
            else:
                self._run_predefined_tests(orchestrator, user_id)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Orchestrator test failed: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def _run_interactive_mode(self, orchestrator, user_id):
        """Run interactive chat session"""
        self.stdout.write('\n🎮 Interactive Chat Mode')
        self.stdout.write('Type your messages below. Type "quit" to exit.')
        self.stdout.write('=' * 50)
        
        session_id = None
        
        try:
            while True:
                user_input = input('\n🧑 You: ')
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_input.strip():
                    continue
                
                # Process message
                response = orchestrator.process_user_message(user_input, user_id, session_id)
                session_id = response.get('session_id')
                
                # Display response
                self._display_response(response)
                
        except KeyboardInterrupt:
            self.stdout.write('\n\n👋 Chat session ended by user')
        except Exception as e:
            self.stdout.write(f'\n❌ Interactive session error: {e}')

    def _test_single_message(self, orchestrator, user_id, message):
        """Test a single message"""
        self.stdout.write(f'\n📝 Testing Single Message')
        self.stdout.write('=' * 40)
        
        self.stdout.write(f'🧑 User: {message}')
        
        response = orchestrator.process_user_message(message, user_id)
        self._display_response(response)

    def _run_predefined_tests(self, orchestrator, user_id):
        """Run predefined test scenarios"""
        self.stdout.write('\n🧪 Running Predefined Test Scenarios')
        self.stdout.write('=' * 50)
        
        test_scenarios = [
            {
                'name': 'General Greeting',
                'messages': ['Hello! What can you do?']
            },
            {
                'name': 'Video Crawling Request (English)',
                'messages': [
                    'Find videos about #machinelearning #AI',
                    'Can you crawl videos with #technology hashtag?'
                ]
            },
            {
                'name': 'Knowledge Q&A (English)',
                'messages': [
                    'What do my saved videos say about neural networks?',
                    'Explain machine learning from my video collection'
                ]
            },
            {
                'name': 'Vietnamese Requests',
                'messages': [
                    'Xin chào! Bạn có thể làm gì?',
                    'Tìm video về #học_máy #trí_tuệ_nhân_tạo',
                    'Videos của tôi nói gì về mạng neural?'
                ]
            },
            {
                'name': 'Edge Cases',
                'messages': [
                    '',  # Empty message
                    'asdfghjkl',  # Random text
                    'What is the meaning of life?'  # Off-topic
                ]
            }
        ]
        
        for scenario in test_scenarios:
            self.stdout.write(f'\n🎯 Scenario: {scenario["name"]}')
            self.stdout.write('-' * 30)
            
            session_id = None
            
            for i, message in enumerate(scenario['messages']):
                display_message = message if message else '[EMPTY MESSAGE]'
                
                self.stdout.write(f'\n🧑 User: {display_message}')
                
                # Process original message (including empty ones)
                response = orchestrator.process_user_message(message, user_id, session_id)
                session_id = response.get('session_id')
                
                # Display response
                self._display_response(response, compact=True)

        # Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('✅ All test scenarios completed!'))
        self.stdout.write('\n💡 Next Steps:')
        self.stdout.write('1. Test the REST API endpoints:')
        self.stdout.write('   POST /api/chat/message/')
        self.stdout.write('   GET  /api/chat/capabilities/')
        self.stdout.write('2. Run interactive mode: --interactive')
        self.stdout.write('3. Implement actual video crawling and Q&A agents')

    def _display_response(self, response, compact=False):
        """Display formatted response"""
        if response.get('success'):
            intent = response.get('user_intent', 'unknown')
            task = response.get('task', 'unknown')
            confidence = response.get('confidence', 0.0)
            
            if compact:
                self.stdout.write(f'🤖 Assistant ({task}/{intent}, {confidence:.2f}):')
                # Truncate long messages in compact mode
                message = response['message']
                if len(message) > 200:
                    message = message[:200] + '...'
                self.stdout.write(f'   {message.replace(chr(10), " ")}')
            else:
                self.stdout.write(f'\n🤖 Assistant:')
                self.stdout.write(f'   Task: {task}')
                self.stdout.write(f'   Intent: {intent}')
                self.stdout.write(f'   Confidence: {confidence:.2f}')
                self.stdout.write(f'   Session: {response.get("session_id", "none")}')
                self.stdout.write('\n   Response:')
                for line in response['message'].split('\n'):
                    self.stdout.write(f'   {line}')
                
                # Show additional data if available
                if response.get('data') and not compact:
                    self.stdout.write(f'\n   Data: {json.dumps(response["data"], indent=2)}')
        else:
            self.stdout.write(self.style.ERROR(f'❌ Error: {response.get("message", "Unknown error")}'))
            if response.get('error'):
                self.stdout.write(f'   Details: {response["error"]}')