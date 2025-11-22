import os
import time
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()


class GeminiEngine:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("❌ Chưa cấu hình GEMINI_API_KEY trong .env")

        genai.configure(api_key=api_key)
        print("✨ Gemini Engine đã sẵn sàng (Sử dụng model 1.5 Flash)")

    def upload_to_gemini(self, path, mime_type="video/mp4"):
        """Upload file lên Google Server để xử lý"""
        try:
            file = genai.upload_file(path, mime_type=mime_type)
            print(f"   📤 Đang upload video: {file.display_name}...")
            return file
        except Exception as e:
            print(f"❌ Lỗi upload: {e}")
            return None

    def wait_for_files_active(self, files):
        """Đợi Google xử lý file (Video cần thời gian để index)"""
        print("   ⏳ Đang đợi Google xử lý video...")
        for name in (file.name for file in files):
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(2)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(
                    f"File {file.name} bị lỗi trạng thái: {file.state.name}"
                )
        print("\n   ✅ Video đã sẵn sàng!")

    def analyze_video(self, video_path, post_text=""):
        """Gửi video + caption gốc cho Gemini phân tích"""
        print(f"\n🧠 Đang gửi video sang Gemini: {os.path.basename(video_path)}...")

        # 1. Upload
        video_file = self.upload_to_gemini(video_path)
        if not video_file:
            return None

        # 2. Wait
        try:
            self.wait_for_files_active([video_file])
        except Exception as e:
            print(f"❌ Lỗi xử lý file: {e}")
            return None

        # 3. Generate Content
        # Prompt này yêu cầu trả về JSON structure giống hệ thống cũ của bạn
        model = genai.GenerativeModel(model_name="gemini-2.5-flash")

        system_prompt = """
        You are an expert content analyzer. Analyze the provided video and the author's caption.
        Return the result in valid JSON format.
        
        The JSON structure should be:
        {
            "transcript_summary": "Summary of what is said in the video",
            "visual_description": "Description of the visual scene, lighting, and emotions",
            "key_frames": [
                {"timestamp": "00:05", "description": "What happens here"}
            ],
            "is_relevant_to_intent": true/false,
            "reasoning": "Why it matches or does not match the intent"
        }
        """

        user_prompt = f"Author's Caption: {post_text}\nAnalyze this video."

        try:
            response = model.generate_content(
                [video_file, system_prompt, user_prompt],
                generation_config={"response_mime_type": "application/json"},
            )

            # Clean up: Xóa file trên server Google để tiết kiệm dung lượng
            genai.delete_file(video_file.name)

            return json.loads(response.text)

        except Exception as e:
            print(f"❌ Lỗi inference Gemini: {e}")
            return None


# --- CHẠY THỬ ---
if __name__ == "__main__":
    # Giả lập input từ Sourcer
    video_path = "temp_data/6952571625178975493.mp4"  # Đảm bảo file này tồn tại
    caption = "Part 2: quality mental healthcare is a privilege."

    if os.path.exists(video_path):
        engine = GeminiEngine()
        result = engine.analyze_video(video_path, caption)
        print("\n✅ KẾT QUẢ GEMINI:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("⚠️ Không tìm thấy file video để test.")
