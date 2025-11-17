from google import genai
from google.genai import types

# from django.conf import settings


def summarize_video(video_path: str) -> str:
    """
    Uploads and uses the Gemini model to summarize the video content.

    Args:
        video_path (str): The absolute path to the video file (must be < 20MB).

    Returns:
        str: A 3-sentence Vietnamese summary of the video, or an error message.
    """
    api_key = "AIzaSyB0mP_2EPFFLDWNh9uX7jdnS6BS6AXBr84"
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

    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=types.Content(
                parts=[
                    types.Part(
                        inline_data=types.Blob(data=video_bytes, mime_type="video/mp4")
                    ),
                    types.Part(
                        text="Hãy tóm tắt video này trong dưới 10 câu tiếng Việt."
                        " Kết quả tóm tắt nên ngắn gọn, súc tích, và bao gồm các điểm chính của video."
                        " Thông tin tóm tắt nên thể hiện được các mối quan hệ của những thực thể trong video."
                    ),
                ]
            ),
        )

        if (
            response
            and response.candidates
            and len(response.candidates) > 0
            and response.candidates[0].content
            and response.candidates[0].content.parts
            and len(response.candidates[0].content.parts) > 0
        ):
            return response.candidates[0].content.parts[0].text
        else:
            return "No valid response received from Gemini API."

    except Exception as e:
        return f"Error calling Gemini API: {e}"


if __name__ == "__main__":
    # Your sample video path (replace with the actual path)
    video_file_name = "/home/aaronpham/Coding/ReelsAI/rag/video-strongther-20210418184849-6952571625178975493.mp4"

    print(f"Summarizing video: {video_file_name}...")
    summary = summarize_video(video_file_name)

    print("\n--- SUMMARY RESULT ---")
    print(summary)

    # Save summary to txt file
    output_file = "/home/aaronpham/Coding/ReelsAI/backend/video_summary.txt"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"\nSummary saved to: {output_file}")
    except Exception as e:
        print(f"Error saving summary to file: {e}")
