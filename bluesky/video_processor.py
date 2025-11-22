import os
import cv2
import requests
import subprocess
import json


class VideoPreprocessor:
    def __init__(self, temp_folder="temp_data"):
        self.temp_folder = temp_folder
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

    def download_video(self, video_data):
        """
        Tải video dựa trên ưu tiên: mediaUrls (link trực tiếp) -> webVideoUrl
        """
        video_id = video_data.get("id")

        # Ưu tiên 1: Lấy link từ mediaUrls (Link server Apify - nhanh và ổn định)
        download_url = video_data.get("mediaUrls")

        # Xử lý trường hợp mediaUrls có thể là list hoặc string
        if isinstance(download_url, list) and len(download_url) > 0:
            download_url = download_url[0]

        # Ưu tiên 2: Nếu không có mediaUrls, dùng webVideoUrl (Link gốc TikTok)
        if not download_url:
            download_url = video_data.get("webVideoUrl")
            print(
                "⚠️ Không tìm thấy mediaUrls, thử dùng webVideoUrl (có thể thất bại với requests thường)"
            )

        if not download_url:
            print("❌ Không tìm thấy URL tải xuống nào.")
            return None

        try:
            save_path = os.path.join(self.temp_folder, f"{video_id}.mp4")

            # Nếu file đã tồn tại thì bỏ qua để tiết kiệm thời gian test
            if os.path.exists(save_path):
                print(f"✅ Video {video_id} đã tồn tại, bỏ qua download.")
                return save_path

            print(f"⬇️ Đang tải video từ: {download_url[:50]}...")
            response = requests.get(download_url, stream=True)

            if response.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        f.write(chunk)
                print(f"✅ Tải xong: {save_path}")
                return save_path
            else:
                print(f"❌ Lỗi tải video (Status {response.status_code})")
                return None
        except Exception as e:
            print(f"❌ Exception download: {e}")
            return None

    def extract_audio(self, video_path):
        """Tách audio chuẩn 16kHz mono cho model Whisper"""
        try:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(self.temp_folder, f"{base_name}.wav")

            if os.path.exists(audio_path):
                return audio_path

            # Lệnh ffmpeg tối ưu
            command = [
                "ffmpeg",
                "-i",
                video_path,
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                audio_path,
                "-y",
                "-loglevel",
                "quiet",
            ]
            subprocess.run(command, check=True)
            return audio_path
        except Exception as e:
            print(f"❌ Lỗi tách audio (kiểm tra lại FFmpeg): {e}")
            return None

    def extract_keyframes(self, video_path, interval=2):
        """Cắt frame mỗi 2 giây"""
        frames_dir = os.path.join(
            self.temp_folder, f"frames_{os.path.basename(video_path)}"
        )
        if not os.path.exists(frames_dir):
            os.makedirs(frames_dir)

        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            return []  # Lỗi file video hỏng

        frame_interval = int(fps * interval)
        saved_frames = []
        count = 0
        saved_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if count % frame_interval == 0:
                # Resize về chiều ngang 640px (chuẩn input cho các model Vision nhỏ)
                h, w = frame.shape[:2]
                new_w = 640
                new_h = int(h * (new_w / w))
                resized = cv2.resize(frame, (new_w, new_h))

                frame_name = f"frame_{saved_count}.jpg"
                frame_path = os.path.join(frames_dir, frame_name)
                cv2.imwrite(frame_path, resized)
                saved_frames.append(frame_path)
                saved_count += 1

            count += 1

        cap.release()
        return saved_frames

    def process_pipeline(self, record):
        """Hàm chính gọi toàn bộ quy trình"""
        print(f"\n--- Bắt đầu xử lý Record ID: {record.get('id')} ---")

        # 1. Download
        video_path = self.download_video(record)
        if not video_path:
            return None

        # 2. Extract Audio
        print("🔊 Đang tách audio...")
        audio_path = self.extract_audio(video_path)

        # 3. Extract Frames
        print("🖼️ Đang cắt frames...")
        frames = self.extract_keyframes(video_path, interval=2)

        result = {
            "id": record.get("id"),
            "original_text": record.get("text"),  # Caption gốc từ TikTok
            "paths": {
                "video": video_path,
                "audio": audio_path,
                "frames_folder": os.path.dirname(frames[0]) if frames else None,
                "frame_count": len(frames),
            },
        }
        return result


# --- CHẠY THỬ VỚI RECORD MẪU CỦA BẠN ---
if __name__ == "__main__":
    # Dữ liệu bạn cung cấp
    sample_record = {
        "idx": 0,
        "id": "6952571625178975493",
        "text": "Part 2: quality mental healthcare is a privilege. #tiktoktherapist #therapistsoftiktok #tiktoktherapy",
        "author_username": "strongtherapy",
        "webVideoUrl": "https://www.tiktok.com/@strongtherapy/video/6952571625178975493",
        "mediaUrls": "https://api.apify.com/v2/key-value-stores/xlozLZ1UkQfyqg753/records/video-strongther-20210418184849-6952571625178975493.mp4",
    }

    processor = VideoPreprocessor()
    result = processor.process_pipeline(sample_record)

    if result:
        print("\n✅ XỬ LÝ HOÀN TẤT!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
