import warnings
from typing import Dict, List, Optional, Any, Callable
from loguru import logger
from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError


class ResourceEntry:
    """
    Represents a registered model resource within the dynamic permission catalog.
    """

    def __init__(
        self,
        app_label: str,
        model: str,
        label: str,
        icon: str,
        scopes: List[str],
        actions: List[str],
        instances_resolver: Optional[Callable[[Any], Any]] = None,
    ):
        self.app_label = app_label.lower()
        self.model = model.lower()
        self.label = label
        self.icon = icon
        self.scopes = scopes  # e.g., ["workspace"], ["tenant", "workspace"], ["global"]
        self.actions = actions  # e.g., ["view", "change", "delete", "add"]
        self.instances_resolver = instances_resolver

    @property
    def primary_scope(self) -> str:
        return self.scopes[0] if self.scopes else "workspace"

    def get_instances(self, workspace: Any) -> Any:
        """
        Retrieves active model instances within the specified workspace.
        Uses custom resolver if provided, otherwise falls back to standard workspace relations.
        """
        if self.instances_resolver:
            return self.instances_resolver(workspace)

        model_class = apps.get_model(self.app_label, self.model)
        if model_class is None:
            return []

        if self.model == "tenant":
            return [workspace.tenant] if workspace and getattr(workspace, "tenant", None) else []
        if self.model == "workspace":
            return [workspace] if workspace else []

        # Standard workspace ForeignKey or related manager
        if hasattr(workspace, f"{self.model}_set"):
            return getattr(workspace, f"{self.model}_set").all()
        elif hasattr(model_class, "workspace"):
            return model_class.objects.filter(workspace=workspace)
        elif self.model == "location":
            return model_class.objects.filter(gateway__workspace=workspace).distinct()
        elif self.model == "user":
            from users.models import User
            return User.objects.filter(workspacemembership__workspace=workspace).distinct()
        elif self.model == "ticket":
            return model_class.objects.filter(user__workspacemembership__workspace=workspace).distinct()
        elif self.model == "comment":
            return model_class.objects.filter(ticket__user__workspacemembership__workspace=workspace).distinct()

        return []

    def to_dict(self, allowed_actions: Optional[List[str]] = None) -> dict:
        actions = self.actions
        if allowed_actions is not None:
            actions = [a for a in self.actions if a in allowed_actions]
        return {
            "model": self.model,
            "label": self.label,
            "scope": self.primary_scope,
            "scopes": self.scopes,
            "actions": actions,
        }


class CategoryEntry:
    """
    Represents a domain category grouping multiple resource entries.
    """

    def __init__(self, key: str, label: str, icon: str):
        self.key = key
        self.label = label
        self.icon = icon
        self.resources: Dict[str, ResourceEntry] = {}

    def add_resource(self, resource: ResourceEntry):
        self.resources[resource.model] = resource

    def to_dict(self, allowed_actions: Optional[List[str]] = None, scope_filter: Optional[str] = None) -> Optional[dict]:
        filtered_resources = []
        for res in self.resources.values():
            if scope_filter:
                if scope_filter not in res.scopes:
                    continue
            res_dict = res.to_dict(allowed_actions=allowed_actions)
            if res_dict["actions"]:
                filtered_resources.append(res_dict)

        if not filtered_resources:
            return None

        return {
            "key": self.key,
            "label": self.label,
            "icon": self.icon,
            "resources": filtered_resources,
        }


