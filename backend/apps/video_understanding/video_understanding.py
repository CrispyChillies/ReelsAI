from google import genai
from google.genai import types
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)


def summarize_video(video_path: str, max_retries: int = 3) -> str:
    """
    Uploads and uses the Gemini model to summarize the video content.
    Implements retry logic with exponential backoff for 503 overload errors.

    Args:
        video_path (str): The absolute path to the video file (must be < 20MB).
        max_retries (int): Maximum number of retry attempts (default: 3)

    Returns:
        str: A Vietnamese summary of the video, or an error message.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables."

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        return f"Error initializing Gemini client: {e}"

    try:
        with open(video_path, "rb") as f:
            video_bytes = f.read()
    except FileNotFoundError:
        return f"Error: Video file not found at path '{video_path}'."
    except Exception as e:
        return f"Error reading video file: {e}"

    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            logger.info(f"Calling Gemini API (attempt {attempt + 1}/{max_retries})...")

            response = client.models.generate_content(
                model="models/gemini-2.5-flash",
                contents=types.Content(
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                data=video_bytes, mime_type="video/mp4"
                            )
                        ),
                        types.Part(
                            text="Hãy tóm tắt video này trong dưới 10 câu tiếng Việt."
                            " Kết quả tóm tắt nên ngắn gọn, súc tích, và bao gồm các điểm chính của video."
                            " Thông tin tóm tắt nên thể hiện được các mối quan hệ của những thực thể trong video."
                        ),
                    ]
                ),
            )

            # Check if response is valid
            if (
                response
                and response.candidates
                and len(response.candidates) > 0
                and response.candidates[0].content
                and response.candidates[0].content.parts
                and len(response.candidates[0].content.parts) > 0
            ):
                summary = response.candidates[0].content.parts[0].text
                logger.info("Summary generated successfully")
                return summary
            else:
                return "No valid response received from Gemini API."

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Attempt {attempt + 1} failed: {error_msg}")

            # Check if it's a transient error (503, overload, rate limit, UNAVAILABLE)
            is_transient_error = (
                "503" in error_msg
                or "overloaded" in error_msg.lower()
                or "unavailable" in error_msg.lower()
                or "rate" in error_msg.lower()
                or "quota" in error_msg.lower()
                or "UNAVAILABLE" in error_msg
            )

            if is_transient_error:
                if attempt < max_retries - 1:
                    # Exponential backoff: 2^(attempt+1) seconds (2s, 4s, 8s)
                    wait_time = 2 ** (attempt + 1)
                    logger.info(
                        f"Transient error detected. Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                    continue  # Retry
                else:
                    # Max retries reached
                    return (
                        f"Error: Gemini API is temporarily unavailable after {max_retries} attempts. "
                        f"Please try again later. Last error: {error_msg}"
                    )
            else:
                # Non-transient error, fail immediately
                return f"Error calling Gemini API: {error_msg}"

    # Should not reach here, but just in case
    return f"Error: Failed after {max_retries} attempts"


# if __name__ == "__main__":
#     # Your sample video path (replace with the actual path)
#     video_file_name = "/home/aaronpham/Coding/ReelsAI/rag/video-strongther-20210418184849-6952571625178975493.mp4"
#
#     print(f"Summarizing video: {video_file_name}...")
#     summary = summarize_video(video_file_name, max_retries=3)
#
#     print("\n--- SUMMARY RESULT ---")
#     print(summary)
#
#     # Save summary to txt file
#     output_file = "/home/aaronpham/Coding/ReelsAI/backend/video_summary.txt"
#     try:
#         with open(output_file, "w", encoding="utf-8") as f:
#             f.write(summary)
#         print(f"\nSummary saved to: {output_file}")
#     except Exception as e:
#         print(f"Error saving summary to file: {e}")
