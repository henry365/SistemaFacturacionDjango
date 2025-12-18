from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Count, Sum
from .models import Vendedor
import re

class VendedorSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    usuario_username = serializers.ReadOnlyField(source='usuario.username')
    total_clientes = serializers.SerializerMethodField()
    total_ventas = serializers.SerializerMethodField()
    
    class Meta:
        model = Vendedor
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')
    
    def get_total_clientes(self, obj):
        """Contar clientes asignados al vendedor"""
        return obj.clientes.count()
    
    def get_total_ventas(self, obj):
        """Calcular total de ventas del vendedor"""
        from ventas.models import Factura
        ventas = Factura.objects.filter(vendedor=obj)
        total = ventas.aggregate(total=Sum('total'))['total'] or 0
        return float(total)
    
    def validate_correo(self, value):
        """Validar formato de correo electrónico"""
        if value:
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
    
    def validate_comision_porcentaje(self, value):
        """Validar que la comisión esté entre 0 y 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("La comisión debe estar entre 0 y 100.")
        return value
    
    def validate(self, data):
        """Validaciones de negocio personalizadas"""
        # Validar cédula única por empresa
        cedula = data.get('cedula')
        if cedula:
            empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
            if empresa:
                queryset = Vendedor.objects.filter(empresa=empresa, cedula=cedula)
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError({
                        "cedula": f"Ya existe un vendedor con esta cédula en la empresa {empresa.nombre}."
                    })
        return data
