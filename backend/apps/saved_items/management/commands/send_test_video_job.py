"""
Django management command to send test jobs to the video processing queue.
Useful for testing the video worker without external job producers.
"""

import json
import pika
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    """Management command to send test jobs to video processing queue"""
    
    help = "Send test video processing jobs to RabbitMQ queue for testing the worker"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--queue-name',
            type=str,
            default='video_processing',
            help='Name of the RabbitMQ queue (default: video_processing)'
        )
        parser.add_argument(
            '--rabbitmq-host',
            type=str,
            default='localhost',
            help='RabbitMQ host (default: localhost)'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID for the test job (if not provided, will use first admin user)'
        )
        parser.add_argument(
            '--content-id',
            type=int,
            help='Content ID for the test job (required if --custom-job is used)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of test jobs to send (default: 1)'
        )
        parser.add_argument(
            '--custom-job',
            action='store_true',
            help='Send custom job with specified user-id and content-id'
        )
    
    def handle(self, *args, **options):
        """Send test jobs to the video processing queue"""
        
        queue_name = options['queue_name']
        rabbitmq_host = options['rabbitmq_host']
        count = options['count']
        custom_job = options['custom_job']
        
        # Get user ID
        user_id = options.get('user_id')
        if not user_id:
            try:
                # Get first admin user
                admin_user = User.objects.filter(is_staff=True).first()
                if admin_user:
                    user_id = admin_user.id
                    self.stdout.write(f"📝 Using admin user: {admin_user.username} (ID: {user_id})")
                else:
                    # Get any user
                    any_user = User.objects.first()
                    if any_user:
                        user_id = any_user.id
                        self.stdout.write(f"📝 Using user: {any_user.username} (ID: {user_id})")
                    else:
                        self.stdout.write(
                            self.style.ERROR("❌ No users found in database. Create a user first.")
                        )
                        return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error finding user: {e}")
                )
                return
        
        # Connect to RabbitMQ
        try:
            self.stdout.write(f"🔌 Connecting to RabbitMQ at {rabbitmq_host}")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbitmq_host)
            )
            channel = connection.channel()
            
            # Declare queue
            channel.queue_declare(queue=queue_name, durable=True)
            
            # Send test jobs
            self.stdout.write(f"📤 Sending {count} test job(s) to queue '{queue_name}'")
            
            for i in range(count):
                if custom_job:
                    content_id = options.get('content_id')
                    if not content_id:
                        self.stdout.write(
                            self.style.ERROR("❌ --content-id is required when using --custom-job")
                        )
                        return
                else:
                    # Generate fake content ID for testing
                    content_id = 1000 + i
                
                job = {
                    "user_id": user_id,
                    "content_id": content_id,
                    "content_url": f"https://www.example.com/content/{content_id}"
                }
                
                channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=json.dumps(job),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Make message persistent
                    )
                )
                
                self.stdout.write(
                    f"✅ Sent job {i+1}/{count}: user_id={user_id}, content_id={content_id}"
                )
            
            connection.close()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"🎉 Successfully sent {count} test job(s) to the queue!\\n"
                    f"💡 Now run the worker with: python manage.py run_video_worker"
                )
            )
            
        except pika.exceptions.AMQPConnectionError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to connect to RabbitMQ: {e}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error sending test jobs: {e}")
            )