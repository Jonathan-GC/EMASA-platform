from django.contrib import admin

from .models import PassScope, SupportHallPass, TechnicianAssignment


@admin.register(PassScope)
class PassScopeAdmin(admin.ModelAdmin):
    list_display = ("code", "label")
    search_fields = ("code", "label")


@admin.register(SupportHallPass)
class SupportHallPassAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "technician",
        "ticket",
        "workspace",
        "permission_level",
        "status",
        "granted_by",
        "expires_at",
    )
    list_filter = ("status", "permission_level", "workspace")
    search_fields = ("id", "technician__username", "ticket__title", "workspace__name")
    readonly_fields = ("id", "granted_at", "upgraded_at", "revoked_at")
    filter_horizontal = ("scopes",)


@admin.register(TechnicianAssignment)
class TechnicianAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "technician", "ticket", "workspace", "status", "expires_at")
    list_filter = ("status", "workspace")
    search_fields = ("id", "technician__username", "ticket__title", "workspace__name")
    readonly_fields = ("id", "granted_at")
