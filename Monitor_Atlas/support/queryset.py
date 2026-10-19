from django.db.models import Q


def get_pass_aware_queryset(user, model, request, base_queryset=None):
    """
    Build a queryset that unions Guardian-object-permission results with
    objects from workspaces where the user has an active hall pass.

    Must be applied on top of get_objects_for_user (never on raw Model.objects.all()),
    so permission filtering is never bypassed.
    """
    from guardian.shortcuts import get_objects_for_user
    from support.models import SupportHallPass
    from django.utils import timezone

    if base_queryset is None:
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        base_queryset = get_objects_for_user(
            user,
            f"{app_label}.view_{model_name}",
            klass=model,
            accept_global_perms=False,
        )

    # Collect workspace IDs from active hall passes
    active_passes = SupportHallPass.objects.filter(
        technician=user,
        status__in=["ACTIVE", "active"],
        expires_at__gt=timezone.now(),
    )

    pass_workspace_ids = list(
        active_passes.values_list("workspace_id", flat=True).distinct()
    )

    if pass_workspace_ids:
        pass_queryset = model.objects.filter(workspace_id__in=pass_workspace_ids)
        base_queryset = base_queryset.union(pass_queryset)

    return base_queryset


def get_pass_workspace_ids(user):
    """
    Return a list of workspace IDs where the user has an active hall pass.
    """
    from support.models import SupportHallPass
    from django.utils import timezone

    return list(
        SupportHallPass.objects.filter(
            technician=user,
            status__in=["ACTIVE", "active"],
            expires_at__gt=timezone.now(),
        )
        .values_list("workspace_id", flat=True)
        .distinct()
    )
