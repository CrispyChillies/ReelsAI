from django.urls import path
from .views import save_item_view

urlpatterns = [
    path("save-item", save_item_view, name="save_item"),
]
