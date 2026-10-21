from django.db.models import Q


def get_pass_workspace_ids(user):
    """
    Return the workspace IDs where the user holds an active, unexpired hall pass.
    """
    from django.utils import timezone
    from support.models import SupportHallPass

    if not user or not user.is_authenticated:
        return []

    return list(
        SupportHallPass.objects.filter(
            technician=user,
            status__in=["ACTIVE", "active"],
            expires_at__gt=timezone.now(),
        )
        .values_list("workspace_id", flat=True)
        .distinct()
    )


def get_pass_aware_queryset(user, model, request, base_queryset=None):
    """
    Combine Guardian object-permission results with objects that live in
    workspaces where the user holds an active hall pass.

    The hall pass is the authority for pass-covered workspaces: no Guardian
    rows are created when a pass is granted, so they must be unioned in here.
    """
    from guardian.shortcuts import get_objects_for_user

    if base_queryset is None:
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        base_queryset = get_objects_for_user(
            user,
            f"{app_label}.view_{model_name}",
            klass=model,
            accept_global_perms=False,
        )

    pass_workspace_ids = get_pass_workspace_ids(user)
    if pass_workspace_ids:
        pass_queryset = model.objects.filter(workspace_id__in=pass_workspace_ids)
        base_queryset = (base_queryset | pass_queryset).distinct()

    return base_queryset
