import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load biến môi trường
load_dotenv()


class BonsaiPlanner:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ Cảnh báo: Chưa có OPENAI_API_KEY trong .env")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)

    def generate_plan(self, user_intent: str):
        """
        Dịch ý định người dùng thành cấu hình search và filter.
        Tương ứng với component Planning trong bài báo.
        """
        if not self.client:
            return None

        print(f"🧠 Planner đang phân tích ý định: '{user_intent}'...")

        # System Prompt: Định nghĩa vai trò của Planner
        system_prompt = """
        You are the 'Planner' module of the BONSAI feed system.
        Your goal is to translate a user's natural language intent into a structured configuration JSON.
        
        Output JSON format must be:
        {
            "search_queries": ["query1", "query2"],
            "include_criteria": "short description of what to include",
            "exclude_criteria": "short description of what to exclude",
            "ranking_preference": "balanced" (or "fresh", "focused")
        }
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Dùng model nhỏ cho nhanh và rẻ
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_intent},
                ],
                response_format={"type": "json_object"},  # Bắt buộc trả về JSON
                temperature=0.2,  # Giảm sáng tạo để tăng độ chính xác
            )

            # Parse kết quả trả về
            plan_json = response.choices[0].message.content
            return json.loads(plan_json)

        except Exception as e:
            print(f"❌ Lỗi Planner: {e}")
            return None


# --- PHẦN TEST CHẠY THỬ ---
if __name__ == "__main__":
    planner = BonsaiPlanner()

    # Giả lập input người dùng (liên quan đến Thesis của bạn)
    user_input = "I want to find latest research papers about Explainable AI (xAI) applied in Medical Imaging like X-ray or MRI. I don't want to see basic tutorials or crypto news."

    plan = planner.generate_plan(user_input)

    if plan:
        print("\n--- KẾT QUẢ PLANNER (JSON) ---")
        print(json.dumps(plan, indent=4, ensure_ascii=False))

        # Logic nối với Sourcer (Demo logic)
        print("\n--- KẾ HOẠCH TIẾP THEO ---")
        print(f"1. Hệ thống sẽ search các từ khóa: {plan.get('search_queries')}")
        print(
            f"2. Sau đó sẽ lọc bài dựa trên tiêu chí Include: '{plan.get('include_criteria')}'"
        )
        print(
            f"3. Và loại bỏ bài dựa trên tiêu chí Exclude: '{plan.get('exclude_criteria')}'"
        )
