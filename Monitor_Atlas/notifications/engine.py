from django.db.models import QuerySet

from loguru import logger

from .models import FCMDevice, Notification, NotificationSettings

import firebase_admin
from firebase_admin import messaging


class NotificationsEngine:
    @staticmethod
    def send_notification(users, title, message, type, topic, extra_data=None):
        if not users:
            return {"notified": 0, "skipped": 0, "invalid_tokens_cleaned": 0}

        opted_in_users = _filter_users_by_topic_preferences(users, topic)

        if not opted_in_users:
            logger.debug(f"All users skipped for topic '{topic}' due to preferences")
            return {"notified": 0, "skipped": len(users), "invalid_tokens_cleaned": 0}

        _persist_notifications(opted_in_users, title, message, type, topic)

        tokens = _fetch_active_tokens(opted_in_users)

        if not tokens:
            logger.debug("No active FCM tokens found for opted-in users")
            return {
                "notified": 0,
                "skipped": len(users) - len(opted_in_users),
                "invalid_tokens_cleaned": 0,
            }

        cleaned_count = _dispatch_fcm(tokens, title, message, type, topic, extra_data)

        return {
            "notified": len(opted_in_users),
            "skipped": len(users) - len(opted_in_users),
            "invalid_tokens_cleaned": cleaned_count,
        }


def _filter_users_by_topic_preferences(users, topic):
    if not isinstance(users, QuerySet):
        from users.models import User
        user_ids = [u.id if hasattr(u, "id") else u for u in users]
        users = User.objects.filter(id__in=user_ids)

    user_ids = list(users.values_list("id", flat=True))

    prefs = NotificationSettings.objects.filter(user_id__in=user_ids)
    prefs_map = {p.user_id: p.topic_preferences for p in prefs}

    opted_in = []
    for user in users:
        prefs = prefs_map.get(user.id, {})
        if prefs.get(topic, True):
            opted_in.append(user)

    return opted_in


def _persist_notifications(users, title, message, type, topic):
    notifications = [
        Notification(
            title=title,
            message=message,
            type=type,
            topic=topic,
            user=user,
        )
        for user in users
    ]
    Notification.objects.bulk_create(notifications)
    logger.debug(f"Persisted {len(notifications)} notification records")


def _fetch_active_tokens(users):
    user_ids = [u.id for u in users]
    devices = FCMDevice.objects.filter(user_id__in=user_ids, is_active=True)
    return list(devices.values("id", "fcm_token", "user_id"))


def _dispatch_fcm(tokens, title, message, type, topic, extra_data):
    if not firebase_admin._apps:
        logger.warning("Firebase not initialized; skipping FCM dispatch")
        return 0

    android_config = messaging.AndroidConfig(
        priority="high",
        notification=messaging.AndroidNotification(
            channel_id=type if type in ("warning", "error") else "info",
        ),
    )

    apns_config = messaging.APNSConfig(
        payload=messaging.APNSPayload(
            aps=messaging.Aps(sound="default"),
        ),
    )

    fcm_messages = []
    for token_info in tokens:
        msg = messaging.Message(
            token=token_info["fcm_token"],
            notification=messaging.Notification(title=title, body=message),
            data={
                "type": type,
                "topic": topic,
                **(extra_data or {}),
            },
            android=android_config,
            apns=apns_config,
        )
        fcm_messages.append(msg)

    response = messaging.send_each(fcm_messages)

    invalid_token_ids = set()
    for idx, resp in enumerate(response.responses):
        if not resp.success:
            exc = resp.exception
            if exc is not None:
                try:
                    from firebase_admin.exceptions import NotFoundError
                    if isinstance(exc, NotFoundError):
                        invalid_token_ids.add(tokens[idx]["id"])
                        continue
                except ImportError:
                    pass
                logger.warning(
                    f"FCM send failed for token {tokens[idx]['fcm_token'][:20]}...: {exc}"
                )

    if invalid_token_ids:
        FCMDevice.objects.filter(id__in=invalid_token_ids).update(is_active=False)
        logger.info(f"Deactivated {len(invalid_token_ids)} invalid FCM tokens")

    return len(invalid_token_ids)
