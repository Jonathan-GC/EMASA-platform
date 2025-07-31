from rest_framework import serializers
from .models import Role, WorkspaceMembership
from users.models import User
from organizations.models import Workspace

class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Role.
    Permite la serialización y validación de los campos de un rol dentro de un workspace.
    """
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'color', 'workspace']

    def validate_name(self, value):
        """
        Valida que el nombre del rol tenga al menos 3 caracteres.
        """
        if len(value.strip()) < 3:
            raise serializers.ValidationError("El nombre del rol debe tener al menos 3 caracteres.")
        return value

    def validate_color(self, value):
        """
        Valida que el color esté en formato hexadecimal (ejemplo: #FF5733).
        """
        if not value.startswith("#") or len(value) != 7:
            raise serializers.ValidationError("El color debe estar en formato hexadecimal (ej: #FF5733).")
        return value


class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo WorkspaceMembership.
    Permite la serialización y validación de la membresía de un usuario en un workspace.
    """
    class Meta:
        model = WorkspaceMembership
        fields = ['id', 'workspace', 'user', 'role']

    def validate(self, data):
        """
        Valida que el usuario no esté ya registrado como miembro en el mismo workspace.
        """
        user = data.get('user')
        workspace = data.get('workspace')

        if WorkspaceMembership.objects.filter(user=user, workspace=workspace).exists():
            raise serializers.ValidationError("Este usuario ya es miembro de este workspace.")

        return data
    
class WorkspaceMembershipDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detallado para WorkspaceMembership.
    Incluye información anidada del usuario, rol y workspace.
    """
    user = serializers.StringRelatedField()
    role = RoleSerializer()
    workspace = serializers.StringRelatedField()

    class Meta:
        model = WorkspaceMembership
        fields = ['id', 'workspace', 'user', 'role']