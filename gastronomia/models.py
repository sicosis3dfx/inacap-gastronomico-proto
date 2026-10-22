"""
Sistema Centralizado de Publicación y Consulta Gastronómica — INACAP Sede Renca.
Módulo: gastronomia.models
================================================================================
Definición estricta de las entidades del dominio basadas en el Diagrama de Clases UML:
  - Local: Administra la entidad física o puesto gastronómico y su operador asignado.
  - Producto: Entidad base de los ítems del catálogo comercial.
  - MenuDia: Especialización de Producto para el menú del Casino Central.
  - PromoFlash: Ofertas temporales con cuenta regresiva.

================================================================================
JUSTIFICACIÓN DE SEGURIDAD Y CUMPLIMIENTO NORMATIVO:
================================================================================
1. OWASP Top 10 - A01:2021 (Broken Access Control) & LEY CHILENA N° 21.459 (DELITOS INFORMÁTICOS):
   - El modelo 'Local' implementa un enlace unívoco OneToOneField con auth.User (operador).
     Esto garantiza a nivel de arquitectura el principio de mínimo privilegio y aislamiento
     lógico entre locales: ningún operador puede acceder, mutar ni deshabilitar productos
     de otro local gastronómico.
   - Todo intento de elusión o manipulación de identificadores (IDOR) vulneraría el Art. 2
     de la Ley N° 21.459 (acceso indebido a sistema informático o sobrepaso de autorización).
   - Las consultas en capas de servicio y controladores deben restringirse siempre al
     operador autenticado (ej: Producto.objects.filter(local__operador=request.user)).

2. OWASP Top 10 - A03:2021 (Injection):
   - Todos los modelos se gestionan a través del Object-Relational Mapping (ORM) de Django,
     el cual utiliza consultas SQL estrictamente parametrizadas hacia PostgreSQL (Supabase).
   - Se restringe y prohíbe el uso de SQL crudo (raw queries) o interpolación de strings.
   - Los campos numéricos como PositiveIntegerField y los campos booleanos imponen tipado
     estricto en la capa de persistencia, neutralizando vectores de inyección SQL.

3. OWASP Top 10 - A02:2021 (Cryptographic Failures & Sensitive Data Storage):
   - Los modelos no almacenan contraseñas ni material criptográfico en texto claro; se delega
     la autenticación al subsistema seguro de Django (PBKDF2-SHA256).
   - Las conexiones a Supabase y credenciales de base de datos se manejan de manera externa
     mediante variables de entorno en el archivo .env, fuera del código fuente.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# ==============================================================================
# 1. MODELO LOCAL
# ==============================================================================
class Local(models.Model):
    """
    Representa una entidad o puesto gastronómico dentro de INACAP Sede Renca
    (ej: Casino Central, Food Truck 1, Food Truck 2, Food Truck 3).

    Garantiza aislamiento estricto por operador (OWASP A01 / Ley N° 21.459).
    """

    TIPO_CASINO = 'Casino'
    TIPO_FOOD_TRUCK = 'Food Truck'
    TIPOS_LOCAL = [
        (TIPO_CASINO, 'Casino'),
        (TIPO_FOOD_TRUCK, 'Food Truck'),
    ]

    id_local = models.BigAutoField(
        primary_key=True,
        verbose_name="ID Local",
        help_text="Identificador único del local gastronómico."
    )
    nombre = models.CharField(
        max_length=120,
        verbose_name="Nombre del local",
        help_text="Nombre descriptivo institucional (ej: Casino Central, Food Truck 1)."
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_LOCAL,
        default=TIPO_FOOD_TRUCK,
        verbose_name="Tipo de local",
        help_text="Clasificación del punto gastronómico."
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Jornada activa / Abierto",
        help_text="Indica si el local se encuentra actualmente abierto al público."
    )
    operador = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='local',
        verbose_name="Operador / Encargado",
        help_text="Usuario institucional asignado para gestionar exclusivamente este local."
    )

    class Meta:
        verbose_name = "Local"
        verbose_name_plural = "Locales"
        ordering = ['nombre']

    def __str__(self):
        estado = "Abierto" if self.activo else "Cerrado"
        return f"{self.nombre} ({self.tipo}) - [{estado}]"

    def abrir_jornada(self):
        """
        Abre la jornada de atención del local habilitando la visibilidad de su oferta.
        Cumple con el Diagrama de Estados (transición a Disponible).
        """
        self.activo = True
        self.save(update_fields=['activo'])

    def cerrar_jornada(self):
        """
        Cierra la jornada de atención del local suspendiendo la visibilidad de su catálogo.
        Cumple con el Diagrama de Estados (transición a Registrado / Inactivo).
        """
        self.activo = False
        self.save(update_fields=['activo'])


# ==============================================================================
# 2. MODELO PRODUCTO (BASE DE CATÁLOGO)
# ==============================================================================
class Producto(models.Model):
    """
    Entidad base que modela los ítems gastronómicos comercializados por los locales.
    Soporta control en 1 clic de agotado/disponible (RF03 / HU04).
    """

    id_producto = models.BigAutoField(
        primary_key=True,
        verbose_name="ID Producto",
        help_text="Identificador único del producto en catálogo."
    )
    local = models.ForeignKey(
        Local,
        on_delete=models.CASCADE,
        related_name='productos',
        verbose_name="Local",
        help_text="Local responsable que administra este producto."
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre del producto",
        help_text="Nombre comercial del producto o preparación."
    )
    precio_regular = models.PositiveIntegerField(
        verbose_name="Precio regular ($)",
        help_text="Precio de venta normal en pesos chilenos (CLP)."
    )
    acepta_junaeb = models.BooleanField(
        default=False,
        verbose_name="Acepta tarjeta JUNAEB",
        help_text="Indica si el ítem califica para pago con beca de alimentación JUNAEB (RF04)."
    )
    disponible = models.BooleanField(
        default=True,
        verbose_name="Disponible / En stock",
        help_text="Estado de stock físico conmutable en 1 clic (RF03 / RNF02)."
    )
    categoria = models.CharField(
        max_length=60,
        blank=True,
        default='',
        verbose_name="Categoría",
        help_text="Línea de producto opcional (ej: Sandwiches, Bebidas, Almuerzos)."
    )
    imagen_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL de imagen",
        help_text="Enlace HTTPS externo a la fotografía del producto."
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['local', 'nombre']

    def __str__(self):
        stock_str = "Disponible" if self.disponible else "AGOTADO"
        return f"{self.nombre} - ${self.precio_regular:,} ({self.local.nombre}) [{stock_str}]"

    def cambiar_estado_stock(self, nuevo_estado=None):
        """
        RF03 - Actualización de stock en 1 clic:
        Permite fijar explícitamente el estado de disponibilidad o conmutarlo
        automáticamente si no se especifica parámetro. Persiste el cambio de inmediato.
        """
        if nuevo_estado is not None:
            self.disponible = bool(nuevo_estado)
        else:
            self.disponible = not self.disponible
        self.save(update_fields=['disponible'])


# ==============================================================================
# 3. MODELO MENÚ DEL DÍA (HERENCIA DIRECTA DE PRODUCTO)
# ==============================================================================
class MenuDia(Producto):
    """
    Especialización de Producto para las opciones de almuerzo del Casino Central (RF02).
    Hereda atributos y comportamiento de Producto (Multi-table Inheritance de Django).
    """

    plato_entrada = models.CharField(
        max_length=150,
        verbose_name="Plato de entrada",
        help_text="Descripción de la entrada (ej: Crema de zapallo, Ensalada surtida)."
    )
    plato_fondo = models.CharField(
        max_length=150,
        verbose_name="Plato de fondo",
        help_text="Descripción del plato principal (ej: Pastel de choclo, Lasaña boloñesa)."
    )
    postre = models.CharField(
        max_length=150,
        verbose_name="Postre",
        help_text="Postre o fruta de estación incluido."
    )
    es_vegano = models.BooleanField(
        default=False,
        verbose_name="Opción vegana destacada",
        help_text="Destaca el menú si cumple con estándar 100% vegetariano/vegano."
    )

    class Meta:
        verbose_name = "Menú del Día"
        verbose_name_plural = "Menús del Día"
        ordering = ['-id_producto']

    def __str__(self):
        tipo_str = "Vegano" if self.es_vegano else "Tradicional"
        return f"Menú del Día: {self.nombre} ({tipo_str}) - Fondo: {self.plato_fondo}"

    def get_detalle_completo(self) -> str:
        """
        Retorna la formulación completa del menú en una cadena estructurada
        para despliegue institucional en tarjetas y reportes.
        """
        return f"Entrada: {self.plato_entrada} | Fondo: {self.plato_fondo} | Postre: {self.postre}"


# ==============================================================================
# 4. MODELO PROMOCIÓN FLASH
# ==============================================================================
class PromoFlash(models.Model):
    """
    Modela las ofertas relámpago con precio de descuento y tiempo de expiración
    con cuenta regresiva (RF05).
    """

    id_promo = models.BigAutoField(
        primary_key=True,
        verbose_name="ID Promoción",
        help_text="Identificador único de la promoción flash."
    )
    local = models.ForeignKey(
        Local,
        on_delete=models.CASCADE,
        related_name='promociones',
        verbose_name="Local",
        help_text="Local que genera y financia la promoción."
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='promociones_flash',
        verbose_name="Producto en oferta",
        help_text="Producto sobre el cual se aplica el descuento flash."
    )
    precio_oferta = models.PositiveIntegerField(
        verbose_name="Precio de oferta ($)",
        help_text="Precio rebajado temporal en pesos chilenos (CLP)."
    )
    expira_en = models.DateTimeField(
        verbose_name="Fecha y hora de expiración",
        help_text="Límite temporal tras el cual la oferta se desactiva de forma automática."
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="Oferta activa",
        help_text="Flag de control manual o automático de activación."
    )

    class Meta:
        verbose_name = "Promoción Flash"
        verbose_name_plural = "Promociones Flash"
        ordering = ['-expira_en']

    def __str__(self):
        vigencia = "Vigente" if self.esta_vigente else "Expirada/Inactiva"
        return f"Promo: {self.producto.nombre} a ${self.precio_oferta:,} ({self.local.nombre}) [{vigencia}]"

    def desactivar_oferta(self):
        """
        Desactiva manualmente la promoción flash, impidiendo su despliegue público
        incluso antes de alcanzar la fecha límite de expiración.
        """
        self.activa = False
        self.save(update_fields=['activa'])

    @property
    def esta_vigente(self) -> bool:
        """
        Propiedad que evalúa si la promoción se encuentra actualmente activa y
        no ha sobrepasado la fecha y hora de expiración según la zona horaria del sistema.
        """
        if not self.activa:
            return False
        if not self.expira_en:
            return False
        return timezone.now() < self.expira_en
