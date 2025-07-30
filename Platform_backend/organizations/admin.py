from django.contrib import admin
from .models import Workspace, Organization, Region

class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(Organization)
admin.site.register(Region)
