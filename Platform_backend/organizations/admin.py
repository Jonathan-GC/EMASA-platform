from django.contrib import admin

from .models import Workspace, Tenant, Subscription

class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'tenant')

class TenantAdmin(admin.ModelAdmin):
    list_display = ('name',)

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Workspace, WorkspaceAdmin)
admin.site.register(Tenant, TenantAdmin)
admin.site.register(Subscription, SubscriptionAdmin)