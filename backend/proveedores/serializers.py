from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Proveedor

class ProveedorSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    
    class Meta:
        model = Proveedor
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')

    def validate_correo_electronico(self, value):
        """Validar formato de correo electrónico"""
        if value:
            try:
                validate_email(value)
            except ValidationError:
                raise serializers.ValidationError("Formato de correo electrónico inválido.")
        return value

    def validate_telefono(self, value):
        """Validar formato de teléfono"""
        if value:
            import re
            # Teléfono puede tener formato: 809-555-1234 o (809) 555-1234 o 8095551234
            if not re.match(r'^[\d\s\-\(\)]+$', value):
                raise serializers.ValidationError("El teléfono contiene caracteres inválidos.")
            
            # Remover caracteres especiales para validar longitud
            telefono_sin_formato = re.sub(r'[\s\-\(\)]', '', value)
            if len(telefono_sin_formato) < 10 or len(telefono_sin_formato) > 15:
                raise serializers.ValidationError("El teléfono debe tener entre 10 y 15 dígitos.")
        return value

    def validate(self, data):
        """Validaciones de negocio personalizadas"""
        # Validar RNC obligatorio cuando tipo_identificacion es RNC
        if data.get('tipo_identificacion') == 'RNC' and not data.get('numero_identificacion'):
            raise serializers.ValidationError({
                "numero_identificacion": "El RNC es obligatorio cuando el tipo de identificación es RNC."
            })
        
        # Validar número de identificación único por empresa
        numero_identificacion = data.get('numero_identificacion')
        if numero_identificacion:
            empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
            if empresa:
                queryset = Proveedor.objects.filter(
                    empresa=empresa,
                    numero_identificacion=numero_identificacion
                )
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError({
                        "numero_identificacion": f"Ya existe un proveedor con este número de identificación en la empresa {empresa.nombre}."
                    })
        
        return data
