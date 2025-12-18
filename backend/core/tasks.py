"""
Django 6.0 Background Tasks para notificaciones y emails.

Estas tareas permiten enviar notificaciones de forma asíncrona,
evitando bloquear las operaciones del usuario.
"""
from django.tasks import task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models
import logging

logger = logging.getLogger(__name__)


@task
def enviar_email_notificacion(
    destinatario: str,
    asunto: str,
    mensaje: str,
    mensaje_html: str = None
) -> dict:
    """
    Envía un email de notificación.

    Args:
        destinatario: Email del destinatario
        asunto: Asunto del email
        mensaje: Contenido del email en texto plano
        mensaje_html: Contenido del email en HTML (opcional)

    Returns:
        dict con el resultado del envío
    """
    logger.info(f"Enviando email a {destinatario}: {asunto}")

    try:
        if mensaje_html:
            email = EmailMultiAlternatives(
                subject=asunto,
                body=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[destinatario]
            )
            email.attach_alternative(mensaje_html, "text/html")
            email.send()
        else:
            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destinatario],
                fail_silently=False
            )

        logger.info(f"Email enviado exitosamente a {destinatario}")
        return {
            'status': 'sent',
            'destinatario': destinatario,
            'asunto': asunto
        }

    except Exception as e:
        logger.error(f"Error enviando email a {destinatario}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@task
def notificar_factura_creada(factura_id: int) -> dict:
    """
    Envía notificación de factura creada al cliente.

    Args:
        factura_id: ID de la factura

    Returns:
        dict con el resultado
    """
    from ventas.models import Factura

    logger.info(f"Notificando creación de factura {factura_id}")

    try:
        factura = Factura.objects.select_related(
            'cliente', 'empresa', 'usuario_creacion'
        ).get(id=factura_id)
        cliente = factura.cliente

        if not cliente.email:
            return {
                'status': 'skipped',
                'reason': 'Cliente sin email'
            }

        asunto = f"Factura #{factura.numero_factura or factura.id} - {factura.empresa.nombre}"

        # Mensaje de texto plano
        mensaje = f"""
Estimado/a {cliente.nombre},

Se ha generado una nueva factura a su nombre.

Detalles:
- Número: {factura.numero_factura or factura.id}
- Fecha: {factura.fecha.strftime('%d/%m/%Y')}
- Total: RD$ {factura.total:,.2f}
- Estado: {factura.get_estado_display()}

Gracias por su preferencia.

{factura.empresa.nombre}
        """

        # Mensaje HTML usando template
        try:
            mensaje_html = render_to_string('emails/factura_creada.html', {
                'factura': factura,
                'empresa': factura.empresa
            })
        except Exception as e:
            logger.warning(f"Error renderizando template HTML: {e}")
            mensaje_html = None

        result = enviar_email_notificacion.call(
            destinatario=cliente.email,
            asunto=asunto,
            mensaje=mensaje,
            mensaje_html=mensaje_html
        )

        return {
            'status': 'completed',
            'factura_id': factura_id,
            'email_result': result
        }

    except Factura.DoesNotExist:
        return {
            'status': 'error',
            'error': f'Factura {factura_id} no encontrada'
        }
    except Exception as e:
        logger.error(f"Error notificando factura {factura_id}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@task
def notificar_cxc_vencida(cuenta_id: int) -> dict:
    """
    Envía notificación de cuenta por cobrar vencida al cliente.

    Args:
        cuenta_id: ID de la cuenta por cobrar

    Returns:
        dict con el resultado
    """
    from cuentas_cobrar.models import CuentaPorCobrar
    from django.utils import timezone

    logger.info(f"Notificando CxC vencida {cuenta_id}")

    try:
        cuenta = CuentaPorCobrar.objects.select_related(
            'cliente', 'empresa', 'factura'
        ).get(id=cuenta_id)
        cliente = cuenta.cliente

        if not cliente.email:
            return {
                'status': 'skipped',
                'reason': 'Cliente sin email'
            }

        dias_vencidos = (timezone.now().date() - cuenta.fecha_vencimiento).days

        asunto = f"Recordatorio de pago - Cuenta vencida - {cuenta.empresa.nombre}"

        # Mensaje de texto plano
        mensaje = f"""
Estimado/a {cliente.nombre},

Le recordamos que tiene una cuenta pendiente de pago con nosotros.

Detalles:
- Factura: {cuenta.factura.numero_factura if cuenta.factura else 'N/A'}
- Fecha vencimiento: {cuenta.fecha_vencimiento.strftime('%d/%m/%Y')}
- Días vencidos: {dias_vencidos}
- Monto pendiente: RD$ {cuenta.monto_pendiente:,.2f}

Por favor, realice el pago a la brevedad posible.

Gracias por su atención.

{cuenta.empresa.nombre}
        """

        # Mensaje HTML usando template
        try:
            mensaje_html = render_to_string('emails/cxc_vencida.html', {
                'cuenta': cuenta,
                'empresa': cuenta.empresa,
                'dias_vencidos': dias_vencidos
            })
        except Exception as e:
            logger.warning(f"Error renderizando template HTML: {e}")
            mensaje_html = None

        result = enviar_email_notificacion.call(
            destinatario=cliente.email,
            asunto=asunto,
            mensaje=mensaje,
            mensaje_html=mensaje_html
        )

        return {
            'status': 'completed',
            'cuenta_id': cuenta_id,
            'email_result': result
        }

    except CuentaPorCobrar.DoesNotExist:
        return {
            'status': 'error',
            'error': f'Cuenta {cuenta_id} no encontrada'
        }
    except Exception as e:
        logger.error(f"Error notificando CxC {cuenta_id}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }


@task
def notificar_stock_bajo(alerta_id: int = None, empresa_id: int = None) -> dict:
    """
    Envía notificación de stock bajo a los administradores.

    Puede recibir un alerta_id específico o un empresa_id para notificar
    todos los productos con stock bajo de una empresa.

    Args:
        alerta_id: ID de la alerta de inventario (opcional)
        empresa_id: ID de la empresa para notificar múltiples alertas (opcional)

    Returns:
        dict con el resultado
    """
    from inventario.models import AlertaInventario, InventarioProducto
    from usuarios.models import User

    logger.info(f"Notificando alerta de stock (alerta_id={alerta_id}, empresa_id={empresa_id})")

    try:
        if alerta_id:
            # Modo: notificar una alerta específica
            alerta = AlertaInventario.objects.select_related(
                'producto', 'almacen', 'empresa'
            ).get(id=alerta_id)

            empresa = alerta.empresa
            productos_stock_bajo = [{
                'producto': alerta.producto,
                'almacen': alerta.almacen,
                'cantidad_disponible': 0,  # Se llenará después
                'stock_minimo': alerta.producto.stock_minimo
            }]

        elif empresa_id:
            # Modo: notificar todos los productos con stock bajo de la empresa
            from empresas.models import Empresa
            empresa = Empresa.objects.get(id=empresa_id)

            productos_stock_bajo = list(
                InventarioProducto.objects.select_related('producto', 'almacen')
                .filter(
                    empresa=empresa,
                    cantidad_disponible__lte=models.F('stock_minimo')
                )
            )

            if not productos_stock_bajo:
                return {
                    'status': 'skipped',
                    'reason': 'No hay productos con stock bajo'
                }
        else:
            return {
                'status': 'error',
                'error': 'Debe especificar alerta_id o empresa_id'
            }

        # Obtener administradores de la empresa
        admins = User.objects.filter(
            empresa=empresa,
            is_staff=True,
            is_active=True
        ).exclude(email='')

        if not admins.exists():
            return {
                'status': 'skipped',
                'reason': 'No hay administradores con email'
            }

        asunto = f"Alerta de inventario - Stock bajo - {empresa.nombre}"

        # Mensaje de texto plano
        productos_texto = "\n".join([
            f"- {p.producto.nombre} ({p.almacen.nombre}): {p.cantidad_disponible} unidades"
            for p in productos_stock_bajo
        ])
        mensaje = f"""
Alerta de Inventario - Stock Bajo

Los siguientes productos tienen stock bajo y requieren reabastecimiento:

{productos_texto}

Por favor, tome las acciones necesarias para reabastecer el inventario.

Sistema de Facturación - {empresa.nombre}
        """

        # Mensaje HTML usando template
        try:
            mensaje_html = render_to_string('emails/stock_bajo.html', {
                'productos': productos_stock_bajo,
                'empresa': empresa
            })
        except Exception as e:
            logger.warning(f"Error renderizando template HTML: {e}")
            mensaje_html = None

        enviados = 0
        for admin in admins:
            result = enviar_email_notificacion.call(
                destinatario=admin.email,
                asunto=asunto,
                mensaje=mensaje,
                mensaje_html=mensaje_html
            )
            if result.get('status') == 'sent':
                enviados += 1

        return {
            'status': 'completed',
            'alerta_id': alerta_id,
            'empresa_id': empresa_id,
            'productos_notificados': len(productos_stock_bajo),
            'emails_enviados': enviados
        }

    except AlertaInventario.DoesNotExist:
        return {
            'status': 'error',
            'error': f'Alerta {alerta_id} no encontrada'
        }
    except Exception as e:
        logger.error(f"Error notificando alerta stock: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
