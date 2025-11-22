import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class BonsaiCurator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None

    def rate_post(self, post_content: str, criteria: dict):
        """
        Chấm điểm bài viết dựa trên tiêu chí.
        Input:
            - post_content: Nội dung text của bài post.
            - criteria: Dictionary chứa 'include_criteria' và 'exclude_criteria' (từ Planner).
        Output:
            - Dictionary {score: int, reasoning: str}
        """
        if not self.client:
            return {"score": 0, "reasoning": "No API Client"}

        # Prompt Engineering: Dạy cho LLM cách chấm điểm theo chuẩn BONSAI
        system_prompt = """
        You are the 'Curator' module of a personalized feed system.
        Your task is to rate a social media post based on the user's specific intent.
        
        Scoring Scale:
        - 8-10: Strongly matches 'Include' criteria (High quality, exact topic).
        - 5-7:  General match (Relevant but broad).
        - 1-2:  Matches 'Exclude' criteria or irrelevant (Show less).
        - 0:    Toxic, spam, or explicitly forbidden content (Never show).

        Output Format (JSON only):
        {
            "score": <int 0-10>,
            "reasoning": "<short explanation why>",
            "summary": "<concise summary of the post content in 1-2 sentences>"
        }
        """

        user_message = f"""
        USER INTENT:
        - Include: {criteria.get('include_criteria')}
        - Exclude: {criteria.get('exclude_criteria')}

        POST CONTENT TO RATE:
        "{post_content}"
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,  # Cần nhất quán, không sáng tạo lung tung
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"❌ Lỗi Curator: {e}")
            return {"score": 0, "reasoning": "Error"}


# --- PHẦN TEST CHẠY THỬ (GIẢ LẬP) ---
if __name__ == "__main__":
    curator = BonsaiCurator()

    # 1. Giả lập tiêu chí từ Planner (bạn vừa chạy xong)
    mock_criteria = {
        "include_criteria": "latest research papers on Explainable AI in medical imaging applications",
        "exclude_criteria": "basic tutorials and cryptocurrency news",
    }

    # 2. Giả lập danh sách bài viết từ Sourcer (có bài tốt, bài rác)
    mock_posts = [
        {
            "author": "researcher_A",
            "text": "Just published our new paper on using SHAP values to interpret Chest X-ray classifications. We found that...",
        },
        {
            "author": "crypto_bro",
            "text": "Bitcoin is pumping! xAI token is the next big thing. Buy now! 🚀🌕",
        },
        {
            "author": "student_B",
            "text": "Can someone explain what AI is? I am new to this.",
        },
    ]

    print(f"🎯 Tiêu chí lọc: {mock_criteria['include_criteria']}")
    print("--- BẮT ĐẦU CHẤM ĐIỂM ---\n")

    for post in mock_posts:
        rating = curator.rate_post(post["text"], mock_criteria)

        # Hiển thị kết quả
        print(f"Post: [{post['text'][:50]}...]")
        print(f"-> Điểm: {rating['score']}/10")
        print(f"-> Lý do: {rating['reasoning']}")
        print("-" * 30)
