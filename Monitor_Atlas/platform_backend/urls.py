"""
URL configuration for platform_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from users.views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    csrf_setup,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/users/", include("users.urls")),
    path("api/v1/roles/", include("roles.urls")),
    path("api/v1/organizations/", include("organizations.urls")),
    path("api/v1/infrastructure/", include("infrastructure.urls")),
    path("api/v1/chirpstack/", include("chirpstack.urls")),
    path(
        "api/v1/token/",
        CookieTokenObtainPairView.as_view(),
        name="cookie_token_obtain_pair",
    ),
    path(
        "api/v1/token/refresh/",
        CookieTokenRefreshView.as_view(),
        name="cookie_token_refresh",
    ),
    path("api/v1/logout/", LogoutView.as_view(), name="logout"),
    path("api/v1/csrf/", csrf_setup, name="csrf_setup"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
