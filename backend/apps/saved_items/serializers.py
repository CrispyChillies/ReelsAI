from rest_framework import serializers
from .models import UserSavedItem


class SaveItemRequestSerializer(serializers.Serializer):
    social_post_id = serializers.IntegerField()
    tags = serializers.ListField(
        child=serializers.CharField(), required=False, default=[]
    )
    notes = serializers.CharField(required=False, allow_blank=True)


class SaveItemResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    saved_id = serializers.IntegerField()
