import openai
from moviepy.editor import VideoFileClip
import os
import tempfile


class VideoCaptioningService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def transcribe_and_summarize(self, video_file):
        """
        Transcribe and summarize video in Vietnamese or English
        """
        # Create temporary video file
        temp_video_path = None
        audio_path = None
        video = None

        try:
            # Create temporary video file with delete=False to keep it until we're done
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                for chunk in video_file.chunks():
                    temp_video.write(chunk)
                temp_video_path = temp_video.name

            # Extract audio from video
            video = VideoFileClip(temp_video_path)
            if video is None or video.audio is None:
                raise Exception("No audio track found in the video.")

            # Create temporary audio file with delete=False
            temp_audio_fd, audio_path = tempfile.mkstemp(suffix=".mp3")
            os.close(temp_audio_fd)  # Close the file descriptor

            # Write audio to the temporary file
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)

            # Transcribe using OpenAI Whisper
            with open(audio_path, "rb") as audio_file:
                transcript_result = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                )

            detected_language = transcript_result.language
            transcript = transcript_result.text

            # Language-specific prompts
            prompts = {
                "vi": {
                    "system": "Bạn là một trợ lý AI chuyên phân tích nội dung video. Hãy tóm tắt một cách chính xác và súc tích.",
                    "user": f"Tóm tắt nội dung chính của video từ transcript sau:\n\n{transcript}",
                },
                "en": {
                    "system": "You are an AI assistant specialized in video content analysis. Provide accurate and concise summaries.",
                    "user": f"Summarize the main content of the video from this transcript:\n\n{transcript}",
                },
            }

            # Choose prompt based on detected language
            if detected_language in ["vi", "vietnamese"]:
                selected_prompts = prompts["vi"]
            elif detected_language in ["en", "english"]:
                selected_prompts = prompts["en"]
            else:
                # Default to English for other languages
                selected_prompts = prompts["en"]

            # Generate summary
            summary_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": selected_prompts["system"]},
                    {"role": "user", "content": selected_prompts["user"]},
                ],
                max_tokens=300,
                temperature=0.3,
            )

            return {
                "transcript": transcript,
                "detected_language": detected_language,
                "summary": summary_response.choices[0].message.content,
            }

        except Exception as e:
            # Log the error for debugging
            print(f"Error in video processing: {str(e)}")
            raise e

        finally:
            # Cleanup - make sure we clean up even if there are errors
            try:
                if video is not None:
                    video.close()
            except Exception as e:
                print(f"Error closing video: {e}")

            try:
                if temp_video_path and os.path.exists(temp_video_path):
                    os.remove(temp_video_path)
            except Exception as e:
                print(f"Error removing temp video: {e}")

            try:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception as e:
                print(f"Error removing temp audio: {e}")
