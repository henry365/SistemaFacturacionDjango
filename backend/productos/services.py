"""
Servicios para el módulo Productos

Este módulo centraliza la lógica de negocio para operaciones
complejas relacionadas con productos.
"""
import logging
from decimal import Decimal
from typing import List, Dict, Optional, Any
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Categoria, Producto, ImagenProducto, ReferenciasCruzadas
from .constants import (
    TIPO_REFERENCIA_SUSTITUTO,
    TIPOS_PRODUCTO_SIN_STOCK,
    ITBIS_DEFAULT
)

logger = logging.getLogger(__name__)


class ServicioProducto:
    """
    Servicio para operaciones complejas con productos.
    """

    @staticmethod
    def calcular_precio_final(
        precio_base: Decimal,
        descuento_porcentaje: Decimal = Decimal('0'),
        itbis_porcentaje: Decimal = Decimal(str(ITBIS_DEFAULT)),
        es_exento: bool = False
    ) -> Decimal:
        """
        Calcula el precio final de un producto.

        Args:
            precio_base: Precio base del producto
            descuento_porcentaje: Porcentaje de descuento (0-100)
            itbis_porcentaje: Porcentaje de ITBIS (0-100)
            es_exento: Si el producto está exento de ITBIS

        Returns:
            Precio final con descuento e ITBIS aplicados
        """
        # Aplicar descuento
        precio_con_descuento = precio_base
        if descuento_porcentaje > 0:
            descuento = precio_base * (descuento_porcentaje / Decimal('100'))
            precio_con_descuento = precio_base - descuento

        # Aplicar ITBIS si no es exento
        if not es_exento and itbis_porcentaje > 0:
            itbis = precio_con_descuento * (itbis_porcentaje / Decimal('100'))
            precio_final = precio_con_descuento + itbis
        else:
            precio_final = precio_con_descuento

        return precio_final.quantize(Decimal('0.01'))

    @staticmethod
    @transaction.atomic
    def crear_producto_con_categorias(
        datos_producto: Dict[str, Any],
        categorias_nombres: List[str],
        usuario=None
    ) -> Producto:
        """
        Crea un producto y le asigna categorías.

        Args:
            datos_producto: Diccionario con datos del producto
            categorias_nombres: Lista de nombres de categorías
            usuario: Usuario que crea el producto

        Returns:
            Producto creado
        """
        # Agregar usuario de auditoría
        if usuario:
            datos_producto['usuario_creacion'] = usuario
            datos_producto['usuario_modificacion'] = usuario

        # Crear producto
        producto = Producto.objects.create(**datos_producto)

        # Obtener o crear categorías y asignarlas
        for nombre in categorias_nombres:
            nombre = nombre.strip()
            if nombre:
                categoria, created = Categoria.objects.get_or_create(
                    nombre=nombre,
                    defaults={
                        'usuario_creacion': usuario,
                        'usuario_modificacion': usuario
                    } if usuario else {}
                )
                producto.categorias.add(categoria)

        logger.info(
            f"Producto creado: {producto.codigo_sku} - {producto.nombre} "
            f"con {producto.categorias.count()} categorías"
        )

        return producto

    @staticmethod
    def obtener_productos_por_tipo(tipo_producto: str, solo_activos: bool = True) -> List[Producto]:
        """
        Obtiene productos filtrados por tipo.

        Args:
            tipo_producto: Tipo de producto (ALMACENABLE, SERVICIO, etc.)
            solo_activos: Si solo debe retornar productos activos

        Returns:
            Lista de productos del tipo especificado
        """
        qs = Producto.objects.filter(tipo_producto=tipo_producto)
        if solo_activos:
            qs = qs.filter(activo=True)
        return list(qs)

    @staticmethod
    def buscar_productos(
        termino: str,
        solo_activos: bool = True,
        categorias: Optional[List[int]] = None
    ) -> List[Producto]:
        """
        Busca productos por término en código SKU, nombre o descripción.

        Args:
            termino: Término de búsqueda
            solo_activos: Si solo debe buscar en productos activos
            categorias: IDs de categorías para filtrar

        Returns:
            Lista de productos que coinciden
        """
        from django.db.models import Q

        qs = Producto.objects.filter(
            Q(codigo_sku__icontains=termino) |
            Q(nombre__icontains=termino) |
            Q(descripcion__icontains=termino)
        )

        if solo_activos:
            qs = qs.filter(activo=True)

        if categorias:
            qs = qs.filter(categorias__id__in=categorias).distinct()

        return list(qs)


