# Plan de Migración: Permission Keys → Django Guardian

## Resumen
Migración del sistema custom de Permission Keys a Django Guardian para aprovechar permisos a nivel de objeto (object-level permissions) en un entorno multi-tenant, manteniendo el modelo `Role` existente y mapeándolo a grupos de Django.

---

## 1. Preparación del Entorno

### 1.1 Instalación de Django Guardian
- Instalar `django-guardian` en requirements.txt
- Agregar `'guardian'` a `INSTALLED_APPS` en settings.py
- Configurar backend de autenticación: `AUTHENTICATION_BACKENDS` con `ObjectPermissionBackend`
- Ejecutar migraciones de guardian: `python manage.py migrate`

### 1.2 Configuración Multi-tenant
- Establecer convención de nombres para grupos: `{tenant.name}_{role.name}` (identificador único)
- El campo `Role.name` será el nombre visible del grupo
- Mapeo 1:1 entre `Role` y `django.contrib.auth.models.Group`

---

## 2. Eliminación del Sistema de Permission Keys

### 2.1 Modelos a Eliminar
**Archivo:** `roles/models.py`
- Eliminar modelo `PermissionKey`
- Eliminar modelo `RolePermission`
- Mantener modelo `Role` (será adaptado)
- Mantener modelo `WorkspaceMembership`

### 2.2 Archivos a Eliminar/Refactorizar
- **roles/permissions.py**: Eliminar completamente las clases:
  - `has_permission()` function
  - `HasPermissionKey` class
  - Mantener `IsAdminOrIsAuthenticatedReadOnly` (actualizar si es necesario)
  
- **roles/mixins.py**: Eliminar completamente:
  - `PermissionKeyMixin` class
  - Todo el código relacionado con `create_permission_keys()`

- **roles/views.py**: 
  - Eliminar `PermissionKeyViewSet`
  - Eliminar `RolePermissionViewSet`
  - Actualizar `RoleViewSet` (remover referencia a `PermissionKeyMixin`)
  - Actualizar `WorkspaceMembershipViewSet` (remover referencia a `PermissionKeyMixin`)

- **roles/serializers.py**:
  - Eliminar `PermissionKeySerializer`
  - Eliminar `RolePermissionSerializer`

- **roles/urls.py**:
  - Eliminar rutas de `permission-keys` y `role-permissions`

### 2.3 Búsqueda y Reemplazo Global
Buscar en todo el proyecto y eliminar/reemplazar:
- `from roles.permissions import HasPermissionKey`
- `from roles.mixins import PermissionKeyMixin`
- `permission_classes = [HasPermissionKey]`
- `PermissionKeyMixin` en definiciones de clases
- Llamadas a `self.create_permission_keys()`

**Archivos a revisar:**
- `users/views.py` (UserViewSet, RegisterView)
- `infrastructure/views.py` (todos los ViewSets)
- `organizations/views.py` (WorkspaceViewSet, TenantViewSet, SubscriptionViewSet)
- `chirpstack/views.py` (DeviceProfileViewSet, DeviceProfileTemplateViewSet, ApiUserViewSet)

### 2.4 Migraciones de Base de Datos
- Crear migración para eliminar `PermissionKey` y `RolePermission`
- Como la BD está vacía, simplemente eliminar las tablas en la migración

---

## 3. Adaptación del Modelo Role para Django Guardian

### 3.1 Actualizar Modelo Role
**Archivo:** `roles/models.py`

Agregar/modificar:
```python
from django.contrib.auth.models import Group

class Role(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=20, default="#bfbfbf")
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Auto-crear grupo de Django al crear Role
        if not self.pk and not self.group:
            tenant = self.workspace.tenant
            group_identifier = f"{tenant.name}_{self.name}"
            group, created = Group.objects.get_or_create(
                name=group_identifier,
                defaults={'verbose_name': self.name}  # Si django-guardian lo soporta
            )
            self.group = group
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Eliminar grupo asociado al eliminar Role
        if self.group:
            self.group.delete()
        super().delete(*args, **kwargs)
```

### 3.2 Actualizar WorkspaceMembership
Agregar signal o override de save() para sincronizar usuarios con grupos:
```python
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    # Agregar usuario al grupo del role
    if self.role.group:
        self.user.groups.add(self.role.group)

def delete(self, *args, **kwargs):
    # Remover usuario del grupo
    if self.role.group:
        self.user.groups.remove(self.role.group)
    super().delete(*args, **kwargs)
```

---

## 4. Implementar Revocación de Permisos al Eliminar Objetos

### 4.1 Signal para Revocar Permisos
**Archivo:** `roles/signals.py` (crear)

