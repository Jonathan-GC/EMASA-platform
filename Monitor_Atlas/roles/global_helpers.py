from organizations.models import Tenant

MONITOR_TENANT = Tenant.objects.filter(is_global=True).first()

GLOBAL_ROLES = ["admin", "manager", "technician", "viewer"]

# Global scope
