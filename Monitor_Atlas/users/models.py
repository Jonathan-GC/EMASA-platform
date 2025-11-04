from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from organizations.models import Tenant


class Address(models.Model):
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)

    class Meta:
        abstract = True


class MainAddress(Address):
    pass


class BillingAddress(Address):
    user = models.OneToOneField(
        "User", on_delete=models.CASCADE, related_name="billing_address"
    )
    country = models.CharField(max_length=100)


class UserBase(models.Model):
    code = models.CharField(max_length=80, null=True, blank=True)
    sub = models.CharField(max_length=80, null=True, blank=True)
    img = models.CharField(max_length=255, blank=True, null=True)
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
    username = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def has_module_perms(self, app_label):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        return super().has_perm(perm, obj)

    def __str__(self):
        return self.username
