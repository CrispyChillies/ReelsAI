from django.urls import path
from . import views

urlpatterns = [
    path("save/", views.save_item_view, name="save-item"),
    path("list/", views.list_saved_items, name="list_saved_items"),
    path("delete/<int:item_id>/", views.delete_saved_item, name="delete_saved_item"),
]
