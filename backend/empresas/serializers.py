from rest_framework import serializers
from .models import Empresa
import re

class EmpresaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo Empresa"""
    
    class Meta:
        model = Empresa
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion')

    def validate_rnc(self, value):
        """Validar formato de RNC (solo números y guiones)"""
        if value:
            # RNC puede tener formato: 123456789 o 123-45678-9
            if not re.match(r'^[\d-]+$', value):
                raise serializers.ValidationError("El RNC solo puede contener números y guiones.")
            
            # Remover guiones para validar longitud
            rnc_sin_guiones = value.replace('-', '')
            if len(rnc_sin_guiones) < 9 or len(rnc_sin_guiones) > 11:
                raise serializers.ValidationError("El RNC debe tener entre 9 y 11 dígitos.")
        
        return value

    def validate_telefono(self, value):
        """Validar formato de teléfono"""
        if value:
            # Teléfono puede tener formato: 809-555-1234 o (809) 555-1234 o 8095551234
            if not re.match(r'^[\d\s\-\(\)]+$', value):
                raise serializers.ValidationError("El teléfono contiene caracteres inválidos.")
            
            # Remover caracteres especiales para validar longitud
            telefono_sin_formato = re.sub(r'[\s\-\(\)]', '', value)
            if len(telefono_sin_formato) < 10 or len(telefono_sin_formato) > 15:
                raise serializers.ValidationError("El teléfono debe tener entre 10 y 15 dígitos.")
        
        return value

    def validate_configuracion_fiscal(self, value):
        """Validar que configuracion_fiscal sea un diccionario válido"""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError("La configuración fiscal debe ser un objeto JSON válido.")
        return value

    def validate(self, data):
        """Validaciones de negocio personalizadas"""
        # Validar que el nombre no esté vacío
        nombre = data.get('nombre', '')
        if not nombre or not nombre.strip():
            raise serializers.ValidationError({"nombre": "El nombre de la empresa es obligatorio."})
        
        # Validar RNC único (excepto si es actualización del mismo registro)
        rnc = data.get('rnc')
        if rnc:
            queryset = Empresa.objects.filter(rnc=rnc)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({
                    "rnc": f"Ya existe una empresa con el RNC {rnc}."
                })
        
        return data

