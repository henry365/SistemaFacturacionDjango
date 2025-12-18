"""
Mixins de validación para modelos del Sistema de Facturación.

Este módulo implementa el principio DRY proporcionando mixins reutilizables
para validaciones comunes que se repiten en múltiples modelos.

Uso:
    class MiModelo(ValidateMultitenantMixin, ValidateMoneyFieldsMixin, models.Model):
        ...

        def clean(self):
            super().clean()
            self.validate_belongs_to_empresa()
            self.validate_money_fields()
"""
from django.core.exceptions import ValidationError


class ValidateMultitenantMixin:
    """
    Mixin para validar que las relaciones pertenezcan a la misma empresa.

    Valida automáticamente los campos: cliente, proveedor, producto,
    almacen, vendedor cuando existen en el modelo.

    Uso:
        def clean(self):
            super().clean()
            self.validate_belongs_to_empresa()
    """

    # Campos a validar (pueden ser override en subclases)
    MULTITENANT_FIELDS = ['cliente', 'proveedor', 'producto', 'almacen', 'vendedor']

    def validate_belongs_to_empresa(self):
        """
        Valida que todos los campos relacionados pertenezcan a la misma empresa.

        Raises:
            ValidationError: Si algún campo no pertenece a la empresa del modelo.
        """
        if not hasattr(self, 'empresa') or not self.empresa:
            return

        for field_name in self.MULTITENANT_FIELDS:
            if hasattr(self, field_name):
                related_obj = getattr(self, field_name, None)
                if related_obj and hasattr(related_obj, 'empresa'):
                    if related_obj.empresa and related_obj.empresa != self.empresa:
                        raise ValidationError({
                            field_name: f'El {field_name} debe pertenecer a la misma empresa.'
                        })


class ValidateMoneyFieldsMixin:
    """
    Mixin para validar que los campos monetarios no sean negativos.

    Valida automáticamente los campos definidos en MONEY_FIELDS.

    Uso:
        def clean(self):
            super().clean()
            self.validate_money_fields()
    """

    # Campos monetarios a validar (pueden ser override en subclases)
    MONEY_FIELDS = ['monto', 'total', 'subtotal', 'impuestos', 'itbis',
                    'descuento', 'monto_pendiente', 'monto_pagado', 'monto_cobrado']

    def validate_money_fields(self):
        """
        Valida que los campos monetarios no tengan valores negativos.

        Raises:
            ValidationError: Si algún campo tiene valor negativo.
        """
        for field_name in self.MONEY_FIELDS:
            if hasattr(self, field_name):
                value = getattr(self, field_name, None)
                if value is not None and value < 0:
                    raise ValidationError({
                        field_name: f'El campo {field_name} no puede ser negativo.'
                    })


class ValidateQuantityMixin:
    """
    Mixin para validar que las cantidades sean positivas.

    Uso:
        def clean(self):
            super().clean()
            self.validate_quantity_fields()
    """

    # Campos de cantidad a validar
    QUANTITY_FIELDS = ['cantidad', 'cantidad_recibida', 'cantidad_devuelta']

    def validate_quantity_fields(self):
        """
        Valida que los campos de cantidad sean mayores a cero.

        Raises:
            ValidationError: Si algún campo tiene valor <= 0.
        """
        for field_name in self.QUANTITY_FIELDS:
            if hasattr(self, field_name):
                value = getattr(self, field_name, None)
                if value is not None and value <= 0:
                    raise ValidationError({
                        field_name: f'La {field_name} debe ser mayor a cero.'
                    })


class ValidateDateRangeMixin:
    """
    Mixin para validar rangos de fechas.

    Uso:
        class MiModelo(ValidateDateRangeMixin, models.Model):
            fecha_inicio = models.DateField()
            fecha_fin = models.DateField()

            DATE_RANGE_PAIRS = [('fecha_inicio', 'fecha_fin')]

            def clean(self):
                super().clean()
                self.validate_date_ranges()
    """

    # Pares de fechas a validar [(fecha_inicio, fecha_fin), ...]
    DATE_RANGE_PAIRS = []

    def validate_date_ranges(self):
        """
        Valida que las fechas de inicio sean anteriores a las de fin.

        Raises:
            ValidationError: Si alguna fecha de inicio es posterior a su fecha fin.
        """
        for fecha_inicio_field, fecha_fin_field in self.DATE_RANGE_PAIRS:
            if hasattr(self, fecha_inicio_field) and hasattr(self, fecha_fin_field):
                fecha_inicio = getattr(self, fecha_inicio_field, None)
                fecha_fin = getattr(self, fecha_fin_field, None)
                if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
                    raise ValidationError({
                        fecha_fin_field: f'{fecha_fin_field} no puede ser anterior a {fecha_inicio_field}.'
                    })


class DisplayChoicesMixin:
    """
    Mixin que proporciona propiedades para mostrar valores de campos choices.

    Genera automáticamente properties como estado_display, tipo_display, etc.
    basándose en los campos que tienen choices definidos.
    """

    @property
    def estado_display(self):
        """Retorna el valor legible del estado."""
        if hasattr(self, 'get_estado_display'):
            return self.get_estado_display()
        return getattr(self, 'estado', None)

    @property
    def tipo_display(self):
        """Retorna el valor legible del tipo."""
        if hasattr(self, 'get_tipo_display'):
            return self.get_tipo_display()
        return getattr(self, 'tipo', None)

    @property
    def metodo_pago_display(self):
        """Retorna el valor legible del método de pago."""
        if hasattr(self, 'get_metodo_pago_display'):
            return self.get_metodo_pago_display()
        return getattr(self, 'metodo_pago', None)

    @property
    def motivo_display(self):
        """Retorna el valor legible del motivo."""
        if hasattr(self, 'get_motivo_display'):
            return self.get_motivo_display()
        return getattr(self, 'motivo', None)


class ActualizarEstadoMixin:
    """
    Mixin para actualizar estado basado en montos pendientes.

    Útil para CuentaPorCobrar, CuentaPorPagar y modelos similares.

    Uso:
        class CuentaPorCobrar(ActualizarEstadoMixin, models.Model):
            CAMPO_MONTO_PAGADO = 'monto_cobrado'
            ESTADO_PAGADO = 'COBRADA'

            def save(self, *args, **kwargs):
                self.actualizar_estado()
                super().save(*args, **kwargs)
    """

    # Override en subclases
    CAMPO_MONTO_PAGADO = 'monto_pagado'
    ESTADO_PAGADO = 'PAGADA'
    ESTADO_PARCIAL = 'PARCIAL'
    ESTADO_VENCIDA = 'VENCIDA'
    ESTADO_PENDIENTE = 'PENDIENTE'

    def actualizar_estado(self):
        """
        Actualiza el estado basado en el monto pendiente y fecha de vencimiento.
        """
        from datetime import date

        monto_pendiente = getattr(self, 'monto_pendiente', None)
        monto_pagado = getattr(self, self.CAMPO_MONTO_PAGADO, 0) or 0
        fecha_vencimiento = getattr(self, 'fecha_vencimiento', None)

        if monto_pendiente is not None and monto_pendiente <= 0:
            self.estado = self.ESTADO_PAGADO
        elif monto_pagado > 0:
            self.estado = self.ESTADO_PARCIAL
        elif fecha_vencimiento and fecha_vencimiento < date.today():
            self.estado = self.ESTADO_VENCIDA
        else:
            self.estado = self.ESTADO_PENDIENTE
