from django.contrib import admin
from .models import Role, WorkspaceMembership


class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ("id",)


admin.site.register(Role, RoleAdmin)
admin.site.register(WorkspaceMembership, WorkspaceMembershipAdmin)