```python
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from guardian.shortcuts import remove_obj_perms_for_group

@receiver(pre_delete)
def revoke_permissions_on_delete(sender, instance, **kwargs):
    """
    Revoca todos los permisos de grupos sobre un objeto antes de eliminarlo.
    """
    # Solo aplicar a modelos que tengan permisos de objeto
    if hasattr(instance, '_meta'):
        # Obtener todos los grupos con permisos sobre este objeto
        from django.contrib.auth.models import Group
        for group in Group.objects.all():
            remove_obj_perms_for_group(group, instance)
```

### 4.2 Registrar Signals
**Archivo:** `roles/apps.py`
```python
def ready(self):
    import roles.signals
```

### 4.3 Implementación por Modelo
Alternativamente, implementar `delete()` override en cada modelo crítico:
- Device
- Machine
- Application
- Gateway
- Workspace
- Tenant
- User
- etc.

---

## 5. Helpers para Asignación de Permisos

### 5.1 Crear Módulo de Utilidades
**Archivo:** `roles/guardian_helpers.py` (crear)

```python
from guardian.shortcuts import assign_perm, remove_perm
from django.contrib.contenttypes.models import ContentType

class PermissionManager:
    """
    Gestor centralizado para asignación de permisos con Django Guardian.
    """
    
    # Mapeo de scopes a permisos CRUD
    PERMISSION_MAP = {
        'device': ['view_device', 'add_device', 'change_device', 'delete_device'],
        'machine': ['view_machine', 'add_machine', 'change_machine', 'delete_machine'],
        'application': ['view_application', 'add_application', 'change_application', 'delete_application'],
        'gateway': ['view_gateway', 'add_gateway', 'change_gateway', 'delete_gateway'],
        'user': ['view_user', 'add_user', 'change_user', 'delete_user'],
        # ... agregar todos los modelos
    }
    
    @staticmethod
    def assign_permission(role, obj, permission_codename):
        """
        Asigna un permiso específico a un role (grupo) sobre un objeto.
        
        Args:
            role: Instancia de Role
            obj: Objeto sobre el cual asignar permiso
            permission_codename: Código del permiso (ej: 'view_device')
        """
        if role.group:
            assign_perm(permission_codename, role.group, obj)
    
    @staticmethod
    def assign_permissions_batch(role, objects, permissions):
        """
        Asigna múltiples permisos a un role sobre múltiples objetos.
        
        Args:
            role: Instancia de Role
            objects: Lista/QuerySet de objetos
            permissions: Lista de permission_codenames
        """
        if not role.group:
            return
        
        for obj in objects:
            for perm in permissions:
                assign_perm(perm, role.group, obj)
    
    @staticmethod
    def assign_all_permissions(role, obj):
        """
        Asigna todos los permisos CRUD a un role sobre un objeto.
        """
        model_name = obj._meta.model_name
        permissions = PermissionManager.PERMISSION_MAP.get(model_name, [])
        
        if role.group:
            for perm in permissions:
                assign_perm(perm, role.group, obj)
    
    @staticmethod
    def assign_workspace_permissions(role, workspace):
        """
        Asigna permisos sobre todos los objetos de un workspace a un role.
        Útil para setup inicial o cuando se agrega un nuevo role.
        
        Args:
            role: Instancia de Role
            workspace: Instancia de Workspace
        """
        # Asignar permisos sobre el workspace mismo
        PermissionManager.assign_all_permissions(role, workspace)
        
        # Asignar permisos sobre todos los objetos relacionados
        for device in workspace.device_set.all():
            PermissionManager.assign_all_permissions(role, device)
        
        for machine in workspace.machine_set.all():
            PermissionManager.assign_all_permissions(role, machine)
        
        for gateway in workspace.gateway_set.all():
            PermissionManager.assign_all_permissions(role, gateway)
        
        # ... otros modelos relacionados
    
    @staticmethod
    def revoke_permission(role, obj, permission_codename):
        """Revoca un permiso específico."""
        if role.group:
            remove_perm(permission_codename, role.group, obj)
    
    @staticmethod
    def revoke_all_permissions(role, obj):
        """Revoca todos los permisos de un role sobre un objeto."""
        from guardian.shortcuts import remove_obj_perms_for_group
        if role.group:
            remove_obj_perms_for_group(role.group, obj)
```

### 5.2 Mixin para ViewSets
**Archivo:** `roles/mixins.py` (reescribir)

```python
from .guardian_helpers import PermissionManager

class GuardianPermissionMixin:
    """
    Mixin para ViewSets que automáticamente asigna permisos
    al crear objetos basándose en el workspace del usuario.
    """
    
    def perform_create(self, serializer):
        instance = serializer.save()
        
        # Obtener workspace del usuario actual
        membership = self.request.user.workspacemembership_set.first()
        if membership:
            workspace = membership.workspace
            
            # Asignar permisos a todos los roles del workspace
            for role in workspace.role_set.all():
                if role.is_admin:
                    # Admin tiene todos los permisos
                    PermissionManager.assign_all_permissions(role, instance)
                else:
                    # Roles normales solo lectura inicial
                    model_name = instance._meta.model_name
                    view_perm = f'view_{model_name}'
                    PermissionManager.assign_permission(role, instance, view_perm)
```

