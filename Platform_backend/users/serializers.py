from rest_framework import serializers
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "code",
            "username",
            "email",
            "first_name",
            "middle_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
            "phone",
            "address",
        ]
    def validate_username(self, value):
        """
        Validates the username field to ensure that the username is unique
        and has a minimum length requirement. Raises a ValidationError if
        the username already exists in the database or if its length is
        less than 4 characters.
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username already exists.")
        if len(value) < 4:
            raise serializers.ValidationError(
                "The username must be at least 4 characters long."
            )
        return value

    def validate_names_and_last_names(self, value):
        """
        Validates that the first name, middle name and last name contain only letters.
        Raises a ValidationError if any of them contain numbers or special characters.
        """
        user = User.objects.filter(username=value)
        if (
            not user.first_name.isalpha()
            or not user.middle_name.isalpha()
            or not user.last_name.isalpha()
        ):
            raise serializers.ValidationError(
                "First name, middle name or last name must contain only letters."
            )
        return value

    def validate_phone(self, value):
        """
        Validates the phone number field to ensure that it contains only numbers
        and has a minimum length requirement. Raises a ValidationError if the
        phone number contains any non-digit characters or if its length is less
        than 10 characters.
        """
        if not value.isdigit() or len(value) < 10:        
            raise serializers.ValidationError(
                "Phone number must be at least 10 digits long and contain only numbers."
            )
        return value