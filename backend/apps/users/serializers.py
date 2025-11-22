from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_username(self, value):
        """Check if username already exists"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

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

class UserResponseSerializer(serializers.ModelSerializer):
    """Serializer for returning user information (read-only)"""
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active", "date_joined"]
        read_only_fields = ["id", "username", "email", "first_name", "last_name", "is_active", "date_joined"]

class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]
        extra_kwargs = {
            "username": {"required": False},
            "email": {"required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    current_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, min_length=8)