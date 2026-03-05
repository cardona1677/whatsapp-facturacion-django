from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from .models import MensajeWhatsApp
import json
import requests
from urllib.parse import unquote

# ============================================
# MODO SIMULACIÓN - Para pruebas
# ============================================
MODO_SIMULACION = True  # Cambiar a False para usar Twilio real
# ============================================


@csrf_exempt
@require_http_methods(["GET"])
def enviar_factura_url(request):
    """
    API para enviar mensaje de WhatsApp desde URL con query parameters
    
    Ejemplo de uso:
    GET https://whatsapp.oficinapro-mail.com?client_name=Juan%20Perez&company_name=Grupo%20Familia&invoice_name=FE154&invoice_amount=150000&invoice_id=1545&company_domain=somosbdc.oficinapro.co&client_phone=573045328385
    
    Parámetros:
    - client_name: Nombre del cliente (ej: Juan Perez)
    - company_name: Nombre de la empresa (ej: Grupo Familia)
    - invoice_name: Número de factura (ej: FE154)
    - invoice_amount: Valor de la factura (ej: 150000)
    - invoice_id: ID de la factura (ej: 1545)
    - company_domain: Dominio de la empresa (ej: somosbdc.oficinapro.co)
    - client_phone: Teléfono del cliente (ej: 573045328385)
    """
    mensaje_registro = None
    
    try:
        # Obtener parámetros de la URL
        client_name = unquote(request.GET.get('client_name', 'Cliente'))
        company_name = unquote(request.GET.get('company_name', 'Oficinapro'))
        invoice_name = request.GET.get('invoice_name', '')
        invoice_amount = request.GET.get('invoice_amount', '0')
        invoice_id = request.GET.get('invoice_id', '')
        company_domain = request.GET.get('company_domain', '')
        client_phone = request.GET.get('client_phone', '')
        
        # Validar datos requeridos
        if not invoice_name or not client_phone:
            return JsonResponse({
                'success': False,
                'error': 'invoice_name y client_phone son campos requeridos',
                'ejemplo': 'https://whatsapp.oficinapro-mail.com?client_name=Juan%20Perez&company_name=Grupo%20Familia&invoice_name=FE154&invoice_amount=150000&invoice_id=1545&company_domain=somosbdc.oficinapro.co&client_phone=573045328385'
            }, status=400)
        
        # Asegurar que el teléfono tenga el formato correcto (+57...)
        telefono = client_phone if client_phone.startswith('+') else f'+{client_phone}'
        
        # Construir el link según especificaciones: https://[company_domain]/invoice/[invoice_id]
        if company_domain and invoice_id:
            link_factura = f"https://{company_domain}/invoice/{invoice_id}"
        else:
            link_factura = f"{settings.BASE_URL}/facturas/{invoice_name}"
        
        # Formatear el valor (agregar $ y separadores de miles si es necesario)
        try:
            valor_formateado = f"${int(invoice_amount):,}"
        except:
            valor_formateado = f"${invoice_amount}"
        
        # Crear mensaje personalizado (para referencia en BD)
        mensaje = f"""Estimado {client_name}, la empresa {company_name} ha emitido la factura número {invoice_name} por un valor de {valor_formateado}. Puede consultarla en el siguiente enlace: {link_factura}. Si tiene alguna inquietud, por favor comuníquese con nosotros."""
        
        # ============================================
        # CREAR REGISTRO EN BASE DE DATOS
        # ============================================
        mensaje_registro = MensajeWhatsApp.objects.create(
            numero_factura=invoice_name,
            telefono=telefono,
            nombre_cliente=client_name,
            mensaje=mensaje,
            link_factura=link_factura,
            modo='SIMULACION' if MODO_SIMULACION else 'REAL',
            estado='queued'
        )
        
        print(f"\n✅ Registro creado en BD: ID={mensaje_registro.id}")
        
        # ============================================
        # MODO SIMULACIÓN
        # ============================================
        if MODO_SIMULACION:
            print("\n" + "="*70)
            print("🧪 MODO SIMULACIÓN ACTIVADO")
            print("="*70)
            print(f"📱 De: whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}")
            print(f"📱 Para: whatsapp:{telefono}")
            print(f"👤 Cliente: {client_name}")
            print(f"🏪 Empresa: {company_name}")
            print(f"📄 Factura: {invoice_name}")
            print(f"💰 Valor: {valor_formateado}")
            print(f"🔗 Link: {link_factura}")
            print(f"💾 ID Registro BD: {mensaje_registro.id}")
            print(f"📋 Template SID: {settings.TWILIO_WHATSAPP_TEMPLATE_SID}")
            print(f"\n📝 Mensaje que se enviará:")
            print("-" * 70)
            print(mensaje)
            print("="*70 + "\n")
            
            # Actualizar registro con simulación
            mensaje_registro.twilio_sid = f'SM_simulado_{mensaje_registro.id}'
            mensaje_registro.estado = 'sent'
            mensaje_registro.fecha_envio = timezone.now()
            mensaje_registro.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Mensaje enviado correctamente (SIMULADO)',
                'modo': 'SIMULACION',
                'registro_id': mensaje_registro.id,
                'datos': {
                    'client_name': client_name,
                    'company_name': company_name,
                    'invoice_name': invoice_name,
                    'invoice_amount': valor_formateado,
                    'telefono': telefono,
                    'link': link_factura,
                    'sid': mensaje_registro.twilio_sid,
                    'estado': mensaje_registro.estado
                }
            }, status=200)
        
        # ============================================
        # MODO REAL - USAR PLANTILLA APROBADA
        # ============================================
        
        if not all([settings.TWILIO_ACCOUNT_SID, 
                   settings.TWILIO_AUTH_TOKEN, 
                   settings.TWILIO_WHATSAPP_NUMBER,
                   settings.TWILIO_WHATSAPP_TEMPLATE_SID]):
            mensaje_registro.marcar_como_fallido('Credenciales o Template SID no configurados')
            return JsonResponse({
                'success': False,
                'error': 'Credenciales de Twilio o Template SID no configurados',
                'registro_id': mensaje_registro.id
            }, status=500)
        
        print(f"\n📤 Enviando mensaje REAL por WhatsApp (con plantilla aprobada)...")
        print(f"💾 ID Registro BD: {mensaje_registro.id}")
        print(f"📱 De: whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}")
        print(f"📱 Para: whatsapp:{telefono}")
        print(f"📋 Template SID: {settings.TWILIO_WHATSAPP_TEMPLATE_SID}")
        
        # Variables según plantilla aprobada:
        # Estimado {{1}}, la empresa {{2}} ha emitido la factura número {{3}}
        # por un valor de {{4}}.
        # Puede consultarla en el siguiente enlace: {{5}}.
        # Si tiene alguna inquietud, por favor comuníquese con nosotros.
        
        content_variables = json.dumps({
            "1": client_name,         # {{1}} nombre del cliente
            "2": company_name,        # {{2}} nombre de la empresa
            "3": invoice_name,        # {{3}} número de factura
            "4": valor_formateado,    # {{4}} valor/monto
            "5": link_factura         # {{5}} link para consultar
        })
        
        print(f"\n📝 Variables de contenido:")
        print(f"  {content_variables}")
        print(f"\n📄 Mensaje que se enviará:")
        print("-" * 70)
        print(mensaje)
        print("-" * 70)
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

        response = requests.post(
            url,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            data={
                "From": f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                "To": f"whatsapp:{telefono}",
                "ContentSid": settings.TWILIO_WHATSAPP_TEMPLATE_SID,
                "ContentVariables": content_variables
            },
            timeout=10
        )

        print(f"\n📊 Status Code: {response.status_code}")
        
        if response.status_code == 201:
            response_data = response.json()
            
            # Actualizar registro
            mensaje_registro.twilio_sid = response_data.get('sid')
            mensaje_registro.estado = response_data.get('status', 'sent')
            mensaje_registro.precio = response_data.get('price')
            mensaje_registro.fecha_envio = timezone.now()
            mensaje_registro.datos_adicionales = response_data
            mensaje_registro.save()
            
            print(f"✅ Mensaje enviado exitosamente!")
            print(f"🆔 SID: {mensaje_registro.twilio_sid}")
            print(f"📊 Estado: {mensaje_registro.estado}")
            print(f"\n🎉 ¡Mensaje en cola para entrega!")
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Mensaje enviado correctamente usando plantilla aprobada',
                'modo': 'REAL',
                'registro_id': mensaje_registro.id,
                'datos': {
                    'client_name': client_name,
                    'company_name': company_name,
                    'invoice_name': invoice_name,
                    'invoice_amount': valor_formateado,
                    'telefono': telefono,
                    'template_sid': settings.TWILIO_WHATSAPP_TEMPLATE_SID,
                    'sid': mensaje_registro.twilio_sid,
                    'estado': mensaje_registro.estado,
                    'link': link_factura
                }
            }, status=200)
        else:
            error_data = response.json()
            mensaje_registro.marcar_como_fallido(error_data)
            
            print(f"❌ Error de Twilio: {error_data}")
            
            return JsonResponse({
                'success': False,
                'error': 'Error al enviar a Twilio',
                'detalle': error_data,
                'registro_id': mensaje_registro.id
            }, status=response.status_code)
            
    except Exception as e:
        if mensaje_registro:
            mensaje_registro.marcar_como_fallido(str(e))
        
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False,
            'error': str(e),
            'registro_id': mensaje_registro.id if mensaje_registro else None
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def enviar_factura_whatsapp(request):
    """
    API LEGACY para enviar mensaje de WhatsApp con JSON POST
    (Mantener para compatibilidad con tests existentes)
    """
    mensaje_registro = None
    
    try:
        # Parsear datos del request
        data = json.loads(request.body)
        numero_factura = data.get('numero_factura')
        telefono = data.get('telefono')
        nombre_cliente = data.get('nombre_cliente', 'Cliente')
        nombre_comercio = data.get('nombre_comercio', 'Oficinapro')
        valor_factura = data.get('valor_factura', '0')
        
        # Validar datos requeridos
        if not numero_factura or not telefono:
            return JsonResponse({
                'success': False,
                'error': 'numero_factura y telefono son campos requeridos'
            }, status=400)
        
        # Formar el link de la factura
        link_factura = f"{settings.BASE_URL}/facturas/{numero_factura}"
        
        # Crear mensaje personalizado (para referencia en BD)
        mensaje = f"""Estimado {nombre_cliente}, la empresa {nombre_comercio} ha emitido la factura número {numero_factura} por un valor de {valor_factura}. Puede consultarla en el siguiente enlace: {link_factura}. Si tiene alguna inquietud, por favor comuníquese con nosotros."""
        
        mensaje_registro = MensajeWhatsApp.objects.create(
            numero_factura=numero_factura,
            telefono=telefono,
            nombre_cliente=nombre_cliente,
            mensaje=mensaje,
            link_factura=link_factura,
            modo='SIMULACION' if MODO_SIMULACION else 'REAL',
            estado='queued'
        )
        
        print(f"\n✅ Registro creado en BD: ID={mensaje_registro.id}")
        
        if MODO_SIMULACION:
            mensaje_registro.twilio_sid = f'SM_simulado_{mensaje_registro.id}'
            mensaje_registro.estado = 'sent'
            mensaje_registro.fecha_envio = timezone.now()
            mensaje_registro.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Mensaje enviado correctamente (SIMULADO)',
                'modo': 'SIMULACION',
                'registro_id': mensaje_registro.id
            }, status=200)
        
        if not all([settings.TWILIO_ACCOUNT_SID, 
                   settings.TWILIO_AUTH_TOKEN, 
                   settings.TWILIO_WHATSAPP_NUMBER,
                   settings.TWILIO_WHATSAPP_TEMPLATE_SID]):
            mensaje_registro.marcar_como_fallido('Credenciales o Template SID no configurados')
            return JsonResponse({
                'success': False,
                'error': 'Credenciales de Twilio o Template SID no configurados'
            }, status=500)
        
        content_variables = json.dumps({
            "1": nombre_cliente,
            "2": nombre_comercio,
            "3": numero_factura,
            "4": valor_factura,
            "5": link_factura
        })
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

        response = requests.post(
            url,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            data={
                "From": f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                "To": f"whatsapp:{telefono}",
                "ContentSid": settings.TWILIO_WHATSAPP_TEMPLATE_SID,
                "ContentVariables": content_variables
            },
            timeout=10
        )
        
        if response.status_code == 201:
            response_data = response.json()
            mensaje_registro.twilio_sid = response_data.get('sid')
            mensaje_registro.estado = response_data.get('status', 'sent')
            mensaje_registro.precio = response_data.get('price')
            mensaje_registro.fecha_envio = timezone.now()
            mensaje_registro.datos_adicionales = response_data
            mensaje_registro.save()
            
            return JsonResponse({
                'success': True,
                'mensaje': 'Mensaje enviado correctamente',
                'registro_id': mensaje_registro.id,
                'datos': {
                    'sid': mensaje_registro.twilio_sid,
                    'estado': mensaje_registro.estado
                }
            }, status=200)
        else:
            error_data = response.json()
            mensaje_registro.marcar_como_fallido(error_data)
            return JsonResponse({
                'success': False,
                'error': 'Error al enviar a Twilio',
                'detalle': error_data
            }, status=response.status_code)
            
    except Exception as e:
        if mensaje_registro:
            mensaje_registro.marcar_como_fallido(str(e))
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def health_check(request):
    """Endpoint para verificar el servicio"""
    config_ok = all([
        settings.TWILIO_ACCOUNT_SID,
        settings.TWILIO_AUTH_TOKEN,
        settings.TWILIO_WHATSAPP_NUMBER,
        settings.TWILIO_WHATSAPP_TEMPLATE_SID
    ])
    
    try:
        total = MensajeWhatsApp.objects.count()
        enviados = MensajeWhatsApp.objects.filter(estado='sent').count()
        fallidos = MensajeWhatsApp.objects.filter(estado='failed').count()
    except:
        total = enviados = fallidos = 0
    
    modo = "SIMULACION ✅" if MODO_SIMULACION else "REAL 🔴"
    
    return JsonResponse({
        'status': 'online',
        'servicio': 'WhatsApp Facturación API',
        'modo': modo,
        'configuracion_twilio': 'OK' if config_ok else 'FALTA CONFIGURACIÓN',
        'estadisticas': {
            'total_mensajes': total,
            'enviados': enviados,
            'fallidos': fallidos
        }
    })


