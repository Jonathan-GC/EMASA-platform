from guardian.shortcuts import get_users_with_perms

from infrastructure.models import Device
from users.models import User


def get_users_for_device(dev_eui):
    device = Device.objects.filter(dev_eui=dev_eui).first()
    if not device:
        raise ValueError(f"Device with dev_eui '{dev_eui}' not found.")

    users = get_users_with_perms(device, only_with_perms_in=["view_device"])
    superuser = User.objects.filter(is_superuser=True).first()

    result = list(users)

    if superuser and superuser not in users:
        result.append(superuser)

    if not result:
        raise ValueError(
            f"No users found with permission to view device '{dev_eui}'."
        )

    return result
