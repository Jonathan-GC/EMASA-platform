from rest_framework import serializers
from django.core.validators import validate_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User

class UserSerializer(serializers.ModelSerializer):
    # Campo para la contraseña (solo escritura)
    password = serializers.CharField(write_only=True, required=True)
    # Campo para confirmar la contraseña (solo escritura)
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm Password")

    class Meta:
        model = User
        # Campos que serán serializados/deserializados
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined')

    # Valida que el nombre de usuario sea único y tenga longitud mínima
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        if len(value) < 4:
            raise serializers.ValidationError("El nombre de usuario debe tener al menos 4 caracteres.")
        return value
    
    # Valida el primer nombre (puedes ajustar la lógica según tus necesidades)
    def validate_first_name(self, value):
        # Este chequeo parece incorrecto, deberías validar solo letras, no existencia en username
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("First name must contain only letters.")
        if len(value) < 4:
            raise serializers.ValidationError("te username must be at least 4 characters long.")
        return value
    
    # Valida la contraseña usando las reglas de Django
    def validate_password(self, value):
        try:
            validate_password(value)  # Usa las validaciones de Django (longitud, complejidad, etc.)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    # Valida el teléfono (si el modelo lo tiene)
    def validate_phone(self, value):
        if not value.isdigit() or len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits long and contain only numbers.")
        return value
    
    # Validación general: asegura que ambas contraseñas coincidan
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": "Las contraseñas no coinciden."})
        return data
    
    # Crea el usuario usando el método de Django, omitiendo password2
    def create(self, validated_data):
        validated_data.pop('password2')  # no se guarda en el modelo
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user