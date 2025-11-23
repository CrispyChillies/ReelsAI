import requests
import json


class HyperClovaXClient:
    def __init__(self, host, api_key, api_key_primary, request_id):
        self.host = host
        self.api_key = api_key
        self.api_key_primary = api_key_primary
        self.request_id = request_id

    def completion(
        self,
        messages,
        top_p=0.8,
        top_k=0,
        max_tokens=256,
        temperature=0.5,
        repeat_penalty=5.0,
    ):
        headers = {
            "X-NCP-CLOVASTUDIO-API-KEY": self.api_key,
            "X-NCP-APIGW-API-KEY": self.api_key_primary,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id,
            "Content-Type": "application/json; charset=utf-8",
            # Đôi khi cần thêm header này nếu dùng stream
            # 'Accept': 'text/event-stream'
        }

        data = {
            "messages": messages,
            "topP": top_p,
            "topK": top_k,
            "maxTokens": max_tokens,
            "temperature": temperature,
            "repeatPenalty": repeat_penalty,
            "stopBefore": [],
            "includeAiFilters": True,
            "seed": 0,
        }

        try:
            response = requests.post(
                self.host
                + "/testapp/v1/chat-completions/HCX-003",  # Endpoint mẫu, thay bằng URL thật của bạn
                headers=headers,
                json=data,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error calling API: {e}")
            return None


# --- CẤU HÌNH CỦA BẠN ---
# Lấy các thông tin này từ CLOVA Studio Console
HOST_URL = "https://clovastudio.apigw.ntruss.com"
API_KEY = "YOUR_CLOVA_STUDIO_API_KEY"
API_GATEWAY_KEY = "YOUR_APIGW_API_KEY"
REQUEST_ID = "my-test-req-001"

# Khởi tạo client
client = HyperClovaXClient(HOST_URL, API_KEY, API_GATEWAY_KEY, REQUEST_ID)

# Tạo hội thoại mẫu
messages = [
    {"role": "system", "content": "Bạn là một trợ lý AI hữu ích và thông minh."},
    {
        "role": "user",
        "content": "Hãy giải thích ngắn gọn về HyperCLOVA X bằng tiếng Việt.",
    },
]

# Gọi API
result = client.completion(messages)

# In kết quả
if result:
    print(json.dumps(result, indent=2, ensure_ascii=False))
    # Thường nội dung trả về nằm ở result['result']['message']['content']
