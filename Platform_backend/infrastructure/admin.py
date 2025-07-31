from django.contrib import admin
from .models import Gateway, Machine, NodeType, Node, Service

class GatewayAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
class MachineAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
class NodeTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
class NodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    
admin.site.register(Gateway, GatewayAdmin)
admin.site.register(Machine, MachineAdmin)
admin.site.register(NodeType, NodeTypeAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(Service, ServiceAdmin)