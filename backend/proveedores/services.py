"""
Servicios para el módulo Proveedores

Este módulo centraliza la lógica de negocio para operaciones
complejas relacionadas con proveedores.
"""
import logging
from typing import Dict, List, Any
from decimal import Decimal
from django.db.models import Sum

from .models import Proveedor

logger = logging.getLogger(__name__)


class ServicioProveedor:
    """
    Servicio para operaciones complejas con proveedores.
    """

    @staticmethod
    def obtener_estadisticas_compras(proveedor: Proveedor) -> Dict[str, Any]:
        """
        Obtiene estadísticas de compras de un proveedor.

        Args:
            proveedor: Proveedor para el cual obtener estadísticas

        Returns:
            Diccionario con estadísticas de compras
        """
        from compras.models import Compra

        compras = Compra.objects.filter(proveedor=proveedor)
        total_compras = compras.count()
        total_comprado = compras.aggregate(total=Sum('total'))['total'] or Decimal('0')
        total_pagado = compras.aggregate(total=Sum('monto_pagado'))['total'] or Decimal('0')
        total_pendiente = total_comprado - total_pagado

        logger.info(f"Estadísticas de compras obtenidas para proveedor {proveedor.nombre}")

        return {
            'total_compras': total_compras,
            'total_comprado': float(total_comprado),
            'total_pagado': float(total_pagado),
            'total_pendiente': float(total_pendiente),
        }

    @staticmethod
    def obtener_estadisticas_ordenes(proveedor: Proveedor) -> Dict[str, Any]:
        """
        Obtiene estadísticas de órdenes de compra de un proveedor.

        Args:
            proveedor: Proveedor para el cual obtener estadísticas

        Returns:
            Diccionario con estadísticas de órdenes
        """
        from compras.models import OrdenCompra

        ordenes = OrdenCompra.objects.filter(proveedor=proveedor)
        total_ordenes = ordenes.count()
        total_ordenado = ordenes.aggregate(total=Sum('total'))['total'] or Decimal('0')

        logger.info(f"Estadísticas de órdenes obtenidas para proveedor {proveedor.nombre}")

        return {
            'total_ordenes': total_ordenes,
            'total_ordenado': float(total_ordenado),
        }

    @staticmethod
    def obtener_historial_compras(proveedor: Proveedor) -> Dict[str, Any]:
        """
        Obtiene historial completo de compras de un proveedor.

        Args:
            proveedor: Proveedor para el cual obtener historial

        Returns:
            Diccionario con lista de compras y estadísticas
        """
        from compras.models import Compra

        compras = Compra.objects.filter(proveedor=proveedor).order_by('-fecha_compra')

        data = [{
            'id': c.id,
            'numero_factura': c.numero_factura_proveedor,
            'ncf': c.numero_ncf,
            'fecha_compra': c.fecha_compra,
            'total': float(c.total),
            'estado': c.estado,
            'monto_pagado': float(c.monto_pagado),
            'monto_pendiente': float(c.total - c.monto_pagado),
            'tipo_gasto': c.tipo_gasto
        } for c in compras]

        logger.info(f"Historial de compras obtenido para proveedor {proveedor.nombre}: {len(data)} compras")

        return {
            'proveedor': proveedor.nombre,
            'total_compras': len(data),
            'total_comprado': sum(float(c['total']) for c in data),
            'total_pagado': sum(float(c['monto_pagado']) for c in data),
            'total_pendiente': sum(float(c['monto_pendiente']) for c in data),
            'compras': data
        }

    @staticmethod
    def obtener_historial_ordenes(proveedor: Proveedor) -> Dict[str, Any]:
        """
        Obtiene historial completo de órdenes de compra de un proveedor.

        Args:
            proveedor: Proveedor para el cual obtener historial

        Returns:
            Diccionario con lista de órdenes y estadísticas
        """
        from compras.models import OrdenCompra

        ordenes = OrdenCompra.objects.filter(proveedor=proveedor).order_by('-fecha_emision')

        data = [{
            'id': o.id,
            'fecha_emision': o.fecha_emision,
            'fecha_entrega_esperada': o.fecha_entrega_esperada,
            'estado': o.estado,
            'total': float(o.total),
            'subtotal': float(o.subtotal),
            'impuestos': float(o.impuestos),
            'descuentos': float(o.descuentos)
        } for o in ordenes]

        logger.info(f"Historial de órdenes obtenido para proveedor {proveedor.nombre}: {len(data)} órdenes")

        return {
            'proveedor': proveedor.nombre,
            'total_ordenes': len(data),
            'total_ordenado': sum(float(o['total']) for o in data),
            'ordenes': data
        }

    @staticmethod
    def obtener_resumen_completo(proveedor: Proveedor) -> Dict[str, Any]:
        """
        Obtiene resumen completo del proveedor con todas las estadísticas.

        Args:
            proveedor: Proveedor para el cual obtener resumen

        Returns:
            Diccionario con resumen completo
        """
        estadisticas_compras = ServicioProveedor.obtener_estadisticas_compras(proveedor)
        estadisticas_ordenes = ServicioProveedor.obtener_estadisticas_ordenes(proveedor)

        logger.info(f"Resumen completo obtenido para proveedor {proveedor.nombre}")

        return {
            'estadisticas': {
                **estadisticas_compras,
                **estadisticas_ordenes,
            }
        }

    @staticmethod
    def obtener_proveedores_activos_por_empresa(empresa_id: int) -> List[Proveedor]:
        """
        Obtiene todos los proveedores activos de una empresa.

        Args:
            empresa_id: ID de la empresa

        Returns:
            Lista de proveedores activos
        """
        return list(Proveedor.objects.filter(
            empresa_id=empresa_id,
            activo=True
        ).order_by('nombre'))

    @staticmethod
    def buscar_proveedores(
        termino: str,
        empresa_id: int,
        solo_activos: bool = True
    ) -> List[Proveedor]:
        """
        Busca proveedores por término en nombre, identificación o contacto.

        Args:
            termino: Término de búsqueda
            empresa_id: ID de la empresa
            solo_activos: Si solo debe buscar en proveedores activos

        Returns:
            Lista de proveedores que coinciden
        """
        from django.db.models import Q

        qs = Proveedor.objects.filter(
            empresa_id=empresa_id
        ).filter(
            Q(nombre__icontains=termino) |
            Q(numero_identificacion__icontains=termino) |
            Q(telefono__icontains=termino) |
            Q(correo_electronico__icontains=termino)
        )

        if solo_activos:
            qs = qs.filter(activo=True)

        return list(qs.order_by('nombre'))
