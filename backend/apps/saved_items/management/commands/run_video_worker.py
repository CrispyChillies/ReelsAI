"""
Django management command to run the video processing worker.
This command starts a RabbitMQ consumer that processes video content jobs.
"""

import signal
import sys
import json
import time
import pika
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from supabase import create_client


class Command(BaseCommand):
    """Management command to run the video processing worker"""
    
    help = "Start the video processing worker that consumes jobs from RabbitMQ queue"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None
        self.channel = None
        self.should_stop = False
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--queue-name',
            type=str,
            default='video_processing',
            help='Name of the RabbitMQ queue to consume from (default: video_processing)'
        )
        parser.add_argument(
            '--rabbitmq-host',
            type=str,
            default='localhost',
            help='RabbitMQ host (default: localhost)'
        )
        parser.add_argument(
            '--rabbitmq-port',
            type=int,
            default=5672,
            help='RabbitMQ port (default: 5672)'
        )
        parser.add_argument(
            '--heartbeat',
            type=int,
            default=600,
            help='RabbitMQ connection heartbeat in seconds (default: 600)'
        )
        parser.add_argument(
            '--prefetch-count',
            type=int,
            default=1,
            help='Number of messages to prefetch (default: 1)'
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of retries for API calls (default: 3)'
        )
    
    def handle(self, *args, **options):
        """Main entry point for the management command"""
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.queue_name = options['queue_name']
        self.rabbitmq_host = settings.RABBITMQ_HOST or options['rabbitmq_host']
        self.rabbitmq_port = settings.RABBITMQ_PORT or options['rabbitmq_port']
        self.heartbeat = options['heartbeat']
        self.prefetch_count = options['prefetch_count']
        self.max_retries = options['max_retries']
        
        # Validate required settings
        if not self._validate_settings():
            return
        
        # Initialize Supabase client
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        
        # Start the worker
        self._start_worker()
    
    def _validate_settings(self):
        """Validate required Django settings"""
        required_settings = [
            'SUPABASE_URL',
            'SUPABASE_KEY',
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Missing required settings: {', '.join(missing_settings)}"
                )
            )
            return False
        
        # Check SERVICE_URLS
        if not hasattr(settings, 'SERVICE_URLS') or not settings.SERVICE_URLS:
            self.stdout.write(
                self.style.ERROR("❌ Missing SERVICE_URLS setting")
            )
            return False
        
        service_urls = settings.SERVICE_URLS
        required_urls = ['RAG_API_URL']
        missing_urls = []
        
        for url_key in required_urls:
            if url_key not in service_urls or not service_urls[url_key]:
                missing_urls.append(url_key)
        
        if missing_urls:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ Missing required SERVICE_URLS: {', '.join(missing_urls)}"
                )
            )
            return False
        
        return True
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.stdout.write(
            self.style.WARNING(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        )
        self.should_stop = True
        if self.channel:
            self.channel.stop_consuming()
    
    def _start_worker(self):
        """Start the RabbitMQ worker"""
        try:
            # Connect to RabbitMQ
            self.stdout.write(f"🔌 Connecting to RabbitMQ at {self.rabbitmq_host}:{self.rabbitmq_port}")
            
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.rabbitmq_host,
                    port=self.rabbitmq_port,
                    heartbeat=self.heartbeat
                )
            )
            self.channel = self.connection.channel()
            
            # Declare queue (ensure it exists)
            self.channel.queue_declare(queue=self.queue_name, durable=True)
            
            # Set QoS
            self.channel.basic_qos(prefetch_count=self.prefetch_count)
            
            # Set up message callback
            self.channel.basic_consume(
                queue=self.queue_name, 
                on_message_callback=self._process_message
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"🐇 Video processing worker started successfully!\n"
                    f"📋 Queue: {self.queue_name}\n"
                    f"🔌 Host: {self.rabbitmq_host}:{self.rabbitmq_port}\n"
                    f"⚡ Prefetch: {self.prefetch_count}\n"
                    f"🔄 Max retries: {self.max_retries}\n"
                    f"👀 Waiting for video processing jobs... (Press Ctrl+C to stop)"
                )
            )
            
            # Start consuming
            self.channel.start_consuming()
            
        except pika.exceptions.AMQPConnectionError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to connect to RabbitMQ: {e}")
            )
        except KeyboardInterrupt:
            self._signal_handler(2, None)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Unexpected error in worker: {e}")
            )
        finally:
            self._cleanup()
    
    def _process_message(self, ch, method, properties, body):
        """Process a single message from the queue"""
        try:
            # Parse job data
            job = json.loads(body.decode())
            user_id = job.get('user_id')
            content_id = job.get('content_id')
            
            if not user_id or not content_id:
                self.stdout.write(
                    self.style.ERROR(f"❌ Invalid job data: {job}")
                )
                ch.basic_nack(method.delivery_tag, requeue=False)
                return
            
            self.stdout.write(
                f"🚀 Processing content {content_id} for user {user_id}"
            )
            
            # Process the job
            success = self._process_video_job(user_id, content_id)
            
            if success:
                # Acknowledge message
                ch.basic_ack(method.delivery_tag)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Successfully processed content {content_id}"
                    )
                )
            else:
                # Reject message (don't requeue to avoid infinite loops)
                ch.basic_nack(method.delivery_tag, requeue=False)
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Failed to process content {content_id}"
                    )
                )
                
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Invalid JSON in message: {e}")
            )
            ch.basic_nack(method.delivery_tag, requeue=False)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error processing message: {e}")
            )
            ch.basic_nack(method.delivery_tag, requeue=False)
    
    def _process_video_job(self, user_id: int, content_id: int) -> bool:
        """Process video: fetch URL → summarize → send to RAG"""
        try:
            # Step 1: Fetch media URL from Supabase
            self.stdout.write(f"📹 Fetching media URL for content {content_id}")
            resp = (
                self.supabase.table("content_crawling")
                .select("mediaUrls")
                .eq("id", content_id)
                .execute()
            )
            
            if not resp.data:
                self.stdout.write("❌ No media URL found in Supabase")
                return False
            
            media_url = resp.data[0]["mediaUrls"]
            self.stdout.write(f"📹 Media URL retrieved: {media_url[:60]}...")
            
            # Step 2: Call video summarizer with retry logic
            summary = self._get_video_summary(media_url)
            if not summary:
                return False
            
            self.stdout.write(f"📝 Summary generated: {summary[:100]}...")
            
            # Step 3: Send to RAG system
            return self._send_to_rag(user_id, content_id, summary)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Unexpected error in _process_video_job: {e}")
            )
            return False
    
    def _get_video_summary(self, media_url: str) -> str:
        """Get video summary with retry logic"""
        video_url = settings.SERVICE_URLS["VIDEO_UNDERSTANDING_API_URL"]
        
        for attempt in range(self.max_retries):
            try:
                self.stdout.write(
                    f"🔍 Calling video summarizer (attempt {attempt + 1}/{self.max_retries})"
                )
                
                response = requests.post(
                    video_url,
                    json={"video_url": media_url},
                    timeout=120
                )
                
                if response.status_code == 503:
                    # API overloaded
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** (attempt + 1)
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️  API overloaded, retrying in {wait_time}s..."
                            )
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        self.stdout.write("❌ API still overloaded after retries")
                        return ""
                
                response.raise_for_status()
                summary_json = response.json()
                summary = summary_json.get("summary", "")
                
                if summary:
                    return summary
                    
            except requests.exceptions.RequestException as e:
                self.stdout.write(f"❌ Request error: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    self.stdout.write(f"🔄 Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return ""
        
        return ""
    
    def _send_to_rag(self, user_id: int, content_id: int, content_url: str, summary: str) -> bool:
        """Send processed content to RAG system"""
        try:
            rag_url = settings.SERVICE_URLS["RAG_API_URL"]
            self.stdout.write(f"🔍 Sending to RAG system: {rag_url}")
            
            payload = {
                "content_id": str(content_id),
                "content_url": str(content_url),
                "user_id": str(user_id), 
                "summary": summary,
                "platform": "tiktok",
                "timestamp": int(time.time()),
            }
            
            response = requests.put(
                rag_url,
                json=payload,
                timeout=30,
            )
            
            if response.status_code >= 400:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ RAG API error {response.status_code}: {response.text}"
                    )
                )
                return False
            
            self.stdout.write("✅ Successfully sent to RAG system")
            return True
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error calling RAG API: {e}")
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Unexpected error in _send_to_rag: {e}")
            )
            return False
    
    def _cleanup(self):
        """Clean up connections"""
        if self.channel:
            try:
                if not self.channel.is_closed:
                    self.channel.close()
            except:
                pass
        
        if self.connection:
            try:
                if not self.connection.is_closed:
                    self.connection.close()
            except:
                pass
        
        self.stdout.write("👋 Video processing worker stopped")