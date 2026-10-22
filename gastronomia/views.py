"""
Sistema Centralizado de Publicación y Consulta Gastronómica — INACAP Sede Renca.
Módulo: gastronomia.views
================================================================================
Capa de control que implementa:
  - catalogo_publico (RF02 / RF06): Consulta centralizada y responsiva con filtro JUNAEB (RF04).
  - panel_operador (RF01 / RBAC): Vista privada con aislamiento estricto por local (OWASP A01 y Ley 21.459).
  - actualizar_stock (RF03 / HU04): Endpoint asíncrono en tiempo real (<2s / RNF02).

================================================================================
JUSTIFICACIÓN DE SEGURIDAD Y CUMPLIMIENTO NORMATIVO:
================================================================================
1. OWASP Top 10 - A01:2021 (Broken Access Control) & LEY CHILENA N° 21.459 (ACCESO INDEBIDO):
   - 'panel_operador' y 'actualizar_stock' aplican '@login_required'.
   - Cada consulta restringe rigurosamente los registros a: Producto.objects.filter(local__operador=request.user).
   - Cualquier intento de interactuar con productos de otro local retorna HTTP 403 (Forbidden),
     neutralizando ataques de Direct Object Reference (IDOR) y preservando la integridad del sistema.
2. OWASP Top 10 - A03:2021 (Injection):
   - Todas las consultas, búsquedas y filtros se canalizan mediante el ORM de Django (consultas parametrizadas).
   - Se prohíbe el uso de SQL crudo o concatenación de parámetros GET/POST.
3. OWASP Top 10 - A02:2021 (Cryptographic Failures & CSRF Protection):
   - El endpoint asíncrono 'actualizar_stock' valida el token CSRF suministrado en el encabezado
     'X-CSRFToken' por la llamada Fetch de la interfaz móvil.
"""

import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Prefetch, Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import MenuDiaForm, ProductoForm
from .models import Local, MenuDia, Producto, PromoFlash


# ==============================================================================
# 1. CATÁLOGO PÚBLICO (RF02 / RF04 / RF06)
# ==============================================================================
def catalogo_publico(request):
    """
    Vista pública responsiva para la comunidad estudiantil de INACAP Sede Renca.
    Permite consultar la oferta gastronómica del Casino Central y los Food Trucks
    sin requerir autenticación (RF06).

    Soporta:
      - Filtro booleano JUNAEB (?junaeb=1) (RF04).
      - Filtro por local (?local=<id>).
      - Búsqueda por texto (?q=<término>) mediante ORM seguro (OWASP A03).
      - Despliegue de promociones flash vigentes (RF05).
    """
    # Lectura y saneamiento de parámetros GET
    junaeb_param = request.GET.get('junaeb', '').strip().lower()
    filtro_junaeb = junaeb_param in ('1', 'true', 'si', 'yes')
    local_id_param = request.GET.get('local', '').strip()
    query_busqueda = request.GET.get('q', '').strip()

    # Base de consulta: productos pertenecientes a locales con jornada activa
    productos_qs = (
        Producto.objects.filter(local__activo=True)
        .select_related('local')
        .order_by('local__nombre', 'nombre')
    )

    # Filtrado estricto JUNAEB (RF04)
    if filtro_junaeb:
        productos_qs = productos_qs.filter(acepta_junaeb=True)

    # Filtrado por local específico
    if local_id_param.isdigit():
        productos_qs = productos_qs.filter(local_id=int(local_id_param))

    # Búsqueda parametrizada por nombre o categoría (OWASP A03)
    if query_busqueda:
        productos_qs = productos_qs.filter(
            Q(nombre__icontains=query_busqueda) | Q(categoria__icontains=query_busqueda)
        )

    # Recuperación de menús del día específicos para enriquecer datos del Casino
    menus_dia_map = {
        m.id_producto: m
        for m in MenuDia.objects.filter(local__activo=True).select_related('local')
    }

    # Agrupación de productos por local para la presentación visual
    locales_activos = Local.objects.filter(activo=True).order_by('nombre')
    locales_con_productos = []

    for loc in locales_activos:
        # Si se filtró por local específico y no coincide, se omite
        if local_id_param.isdigit() and loc.id_local != int(local_id_param):
            continue

        prods_local = [p for p in productos_qs if p.local_id == loc.id_local]

        # Inyectamos el objeto MenuDia si corresponde a una especialización
        for p in prods_local:
            if p.id_producto in menus_dia_map:
                p.es_menu_dia = True
                p.menu_info = menus_dia_map[p.id_producto]
            else:
                p.es_menu_dia = False
                p.menu_info = None

        # Separamos los menús veganos y tradicionales si es Casino Central (RF02)
        menus_veganos = [p for p in prods_local if getattr(p, 'menu_info', None) and p.menu_info.es_vegano]
        otros_productos = [p for p in prods_local if not (getattr(p, 'menu_info', None) and p.menu_info.es_vegano)]

        locales_con_productos.append({
            'local': loc,
            'productos': prods_local,
            'menus_veganos': menus_veganos,
            'otros_productos': otros_productos,
            'total_items': len(prods_local),
        })

    # Promociones Flash vigentes con cuenta regresiva activa (RF05)
    ahora = timezone.now()
    promos_flash_activas = (
        PromoFlash.objects.filter(
            activa=True,
            expira_en__gt=ahora,
            local__activo=True,
            producto__disponible=True,
        )
        .select_related('producto', 'local')
        .order_by('expira_en')[:4]
    )

    context = {
        'locales_con_productos': locales_con_productos,
        'todos_locales': locales_activos,
        'filtro_junaeb': filtro_junaeb,
        'local_seleccionado': int(local_id_param) if local_id_param.isdigit() else None,
        'query_busqueda': query_busqueda,
        'promos_flash': promos_flash_activas,
        'total_resultados': len(productos_qs),
    }

    return render(request, 'gastronomia/catalogo.html', context)


