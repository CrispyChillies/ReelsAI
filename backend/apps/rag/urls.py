from django.urls import path
from .views import add_item_view, query_items_view

urlpatterns = [
    path("add-item", add_item_view, name="rag_add_item"),
    path("query-items", query_items_view, name="rag_query_items"),
]
