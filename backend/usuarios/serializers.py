from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError as DjangoValidationError
from empresas.models import Empresa
import re

User = get_user_model()

class EmpresaLoginSerializer(serializers.Serializer):
    """Serializer para el primer paso del login: identificar la empresa"""
    empresa_username = serializers.CharField(required=True, help_text="Nombre de usuario de la empresa")
    
    def validate_empresa_username(self, value):
        """Validar que la empresa existe y está activa"""
        try:
            empresa = Empresa.objects.get(nombre=value, activo=True)
        except Empresa.DoesNotExist:
            raise serializers.ValidationError("Empresa no encontrada o inactiva.")
        return value

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para obtener token JWT con validación de empresa"""
    empresa_username = serializers.CharField(required=True, write_only=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        """Validar empresa y credenciales del usuario"""
        empresa_username = attrs.get('empresa_username')
        username = attrs.get('username')
        password = attrs.get('password')
        
        # Validar que la empresa existe y está activa
        try:
            empresa = Empresa.objects.get(nombre=empresa_username, activo=True)
        except Empresa.DoesNotExist:
            raise serializers.ValidationError({
                'empresa_username': 'Empresa no encontrada o inactiva.'
            })
        
        # Autenticar usuario
        user = authenticate(username=username, password=password)
        
        if user is None:
            raise serializers.ValidationError({
                'username': 'Credenciales inválidas.'
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                'username': 'Usuario inactivo.'
            })
        
        # Validar que el usuario pertenece a la empresa
        if user.empresa != empresa:
            raise serializers.ValidationError({
                'empresa_username': 'El usuario no pertenece a esta empresa.'
            })
        
        # Generar token
        refresh = self.get_token(user)
        
        # Agregar información adicional al token
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'rol': user.rol,
                'empresa': {
                    'id': empresa.id,
                    'nombre': empresa.nombre,
                    'rnc': empresa.rnc,
                }
            }
        }
        
        return data
    
    @classmethod
    def get_token(cls, user):
        """Obtener token con información adicional"""
        token = super().get_token(user)
        
        # Agregar información personalizada al token
        token['username'] = user.username
        token['rol'] = user.rol
        if user.empresa:
            token['empresa_id'] = user.empresa.id
            token['empresa_nombre'] = user.empresa.nombre
        
        return token

class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User (lectura y actualización sin password)"""
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    empresa_rnc = serializers.ReadOnlyField(source='empresa.rnc')
    grupos_nombres = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'rol', 
                  'telefono', 'empresa', 'empresa_nombre', 'empresa_rnc', 
                  'is_active', 'is_staff', 'date_joined', 'grupos_nombres')
        read_only_fields = ('id', 'date_joined', 'grupos_nombres')
    
    def get_grupos_nombres(self, obj):
        """Obtener nombres de los grupos del usuario"""
        return [group.name for group in obj.groups.all()]
    
    def validate_email(self, value):
        """Validar formato de correo electrónico"""
        if value:
            from django.core.validators import validate_email
            try:
                validate_email(value)
            except DjangoValidationError:
                raise serializers.ValidationError("Formato de correo electrónico inválido.")
        return value
    
    def validate_telefono(self, value):
        """Validar formato de teléfono"""
        if value:
            if not re.match(r'^[\d\s\-\(\)]+$', value):
                raise serializers.ValidationError("El teléfono contiene caracteres inválidos.")
            telefono_sin_formato = re.sub(r'[\s\-\(\)]', '', value)
            if len(telefono_sin_formato) < 10 or len(telefono_sin_formato) > 15:
                raise serializers.ValidationError("El teléfono debe tener entre 10 y 15 dígitos.")
        return value
    
    def validate(self, data):
        """Validaciones de negocio"""
        # Validar email único por empresa
        email = data.get('email')
        if email:
            empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
            if empresa:
                queryset = User.objects.filter(empresa=empresa, email=email)
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError({
                        "email": f"Ya existe un usuario con este correo electrónico en la empresa {empresa.nombre}."
                    })
        return data


class UserListSerializer(serializers.ModelSerializer):
    """Serializer optimizado para listados de usuarios"""
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'rol', 'rol_display', 'empresa_nombre', 'is_active', 'date_joined'
        )


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios con password"""
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True)
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 
                  'rol', 'telefono', 'empresa', 'empresa_nombre', 'is_active')
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True}
        }
    
    def validate_password(self, value):
        """Validar complejidad del password"""
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, data):
        """Validar que las contraseñas coincidan"""
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({
                "password_confirm": "Las contraseñas no coinciden."
            })
        return data
    
    def create(self, validated_data):
        """Crear usuario con password hasheado"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserUpdateSerializer(UserSerializer):
    """Serializer para actualizar usuarios sin password"""
    pass

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    password_actual = serializers.CharField(required=True, write_only=True)
    password_nuevo = serializers.CharField(required=True, write_only=True, min_length=8)
    password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_password_nuevo(self, value):
        """Validar complejidad del nuevo password"""
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, data):
        """Validar que las nuevas contraseñas coincidan"""
        if data.get('password_nuevo') != data.get('password_confirm'):
            raise serializers.ValidationError({
                "password_confirm": "Las contraseñas no coinciden."
            })
        return data
    
    def validate_password_actual(self, value):
        """Validar que la contraseña actual sea correcta"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value

class GroupSerializer(serializers.ModelSerializer):
    """Serializer para grupos/roles"""
    permisos_count = serializers.SerializerMethodField()
    usuarios_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ('id', 'name', 'permisos_count', 'usuarios_count')
    
    def get_permisos_count(self, obj):
        """Contar permisos del grupo"""
        return obj.permissions.count()
    
    def get_usuarios_count(self, obj):
        """Contar usuarios del grupo"""
        return obj.user_set.count()

class PermissionSerializer(serializers.ModelSerializer):
    """Serializer para permisos"""
    app_label = serializers.ReadOnlyField(source='content_type.app_label')
    model_name = serializers.ReadOnlyField(source='content_type.model')
    
    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename', 'app_label', 'model_name')

