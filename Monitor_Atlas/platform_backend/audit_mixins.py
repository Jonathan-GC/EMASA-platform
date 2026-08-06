from auditlog.context import set_extra_data


class AuditActionMixin:
    """
    Mixin for DRF ViewSets to automatically record the active DRF view/action name
    and extra context into django-auditlog's additional_data JSON context field.
    """

    def dispatch(self, request, *args, **kwargs):
        # Determine the action name from DRF's action property or HTTP method
        action_name = getattr(self, "action", None) or request.method.lower()
        
        context_data = {
            "additional_data": {"action_detail": action_name}
        }
        if hasattr(request, "user") and request.user.is_authenticated:
            context_data["actor"] = request.user

        with set_extra_data(context_data):
            return super().dispatch(request, *args, **kwargs)
