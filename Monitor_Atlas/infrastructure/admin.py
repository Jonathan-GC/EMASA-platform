from django.contrib import admin
from .models import Gateway, Machine, Type, Device, Application

class GatewayAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
class MachineAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
class TypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
admin.site.register(Gateway, GatewayAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Application, ApplicationAdmin)