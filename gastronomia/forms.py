"""
Sistema Centralizado de Publicación y Consulta Gastronómica — INACAP Sede Renca.
Módulo: gastronomia.forms
================================================================================
Formularios basados en ModelForm para la administración de ítems de catálogo y
menús del día del Casino Central y Food Trucks.

CUMPLIMIENTO DE SEGURIDAD (OWASP A03:2021 - Injection & Data Sanitization):
- Saneamiento profundo de entradas y eliminación activa de bloques '<script>' y '<style>'
  junto con sus contenidos para prevenir ataques de Cross-Site Scripting (XSS).
- Neutralización de etiquetas HTML mediante 'django.utils.html.strip_tags'.
- Validación estricta de esquemas URL (solo 'http' y 'https' permitidos, bloqueando
  esquemas maliciosos como 'javascript:' o 'data:').
- Validación de rangos numéricos y coherencia comercial en precios regulares.
- El ORM de Django maneja automáticamente la parametrización de consultas hacia
  PostgreSQL (Supabase), eliminando todo riesgo de SQL Injection.
"""

import re
from urllib.parse import urlparse
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

from .models import Producto, MenuDia


def sanear_texto_seguro(texto: str) -> str:
    """
    Sanea texto neutralizando etiquetas scripts, estilos y HTML malicioso
    conforme al estándar OWASP A03 (prevención de inyecciones de código/XSS).
    """
    if not texto:
        return ''
    # Remueve bloques completos <script>...</script> o <style>...</style>
    sin_scripts = re.sub(r'<(script|style).*?>.*?</\1>', '', texto, flags=re.IGNORECASE | re.DOTALL)
    return strip_tags(sin_scripts).strip()


class ProductoForm(forms.ModelForm):
    """
    Formulario para la creación y actualización de productos gastronómicos
    (Food Trucks y Casino).
    """

    class Meta:
        model = Producto
        fields = [
            'nombre',
            'categoria',
            'precio_regular',
            'acepta_junaeb',
            'disponible',
            'imagen_url',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'Ej: Sandwich Mechada Italiana, Café Latte, Jugo Natural...',
                'maxlength': '150',
                'required': True,
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'Ej: Desayunos, Almuerzos, Bebidas, Sandwiches...',
                'maxlength': '60',
            }),
            'precio_regular': forms.NumberInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'Ej: 2990',
                'min': '100',
                'step': '50',
                'required': True,
            }),
            'acepta_junaeb': forms.CheckboxInput(attrs={
                'class': 'form-check-toggle',
            }),
            'disponible': forms.CheckboxInput(attrs={
                'class': 'form-check-toggle',
            }),
            'imagen_url': forms.URLInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'https://ejemplo.com/imagenes/producto.jpg',
            }),
        }
        labels = {
            'nombre': 'Nombre del Producto',
            'categoria': 'Categoría / Línea',
            'precio_regular': 'Precio Regular ($ CLP)',
            'acepta_junaeb': 'Acepta Tarjeta JUNAEB',
            'disponible': 'Disponible en Stock (Inmediato)',
            'imagen_url': 'URL de Fotografía (Opcional)',
        }
        help_texts = {
            'acepta_junaeb': 'Habilita el ítem para pago con beca de alimentación estudiantil.',
            'disponible': 'Desmarca si el producto se encuentra agotado físicamente.',
            'imagen_url': 'Debe ser un enlace seguro iniciando con https://.',
        }

    # ==========================================================================
    # VALIDACIONES Y SANEAMIENTO OWASP A03
    # ==========================================================================
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        nombre_limpio = sanear_texto_seguro(nombre)
        if not nombre_limpio:
            raise ValidationError("El nombre del producto no puede estar vacío ni contener solo código o etiquetas HTML.")
        if len(nombre_limpio) < 3:
            raise ValidationError("El nombre comercial debe tener al menos 3 caracteres.")
        return nombre_limpio

    def clean_categoria(self):
        categoria = self.cleaned_data.get('categoria', '')
        if categoria:
            return sanear_texto_seguro(categoria)
        return ''

    def clean_precio_regular(self):
        precio = self.cleaned_data.get('precio_regular')
        if precio is None:
            raise ValidationError("Debe ingresar un precio válido.")
        if precio < 100:
            raise ValidationError("El precio debe ser de al menos $100 CLP.")
        if precio > 100000:
            raise ValidationError("El precio no puede exceder los $100.000 CLP.")
        return precio

    def clean_imagen_url(self):
        url = self.cleaned_data.get('imagen_url', '')
        if url:
            parsed = urlparse(url)
            if parsed.scheme.lower() not in ('http', 'https'):
                raise ValidationError("La URL de la imagen debe comenzar estrictamente con 'http://' o 'https://'.")
        return url


