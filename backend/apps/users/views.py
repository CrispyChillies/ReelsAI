from django.contrib.auth.models import User
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import (
    extend_schema, OpenApiExample, OpenApiParameter, OpenApiResponse
)

from .serializers import *  # your existing serializer


class RegisterView(APIView):
    """
    Register a new user and send an email verification link.
    """

    @extend_schema(
        tags=["Auth"],
        summary="Register",
        description="Create a user account and send a verification email with an activation link.",
        request=RegisterRequestSerializer,
        responses={
            201: OpenApiResponse(
                response=MessageResponseSerializer,
                description="Registration succeeded. Verification email sent."
            ),
            400: OpenApiResponse(ErrorResponseSerializer),
        },
        examples=[
            OpenApiExample(
                "Register payload",
                value={"username": "alice", "email": "alice@example.com", "password": "S3cret!"},
                request_only=True,
            ),
            OpenApiExample(
                "Register success",
                value={"message": "Please check your email to confirm registration"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate email confirmation token + link
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            backend_base = getattr(settings, 'BACKEND_BASE_URL', 'http://127.0.0.1:8000')
            verification_link = f"{backend_base}/api/auth/activate/{uid}/{token}/"

            # Send email
            subject = "Xác nhận đăng ký tài khoản - ReelsAI"
            html_message = render_to_string(
                "users/confirm_email.html",
                {"user": user, "activation_link": verification_link}
            )
            plain_message = strip_tags(html_message)
            recipient_list = [user.email]
            send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message)

            return Response({"message": "Please check your email to confirm registration"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivateAccountView(APIView):
    """
    Activate user account via email link (redirects to frontend).
    """

    @extend_schema(
        tags=["Auth"],
        summary="Activate account",
        description="Validate the activation token and activate the account. Redirects to success or failure page.",
        parameters=[
            OpenApiParameter(name="uidb64", required=True, location=OpenApiParameter.PATH, type=str),
            OpenApiParameter(name="token", required=True, location=OpenApiParameter.PATH, type=str),
        ],
        responses={302: OpenApiResponse(description="Redirect to frontend success/failure page")},
    )
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
            return redirect(f"{frontend_base}/verification-failed/")

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
            return redirect(f"{frontend_base}/account-success/")
        else:
            frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
            return redirect(f"{frontend_base}/verification-failed/")


class SignInView(APIView):
    """
    Sign in with username/password to get JWT tokens.
    """

    @extend_schema(
        tags=["Auth"],
        summary="Sign in",
        description="Authenticate the user and return access/refresh JWTs.",
        request=SignInRequestSerializer,
        responses={
            200: SignInResponseSerializer,
            401: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Sign in payload",
                value={"username": "alice", "password": "S3cret!"},
                request_only=True,
            ),
            OpenApiExample(
                "Sign in success",
                value={
                    "access": "<jwt_access>",
                    "refresh": "<jwt_refresh>",
                    "message": "Log in successfully!",
                },
                response_only=True,
            ),
            OpenApiExample(
                "Sign in error",
                value={"error": "Neither username or password is right!"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response(
                {"access": str(refresh.access_token), "refresh": str(refresh), "message": "Log in successfully!"},
                status=status.HTTP_200_OK,
            )
        return Response({"error": "Neither username or password is right!"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    Blacklist a refresh token (if blacklist app is enabled).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Logout",
        description="Invalidate the provided refresh token by blacklisting it.",
        request=LogoutRequestSerializer,
        responses={
            200: MessageResponseSerializer,
            400: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Logout payload",
                value={"refresh_token": "<jwt_refresh>"},
                request_only=True,
            ),
            OpenApiExample(
                "Logout success",
                value={"message": "Logged out successfully"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RequestPasswordResetView(APIView):
    """
    Send a password reset email with uid/token for the user.
    """

    @extend_schema(
        tags=["Auth"],
        summary="Request password reset",
        description="Send a password reset email with a link to the frontend that includes uid and token.",
        request=RequestPasswordResetSerializer,
        responses={
            200: MessageResponseSerializer,
            404: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Reset request payload",
                value={"email": "alice@example.com"},
                request_only=True,
            ),
            OpenApiExample(
                "Reset request success",
                value={"message": "Email đặt lại mật khẩu đã được gửi!"},
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Email không tồn tại trong hệ thống!"}, status=status.HTTP_404_NOT_FOUND)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
        reset_link = f"{frontend_base}/reset-password/{uidb64}/{token}/"

        subject = "Đặt lại mật khẩu cho tài khoản - ReelsAI"
        html_message = render_to_string("users/reset_password_email.html", {"user": user, "reset_link": reset_link})
        plain_message = strip_tags(html_message)
        recipient_list = [user.email]
        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)

        return Response({"message": "Email đặt lại mật khẩu đã được gửi!"}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """
    Reset the password using uid/token from the email.
    """

    @extend_schema(
        tags=["Auth"],
        summary="Reset password",
        description="Validate the reset token and set a new password.",
        parameters=[
            OpenApiParameter(name="uidb64", required=True, location=OpenApiParameter.PATH, type=str),
            OpenApiParameter(name="token", required=True, location=OpenApiParameter.PATH, type=str),
        ],
        request=ResetPasswordRequestSerializer,
        responses={
            200: MessageResponseSerializer,
            302: OpenApiResponse(description="If invalid token, this endpoint redirects to frontend failure page."),
            400: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                "Reset password payload",
                value={"password": "NewS3curePass!"},
                request_only=True,
            ),
            OpenApiExample(
                "Reset success",
                value={"message": "Mật khẩu đã được đặt lại thành công!"},
                response_only=True,
            ),
        ],
    )
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Liên kết đặt lại mật khẩu không hợp lệ!"}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            frontend_base = getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:3000')
            return redirect(f"{frontend_base}/reset-password/failed")

        new_password = request.data.get("password")
        user.set_password(new_password)
        user.save()
        return Response({"message": "Mật khẩu đã được đặt lại thành công!"}, status=status.HTTP_200_OK)