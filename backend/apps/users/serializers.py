from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        user.is_active = False  # Make user inactive until email confirmation
        user.save()
        return user
    
class RegisterRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class MessageResponseSerializer(serializers.Serializer):
    message = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class SignInRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class SignInResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    message = serializers.CharField()

class LogoutRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

class RequestPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordRequestSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)