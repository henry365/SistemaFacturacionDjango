"""
Comando de gestión para generar alertas de inventario.
Ejecutar periódicamente con cron o task scheduler.

Uso:
    python manage.py generar_alertas_inventario
    python manage.py generar_alertas_inventario --dias-vencimiento 30
"""
from django.core.management.base import BaseCommand
from inventario.services import ServicioAlertasInventario


class Command(BaseCommand):
    help = 'Genera alertas de inventario (stock bajo, vencimientos, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias-vencimiento',
            type=int,
            default=30,
            help='Días antes del vencimiento para alertar (default: 30)',
        )

    def handle(self, *args, **options):
        dias_vencimiento = options['dias_vencimiento']
        
        self.stdout.write('Generando alertas de inventario...')
        
        try:
            resultado = ServicioAlertasInventario.generar_todas_las_alertas()
            
            # También verificar vencimientos con el parámetro personalizado
            vencimientos = ServicioAlertasInventario.verificar_vencimientos(dias_vencimiento)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nAlertas generadas exitosamente:\n'
                    f'  - Stock bajo/agotado: {resultado["stock_bajo"]}\n'
                    f'  - Vencimientos: {vencimientos}\n'
                    f'  - Stock excesivo: {resultado["stock_excesivo"]}\n'
                    f'  - Total: {resultado["stock_bajo"] + vencimientos + resultado["stock_excesivo"]}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al generar alertas: {str(e)}')
            )
            raise