class PermissionCatalogRegistry:
    """
    Centralized single source of truth for all assignable permissions across the platform.
    Organized by domain categories, resource models, scopes, and allowable actions.
    """

    _categories: Dict[str, CategoryEntry] = {}
    _model_to_app: Dict[str, str] = {}
    _model_to_category: Dict[str, str] = {}
    _instance = None

    @classmethod
    def get_instance(cls) -> "PermissionCatalogRegistry":
        if cls._instance is None:
            cls._instance = cls()
            cls._initialize_defaults()
        return cls._instance

    @classmethod
    def register_category(cls, key: str, label: str, icon: str) -> CategoryEntry:
        cat = CategoryEntry(key=key, label=label, icon=icon)
        cls._categories[key] = cat
        return cat

    @classmethod
    def register_resource(
        cls,
        category_key: str,
        app_label: str,
        model: str,
        label: str,
        icon: str,
        scopes: List[str],
        actions: Optional[List[str]] = None,
        instances_resolver: Optional[Callable[[Any], Any]] = None,
    ) -> ResourceEntry:
        if category_key not in cls._categories:
            raise KeyError(f"Category '{category_key}' is not registered.")

        if actions is None:
            actions = ["view", "change", "delete"]

        resource = ResourceEntry(
            app_label=app_label,
            model=model,
            label=label,
            icon=icon,
            scopes=scopes,
            actions=actions,
            instances_resolver=instances_resolver,
        )
        cls._categories[category_key].add_resource(resource)
        cls._model_to_app[model.lower()] = app_label.lower()
        cls._model_to_category[model.lower()] = category_key
        return resource

    @classmethod
    def get_categories(cls) -> Dict[str, CategoryEntry]:
        cls._ensure_initialized()
        return cls._categories

    @classmethod
    def get_resource(cls, model_name: str) -> Optional[ResourceEntry]:
        cls._ensure_initialized()
        model_name = model_name.lower()
        cat_key = cls._model_to_category.get(model_name)
        if cat_key and cat_key in cls._categories:
            return cls._categories[cat_key].resources.get(model_name)
        return None

    @classmethod
    def get_model_to_app_map(cls) -> Dict[str, str]:
        cls._ensure_initialized()
        return dict(cls._model_to_app)

    @classmethod
    def get_registered_models(cls) -> List[str]:
        cls._ensure_initialized()
        return list(cls._model_to_app.keys())

    @classmethod
    def _ensure_initialized(cls):
        if not cls._categories:
            cls._initialize_defaults()

    @classmethod
    def _initialize_defaults(cls):
        """Pre-registers core platform models and domain categories."""
        # 1. Organizations
        cls.register_category("organizations", "Organizaciones", "business")
        cls.register_resource(
            category_key="organizations",
            app_label="organizations",
            model="tenant",
            label="Tenants",
            icon="business",
            scopes=["tenant", "global"],
            actions=["view", "change", "delete"],
            instances_resolver=lambda ws: [ws.tenant] if ws and getattr(ws, "tenant", None) else [],
        )
        cls.register_resource(
            category_key="organizations",
            app_label="organizations",
            model="workspace",
            label="Workspaces",
            icon="briefcase",
            scopes=["workspace", "tenant"],
            actions=["view", "change", "delete"],
            instances_resolver=lambda ws: [ws] if ws else [],
        )

        # 2. Infrastructure
        cls.register_category("infrastructure", "Infraestructura", "hardwareChip")
        cls.register_resource(
            category_key="infrastructure",
            app_label="infrastructure",
            model="device",
            label="Dispositivos",
            icon="hardwareChip",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )
        cls.register_resource(
            category_key="infrastructure",
            app_label="infrastructure",
            model="gateway",
            label="Gateways",
            icon="wifi",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )
        cls.register_resource(
            category_key="infrastructure",
            app_label="infrastructure",
            model="application",
            label="Aplicaciones",
            icon="apps",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )
        cls.register_resource(
            category_key="infrastructure",
            app_label="infrastructure",
            model="machine",
            label="Máquinas",
            icon="construct",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )
        cls.register_resource(
            category_key="infrastructure",
            app_label="infrastructure",
            model="location",
            label="Ubicaciones",
            icon="location",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )

        # 3. ChirpStack
        cls.register_category("chirpstack", "ChirpStack", "radio")
        cls.register_resource(
            category_key="chirpstack",
            app_label="chirpstack",
            model="deviceprofile",
            label="Perfiles de Dispositivo",
            icon="documentText",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )
        cls.register_resource(
            category_key="chirpstack",
            app_label="chirpstack",
            model="apiuser",
            label="Usuarios API",
            icon="key",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )

        # 4. Roles
        cls.register_category("roles", "Roles y Permisos", "shield")
        cls.register_resource(
            category_key="roles",
            app_label="roles",
            model="role",
            label="Roles",
            icon="shield",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )
        cls.register_resource(
            category_key="roles",
            app_label="roles",
            model="workspacemembership",
            label="Membresías",
            icon="people",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )

        # 5. Users
        cls.register_category("users", "Usuarios", "person")
        cls.register_resource(
            category_key="users",
            app_label="users",
            model="user",
            label="Usuarios",
            icon="person",
            scopes=["tenant", "workspace"],
            actions=["view", "change", "delete"],
        )

        # 6. Support
        cls.register_category("support", "Soporte", "helpCircle")
        cls.register_resource(
            category_key="support",
            app_label="support",
            model="ticket",
            label="Tickets",
            icon="helpCircle",
            scopes=["tenant", "workspace"],
            actions=["view", "change", "delete"],
        )
        cls.register_resource(
            category_key="support",
            app_label="support",
            model="comment",
            label="Comentarios",
            icon="chatbubble",
            scopes=["workspace"],
            actions=["view", "change", "delete"],
        )

    @classmethod
    def validate_registry(cls) -> bool:
        """
        Validates that all registered models exist in ContentType and that each
        declared action corresponds to a valid auth Permission in the database.
        Raises ValueError if any model or permission is missing.
        """
        cls._ensure_initialized()
        errors = []

        for cat_key, cat in cls._categories.items():
            for model_name, res in cat.resources.items():
                try:
                    ct = ContentType.objects.get(
                        app_label=res.app_label, model=res.model
                    )
                except ContentType.DoesNotExist:
                    errors.append(
                        f"ContentType not found for {res.app_label}.{res.model} (category: {cat_key})"
                    )
                    continue

                for action in res.actions:
                    codename = f"{action}_{res.model}"
                    if not Permission.objects.filter(content_type=ct, codename=codename).exists():
                        errors.append(
                            f"Permission '{codename}' missing for {res.app_label}.{res.model}"
                        )

        if errors:
            err_msg = "; ".join(errors)
            logger.error(f"PermissionCatalogRegistry validation failed: {err_msg}")
            raise ValueError(f"PermissionCatalogRegistry validation errors: {err_msg}")

        return True

    @classmethod
    def get_catalog(
        cls,
        tenant_type: Optional[str] = None,
        scope: Optional[str] = None,
        is_global: bool = False,
        user: Optional[Any] = None,
        tenant: Optional[Any] = None,
    ) -> List[dict]:
        """
        Generates filtered catalog metadata based on caller's authorization context.
        Standard tenants receive only tenant/workspace scoped permissions and safe actions.
        Global administrators or superusers receive the complete platform catalog.
        """
        cls._ensure_initialized()

        if user and getattr(user, "is_superuser", False):
            is_global = True
        elif tenant and getattr(tenant, "is_global", False):
            is_global = True

        # Safe actions for standard tenants vs full actions for global tenants
        allowed_actions = ["view", "change", "delete"] if is_global else ["view", "change"]

        categories_list = []
        for cat in cls._categories.values():
            filtered_resources = []
            for res in cat.resources.values():
                # Filter out global-only resources for standard tenants
                if not is_global and "workspace" not in res.scopes and "tenant" not in res.scopes:
                    continue

                if scope and scope not in res.scopes:
                    continue

                res_dict = res.to_dict(allowed_actions=allowed_actions)
                if res_dict["actions"]:
                    filtered_resources.append(res_dict)

            if filtered_resources:
                categories_list.append(
                    {
                        "key": cat.key,
                        "label": cat.label,
                        "icon": cat.icon,
                        "resources": filtered_resources,
                    }
                )

        return categories_list


# Singleton instance alias
permission_catalog = PermissionCatalogRegistry.get_instance()
