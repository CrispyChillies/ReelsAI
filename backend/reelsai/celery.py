import os
from celery import Celery
from django.conf import settings

# 1. Thiết lập module settings mặc định của Django cho Celery
# Thay 'my_project' bằng tên thư mục chứa settings.py thực tế của bạn
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reelsai.settings")

# 2. Khởi tạo ứng dụng Celery
app = Celery("reelsai")

# 3. Load cấu hình từ file settings.py của Django
# namespace='CELERY' nghĩa là các biến trong settings.py phải có tiền tố CELERY_
# Ví dụ: CELERY_BROKER_URL, CELERY_RESULT_BACKEND
app.config_from_object("django.conf:settings", namespace="CELERY")

# 4. Tự động tìm kiếm các tasks.py trong các app đã cài đặt (INSTALLED_APPS)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