class ServicioReferencias:
    """
    Servicio para gestión de referencias cruzadas entre productos.
    """

    @staticmethod
    @transaction.atomic
    def crear_referencia_bidireccional(
        producto_origen: Producto,
        producto_destino: Producto,
        tipo: str,
        usuario=None
    ) -> ReferenciasCruzadas:
        """
        Crea una referencia cruzada bidireccional entre dos productos.

        Args:
            producto_origen: Producto origen
            producto_destino: Producto destino
            tipo: Tipo de referencia
            usuario: Usuario que crea la referencia

        Returns:
            Referencia creada
        """
        if producto_origen == producto_destino:
            raise ValidationError("No se puede crear una referencia al mismo producto")

        referencia = ReferenciasCruzadas.objects.create(
            producto_origen=producto_origen,
            producto_destino=producto_destino,
            tipo=tipo,
            bidireccional=True,
            usuario_creacion=usuario,
            usuario_modificacion=usuario
        )

        logger.info(
            f"Referencia bidireccional creada: {producto_origen.codigo_sku} <-> "
            f"{producto_destino.codigo_sku} ({tipo})"
        )

        return referencia

    @staticmethod
    def obtener_sustitutos(producto: Producto) -> List[Producto]:
        """
        Obtiene todos los productos sustitutos de un producto.

        Args:
            producto: Producto para el cual buscar sustitutos

        Returns:
            Lista de productos sustitutos
        """
        # Sustitutos donde el producto es origen
        sustitutos_salientes = Producto.objects.filter(
            referencias_hacia__producto_origen=producto,
            referencias_hacia__tipo=TIPO_REFERENCIA_SUSTITUTO,
            referencias_hacia__activa=True,
            activo=True
        )

        # Sustitutos bidireccionales donde el producto es destino
        sustitutos_entrantes = Producto.objects.filter(
            referencias_desde__producto_destino=producto,
            referencias_desde__tipo=TIPO_REFERENCIA_SUSTITUTO,
            referencias_desde__bidireccional=True,
            referencias_desde__activa=True,
            activo=True
        )

        # Combinar y eliminar duplicados
        sustitutos = list(sustitutos_salientes) + list(sustitutos_entrantes)
        return list(set(sustitutos))

    @staticmethod
    def obtener_productos_relacionados(
        producto: Producto,
        tipo: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los productos relacionados con un producto.

        Args:
            producto: Producto para el cual buscar relacionados
            tipo: Tipo específico de relación (opcional)

        Returns:
            Lista de diccionarios con información de productos relacionados
        """
        resultado = []

        # Referencias donde el producto es origen
        qs_origen = ReferenciasCruzadas.objects.filter(
            producto_origen=producto,
            activa=True
        ).select_related('producto_destino')

        if tipo:
            qs_origen = qs_origen.filter(tipo=tipo)

        for ref in qs_origen:
            resultado.append({
                'producto': ref.producto_destino,
                'tipo': ref.tipo,
                'tipo_display': ref.get_tipo_display(),
                'direccion': 'saliente',
                'bidireccional': ref.bidireccional
            })

        # Referencias bidireccionales donde el producto es destino
        qs_destino = ReferenciasCruzadas.objects.filter(
            producto_destino=producto,
            bidireccional=True,
            activa=True
        ).select_related('producto_origen')

        if tipo:
            qs_destino = qs_destino.filter(tipo=tipo)

        for ref in qs_destino:
            resultado.append({
                'producto': ref.producto_origen,
                'tipo': ref.tipo,
                'tipo_display': ref.get_tipo_display(),
                'direccion': 'entrante',
                'bidireccional': ref.bidireccional
            })

        return resultado


class ServicioCategoria:
    """
    Servicio para operaciones con categorías.
    """

    @staticmethod
    def obtener_categorias_con_productos(solo_activas: bool = True) -> List[Dict[str, Any]]:
        """
        Obtiene categorías con conteo de productos.

        Args:
            solo_activas: Si solo debe retornar categorías activas

        Returns:
            Lista de diccionarios con categorías y conteos
        """
        from django.db.models import Count

        qs = Categoria.objects.annotate(
            productos_count=Count('productos')
        )

        if solo_activas:
            qs = qs.filter(activa=True)

        return [
            {
                'id': cat.id,
                'nombre': cat.nombre,
                'productos_count': cat.productos_count
            }
            for cat in qs.order_by('nombre')
        ]

    @staticmethod
    def obtener_productos_sin_categoria() -> List[Producto]:
        """
        Obtiene productos que no tienen categoría asignada.

        Returns:
            Lista de productos sin categoría
        """
        return list(Producto.objects.filter(categorias__isnull=True, activo=True))

    @staticmethod
    @transaction.atomic
    def fusionar_categorias(
        categoria_origen: Categoria,
        categoria_destino: Categoria,
        usuario=None
    ) -> int:
        """
        Fusiona una categoría en otra, moviendo todos sus productos.

        Args:
            categoria_origen: Categoría a eliminar
            categoria_destino: Categoría destino
            usuario: Usuario que realiza la operación

        Returns:
            Número de productos movidos
        """
        if categoria_origen == categoria_destino:
            raise ValidationError("No se puede fusionar una categoría consigo misma")

        productos = list(categoria_origen.productos.all())
        count = len(productos)

        for producto in productos:
            producto.categorias.remove(categoria_origen)
            producto.categorias.add(categoria_destino)
            if usuario:
                producto.usuario_modificacion = usuario
                producto.save(update_fields=['usuario_modificacion'])

        # Desactivar categoría origen
        categoria_origen.activa = False
        if usuario:
            categoria_origen.usuario_modificacion = usuario
        categoria_origen.save()

        logger.info(
            f"Categoría '{categoria_origen.nombre}' fusionada en '{categoria_destino.nombre}'. "
            f"{count} productos movidos."
        )

        return count
