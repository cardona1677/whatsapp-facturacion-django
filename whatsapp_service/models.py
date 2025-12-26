from django.db import models
from django.utils import timezone


class MensajeWhatsApp(models.Model):
    """
    Modelo para registrar todos los mensajes enviados por WhatsApp
    """
    
    # Estados posibles del mensaje
    ESTADO_CHOICES = [
        ('queued', 'En cola'),
        ('sending', 'Enviando'),
        ('sent', 'Enviado'),
        ('delivered', 'Entregado'),
        ('read', 'Leído'),
        ('failed', 'Fallido'),
        ('undelivered', 'No entregado'),
    ]
    
    # Información del destinatario
    numero_factura = models.CharField(max_length=100, db_index=True)
    telefono = models.CharField(max_length=20)
    nombre_cliente = models.CharField(max_length=200)
    
    # Información del mensaje
    mensaje = models.TextField()
    link_factura = models.URLField(max_length=500)
    
    # Respuesta de Twilio
    twilio_sid = models.CharField(max_length=100, unique=True, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='queued')
    precio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Metadata
    modo = models.CharField(max_length=20, default='REAL')
    error_mensaje = models.TextField(null=True, blank=True)
    
    # Timestamps
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_envio = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Información adicional (JSON)
    datos_adicionales = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'mensajes_whatsapp'
        ordering = ['-fecha_creacion']
        verbose_name = 'Mensaje WhatsApp'
        verbose_name_plural = 'Mensajes WhatsApp'
    
    def __str__(self):
        return f"{self.numero_factura} - {self.telefono} - {self.estado}"
    
    def marcar_como_enviado(self):
        self.estado = 'sent'
        self.fecha_envio = timezone.now()
        self.save()
    
    def marcar_como_entregado(self):
        self.estado = 'delivered'
        self.fecha_entrega = timezone.now()
        self.save()
    
    def marcar_como_fallido(self, error):
        self.estado = 'failed'
        self.error_mensaje = str(error)
        self.save()