from rest_framework import serializers
from .models import Cliente, CategoriaCliente

class CategoriaClienteSerializer(serializers.ModelSerializer):
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    
    class Meta:
        model = CategoriaCliente
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')

class ClienteSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.ReadOnlyField(source='categoria.nombre')
    categoria_detalle = CategoriaClienteSerializer(source='categoria', read_only=True)
    vendedor_nombre = serializers.ReadOnlyField(source='vendedor_asignado.nombre')
    vendedor_id = serializers.ReadOnlyField(source='vendedor_asignado.id')
    empresa_nombre = serializers.ReadOnlyField(source='empresa.nombre')
    
    class Meta:
        model = Cliente
        fields = '__all__'
        read_only_fields = ('id', 'uuid', 'fecha_creacion', 'fecha_actualizacion', 'usuario_creacion', 'usuario_modificacion', 'empresa')

    def validate_correo_electronico(self, value):
        """Validar formato de correo electrónico"""
        if value:
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError
            try:
                validate_email(value)
            except ValidationError:
                raise serializers.ValidationError("Formato de correo electrónico inválido.")
        return value

    def validate_limite_credito(self, value):
        """Validar que el límite de crédito no sea negativo"""
        if value < 0:
            raise serializers.ValidationError("El límite de crédito no puede ser negativo.")
        return value

    def validate(self, data):
        """Validaciones de negocio personalizadas"""
        # Validar RNC obligatorio cuando tipo_identificacion es RNC
        if data.get('tipo_identificacion') == 'RNC' and not data.get('numero_identificacion'):
            raise serializers.ValidationError({"numero_identificacion": "El RNC es obligatorio cuando el tipo de identificación es RNC."})
        
        # Validar número de identificación único por empresa
        numero_identificacion = data.get('numero_identificacion')
        if numero_identificacion:
            empresa = data.get('empresa') or (self.instance.empresa if self.instance else None)
            if empresa:
                queryset = Cliente.objects.filter(
                    empresa=empresa,
                    numero_identificacion=numero_identificacion
                )
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError({
                        "numero_identificacion": f"Ya existe un cliente con este número de identificación en la empresa {empresa.nombre}."
                    })
        
        return data
