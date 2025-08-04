from django.contrib import admin
from .models import Role, WorkspaceMembership, PermissionKey, RolePermission

class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ('id',)

class PermissionKeyAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'scope', 'key_type')

class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('id',)

admin.site.register(Role, RoleAdmin)
admin.site.register(WorkspaceMembership, WorkspaceMembershipAdmin)
admin.site.register(PermissionKey, PermissionKeyAdmin)
admin.site.register(RolePermission, RolePermissionAdmin)