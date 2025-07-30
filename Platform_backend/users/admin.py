from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "username",
        "is_staff",
        "is_superuser",
        "first_name",
        "first_last_name",
    )


admin.site.register(User, UserAdmin)
