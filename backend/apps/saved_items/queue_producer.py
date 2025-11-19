import pika
import json
import logging

logger = logging.getLogger(__name__)


def publish_video_job(user_id: int, content_id: int):
    """
    Publish video processing job to RabbitMQ queue
    """
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost", heartbeat=600)
        )
        channel = connection.channel()

        # Declare queue (idempotent)
        channel.queue_declare(queue="video_processing", durable=True)

        message = json.dumps({"user_id": user_id, "content_id": content_id})

        channel.basic_publish(
            exchange="",
            routing_key="video_processing",
            body=message,
            properties=pika.BasicProperties(delivery_mode=2),  # Make message persistent
        )

        connection.close()
        logger.info(f"📤 Job sent → user {user_id}, content {content_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to publish job: {e}")
        return False
