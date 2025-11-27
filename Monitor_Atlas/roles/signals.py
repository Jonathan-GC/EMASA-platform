from django.db.models.signals import pre_delete
from django.dispatch import receiver
from guardian.models import GroupObjectPermission


@receiver(pre_delete)
def revoke_permissions_on_delete(sender, instance, **kwargs):
    """
    Signal to revoke all object-level permissions associated with a Role's group
    before the Role is deleted.
    """
    if not hasattr(instance, "_meta") or not instance._meta.permissions:
        return

    from django.contrib.contenttypes.models import ContentType

    content_type = ContentType.objects.get_for_model(instance)

    GroupObjectPermission.objects.filter(
        content_type=content_type, object_pk=instance.pk
    ).delete()