# ==============================================================================
# 2. PANEL DEL OPERADOR (RF01 / RBAC / OWASP A01 & LEY N° 21.459)
# ==============================================================================
@login_required
def panel_operador(request):
    """
    Vista privada y segura para el encargado de local.
    Implementa aislamiento lógico horizontal: el operador únicamente puede
    visualizar y gestionar el catálogo de su propio establecimiento.

    Cumplimiento:
      - OWASP A01: Broken Access Control.
      - Ley N° 21.459: Prohibición de acceso ilícito a recursos no asignados.
    """
    # Verificación de asignación de local al usuario autenticado
    if not hasattr(request.user, 'local'):
        return HttpResponseForbidden(
            "Acceso Denegado (HTTP 403): Su cuenta no tiene asignado ningún local gastronómico. "
            "Cumplimiento Ley N° 21.459 y política institucional de control de acceso RBAC (OWASP A01)."
        )

    local = request.user.local

    # Manejo de acciones administrativas del operador (POST tradicional)
    if request.method == 'POST':
        action = request.POST.get('action')

        # Conmutación de estado de jornada del local
        if action == 'abrir_jornada':
            local.abrir_jornada()
            messages.success(request, f'Jornada comercial abierta exitosamente para "{local.nombre}".')
            return redirect('panel_operador')

        elif action == 'cerrar_jornada':
            local.cerrar_jornada()
            messages.info(request, f'Jornada cerrada. El catálogo de "{local.nombre}" no será visible públicamente.')
            return redirect('panel_operador')

        # Creación rápida de producto o menú desde el panel
        elif action == 'crear_producto':
            if local.tipo == Local.TIPO_CASINO and request.POST.get('es_menu_dia') == '1':
                form_menu = MenuDiaForm(request.POST)
                if form_menu.is_valid():
                    menu = form_menu.save(commit=False)
                    menu.local = local
                    menu.save()
                    messages.success(request, f'Menú del día "{menu.nombre}" publicado correctamente.')
                    return redirect('panel_operador')
                else:
                    messages.error(request, 'Error al guardar el menú. Revise los campos requeridos.')
            else:
                form_prod = ProductoForm(request.POST)
                if form_prod.is_valid():
                    producto = form_prod.save(commit=False)
                    producto.local = local
                    producto.save()
                    messages.success(request, f'Producto "{producto.nombre}" agregado al catálogo.')
                    return redirect('panel_operador')
                else:
                    messages.error(request, 'Error al registrar el producto. Verifique los datos ingresados.')

    # Consulta estrictamente restringida a los productos del local asignado
    # Aislamiento en base de datos: Producto.objects.filter(local__operador=request.user)
    productos_qs = Producto.objects.filter(local__operador=request.user).order_by('nombre')

    # Identificación de menús del día si el local es Casino
    menus_dia_ids = set()
    if local.tipo == Local.TIPO_CASINO:
        menus_dia_ids = set(
            MenuDia.objects.filter(local=local).values_list('id_producto', flat=True)
        )

    productos_data = []
    for p in productos_qs:
        es_menu = p.id_producto in menus_dia_ids
        productos_data.append({
            'producto': p,
            'es_menu_dia': es_menu,
        })

    # Métricas operativas del turno
    total_productos = productos_qs.count()
    disponibles_count = productos_qs.filter(disponible=True).count()
    agotados_count = productos_qs.filter(disponible=False).count()
    junaeb_count = productos_qs.filter(acepta_junaeb=True).count()

    context = {
        'local': local,
        'productos_data': productos_data,
        'total_productos': total_productos,
        'disponibles_count': disponibles_count,
        'agotados_count': agotados_count,
        'junaeb_count': junaeb_count,
        'form_producto': ProductoForm(),
        'form_menu': MenuDiaForm() if local.tipo == Local.TIPO_CASINO else None,
    }

    return render(request, 'gastronomia/panel_operador.html', context)


