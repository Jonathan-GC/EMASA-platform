from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from loguru import logger
from auditlog.models import LogEntry

from users.models import User
from organizations.models import Tenant, Workspace
from organizations.helpers import get_or_create_default_workspace, get_no_role
from roles.models import WorkspaceMembership
from roles.helpers import (
    revoke_user_tenant_permissions,
    assign_new_user_base_permissions,
)
from chirpstack.models import ApiUser
from chirpstack.chirpstack_api import sync_api_user_update


class UserTenantTransferService:
    """
    Service that orchestrates the atomic transfer of a user account from a
    source tenant to a destination tenant, purging old permissions, establishing
    default workspace roles, synchronizing external ChirpStack records, and
    recording an immutable audit log entry.
    """

    @classmethod
    def transfer_user(
        cls, user: User, destination_tenant: Tenant, actor: User = None
    ) -> dict:
        """
        Atomically migrates user to destination tenant, revokes prior permissions,
        assigns default workspace with "Sin rol", syncs ChirpStack ApiUser, and records audit log.

        Args:
            user (User): The user to transfer.
            destination_tenant (Tenant): The destination tenant.
            actor (User): The administrator performing the transfer.

        Returns:
            dict: Transfer outcome summary with status, user_id, tenant_id, chirpstack_synced, and audit_log_id.

        Raises:
            ValidationError: If pre-conditions are violated.
            Exception: Re-raised on unexpected database errors to guarantee atomic rollback.
        """
        if not user:
            raise ValidationError("Target user must be provided.")
        if not destination_tenant:
            raise ValidationError("Destination tenant must be provided.")

        source_tenant = user.tenant
        if source_tenant and str(source_tenant.id) == str(destination_tenant.id):
            raise ValidationError("Source and destination tenants cannot be identical.")

        with transaction.atomic():
            # 1. Purge all permissions, memberships, and groups from source tenant
            if source_tenant:
                revoke_user_tenant_permissions(user, source_tenant)

            # 2. Update user tenant affiliation
            user.tenant = destination_tenant
            user.save(update_fields=["tenant"])

            # 3. Retrieve destination default workspace and assign default "Sin rol"
            default_workspace = get_or_create_default_workspace(destination_tenant)
            default_role = get_no_role(default_workspace)
            WorkspaceMembership.objects.create(
                workspace=default_workspace,
                user=user,
                role=default_role,
            )

            # 4. Initialize base user permissions for new tenant
            assign_new_user_base_permissions(user)

            # 5. External ChirpStack ApiUser synchronization
            api_user = ApiUser.objects.filter(email=user.email).first()
            chirpstack_synced = None
            if api_user:
                api_user.workspace = default_workspace
                api_user.save(update_fields=["workspace"])
                try:
                    sync_response = sync_api_user_update(api_user)
                    api_user.refresh_from_db()
                    chirpstack_synced = api_user.sync_status == "SYNCED"
                except Exception as cs_err:
                    logger.error(
                        f"ChirpStack sync error during transfer of user {user.username}: {cs_err}"
                    )
                    api_user.sync_status = "ERROR"
                    api_user.sync_error = str(cs_err)
                    api_user.save(update_fields=["sync_status", "sync_error"])
                    chirpstack_synced = False

            # 6. Record immutable audit log entry in django-auditlog
            user_content_type = ContentType.objects.get_for_model(User)
            source_tenant_id = str(source_tenant.id) if source_tenant else None
            source_tenant_name = source_tenant.name if source_tenant else None
            dest_tenant_id = str(destination_tenant.id)
            dest_tenant_name = destination_tenant.name

            log_entry = LogEntry.objects.create(
                content_type=user_content_type,
                object_pk=str(user.pk),
                object_repr=str(user),
                action=LogEntry.Action.UPDATE,
                actor=actor,
                changes={
                    "tenant": [source_tenant_name, dest_tenant_name],
                    "tenant_id": [source_tenant_id, dest_tenant_id],
                },
                additional_data={
                    "action_detail": "transfer_tenant",
                    "transfer_type": "tenant_membership_transfer",
                    "source_tenant_id": source_tenant_id,
                    "source_tenant_name": source_tenant_name,
                    "destination_tenant_id": dest_tenant_id,
                    "destination_tenant_name": dest_tenant_name,
                    "target_user_id": str(user.id),
                    "target_username": user.username,
                    "actor_id": str(actor.id) if actor else None,
                    "actor_username": actor.username if actor else None,
                },
            )

        return {
            "status": "success",
            "user_id": str(user.id),
            "tenant_id": str(destination_tenant.id),
            "chirpstack_synced": chirpstack_synced,
            "audit_log_id": log_entry.id,
        }
