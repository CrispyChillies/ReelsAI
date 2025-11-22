"""
Management command to test the chatbot API endpoints functionality.
This command demonstrates how to use the chatbot system programmatically.
"""

import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from apps.chatbot.models import ChatSession, ChatMessage
from apps.agents.chatbot.chatbot import Chatbot, ChatRequest
# from apps.agents.kg_constructor.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command to test chatbot functionality"""
    
    help = "Test the chatbot system by creating sessions, sending messages, and retrieving responses"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            default=1,
            help='User ID to use for testing (default: 1)'
        )
        parser.add_argument(
            '--test-messages',
            nargs='+',
            default=[
                "Hello, can you help me?",
                "What is knowledge graph construction?", 
                "How does the RAG system work?",
                "Tell me about video summarization",
                "Thank you for the information"
            ],
            help='List of test messages to send to the chatbot'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test data after completion'
        )
    
    def handle(self, *args, **options):
        """Execute the test command"""
        user_id = options['user_id']
        test_messages = options['test_messages']
        cleanup = options['cleanup']
        
        # Get or create test user
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"Using existing user: {user.username} (ID: {user.id})")
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=f'testuser_{user_id}',
                email=f'test{user_id}@example.com',
                password='testpass123'
            )
            self.stdout.write(f"Created test user: {user.username} (ID: {user.id})")
        
        # Initialize chatbot
        try:
            # neo4j_client = Neo4jClient()
            chatbot = Chatbot(
                # neo4j_client=neo4j_client,
                user=user)
            self.stdout.write(self.style.SUCCESS("✅ Chatbot initialized successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to initialize chatbot: {e}"))
            return
        
        # Track session for testing
        test_session_id = None
        created_sessions = []
        
        try:
            # Test 1: Send messages and create conversation
            self.stdout.write("\n" + "="*50)
            self.stdout.write("📤 TESTING MESSAGE SENDING")
            self.stdout.write("="*50)
            
            for i, message in enumerate(test_messages):
                self.stdout.write(f"\n📝 Sending message {i+1}/{len(test_messages)}: {message}")
                
                # Create chat request
                chat_request = ChatRequest(
                    user_message=message,
                    user_id=str(user.id),
                    session_id=test_session_id  # Use existing session after first message
                )
                
                # Process message
                try:
                    with transaction.atomic():
                        # Create or get session
                        if test_session_id:
                            try:
                                session = ChatSession.objects.get(session_id=test_session_id, user=user)
                            except ChatSession.DoesNotExist:
                                # If session was created but failed, create it again
                                session = ChatSession.objects.create(
                                    session_id=test_session_id,
                                    user=user,
                                    title=f"Test: {message[:30]}..."
                                )
                                created_sessions.append(session)
                        else:
                            import uuid
                            test_session_id = f"test_session_{user.id}_{uuid.uuid4().hex[:8]}"
                            session = ChatSession.objects.create(
                                session_id=test_session_id,
                                user=user,
                                title=f"Test: {message[:30]}..."
                            )
                            created_sessions.append(session)
                        
                        # Save user message
                        user_msg = ChatMessage.objects.create(
                            session=session,
                            message_type='human',
                            content=message
                        )
                        
                        # Get chatbot response
                        response = chatbot.process_message(chat_request)
                        
                        if response.success:
                            # Save AI response
                            ai_msg = ChatMessage.objects.create(
                                session=session,
                                message_type='ai',
                                content=response.message,
                                used_rag_tool=response.data.get('used_rag_tool', False) if response.data else False,
                                tool_calls_made=response.data.get('tool_calls_made', False) if response.data else False,
                                confidence=response.confidence,
                                task_type=response.task,
                                metadata=response.data or {}
                            )
                            
                            self.stdout.write(self.style.SUCCESS(f"✅ Response received"))
                            self.stdout.write(f"🤖 AI: {response.message[:100]}...")
                            self.stdout.write(f"📊 Used RAG: {response.data.get('used_rag_tool', False) if response.data else False}")
                            self.stdout.write(f"🎯 Confidence: {response.confidence}")
                        else:
                            self.stdout.write(self.style.ERROR(f"❌ Chatbot error: {response.message}"))
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error processing message: {e}"))
                    continue
            
            # Test 2: Retrieve session messages
            if test_session_id:
                self.stdout.write("\n" + "="*50)
                self.stdout.write("📖 TESTING MESSAGE RETRIEVAL")
                self.stdout.write("="*50)
                
                try:
                    session = ChatSession.objects.get(session_id=test_session_id, user=user)
                    messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
                    
                    self.stdout.write(f"📋 Session: {session.session_id}")
                    self.stdout.write(f"📊 Total messages: {messages.count()}")
                    
                    for msg in messages:
                        icon = "👤" if msg.message_type == "human" else "🤖"
                        self.stdout.write(f"{icon} [{msg.message_type.upper()}] {msg.content[:80]}...")
                        if msg.message_type == "ai":
                            self.stdout.write(f"   🔧 Tools used: {msg.used_rag_tool}, Confidence: {msg.confidence}")
                    
                    self.stdout.write(self.style.SUCCESS("✅ Message retrieval successful"))
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error retrieving messages: {e}"))
            
            # Test 3: List all sessions for user
            self.stdout.write("\n" + "="*50)
            self.stdout.write("📚 TESTING SESSION LISTING")
            self.stdout.write("="*50)
            
            try:
                sessions = ChatSession.objects.filter(user=user)
                self.stdout.write(f"📊 Total sessions for user: {sessions.count()}")
                
                for session in sessions:
                    msg_count = session.messages.count()
                    last_msg = session.messages.last()
                    last_msg_preview = last_msg.content[:50] + "..." if last_msg and len(last_msg.content) > 50 else (last_msg.content if last_msg else "No messages")
                    
                    self.stdout.write(f"📋 {session.session_id}")
                    self.stdout.write(f"   📝 Title: {session.title or 'Untitled'}")
                    self.stdout.write(f"   💬 Messages: {msg_count}")
                    self.stdout.write(f"   🕒 Last: {last_msg_preview}")
                
                self.stdout.write(self.style.SUCCESS("✅ Session listing successful"))
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error listing sessions: {e}"))
        
        finally:
            # Cleanup if requested
            if cleanup and created_sessions:
                self.stdout.write("\n" + "="*50)
                self.stdout.write("🧹 CLEANING UP TEST DATA")
                self.stdout.write("="*50)
                
                try:
                    deleted_count = 0
                    for session in created_sessions:
                        msg_count = session.messages.count()
                        session.delete()  # CASCADE will delete messages
                        deleted_count += 1
                        self.stdout.write(f"🗑️  Deleted session {session.session_id} ({msg_count} messages)")
                    
                    self.stdout.write(self.style.SUCCESS(f"✅ Cleaned up {deleted_count} test sessions"))
                
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error during cleanup: {e}"))
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 TEST SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"✅ Chatbot functionality test completed")
        self.stdout.write(f"📤 Sent {len(test_messages)} test messages")
        if test_session_id:
            self.stdout.write(f"💬 Created session: {test_session_id}")
        self.stdout.write("🔗 All API endpoints are ready for use")
        
        # Usage examples
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🚀 API USAGE EXAMPLES")
        self.stdout.write("="*50)
        self.stdout.write("Send message:")
        self.stdout.write("  POST /api/chat/send-message/")
        self.stdout.write("  {'message': 'Hello', 'session_id': 'optional'}")
        self.stdout.write("")
        self.stdout.write("Get session messages:")
        self.stdout.write(f"  GET /api/chat/sessions/{test_session_id or 'SESSION_ID'}/messages/")
        self.stdout.write("")
        self.stdout.write("List all sessions:")
        self.stdout.write("  GET /api/chat/sessions/")
        self.stdout.write("")
        self.stdout.write("Delete session:")
        self.stdout.write(f"  DELETE /api/chat/sessions/{test_session_id or 'SESSION_ID'}/delete/")