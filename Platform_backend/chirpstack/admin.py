from django.contrib import admin
from .models import DeviceProfile, DeviceProfileTemplate, ApiUser, TenantUser

class DeviceProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class DeviceProfileTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class ApiUserAdmin(admin.ModelAdmin):
    list_display = ('api_id', 'email')

class TenantUserAdmin(admin.ModelAdmin):
    list_display = ('api_id', 'user')


admin.site.register(DeviceProfile, DeviceProfileAdmin)
admin.site.register(DeviceProfileTemplate, DeviceProfileTemplateAdmin)
admin.site.register(ApiUser, ApiUserAdmin)
admin.site.register(TenantUser, TenantUserAdmin)


# Register your models here.