@require_http_methods(["GET"])
def historial_mensajes(request):
    """Consultar historial de mensajes"""
    numero_factura = request.GET.get('numero_factura')
    telefono = request.GET.get('telefono')
    estado = request.GET.get('estado')
    limit = int(request.GET.get('limit', 50))
    
    mensajes = MensajeWhatsApp.objects.all()
    
    if numero_factura:
        mensajes = mensajes.filter(numero_factura__icontains=numero_factura)
    if telefono:
        mensajes = mensajes.filter(telefono__icontains=telefono)
    if estado:
        mensajes = mensajes.filter(estado=estado)
    
    mensajes = mensajes[:limit]
    
    data = []
    for msg in mensajes:
        data.append({
            'id': msg.id,
            'numero_factura': msg.numero_factura,
            'telefono': msg.telefono,
            'nombre_cliente': msg.nombre_cliente,
            'twilio_sid': msg.twilio_sid,
            'estado': msg.estado,
            'modo': msg.modo,
            'fecha_creacion': msg.fecha_creacion.isoformat(),
            'fecha_envio': msg.fecha_envio.isoformat() if msg.fecha_envio else None,
            'error_mensaje': msg.error_mensaje
        })
    
    return JsonResponse({
        'success': True,
        'total': len(data),
        'mensajes': data
    })

