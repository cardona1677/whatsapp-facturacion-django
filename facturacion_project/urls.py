"""
URL configuration for facturacion_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# whatsapp_service/urls.py o facturacion_project/urls.py

from django.urls import path
from whatsapp_service import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),

    # NUEVO: Endpoint para recibir por URL (GET)
    path('', views.enviar_factura_url, name='enviar_factura_url'),  # Para whatsapp.oficinapro-mail.com
    
    # LEGACY: Endpoint original (POST JSON)
    path('api/whatsapp/enviar/', views.enviar_factura_whatsapp, name='enviar_factura_whatsapp'),
    
    # Otros endpoints
    path('api/whatsapp/health/', views.health_check, name='health_check'),
    path('api/whatsapp/historial/', views.historial_mensajes, name='historial_mensajes'),
]
