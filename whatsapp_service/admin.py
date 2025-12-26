from django.contrib import admin
from .models import MensajeWhatsApp

@admin.register(MensajeWhatsApp)
class MensajeWhatsAppAdmin(admin.ModelAdmin):
    list_display = ('id', 'numero_factura', 'telefono', 'nombre_cliente', 'estado', 'modo', 'fecha_creacion')
    list_filter = ('estado', 'modo', 'fecha_creacion')
    search_fields = ('numero_factura', 'telefono', 'nombre_cliente', 'twilio_sid')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información', {
            'fields': ('numero_factura', 'telefono', 'nombre_cliente', 'mensaje', 'link_factura')
        }),
        ('Estado', {
            'fields': ('twilio_sid', 'estado', 'precio', 'modo', 'error_mensaje')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_envio', 'fecha_entrega', 'fecha_actualizacion')
        }),
    )