from organizations.models import Tenant
from guardian.shortcuts import assign_perm
from django.contrib.auth.models import Group

MONITOR_TENANT = Tenant.objects.filter(is_global=True).first()

GLOBAL_ROLES = ["admin", "manager", "technician", "viewer"]
GROUP_PREFIX = "global_"

# Global permissions preset

GLOBAL_PERMISSIONS_PRESET = {
    "admin": {
        "organizations": ["tenant", "workspace"],
        "infrastructure": [
            "device",
            "gateway",
            "location",
            "application",
            "machine",
            "type",
        ],
        "roles": [
            "role",
            "workspacemembership",
        ],
        "users": ["user"],
        "chirpstack": [
            "deviceprofile",
            "apiuser",
        ],
    },
    "manager": {
        "organizations": [
            "tenant",
            "workspace",
        ],
        "roles": [
            "role",
            "workspacemembership",
        ],
        "users": ["user"],
    },
    "technician": {
        "infrastructure": [
            "device",
            "gateway",
            "application",
            "machine",
            "type",
        ],
        "chirpstack": [
            "deviceprofile",
            "apiuser",
        ],
    },
    "viewer": {
        "organizations": ["tenant", "workspace"],
    },
}


# Helper functions for global roles and permissions
def set_base_global_add_permissions():
    admin_models = GLOBAL_PERMISSIONS_PRESET["admin"]
    manager_models = GLOBAL_PERMISSIONS_PRESET["manager"]
    technician_models = GLOBAL_PERMISSIONS_PRESET["technician"]

    for role in GLOBAL_ROLES:
        if role == "admin":
            group = Group.objects.get_or_create(name=GROUP_PREFIX + "admin")[0]
            for app in admin_models:
                for model in admin_models[app]:
                    assign_perm(f"{app}.add_{model}", group)

        if role == "manager":
            group = Group.objects.get_or_create(name=GROUP_PREFIX + "manager")[0]
            for app in manager_models:
                for model in manager_models[app]:
                    assign_perm(f"{app}.add_{model}", group)

        if role == "technician":
            group = Group.objects.get_or_create(name=GROUP_PREFIX + "technician")[0]
            for app in technician_models:
                for model in technician_models[app]:
                    assign_perm(f"{app}.add_{model}", group)


def apply_staff_permissions(obj):
    model = obj.__class__.__name__.lower()

    global_admin = Group.objects.get(name=GROUP_PREFIX + "admin")
    global_manager = Group.objects.get(name=GROUP_PREFIX + "manager")
    global_technician = Group.objects.get(name=GROUP_PREFIX + "technician")

    admin_models = GLOBAL_PERMISSIONS_PRESET["admin"]
    manager_models = GLOBAL_PERMISSIONS_PRESET["manager"]
    technician_models = GLOBAL_PERMISSIONS_PRESET["technician"]
    read_only_models = GLOBAL_PERMISSIONS_PRESET["viewer"]

    for app, models in admin_models.items():
        if model in models:
            for perm in ["view", "change", "delete"]:
                assign_perm(f"{perm}_{model}", global_admin, obj)

    for app, models in manager_models.items():
        if model in models:
            for perm in ["view", "change"]:
                assign_perm(f"{perm}_{model}", global_manager, obj)
    for app, models in technician_models.items():
        if model in models:
            for perm in ["view", "change"]:
                assign_perm(f"{perm}_{model}", global_technician, obj)

    for app, models in read_only_models.items():
        if model in models:
            for perm in ["view"]:
                assign_perm(f"{perm}_{model}", global_admin, obj)
                assign_perm(f"{perm}_{model}", global_manager, obj)
                assign_perm(f"{perm}_{model}", global_technician, obj)
    return
