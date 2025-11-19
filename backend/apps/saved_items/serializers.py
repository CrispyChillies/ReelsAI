from rest_framework import serializers


class SaveItemRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    content_id = serializers.IntegerField()


class SaveItemResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    message = serializers.CharField()
    data = serializers.DictField(required=False)
