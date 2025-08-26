from django.contrib import admin
from .models import DeviceProfile, DeviceProfileTemplate, ApiUser

class DeviceProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class DeviceProfileTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

class ApiUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email')


admin.site.register(DeviceProfile, DeviceProfileAdmin)
admin.site.register(DeviceProfileTemplate, DeviceProfileTemplateAdmin)
admin.site.register(ApiUser, ApiUserAdmin)


# Register your models here.
