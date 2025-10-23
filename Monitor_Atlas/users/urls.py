from django.urls import path, include

from rest_framework import routers

from . import views

routers = routers.DefaultRouter()

routers.register(r"user", views.UserViewSet)

urlpatterns = [
    path("", include(routers.urls)),
    path("auth/google/", views.GoogleLoginView.as_view(), name="google-login"),
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path(
        "auth/verify-account/",
        views.AccountVerificationView.as_view(),
        name="verify-account",
    ),
    path(
        "auth/request-password-reset/",
        views.PasswordResetView.as_view(),
        name="request-password-reset",
    ),
    path(
        "auth/reset-password-confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="reset-password-confirm",
    ),
    path(
        "auth/re-send-verification/",
        views.ReSendVerificationEmailView.as_view(),
        name="resend-verification",
    ),
]
