from django.urls import path
from .views import *

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("activate/<uidb64>/<token>/", ActivateAccountView.as_view(), name="activate"),
    path("signin/", SignInView.as_view(), name="signin"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("request-reset-password/", RequestPasswordResetView.as_view(), name="request-reset-password"),
    path("reset-password/<uidb64>/<token>/", ResetPasswordView.as_view(), name="reset-password"),
]