---

## 6. Nueva Implementación de Permisos (permissions.py)

### 6.1 Reescribir permissions.py
**Archivo:** `roles/permissions.py`

```python
from rest_framework.permissions import BasePermission, SAFE_METHODS
from guardian.shortcuts import get_objects_for_user
from loguru import logger

TENANT_ADMIN_SCOPES = ["role", "workspace", "role_permission"]

class HasObjectPermission(BasePermission):
    """
    Verifica permisos a nivel de objeto usando Django Guardian.
    Compatible con enfoque multi-tenant.
    """
    
    def has_permission(self, request, view):
        """
        Verificación a nivel de lista (list, create).
        """
        user = request.user
        
        # Superuser tiene acceso total
        if user.is_superuser:
            return True
        
        # Usuario debe estar autenticado
        if not user.is_authenticated:
            return False
        
        # Usuario debe tener workspace membership
        membership = user.workspacemembership_set.first()
        if not membership:
            logger.warning(f"User {user} has no workspace membership")
            return False
        
        # Para creación, verificar permisos a nivel de modelo
        if request.method == 'POST':
            model = view.queryset.model
            perm_codename = f'{model._meta.app_label}.add_{model._meta.model_name}'
            
            # Admin del tenant tiene permisos automáticos en ciertos scopes
            scope = getattr(view, 'scope', None)
            if membership.role.is_admin and scope in TENANT_ADMIN_SCOPES:
                return True
            
            return user.has_perm(perm_codename)
        
        # Para listado, se filtrará en has_object_permission
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Verificación a nivel de objeto individual (retrieve, update, delete).
        """
        user = request.user
        
        # Superuser tiene acceso total
        if user.is_superuser:
            return True
        
        # Usuario debe estar autenticado
        if not user.is_authenticated:
            return False
        
        membership = user.workspacemembership_set.first()
        if not membership:
            return False
        
        # Verificar multi-tenancy (objetos del mismo tenant)
        group = user.groups.first()
        is_internal = getattr(group, "name", None) == "EMASA"
        
        if not is_internal and obj:
            try:
                obj_org = getattr(getattr(obj, "workspace", None), "organization", None)
            except Exception as e:
                logger.exception(f"Exception getting organization: {e}")
                obj_org = None
            
            if obj_org and obj_org != membership.workspace.organization:
                logger.warning("Organization mismatch")
                return False
        
        # Admin del tenant tiene permisos en ciertos scopes
        scope = getattr(view, 'scope', None)
        if membership.role.is_admin and scope in TENANT_ADMIN_SCOPES:
            return True
        
        # Determinar permiso necesario según método HTTP
        model = obj._meta.model
        permission_map = {
            'GET': f'view_{model._meta.model_name}',
            'PUT': f'change_{model._meta.model_name}',
            'PATCH': f'change_{model._meta.model_name}',
            'DELETE': f'delete_{model._meta.model_name}',
        }
        
        perm_codename = permission_map.get(request.method)
        if not perm_codename:
            return False
        
        # Verificar permiso de objeto con Guardian
        return user.has_perm(f'{model._meta.app_label}.{perm_codename}', obj)


class IsAdminOrIsAuthenticatedReadOnly(BasePermission):
    """
    Mantener sin cambios - para modelos administrativos.
    """
    def has_permission(self, request, view):
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        if request.method in SAFE_METHODS:
            return True
        
        return False
```

---

## 7. Actualización de ViewSets

### 7.1 Patrón de Reemplazo
En todos los ViewSets, reemplazar:
```python
# ANTES
from roles.permissions import HasPermissionKey
from roles.mixins import PermissionKeyMixin

class DeviceViewSet(viewsets.ModelViewSet, PermissionKeyMixin):
    permission_classes = [HasPermissionKey]
    scope = "device"
    
    def perform_create(self, serializer):
        instance = serializer.save()
        self.create_permission_keys(instance, scope="device")
```

Por:
```python
# DESPUÉS
from roles.permissions import HasObjectPermission
from roles.mixins import GuardianPermissionMixin

class DeviceViewSet(viewsets.ModelViewSet, GuardianPermissionMixin):
    permission_classes = [HasObjectPermission]
    scope = "device"
    
    # perform_create heredado del mixin
```

