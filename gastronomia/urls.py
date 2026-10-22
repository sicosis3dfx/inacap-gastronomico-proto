"""
Sistema Centralizado de Publicación y Consulta Gastronómica — INACAP Sede Renca.
Módulo: gastronomia.urls
================================================================================
Definición de rutas URL para:
  - ''                      -> catalogo_publico: Catálogo estudiantil centralizado.
  - 'panel/'                -> panel_operador: Panel de gestión para el encargado de local.
  - 'api/producto/<pk>/stock/' -> actualizar_stock: Switch interactivo asíncrono de stock (RF03).
  - 'login/' / 'logout/'    -> Autenticación institucional de operadores.
"""

from django.urls import path
from . import views

urlpatterns = [
    # 1. Catálogo público para estudiantes y comunidad (RF02 / RF06)
    path('', views.catalogo_publico, name='catalogo_publico'),

    # 2. Panel privado del encargado de local con aislamiento RBAC (RF01 / OWASP A01)
    path('panel/', views.panel_operador, name='panel_operador'),

    # 3. Endpoint asíncrono de conmutación de stock en 1 clic (RF03 / HU04)
    path('api/producto/<int:pk>/stock/', views.actualizar_stock, name='actualizar_stock'),

    # 4. Flujo de autenticación institucional
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
