from django.urls import path
from . import views

urlpatterns = [
    path('enviar/', views.enviar_factura_whatsapp, name='enviar_factura'),
    path('health/', views.health_check, name='health_check'),
    path('historial/', views.historial_mensajes, name='historial'),  # ← NUEVO
]