def dashboard(request):
    return render(request, 'whatsapp_service/dashboard.html')

@require_http_methods(["GET"])
def dashboard_stats(request):
    """Stats para el dashboard - datos reales de la BD"""
    from django.db.models import Count, Sum, Q
    from django.utils import timezone
    from datetime import timedelta
    import json

    # Rango de tiempo
    rango = request.GET.get('range', '30d')
    dias = 7 if rango == '7d' else 90 if rango == '90d' else 30
    fecha_inicio = timezone.now() - timedelta(days=dias)
    fecha_inicio_anterior = fecha_inicio - timedelta(days=dias)

    qs = MensajeWhatsApp.objects.filter(fecha_creacion__gte=fecha_inicio)
    qs_anterior = MensajeWhatsApp.objects.filter(
        fecha_creacion__gte=fecha_inicio_anterior,
        fecha_creacion__lt=fecha_inicio
    )

    # KPIs periodo actual
    total = qs.count()
    entregados = qs.filter(estado='delivered').count()
    fallidos = qs.filter(estado='failed').count()
    costo = qs.aggregate(total=Sum('precio'))['total'] or 0

    # KPIs periodo anterior (para tendencias)
    total_ant = qs_anterior.count()
    entregados_ant = qs_anterior.filter(estado='delivered').count()
    fallidos_ant = qs_anterior.filter(estado='failed').count()

    tasa = round((entregados / total * 100), 1) if total > 0 else 0
    tasa_ant = round((entregados_ant / total_ant * 100), 1) if total_ant > 0 else 0

    def tendencia(actual, anterior):
        if anterior == 0:
            return 0
        return round(((actual - anterior) / anterior) * 100, 1)

    # Distribución por estado
    estados = list(
        MensajeWhatsApp.objects.filter(fecha_creacion__gte=fecha_inicio)
        .values('estado')
        .annotate(total=Count('id'))
    )

    # Envíos por día (últimos N días)
    from django.db.models.functions import TruncDate
    por_dia_raw = (
        qs.annotate(dia=TruncDate('fecha_creacion'))
        .values('dia', 'estado')
        .annotate(total=Count('id'))
        .order_by('dia')
    )

    # Agrupar por día
    dias_map = {}
    for row in por_dia_raw:
        key = row['dia'].strftime('%d/%m')
        if key not in dias_map:
            dias_map[key] = {'dia': key, 'delivered': 0, 'sent': 0, 'failed': 0, 'otros': 0}
        estado_r = row['estado']
        if estado_r in ('delivered', 'sent', 'failed'):
            dias_map[key][estado_r] += row['total']
        else:
            dias_map[key]['otros'] += row['total']

    por_dia = list(dias_map.values())

    # Mensajes recientes
    recientes = []
    for msg in MensajeWhatsApp.objects.order_by('-fecha_creacion')[:20]:
        recientes.append({
            'inv': msg.numero_factura,
            'client': msg.nombre_cliente,
            'phone': msg.telefono,
            'estado': msg.estado,
            'modo': msg.modo,
            'date': msg.fecha_creacion.strftime('%d/%m %H:%M'),
            'cost': f'${float(msg.precio):.4f}' if msg.precio else '---',
        })

    return JsonResponse({
        'kpis': {
            'total': total,
            'tasa_entrega': tasa,
            'costo': float(costo),
            'fallidos': fallidos,
            'tendencia_total': tendencia(total, total_ant),
            'tendencia_tasa': tendencia(tasa, tasa_ant),
            'tendencia_fallidos': tendencia(fallidos, fallidos_ant),
        },
        'estados': estados,
        'por_dia': por_dia,
        'recientes': recientes,
    })