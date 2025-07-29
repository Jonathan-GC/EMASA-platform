from django.conf import settings

class PrefixMixin:
    def __new__(cls, *args, **kwargs):
        if hasattr(cls, "_meta") and cls._meta.abstract is False:
            if not getattr(cls._meta, "db_table", None):
                cls._meta.db_table = f"{settings.DB_PREFIX}_{cls._meta.model_name}"
        return super().__new__(cls)