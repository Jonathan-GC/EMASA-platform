from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User
from .models import NotificationSettings


@receiver(post_save, sender=User)
def create_notification_settings(sender, instance, created, **kwargs):
    if created:
        NotificationSettings.objects.get_or_create(
            user=instance,
            defaults={
                "topic_preferences": {
                    "alerts": True,
                    "updates": True,
                    "general": True,
                }
            },
        )
