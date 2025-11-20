from .models import Notification
from .models import SupportMembership


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


def is_support_member(user) -> bool:
    """Check if the user is a member of the support team.

    Keyword arguments:
        user -- the user to check membership for
    Returns:
        bool -- True if the user is a support team member, False otherwise
    """
    if user:
        return SupportMembership.objects.filter(user=user).exists()
    return False
