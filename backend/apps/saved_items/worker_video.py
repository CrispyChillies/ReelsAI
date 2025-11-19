import pika
import json
import requests
from supabase import create_client
from dotenv import load_dotenv
import os
import time

load_dotenv()

VIDEO_UNDERSTANDING_URL = "http://localhost:8000/api/video-analysis/summarize"
RAG_URL = "http://localhost:8000/api/rag/add-item"


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def process_job(user_id: int, content_id: int):
    """Process video: fetch URL → summarize → send to RAG"""
    print(f"🚀 Processing content {content_id} for user {user_id}")

    try:
        # Step 1: Fetch media URL from Supabase
        resp = (
            supabase.table("video_crawling")
            .select("mediaUrls")
            .eq("id", content_id)
            .execute()
        )

        if not resp.data:
            print("❌ No media URL found.")
            return

        media_url = resp.data[0]["mediaUrls"]
        print(f"📹 Media URL: {media_url}")

        # Step 2: Call Django video summarizer with retry
        max_retries = 3
        summary = None

        for attempt in range(max_retries):
            try:
                print(
                    f"🔍 Calling video summarizer (attempt {attempt + 1}/{max_retries})..."
                )
                summary_resp = requests.post(
                    VIDEO_UNDERSTANDING_URL, json={"video_url": media_url}, timeout=120
                )

                if summary_resp.status_code == 503:
                    # API overloaded, retry with backoff
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)
                        print(f"⚠️  API overloaded, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("❌ API still overloaded after retries")
                        return

                summary_resp.raise_for_status()
                summary_json = summary_resp.json()
                summary = summary_json.get("summary", "")

                if summary:
                    break

            except requests.exceptions.RequestException as e:
                print(f"❌ Request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
                    continue
                return

        if not summary:
            print("❌ Failed to get summary")
            return

        print("📝 Summary:", summary[:60], "...")

        # Step 3: Send to RAG
        try:
            print(f"🔍 Sending to RAG: {RAG_URL}")
            rag_resp = requests.put(
                RAG_URL,
                json={
                    "content_id": str(content_id),
                    "user_id": str(user_id),
                    "summary": summary,
                    "platform": "tiktok",
                },
                timeout=30,
            )

            if rag_resp.status_code >= 400:
                print("❌ RAG API returned error status:", rag_resp.status_code)
                print("📩 Response body:", rag_resp.text)
                rag_resp.raise_for_status()

            print("✅ Successfully updated RAG with summary.")

        except Exception as e:
            print("❌ Exception when calling RAG:")
            print("   ➤ Error:", str(e))
            if "rag_resp" in locals():
                print("   ➤ Raw Response:", rag_resp.text)

    except Exception as e:
        print(f"❌ Unexpected error in process_job: {e}")
        import traceback

        traceback.print_exc()


def main():
    """RabbitMQ consumer - listens for video processing jobs"""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters("localhost", heartbeat=600)
    )
    channel = connection.channel()
    channel.queue_declare(queue="video_processing", durable=True)

    def callback(ch, method, properties, body):
        try:
            job = json.loads(body.decode())
            process_job(job["user_id"], job["content_id"])
            ch.basic_ack(method.delivery_tag)
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            # Optionally reject and requeue
            # ch.basic_nack(method.delivery_tag, requeue=True)

    channel.basic_qos(prefetch_count=1)
    print("🐇 Worker started, waiting for jobs...")
    channel.basic_consume(queue="video_processing", on_message_callback=callback)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\n👋 Worker stopped")
        channel.stop_consuming()
        connection.close()


if __name__ == "__main__":
    main()