### 7.2 Filtrado de QuerySets
Agregar método `get_queryset()` para filtrar por permisos:
```python
from guardian.shortcuts import get_objects_for_user

def get_queryset(self):
    user = self.request.user
    if user.is_superuser:
        return super().get_queryset()
    
    model = self.queryset.model
    perm = f'{model._meta.app_label}.view_{model._meta.model_name}'
    return get_objects_for_user(user, perm, klass=model)
```

---

## 8. Definir Permisos Custom en Modelos

### 8.1 Meta Class en Modelos
Para cada modelo que necesite permisos granulares:

```python
class Device(models.Model):
    # ... campos ...
    
    class Meta:
        permissions = [
            ("activate_device", "Can activate device"),
            ("deactivate_device", "Can deactivate device"),
            ("view_device_data", "Can view device data"),
        ]
```

### 8.2 Modelos a Actualizar
- `infrastructure/models.py`: Device, Machine, Gateway, Application
- `organizations/models.py`: Workspace, Tenant
- `users/models.py`: User (si es necesario)
- `chirpstack/models.py`: DeviceProfile, ApiUser

---

## 9. Testing y Validación

### 9.1 Tests Unitarios
**Archivo:** `roles/tests.py`
- Test creación de Role auto-crea Group
- Test eliminación de Role elimina Group
- Test WorkspaceMembership agrega usuario a grupo
- Test asignación de permisos individuales
- Test asignación de permisos por lote
- Test revocación de permisos al eliminar objeto
- Test filtrado de queryset por permisos
- Test multi-tenancy (aislamiento entre tenants)

### 9.2 Tests de Integración
- Test flujo completo: crear workspace → crear role → asignar permisos → crear usuario → verificar acceso
- Test admin vs usuario normal
- Test permisos de EMASA (interno) vs tenants externos

---

## 10. Migración de Datos (N/A)
Como la base de datos está vacía, no hay migración de datos. Solo:
- Ejecutar `python manage.py makemigrations`
- Ejecutar `python manage.py migrate`
- Los fixtures existentes deberán ser actualizados si contienen PermissionKeys

---

## 11. Documentación

### 11.1 Actualizar README.md
- Eliminar sección de "HasPermissionKey"
- Agregar sección de "Django Guardian Integration"
- Documentar convención de nombres de grupos
- Documentar uso de `PermissionManager` helper
- Documentar cómo agregar permisos custom en modelos

### 11.2 Crear Guía de Uso
**Archivo:** `docs/guardian_usage.md` (crear)
- Cómo asignar permisos a un role
- Cómo verificar permisos de un usuario
- Cómo agregar permisos custom
- Ejemplos de uso con API

---

## 12. Checklist de Implementación

### Fase 1: Preparación
- [ ] Instalar django-guardian
- [ ] Configurar settings.py
- [ ] Ejecutar migraciones de guardian

### Fase 2: Eliminación
- [ ] Eliminar modelos PermissionKey y RolePermission
- [ ] Eliminar HasPermissionKey y PermissionKeyMixin
- [ ] Eliminar viewsets y serializers relacionados
- [ ] Limpiar imports en todos los archivos
- [ ] Crear migración de eliminación

### Fase 3: Adaptación de Role
- [ ] Agregar campo `group` a Role
- [ ] Implementar auto-creación de grupos
- [ ] Implementar eliminación de grupos
- [ ] Actualizar WorkspaceMembership para sincronizar grupos

### Fase 4: Helpers y Permisos
- [ ] Crear guardian_helpers.py con PermissionManager
- [ ] Crear GuardianPermissionMixin
- [ ] Reescribir permissions.py con HasObjectPermission
- [ ] Implementar signals de revocación

### Fase 5: Actualización de ViewSets
- [ ] Actualizar todos los ViewSets (users, infrastructure, organizations, chirpstack)
- [ ] Implementar get_queryset con filtrado
- [ ] Agregar permisos custom en Meta de modelos

### Fase 6: Testing
- [ ] Escribir tests unitarios
- [ ] Escribir tests de integración
- [ ] Validar multi-tenancy

### Fase 7: Documentación
- [ ] Actualizar README.md
- [ ] Crear guía de uso
- [ ] Documentar convenciones

---

## Notas Adicionales

- **Rendimiento**: Django Guardian usa tablas adicionales para permisos de objeto. Considerar índices en tablas grandes.
- **Migración futura**: Si se necesita migrar datos, usar `assign_perm` en un data migration.
- **Permisos granulares**: Aprovechar Meta.permissions para acciones específicas (activate, deactivate, etc.).
- **Caché**: Guardian soporta caché de permisos, configurar si es necesario.
- **Multi-tenancy**: La convención `{tenant.name}_{role.name}` asegura aislamiento entre tenants.

---

## Recursos
- [Django Guardian Docs](https://django-guardian.readthedocs.io/)
- [DRF Object Permissions](https://www.django-rest-framework.org/api-guide/permissions/#object-level-permissions)
