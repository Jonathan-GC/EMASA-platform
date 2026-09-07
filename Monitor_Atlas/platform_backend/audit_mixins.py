import contextvars
from django.db.models.signals import pre_save
from django.dispatch import receiver
from auditlog.models import LogEntry

_current_audit_context = contextvars.ContextVar("_current_audit_context", default={})


@receiver(pre_save, sender=LogEntry)
def populate_auditlog_action_detail(sender, instance, **kwargs):
    ctx = _current_audit_context.get()
    if not ctx:
        return
    if instance.additional_data is None:
        instance.additional_data = {}
    for k, v in ctx.items():
        if k != "actor" and k not in instance.additional_data:
            instance.additional_data[k] = v
    if not instance.actor and ctx.get("actor"):
        instance.actor = ctx["actor"]



class AuditActionMixin:
    """
    Mixin for DRF ViewSets to automatically record the active DRF view/action name
    and extra context into django-auditlog's additional_data JSON context field.
    """

    def dispatch(self, request, *args, **kwargs):
        action_name = (
            getattr(self, "action", None)
            or getattr(self, "action_map", {}).get(request.method.lower())
            or request.method.lower()
        )
        actor = request.user if hasattr(request, "user") and request.user.is_authenticated else None
        token = _current_audit_context.set({
            "action_detail": action_name,
            "actor": actor,
        })
        try:
            return super().dispatch(request, *args, **kwargs)
        finally:
            _current_audit_context.reset(token)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        ctx = dict(_current_audit_context.get())
        if hasattr(request, "user") and request.user.is_authenticated:
            ctx["actor"] = request.user
        action_name = getattr(self, "action", None) or ctx.get("action_detail")
        if action_name:
            ctx["action_detail"] = action_name
        _current_audit_context.set(ctx)

