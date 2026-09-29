from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from organizations.models import Tenant
from organizations.hasher import generate_id


class Address(models.Model):
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)

    class Meta:
        abstract = True


class MainAddress(Address):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )


class BillingAddress(Address):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    user = models.OneToOneField(
        "User", on_delete=models.CASCADE, related_name="billing_address"
    )
    country = models.CharField(max_length=100)


class UserBase(models.Model):
    code = models.CharField(max_length=80, null=True, blank=True)
    img = models.FileField(upload_to="user_images/", blank=True, null=True)
    name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.CharField(max_length=255, unique=True)
    country = models.CharField(max_length=100, default="Colombia")
    phone_code = models.CharField(max_length=4, default="+57")
    phone = models.CharField(max_length=50)
    address = models.ForeignKey(
        MainAddress, on_delete=models.CASCADE, null=True, blank=True
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Users must have a username")

        user = self.model(username=username, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        user = self.create_user(username, password, **extra_fields)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(UserBase, AbstractBaseUser, PermissionsMixin):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    username = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def get_full_name(self):
        return f"{self.name} {self.last_name}"

    def has_module_perms(self, app_label):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        return super().has_perm(perm, obj)

    def __str__(self):
        return self.username


class OAuthAccount(models.Model):
    PROVIDER_CHOICES = [
        ("google", "Google"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="oauth_accounts"
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    provider_user_id = models.CharField(max_length=255)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("provider", "provider_user_id")


class UserSession(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    refresh_token_jti = models.CharField(max_length=255, db_index=True)
    device_name = models.CharField(max_length=255, default="Dispositivo")
    trust_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-last_activity"]

    def __str__(self):
        return f"{self.user.username} - {self.device_name} ({self.ip_address})"


class UserTwoFactorMethod(models.Model):
    METHOD_CHOICES = [
        ("EMAIL", "Email"),
        ("TOTP", "TOTP Authenticator"),
        ("BACKUP_CODES", "Backup Codes"),
    ]

    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="two_factor_methods"
    )
    method_type = models.CharField(max_length=20, choices=METHOD_CHOICES)
    secret = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "method_type")

    def __str__(self):
        return f"{self.user.username} - {self.method_type} (Active: {self.is_active})"


class UserBackupCode(models.Model):
    id = models.CharField(
        max_length=16, primary_key=True, default=generate_id, editable=False
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="backup_codes"
    )
    code_hash = models.CharField(max_length=128)
    is_consumed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - Backup Code (Consumed: {self.is_consumed})"


from auditlog.registry import auditlog

auditlog.register(User)
auditlog.register(MainAddress)
auditlog.register(BillingAddress)
auditlog.register(OAuthAccount)
auditlog.register(UserSession)
auditlog.register(UserTwoFactorMethod)
auditlog.register(UserBackupCode)
