from django.urls import path
from .views import save_item_view

urlpatterns = [
    path("save/", save_item_view, name="save-item"),
    # Sau này có thể thêm: path('list/', list_saved_items, ...)
]