# ==============================================================================
# 3. CONMUTACIÓN DE STOCK ASÍNCRONA (RF03 / HU04 / RNF02)
# ==============================================================================
@login_required
@require_http_methods(['POST', 'PATCH'])
def actualizar_stock(request, pk):
    """
    Endpoint JSON para la actualización instantánea de stock en 1 clic (RF03).
    Responde en menos de 2 segundos persistiendo directamente en Supabase (PostgreSQL).

    Validaciones estrictas de seguridad (OWASP A01 / Ley N° 21.459):
      1. Usuario autenticado con sesión activa.
      2. Pertenencia estricta del producto al local operado por el usuario.
      3. Verificación de token CSRF (X-CSRFToken).
    """
    # 1. Verificación de existencia del producto
    producto = get_object_or_404(Producto, pk=pk)

    # 2. Validación de autorización de local (OWASP A01 / Ley N° 21.459)
    if not hasattr(request.user, 'local') or producto.local.operador != request.user:
        return JsonResponse({
            'success': False,
            'error': (
                'Acceso denegado: Intento no autorizado de conmutar stock sobre un local ajeno. '
                'Operación bloqueada según Art. 2 de la Ley N° 21.459 (OWASP A01).'
            )
        }, status=403)

    # 3. Procesamiento del nuevo estado
    nuevo_estado = None
    if request.content_type == 'application/json' and request.body:
        try:
            payload = json.loads(request.body.decode('utf-8'))
            if 'disponible' in payload:
                nuevo_estado = bool(payload['disponible'])
        except (json.JSONDecodeError, ValueError):
            nuevo_estado = None
    elif 'disponible' in request.POST:
        val = request.POST.get('disponible', '').lower()
        nuevo_estado = val in ('true', '1', 'yes')

    # 4. Actualización del stock mediante el método del modelo
    producto.cambiar_estado_stock(nuevo_estado)

    # 5. Respuesta JSON con nuevo estado (HTTP 200)
    estado_texto = "Disponible" if producto.disponible else "Agotado"
    return JsonResponse({
        'success': True,
        'id_producto': producto.id_producto,
        'nombre': producto.nombre,
        'disponible': producto.disponible,
        'mensaje': f'El producto "{producto.nombre}" ahora está marcado como {estado_texto}.'
    }, status=200)


# ==============================================================================
# 4. AUTENTICACIÓN INSTITUCIONAL (LOGIN / LOGOUT)
# ==============================================================================
def login_view(request):
    """
    Inicio de sesión institucional para operadores de locales y administradores.
    """
    if request.user.is_authenticated:
        if hasattr(request.user, 'local'):
            return redirect('panel_operador')
        return redirect('catalogo_publico')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bienvenido(a), {user.get_full_name() or user.username}.')
            if hasattr(user, 'local'):
                return redirect('panel_operador')
            return redirect('catalogo_publico')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. Intente nuevamente.')
    else:
        form = AuthenticationForm(request)

    return render(request, 'gastronomia/login.html', {'form': form})


def logout_view(request):
    """Cierra la sesión activa del usuario y redirige al catálogo público."""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('catalogo_publico')
