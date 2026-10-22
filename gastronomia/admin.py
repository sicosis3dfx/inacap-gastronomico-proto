"""
Sistema Centralizado de Publicación y Consulta Gastronómica — INACAP Sede Renca.
Módulo: gastronomia.admin
================================================================================
Configuración y personalización del panel de administración institucional:
  - Registro de los cuatro modelos: Local, Producto, MenuDia, PromoFlash.
  - Mitigación preventiva del error admin.E122 asegurando que 'disponible' esté
    declarado en 'list_display' previo a su inclusión en 'list_editable'.
  - Restricción de permisos y aislamiento lógico de catálogos (RBAC) alineado con
    OWASP A01 (Broken Access Control) y Ley Chilena N° 21.459 sobre Delitos Informáticos.
"""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Local, Producto, MenuDia, PromoFlash

User = get_user_model()

# ==============================================================================
# 1. ENCABEZADOS Y TÍTULOS INSTITUCIONALES DEL PANEL ADMINISTRATIVO
# ==============================================================================
admin.site.site_header = "Sistema Gastronómico INACAP Renca"
admin.site.site_title = "Portal Gastronómico"
admin.site.index_title = "Administración de Locales y Catálogo"


# ==============================================================================
# 2. ACCIONES MASIVAS PERSONALIZADAS (OPERATORIA DE JORNADA Y STOCK)
# ==============================================================================
@admin.action(description="🟢 Abrir jornada de locales seleccionados")
def abrir_jornada_action(modeladmin, request, queryset):
    """Abre la jornada comercial de los locales seleccionados."""
    total = queryset.update(activo=True)
    modeladmin.message_user(
        request,
        f"Se ha abierto la jornada para {total} local(es) correctamente."
    )


@admin.action(description="🔴 Cerrar jornada de locales seleccionados")
def cerrar_jornada_action(modeladmin, request, queryset):
    """Cierra la jornada comercial de los locales seleccionados."""
    total = queryset.update(activo=False)
    modeladmin.message_user(
        request,
        f"Se ha cerrado la jornada para {total} local(es) correctamente."
    )


@admin.action(description="✅ Marcar productos seleccionados como DISPONIBLE")
def marcar_disponible_action(modeladmin, request, queryset):
    """Actualiza masivamente el stock a disponible (RF03)."""
    total = queryset.update(disponible=True)
    modeladmin.message_user(
        request,
        f"Se actualizaron {total} ítem(s) como Disponibles."
    )


@admin.action(description="⛔ Marcar productos seleccionados como AGOTADO")
def marcar_agotado_action(modeladmin, request, queryset):
    """Actualiza masivamente el stock a agotado en 1 clic (RF03)."""
    total = queryset.update(disponible=False)
    modeladmin.message_user(
        request,
        f"Se marcaron {total} ítem(s) como AGOTADOS."
    )


@admin.action(description="⏹️ Desactivar promociones seleccionadas")
def desactivar_promociones_action(modeladmin, request, queryset):
    """Desactiva de inmediato las promociones seleccionadas (RF05)."""
    total = queryset.update(activa=False)
    modeladmin.message_user(
        request,
        f"Se desactivaron {total} promoción(es) flash correctamente."
    )


