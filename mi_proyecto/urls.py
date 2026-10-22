"""
URL configuration for mi_proyecto project.
Sistema Centralizado de Publicación y Consulta Gastronómica — INACAP Sede Renca.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Conectamos las rutas del módulo principal gastronomia a la raíz del sitio
    path('', include('gastronomia.urls')),
    path('api-auth/', include('rest_framework.urls')),
]