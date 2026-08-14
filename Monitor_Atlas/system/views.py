from django.apps import apps
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    OpenApiExample,
)

from .serializers import (
    AppsModelsResponseSerializer,
    SystemHealthResponseSerializer,
    HermesHealthSerializer,
    AtlasServicesHealthSerializer,
)
from .health import (
    get_system_health_report,
    check_hermes_health,
    get_atlas_services_health,
)

# Standard platform domain applications
PLATFORM_PROJECT_APPS = [
    "users",
    "roles",
    "organizations",
    "infrastructure",
    "chirpstack",
    "support",
    "notifications",
]


class AppsModelsView(APIView):
    """
    Endpoint for retrieving registered Django applications and their corresponding models.
    Designed for frontend consumption (e.g. dynamic forms, filter builders, audit log filters, role management).
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["System"],
        summary="List Applications and Models",
        description=(
            "Retrieves a list of installed Django applications and their models with metadata "
            "(model name, object class name, verbose names, and database tables).\n\n"
            "- By default, returns platform core apps (`users`, `roles`, `organizations`, `infrastructure`, `chirpstack`, `support`, `notifications`).\n"
            "- Pass `include_all=true` to retrieve all installed apps including Django built-ins (`auth`, `contenttypes`, `sessions`, `auditlog`, etc.).\n"
            "- Pass `app=<label>` to filter by a single application label (e.g., `?app=infrastructure`)."
        ),
        parameters=[
            OpenApiParameter(
                name="include_all",
                description="Include all installed Django apps (built-ins, auth, admin, etc.)",
                required=False,
                type=OpenApiTypes.BOOL,
            ),
            OpenApiParameter(
                name="app",
                description="Filter by specific application label (e.g. 'infrastructure', 'users')",
                required=False,
                type=OpenApiTypes.STR,
            ),
        ],
        examples=[
            OpenApiExample(
                "Apps & Models Response Example",
                summary="Standard apps and models payload",
                description="Example response showing apps, metadata, and models dictionary.",
                value={
                    "apps": [
                        {
                            "app_label": "users",
                            "verbose_name": "Users",
                            "models": [
                                {
                                    "app_label": "users",
                                    "model_name": "user",
                                    "object_name": "User",
                                    "verbose_name": "user",
                                    "verbose_name_plural": "users",
                                    "db_table": "monitor_users",
                                },
                                {
                                    "app_label": "users",
                                    "model_name": "mainaddress",
                                    "object_name": "MainAddress",
                                    "verbose_name": "main address",
                                    "verbose_name_plural": "main addresss",
                                    "db_table": "monitor_main_addresses",
                                },
                            ],
                        },
                        {
                            "app_label": "infrastructure",
                            "verbose_name": "Infrastructure",
                            "models": [
                                {
                                    "app_label": "infrastructure",
                                    "model_name": "device",
                                    "object_name": "Device",
                                    "verbose_name": "device",
                                    "verbose_name_plural": "devices",
                                    "db_table": "monitor_devices",
                                }
                            ],
                        },
                    ],
                    "models_by_app": {
                        "users": ["User", "MainAddress", "BillingAddress", "OAuthAccount"],
                        "infrastructure": ["Machine", "Type", "Application", "Activation", "Device", "Location", "Gateway", "Measurements"],
                    },
                    "all_models": [
                        {
                            "app_label": "users",
                            "model_name": "user",
                            "object_name": "User",
                            "verbose_name": "user",
                            "verbose_name_plural": "users",
                            "db_table": "monitor_users",
                        }
                    ],
                    "total_apps": 2,
                    "total_models": 5,
                },
                response_only=True,
            )
        ],
        responses={200: AppsModelsResponseSerializer},
    )
    def get(self, request, *args, **kwargs):
        include_all = request.query_params.get("include_all", "").lower() in ("true", "1", "yes")
        app_filter = request.query_params.get("app", "").strip().lower()

        apps_list = []
        models_by_app = {}
        all_models = []

        all_app_configs = list(apps.get_app_configs())

        for app_config in all_app_configs:
            app_label = app_config.label

            # Filter by specific app if provided
            if app_filter and app_label.lower() != app_filter:
                continue

            # Filter out non-platform apps unless include_all is requested
            if not include_all and not app_filter and app_label not in PLATFORM_PROJECT_APPS:
                continue

            app_models = list(app_config.get_models())
            if not app_models:
                continue

            model_details = []
            model_names = []

            for model in app_models:
                meta = model._meta
                m_info = {
                    "app_label": app_label,
                    "model_name": meta.model_name,
                    "object_name": meta.object_name,
                    "verbose_name": str(meta.verbose_name),
                    "verbose_name_plural": str(meta.verbose_name_plural),
                    "db_table": meta.db_table,
                }
                model_details.append(m_info)
                model_names.append(meta.object_name)
                all_models.append(m_info)

            app_info = {
                "app_label": app_label,
                "verbose_name": str(app_config.verbose_name),
                "models": model_details,
            }
            apps_list.append(app_info)
            models_by_app[app_label] = model_names

        response_data = {
            "apps": apps_list,
            "models_by_app": models_by_app,
            "all_models": all_models,
            "total_apps": len(apps_list),
            "total_models": len(all_models),
        }

        return Response(response_data, status=status.HTTP_200_OK)


class SystemHealthView(APIView):
    """
    Comprehensive platform healthcheck endpoint providing the status of Atlas services
    (database, storage/R2, email/Mailgun, ChirpStack, Firebase) and Hermes service.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["System - Health"],
        summary="Overall Platform Healthcheck",
        description=(
            "Performs real-time health checks on all platform components:\n"
            "- **Atlas Database**: PostgreSQL connectivity and query latency\n"
            "- **Atlas Storage**: Cloudflare R2 / S3 bucket reachability or local filesystem status\n"
            "- **Atlas Email**: Mailgun API connectivity and domain status\n"
            "- **ChirpStack Integration**: REST API connectivity and authentication\n"
            "- **Firebase Admin SDK**: Credentials configuration\n"
            "- **Hermes Real-Time Service**: HTTP API health, MongoDB, Redis, WebSockets, and MQTT status"
        ),
        parameters=[
            OpenApiParameter(
                name="fail_on_error",
                description="When true, returns HTTP 503 if the core database or system is unhealthy",
                required=False,
                type=OpenApiTypes.BOOL,
            )
        ],
        examples=[
            OpenApiExample(
                "System Health Response Example",
                summary="Healthy platform state",
                value={
                    "status": "healthy",
                    "timestamp": "2026-08-14T18:00:00Z",
                    "version": "1.2.0",
                    "services": {
                        "atlas": {
                            "status": "healthy",
                            "database": {
                                "status": "healthy",
                                "latency_ms": 1.2,
                                "engine": "postgresql",
                                "database": "appdb",
                                "host": "localhost",
                            },
                            "storage": {
                                "enabled": True,
                                "backend": "s3_r2",
                                "status": "healthy",
                                "bucket": "monitor-media",
                                "endpoint_url": "https://account.r2.cloudflarestorage.com",
                                "custom_domain": "https://pub-cdn.dev",
                                "latency_ms": 15.4,
                            },
                            "email": {
                                "configured": True,
                                "status": "healthy",
                                "domain": "mail.example.com",
                                "domain_state": "active",
                                "latency_ms": 45.2,
                            },
                            "chirpstack": {
                                "configured": True,
                                "status": "healthy",
                                "base_url": "http://localhost:8090/api",
                                "latency_ms": 8.6,
                            },
                            "firebase": {
                                "configured": True,
                                "status": "healthy",
                                "credentials_path": "firebase-credentials.json",
                                "file_exists": True,
                            },
                        },
                        "hermes": {
                            "configured": True,
                            "status": "healthy",
                            "api_url": "http://localhost:5000",
                            "ws_url": "ws://localhost:5000",
                            "latency_ms": 3.4,
                            "details": {
                                "status": "healthy",
                                "service": "Monitor_Hermes",
                                "timestamp": "2026-08-14T18:00:00Z",
                                "components": {
                                    "database": {"status": "healthy", "latency_ms": 0.8},
                                    "redis": {"status": "healthy", "latency_ms": 0.5},
                                    "websockets": {
                                        "status": "healthy",
                                        "active_tenants": 3,
                                        "tenant_connections": 12,
                                        "global_connections": 2,
                                        "super_connections": 1,
                                        "total_connections": 15,
                                        "device_subscriptions": 8,
                                    },
                                    "mqtt": {
                                        "status": "connected",
                                        "broker": "localhost",
                                        "port": 1883,
                                    },
                                },
                            },
                        },
                    },
                },
                response_only=True,
            )
        ],
        responses={
            200: SystemHealthResponseSerializer,
            503: SystemHealthResponseSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        report = get_system_health_report()
        fail_on_error = request.query_params.get("fail_on_error", "").lower() in ("true", "1", "yes")
        http_status = status.HTTP_200_OK
        if fail_on_error and report.get("status") == "unhealthy":
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE

        return Response(report, status=http_status)


class HermesHealthView(APIView):
    """
    Focused healthcheck endpoint specifically querying and verifying the Hermes real-time service.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["System - Health"],
        summary="Hermes Service Healthcheck",
        description="Queries Hermes HTTP API health endpoint to verify connectivity and retrieve MongoDB, Redis, WebSockets, and MQTT status.",
        examples=[
            OpenApiExample(
                "Hermes Health Response Example",
                summary="Hermes service status response",
                value={
                    "configured": True,
                    "status": "healthy",
                    "api_url": "http://localhost:5000",
                    "ws_url": "ws://localhost:5000",
                    "latency_ms": 3.2,
                    "details": {
                        "status": "healthy",
                        "service": "Monitor_Hermes",
                        "timestamp": "2026-08-14T18:00:00Z",
                        "components": {
                            "database": {"status": "healthy", "latency_ms": 0.8},
                            "redis": {"status": "healthy", "latency_ms": 0.5},
                            "websockets": {"status": "healthy", "total_connections": 10},
                            "mqtt": {"status": "connected", "broker": "localhost", "port": 1883},
                        },
                    },
                },
                response_only=True,
            )
        ],
        responses={200: HermesHealthSerializer},
    )
    def get(self, request, *args, **kwargs):
        hermes_health = check_hermes_health()
        return Response(hermes_health, status=status.HTTP_200_OK)


class AtlasHealthView(APIView):
    """
    Focused healthcheck endpoint verifying internal Atlas platform services (DB, R2, Mailgun, ChirpStack, Firebase).
    """

    permission_classes = [AllowAny]

    @extend_schema(
        tags=["System - Health"],
        summary="Atlas Services Healthcheck",
        description="Checks internal Atlas services: PostgreSQL database, Cloudflare R2/Storage, Mailgun email service, ChirpStack, and Firebase Admin SDK.",
        examples=[
            OpenApiExample(
                "Atlas Health Response Example",
                summary="Atlas internal services status response",
                value={
                    "status": "healthy",
                    "database": {
                        "status": "healthy",
                        "latency_ms": 1.1,
                        "engine": "postgresql",
                        "database": "appdb",
                        "host": "localhost",
                    },
                    "storage": {
                        "enabled": True,
                        "backend": "s3_r2",
                        "status": "healthy",
                        "bucket": "my-bucket",
                        "latency_ms": 12.0,
                    },
                    "email": {
                        "configured": True,
                        "status": "healthy",
                        "domain": "mg.example.com",
                        "latency_ms": 40.0,
                    },
                    "chirpstack": {
                        "configured": True,
                        "status": "healthy",
                        "base_url": "http://localhost:8090/api",
                        "latency_ms": 6.5,
                    },
                    "firebase": {
                        "configured": True,
                        "status": "healthy",
                        "file_exists": True,
                    },
                },
                response_only=True,
            )
        ],
        responses={200: AtlasServicesHealthSerializer},
    )
    def get(self, request, *args, **kwargs):
        atlas_health = get_atlas_services_health()
        return Response(atlas_health, status=status.HTTP_200_OK)