# ==============================================================================
# 3. ADMINISTRACIÓN DEL MODELO LOCAL
# ==============================================================================
@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    """
    Panel administrativo para la gestión de locales gastronómicos.
    Controla el estado operativo (abierto/cerrado) y vincula al encargado RBAC.
    """
    list_display = (
        'nombre',
        'tipo',
        'operador',
        'activo',
        'total_productos_badge',
    )
    list_editable = ('activo',)
    list_display_links = ('nombre',)
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre', 'operador__username', 'operador__first_name', 'operador__last_name')
    ordering = ('nombre',)
    list_per_page = 20
    actions = [abrir_jornada_action, cerrar_jornada_action]

    fieldsets = (
        ('Identificación del Local', {
            'fields': ('nombre', 'tipo'),
            'description': 'Información general y clasificación del puesto gastronómico.',
        }),
        ('Aislamiento y Operación (RBAC / Ley N° 21.459)', {
            'fields': ('operador', 'activo'),
            'description': (
                'Operador exclusivo asignado (garantiza aislamiento según OWASP A01) '
                'y estado actual de la jornada de atención.'
            ),
        }),
    )

    @admin.display(description="Total Productos")
    def total_productos_badge(self, obj):
        # Cuenta productos usando la relación inversa segura
        if hasattr(obj, 'productos'):
            conteo = obj.productos.count()
        elif hasattr(obj, 'producto_set'):
            conteo = obj.producto_set.count()
        else:
            conteo = 0

        return format_html(
            '<span style="background-color: #004b87; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-weight: bold; font-size: 0.85em;">{} productos</span>',
            conteo
        )

    def get_queryset(self, request):
        """
        OWASP A01 & Ley N° 21.459 (Aislamiento horizontal por operador):
        Si el usuario no es superadministrador, solo puede visualizar su propio local.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(operador=request.user)


# ==============================================================================
# 4. ADMINISTRACIÓN DEL MODELO PRODUCTO
# ==============================================================================
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """
    Panel administrativo para el catálogo de productos.
    
    CRÍTICO PARA EVITAR admin.E122:
    El campo 'disponible' DEBE estar incluido obligatoriamente en 'list_display'
    antes de ser configurado en 'list_editable'.
    """
    # Cumplimiento admin.E122: 'disponible' presente en list_display
    list_display = (
        'id_producto',
        'nombre',
        'local',
        'categoria',
        'precio_regular_formateado',
        'acepta_junaeb',
        'disponible',  # <--- Requerido por list_editable para prevenir admin.E122
    )
    # Switch interactivo en lista para conmutación de stock en 1 clic
    list_editable = ('disponible',)
    list_display_links = ('id_producto', 'nombre')
    list_filter = ('local', 'categoria', 'acepta_junaeb', 'disponible')
    search_fields = ('nombre', 'categoria', 'local__nombre')
    ordering = ('local', 'nombre')
    list_per_page = 25
    actions = [marcar_disponible_action, marcar_agotado_action]

    fieldsets = (
        ('Datos Comerciales', {
            'fields': ('local', 'nombre', 'categoria', 'precio_regular', 'imagen_url'),
            'description': 'Información básica de visualización y comercialización.',
        }),
        ('Disponibilidad y Beneficios Estudiantiles', {
            'fields': ('acepta_junaeb', 'disponible'),
            'description': 'Reglas de financiamiento estudiantil (RF04) y estado físico de stock (RF03).',
        }),
    )

    @admin.display(description="Precio Regular", ordering='precio_regular')
    def precio_regular_formateado(self, obj):
        return f"${obj.precio_regular:,}".replace(",", ".")

    def get_queryset(self, request):
        """
        OWASP A01 & Ley N° 21.459:
        Restringe el catálogo del operador al local que le fue asignado.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(local__operador=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Limita las opciones del campo 'local' en el formulario de edición/creación
        al local correspondiente al operador autenticado.
        """
        if db_field.name == "local" and not request.user.is_superuser:
            kwargs["queryset"] = Local.objects.filter(operador=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ==============================================================================
# 5. ADMINISTRACIÓN DEL MODELO MENÚ DEL DÍA (HERENCIA DE PRODUCTO)
# ==============================================================================
@admin.register(MenuDia)
class MenuDiaAdmin(admin.ModelAdmin):
    """
    Panel administrativo especializado para los menús diarios del Casino Central.
    
    CRÍTICO PARA EVITAR admin.E122:
    'disponible' se incluye en 'list_display' para posibilitar su edición directa
    en línea mediante 'list_editable'.
    """
    # Cumplimiento admin.E122: 'disponible' presente en list_display
    list_display = (
        'id_producto',
        'nombre',
        'local',
        'plato_entrada',
        'plato_fondo',
        'postre',
        'es_vegano_badge',
        'precio_regular_formateado',
        'acepta_junaeb',
        'disponible',  # <--- Requerido por list_editable para prevenir admin.E122
    )
    list_editable = ('disponible',)
    list_display_links = ('id_producto', 'nombre')
    list_filter = ('local', 'es_vegano', 'acepta_junaeb', 'disponible')
    search_fields = ('nombre', 'plato_entrada', 'plato_fondo', 'postre', 'local__nombre')
    ordering = ('-id_producto',)
    list_per_page = 20
    actions = [marcar_disponible_action, marcar_agotado_action]

    fieldsets = (
        ('Menú del Casino Central', {
            'fields': ('local', 'nombre', 'precio_regular', 'imagen_url'),
            'description': 'Información principal del menú publicado.',
        }),
        ('Composición del Menú (RF02)', {
            'fields': ('plato_entrada', 'plato_fondo', 'postre', 'es_vegano'),
            'description': 'Desglose detallado de los platos y distinción de opción vegana destacada.',
        }),
        ('Estado Operativo', {
            'fields': ('acepta_junaeb', 'disponible'),
            'description': 'Disponibilidad del menú del día y acreditación JUNAEB.',
        }),
    )

    @admin.display(description="Precio", ordering='precio_regular')
    def precio_regular_formateado(self, obj):
        return f"${obj.precio_regular:,}".replace(",", ".")

    @admin.display(description="Tipo de Menú", ordering='es_vegano')
    def es_vegano_badge(self, obj):
        if obj.es_vegano:
            return mark_safe(
                '<span style="background-color: #2e7d32; color: white; padding: 3px 8px; '
                'border-radius: 10px; font-weight: bold; font-size: 0.85em;">🌱 Vegano</span>'
            )
        return mark_safe(
            '<span style="background-color: #555; color: white; padding: 3px 8px; '
            'border-radius: 10px; font-size: 0.85em;">🍽️ Tradicional</span>'
        )

    def get_queryset(self, request):
        """Aislamiento horizontal por operador (OWASP A01 / Ley N° 21.459)."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(local__operador=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restringe el campo local exclusivamente al asignado al usuario."""
        if db_field.name == "local" and not request.user.is_superuser:
            kwargs["queryset"] = Local.objects.filter(operador=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ==============================================================================
# 6. ADMINISTRACIÓN DEL MODELO PROMOCIÓN FLASH
# ==============================================================================
@admin.register(PromoFlash)
class PromoFlashAdmin(admin.ModelAdmin):
    """
    Panel administrativo para la gestión de promociones temporales con temporizador.
    Permite auditar el estado de vigencia y desactivar ofertas manualmente.
    """
    list_display = (
        'id_promo',
        'local',
        'producto',
        'precio_oferta_formateado',
        'expira_en',
        'activa',
        'vigencia_badge',
    )
    list_editable = ('activa',)
    list_display_links = ('id_promo', 'producto')
    list_filter = ('local', 'activa', 'expira_en')
    search_fields = ('local__nombre', 'producto__nombre')
    ordering = ('-expira_en',)
    list_per_page = 20
    actions = [desactivar_promociones_action]

    fieldsets = (
        ('Detalles de la Promoción', {
            'fields': ('local', 'producto', 'precio_oferta'),
            'description': 'Producto en promoción y precio con descuento aplicado.',
        }),
        ('Vigencia y Temporizador (RF05)', {
            'fields': ('expira_en', 'activa'),
            'description': 'Fecha/hora límite de expiración y estado de activación.',
        }),
    )

    @admin.display(description="Precio Oferta", ordering='precio_oferta')
    def precio_oferta_formateado(self, obj):
        return f"${obj.precio_oferta:,}".replace(",", ".")

    @admin.display(description="Estado Vigencia", boolean=True)
    def vigencia_badge(self, obj):
        """Evalúa si la promoción está activa y dentro del plazo horario."""
        return obj.esta_vigente

    def get_queryset(self, request):
        """Aislamiento horizontal por operador (OWASP A01 / Ley N° 21.459)."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(local__operador=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restringe opciones de local y productos al local del operador."""
        if not request.user.is_superuser:
            if db_field.name == "local":
                kwargs["queryset"] = Local.objects.filter(operador=request.user)
            elif db_field.name == "producto":
                kwargs["queryset"] = Producto.objects.filter(local__operador=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ==============================================================================
# 7. PERSONALIZACIÓN DEL MODELO USER (DISTINCIÓN DE ROLES INSTITUCIONALES)
# ==============================================================================
if admin.site.is_registered(User):
    admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    Panel institucional para la administración de usuarios con indicador de roles.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol_badge', 'is_active')
    list_filter = ('is_superuser', 'is_staff', 'is_active', 'groups')
    ordering = ('username',)

    @admin.display(description="Rol / Nivel de acceso", ordering='is_superuser')
    def rol_badge(self, obj):
        """Despliega visualmente el nivel de privilegio de la cuenta."""
        if obj.is_superuser:
            return mark_safe('<span style="color: #b71c1c; font-weight: bold;">👑 Superusuario</span>')
        elif obj.is_staff:
            return mark_safe('<span style="color: #004b87; font-weight: bold;">🛡️ Encargado de Local</span>')
        return mark_safe('<span style="color: #555;">👤 Usuario Estándar</span>')
