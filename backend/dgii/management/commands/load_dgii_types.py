from django.core.management.base import BaseCommand
from dgii.models import TipoComprobante

class Command(BaseCommand):
    help = 'Carga los tipos de comprobantes fiscales básicos de la DGII'

    def handle(self, *args, **kwargs):
        tipos = [
            {'codigo': '01', 'nombre': 'Factura de Crédito Fiscal', 'prefijo': 'B'},
            {'codigo': '02', 'nombre': 'Factura de Consumo', 'prefijo': 'B'},
            {'codigo': '03', 'nombre': 'Notas de Débito', 'prefijo': 'B'},
            {'codigo': '04', 'nombre': 'Notas de Crédito', 'prefijo': 'B'},
            {'codigo': '11', 'nombre': 'Proveedores Informales', 'prefijo': 'B'},
            {'codigo': '12', 'nombre': 'Registro Único de Ingresos', 'prefijo': 'B'},
            {'codigo': '13', 'nombre': 'Gastos Menores', 'prefijo': 'B'},
            {'codigo': '14', 'nombre': 'Regímenes Especiales', 'prefijo': 'B'},
            {'codigo': '15', 'nombre': 'Comprobantes Gubernamentales', 'prefijo': 'B'},
            # Series E (Electrónicas) - Opcional, se pueden agregar luego
        ]

        for tipo_data in tipos:
            obj, created = TipoComprobante.objects.get_or_create(
                codigo=tipo_data['codigo'],
                defaults={
                    'nombre': tipo_data['nombre'],
                    'prefijo': tipo_data['prefijo']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Creado: {tipo_data['nombre']} ({tipo_data['codigo']})"))
            else:
                self.stdout.write(f"Ya existe: {tipo_data['nombre']}")
