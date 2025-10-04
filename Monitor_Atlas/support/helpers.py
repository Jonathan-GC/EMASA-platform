from .models import Notification


def notify_user(title: str, message: str, type: str, user):
    """Send a notification to a user.

    Keyword arguments:
        title -- the title of the notification
        message -- the message content of the notification
        type -- the type/category of the notification choices are 'info', 'warning', 'error', 'success'
        user -- the user to whom the notification is sent
    """
    notification = Notification.objects.create(
        title=title, message=message, type=type, user=user
    )
    notification.notify_ws()
