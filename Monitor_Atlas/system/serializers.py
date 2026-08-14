from rest_framework import serializers


class ModelDetailSerializer(serializers.Serializer):
    app_label = serializers.CharField(help_text="The Django app label containing this model.")
    model_name = serializers.CharField(help_text="Lowercased model name (e.g., 'user', 'device').")
    object_name = serializers.CharField(help_text="PascalCase Python class name of the model (e.g., 'User', 'Device').")
    verbose_name = serializers.CharField(help_text="Human-readable singular name.")
    verbose_name_plural = serializers.CharField(help_text="Human-readable plural name.")
    db_table = serializers.CharField(help_text="Underlying database table name.")


class AppDetailSerializer(serializers.Serializer):
    app_label = serializers.CharField(help_text="Unique label of the application (e.g., 'users', 'infrastructure').")
    verbose_name = serializers.CharField(help_text="Human-readable name of the application.")
    models = ModelDetailSerializer(many=True, help_text="List of models belonging to this app.")


class AppsModelsResponseSerializer(serializers.Serializer):
    apps = AppDetailSerializer(many=True, help_text="List of registered applications and their model details.")
    models_by_app = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
        help_text="Dictionary mapping app labels to lists of model class names.",
    )
    all_models = ModelDetailSerializer(many=True, help_text="Flat list of all models across apps.")
    total_apps = serializers.IntegerField(help_text="Total number of apps returned.")
    total_models = serializers.IntegerField(help_text="Total number of models returned.")


class ComponentHealthSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Health status ('healthy', 'unhealthy', 'degraded', 'not_configured').")
    latency_ms = serializers.FloatField(required=False, help_text="Round-trip latency in milliseconds.")
    error = serializers.CharField(required=False, help_text="Error message if unhealthy.")


class DatabaseHealthSerializer(ComponentHealthSerializer):
    engine = serializers.CharField(required=False, help_text="Database engine (e.g., 'postgresql').")
    database = serializers.CharField(required=False, help_text="Database name.")
    host = serializers.CharField(required=False, help_text="Database host.")


class StorageHealthSerializer(ComponentHealthSerializer):
    enabled = serializers.BooleanField(help_text="Whether R2 cloud storage is enabled.")
    backend = serializers.CharField(help_text="Storage backend type ('s3_r2' or 'filesystem').")
    bucket = serializers.CharField(required=False, help_text="R2 bucket name if enabled.")
    endpoint_url = serializers.CharField(required=False, help_text="R2 endpoint URL if enabled.")
    custom_domain = serializers.CharField(required=False, help_text="R2 custom domain if enabled.")
    media_root_writable = serializers.BooleanField(required=False, help_text="Whether local media root is writable.")


class MailgunHealthSerializer(ComponentHealthSerializer):
    configured = serializers.BooleanField(help_text="Whether Mailgun credentials are configured.")
    domain = serializers.CharField(required=False, help_text="Mailgun domain.")
    domain_state = serializers.CharField(required=False, help_text="State of the domain in Mailgun.")
    http_status = serializers.IntegerField(required=False, help_text="HTTP status code from Mailgun API.")


class ChirpstackHealthSerializer(ComponentHealthSerializer):
    configured = serializers.BooleanField(help_text="Whether ChirpStack integration is configured.")
    base_url = serializers.CharField(required=False, help_text="ChirpStack API base URL.")
    http_status = serializers.IntegerField(required=False, help_text="HTTP status code from ChirpStack API.")


class FirebaseHealthSerializer(ComponentHealthSerializer):
    configured = serializers.BooleanField(help_text="Whether Firebase Admin credentials are configured.")
    credentials_path = serializers.CharField(required=False, help_text="Path to credentials file.")
    file_exists = serializers.BooleanField(required=False, help_text="Whether credentials file exists on disk.")


class AtlasServicesHealthSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Overall status of Atlas services.")
    database = DatabaseHealthSerializer(help_text="PostgreSQL database health.")
    storage = StorageHealthSerializer(help_text="Cloudflare R2 / Local Storage health.")
    email = MailgunHealthSerializer(help_text="Mailgun email service health.")
    chirpstack = ChirpstackHealthSerializer(help_text="ChirpStack LoRaWAN server integration health.")
    firebase = FirebaseHealthSerializer(help_text="Firebase Admin SDK health.")


class HermesComponentsSerializer(serializers.Serializer):
    database = ComponentHealthSerializer(required=False, help_text="Hermes MongoDB status.")
    redis = ComponentHealthSerializer(required=False, help_text="Hermes Redis cache status.")
    websockets = serializers.DictField(required=False, help_text="Hermes WebSocket connection counts and stats.")
    mqtt = serializers.DictField(required=False, help_text="Hermes MQTT client connection status.")


class HermesHealthSerializer(serializers.Serializer):
    configured = serializers.BooleanField(help_text="Whether Hermes API URL is configured.")
    status = serializers.CharField(help_text="Status of Hermes service ('healthy', 'degraded', 'unhealthy', 'unreachable', 'not_configured').")
    api_url = serializers.CharField(required=False, help_text="Hermes HTTP API base URL.")
    ws_url = serializers.CharField(required=False, help_text="Hermes WebSocket URL.")
    latency_ms = serializers.FloatField(required=False, help_text="Round-trip latency to Hermes in milliseconds.")
    error = serializers.CharField(required=False, help_text="Error message if unreachable or error occurred.")
    details = serializers.DictField(required=False, help_text="Detailed component status from Hermes (MongoDB, Redis, WebSockets, MQTT).")


class PlatformServicesHealthSerializer(serializers.Serializer):
    atlas = AtlasServicesHealthSerializer(help_text="Atlas core internal services.")
    hermes = HermesHealthSerializer(help_text="Hermes real-time WebSocket & event service.")


class SystemHealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField(help_text="Overall system status ('healthy', 'degraded', 'unhealthy').")
    timestamp = serializers.DateTimeField(help_text="ISO 8601 UTC timestamp of the health check.")
    version = serializers.CharField(help_text="Platform API version.")
    services = PlatformServicesHealthSerializer(help_text="Breakdown of Atlas and Hermes services.")
