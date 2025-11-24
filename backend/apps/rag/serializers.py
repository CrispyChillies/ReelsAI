from rest_framework import serializers


class ItemDataSerializer(serializers.Serializer):
    content_id = serializers.CharField(max_length=64)
    content_url = serializers.CharField(max_length=200)
    user_id = serializers.CharField(max_length=64)
    platform = serializers.CharField(max_length=20)
    summary = serializers.CharField()
    timestamp = serializers.IntegerField(
        required=False, allow_null=True
    )  # Optional nếu muốn giữ


class QueryRequestSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=64)
    query = serializers.CharField()
    top_k = serializers.IntegerField(default=5, required=False)
    from_timestamp = serializers.IntegerField(required=False, allow_null=True)
    platform = serializers.CharField(max_length=20, required=False, allow_null=True)
