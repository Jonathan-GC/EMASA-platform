from .models import SupportMembership


def is_support_member(user) -> bool:
    """Check if the user is a member of the support team.

    Keyword arguments:
        user -- the user to check membership for
    Returns:
        bool -- True if the user is a support team member, False otherwise
    """
    if user:
        return SupportMembership.objects.filter(user=user.id).exists()
    return False
