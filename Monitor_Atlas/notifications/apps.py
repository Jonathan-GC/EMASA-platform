from django.apps import AppConfig

import firebase_admin
from firebase_admin import credentials
from django.conf import settings


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_ADMIN_CREDENTIALS)
            firebase_admin.initialize_app(cred)

        import notifications.signals  # noqa