class MenuDiaForm(forms.ModelForm):
    """
    Formulario especializado para la formulación de los menús diarios
    del Casino Central (RF02).
    """

    class Meta:
        model = MenuDia
        fields = [
            'nombre',
            'precio_regular',
            'plato_entrada',
            'plato_fondo',
            'postre',
            'es_vegano',
            'acepta_junaeb',
            'disponible',
            'imagen_url',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'Ej: Menú 1 - Clásico Chileno, Menú 2 - Pasta Artesanal...',
                'maxlength': '150',
                'required': True,
            }),
            'precio_regular': forms.NumberInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'Ej: 3800',
                'min': '100',
                'step': '50',
                'required': True,
            }),
            'plato_entrada': forms.TextInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'Ej: Crema de verduras, Ensalada a la chilena, Sopaipillas...',
                'maxlength': '150',
                'required': True,
            }),
            'plato_fondo': forms.TextInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'Ej: Cazuela de ave, Charquicán, Pastel de choclo, Garbanzos...',
                'maxlength': '150',
                'required': True,
            }),
            'postre': forms.TextInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'Ej: Fruta de la estación, Flan casero, Jalea...',
                'maxlength': '150',
                'required': True,
            }),
            'es_vegano': forms.CheckboxInput(attrs={
                'class': 'form-check-toggle',
            }),
            'acepta_junaeb': forms.CheckboxInput(attrs={
                'class': 'form-check-toggle',
            }),
            'disponible': forms.CheckboxInput(attrs={
                'class': 'form-check-toggle',
            }),
            'imagen_url': forms.URLInput(attrs={
                'class': 'form-input-control',
                'placeholder': 'https://ejemplo.com/imagenes/menu.jpg',
            }),
        }
        labels = {
            'nombre': 'Título del Menú Diario',
            'precio_regular': 'Precio del Almuerzo ($ CLP)',
            'plato_entrada': 'Plato de Entrada',
            'plato_fondo': 'Plato Principal / Fondo',
            'postre': 'Postre',
            'es_vegano': 'Opción Vegana Destacada (Casino Central)',
            'acepta_junaeb': 'Acepta Tarjeta JUNAEB',
            'disponible': 'Disponible en Stock',
            'imagen_url': 'URL de Fotografía del Plato (Opcional)',
        }
        help_texts = {
            'es_vegano': 'El Casino Central publica 1 alternativa destacada 100% vegana junto a 2 tradicionales.',
            'acepta_junaeb': 'Indica si este menú diario califica para pago con beneficio estudiantil.',
        }

    # ==========================================================================
    # VALIDACIONES Y SANEAMIENTO OWASP A03
    # ==========================================================================
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        nombre_limpio = sanear_texto_seguro(nombre)
        if not nombre_limpio:
            raise ValidationError("El título del menú no puede estar vacío.")
        return nombre_limpio

    def clean_plato_entrada(self):
        entrada = self.cleaned_data.get('plato_entrada', '')
        entrada_limpia = sanear_texto_seguro(entrada)
        if not entrada_limpia:
            raise ValidationError("Debe detallar el plato de entrada.")
        return entrada_limpia

    def clean_plato_fondo(self):
        fondo = self.cleaned_data.get('plato_fondo', '')
        fondo_limpio = sanear_texto_seguro(fondo)
        if not fondo_limpio:
            raise ValidationError("Debe detallar el plato de fondo principal.")
        return fondo_limpio

    def clean_postre(self):
        postre = self.cleaned_data.get('postre', '')
        postre_limpio = sanear_texto_seguro(postre)
        if not postre_limpio:
            raise ValidationError("Debe detallar el postre incluido.")
        return postre_limpio

    def clean_precio_regular(self):
        precio = self.cleaned_data.get('precio_regular')
        if precio is None or precio < 100:
            raise ValidationError("El precio del menú debe ser de al menos $100 CLP.")
        return precio

    def clean_imagen_url(self):
        url = self.cleaned_data.get('imagen_url', '')
        if url:
            parsed = urlparse(url)
            if parsed.scheme.lower() not in ('http', 'https'):
                raise ValidationError("La URL de la imagen debe ser un enlace http o https válido.")
        return url
