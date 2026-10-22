"""
Sistema Centralizado de Publicación y Consulta Gastronómica — INACAP Sede Renca.
Módulo: gastronomia.tests
================================================================================
Batería de pruebas unitarias y de integración para validar:
  - Modelos de dominio y métodos de ciclo de vida (Local, Producto, MenuDia, PromoFlash).
  - RF01 / OWASP A01 y Ley N° 21.459: Aislamiento estricto de operadores y bloqueo 403.
  - RF02 / RF06: Catálogo público estudiantil responsivo.
  - RF03 / HU04: Conmutación de stock en 1 clic (< 2 seg) vía endpoint asíncrono.
  - RF04: Filtrado booleano JUNAEB.
  - RF05: Evaluación de vigencia de Promociones Flash.
  - OWASP A03: Saneamiento de datos e inyección de código en formularios.
"""

from datetime import timedelta
import json
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .forms import ProductoForm, MenuDiaForm
from .models import Local, Producto, MenuDia, PromoFlash


class GastronomiaModelosTest(TestCase):
    """Pruebas unitarias de la lógica de dominio y comportamiento de modelos."""

    def setUp(self):
        self.user_casino = User.objects.create_user(username='op_casino', password='Password123!')
        self.local_casino = Local.objects.create(
            nombre="Casino Central",
            tipo=Local.TIPO_CASINO,
            activo=True,
            operador=self.user_casino
        )
        self.prod_cafe = Producto.objects.create(
            local=self.local_casino,
            nombre="Café Grano Americano",
            precio_regular=1500,
            acepta_junaeb=False,
            disponible=True
        )
        self.menu_vegano = MenuDia.objects.create(
            local=self.local_casino,
            nombre="Almuerzo Vegano",
            precio_regular=3800,
            acepta_junaeb=True,
            disponible=True,
            plato_entrada="Ensalada Verde con Palta",
            plato_fondo="Guiso de Lentejas con Champiñones",
            postre="Manzana Asada",
            es_vegano=True
        )

    def test_ciclo_jornada_local(self):
        """Verifica la apertura y cierre de jornada."""
        self.local_casino.cerrar_jornada()
        self.assertFalse(self.local_casino.activo)
        self.local_casino.abrir_jornada()
        self.assertTrue(self.local_casino.activo)

    def test_cambiar_estado_stock_producto(self):
        """RF03: Verifica la conmutación de stock."""
        self.prod_cafe.cambiar_estado_stock(False)
        self.assertFalse(self.prod_cafe.disponible)
        self.prod_cafe.cambiar_estado_stock(True)
        self.assertTrue(self.prod_cafe.disponible)
        # Conmutación automática sin parámetro
        self.prod_cafe.cambiar_estado_stock()
        self.assertFalse(self.prod_cafe.disponible)

    def test_menu_dia_get_detalle_completo(self):
        """Verifica el método get_detalle_completo del Menú del Día."""
        detalle = self.menu_vegano.get_detalle_completo()
        self.assertIn("Ensalada Verde con Palta", detalle)
        self.assertIn("Guiso de Lentejas con Champiñones", detalle)
        self.assertIn("Manzana Asada", detalle)

    def test_promo_flash_vigencia(self):
        """RF05: Evalúa la propiedad esta_vigente con fecha futura y expirada."""
        ahora = timezone.now()
        promo_activa = PromoFlash.objects.create(
            local=self.local_casino,
            producto=self.prod_cafe,
            precio_oferta=990,
            expira_en=ahora + timedelta(hours=2),
            activa=True
        )
        self.assertTrue(promo_activa.esta_vigente)

        # Desactivación manual
        promo_activa.desactivar_oferta()
        self.assertFalse(promo_activa.esta_vigente)

        # Promo expirada por tiempo
        promo_expirada = PromoFlash.objects.create(
            local=self.local_casino,
            producto=self.prod_cafe,
            precio_oferta=990,
            expira_en=ahora - timedelta(minutes=5),
            activa=True
        )
        self.assertFalse(promo_expirada.esta_vigente)


class CatalogoPublicoViewsTest(TestCase):
    """Pruebas para la vista de consulta pública estudiantil."""

    def setUp(self):
        self.client = Client()
        self.u1 = User.objects.create_user(username='u_ft1', password='Password123!')
        self.local1 = Local.objects.create(nombre="Food Truck 1", tipo=Local.TIPO_FOOD_TRUCK, activo=True, operador=self.u1)

        self.p_junaeb = Producto.objects.create(
            local=self.local1,
            nombre="Sandwich Ave Palta",
            precio_regular=2500,
            acepta_junaeb=True,
            disponible=True
        )
        self.p_no_junaeb = Producto.objects.create(
            local=self.local1,
            nombre="Bebida Energética",
            precio_regular=1800,
            acepta_junaeb=False,
            disponible=True
        )

    def test_catalogo_publico_acceso_anonimo(self):
        """RF06: La navegación pública no exige autenticación."""
        response = self.client.get(reverse('catalogo_publico'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sandwich Ave Palta")
        self.assertContains(response, "Bebida Energética")

    def test_filtrado_junaeb(self):
        """RF04: ?junaeb=1 oculta los ítems que no aceptan tarjeta JUNAEB."""
        response = self.client.get(reverse('catalogo_publico'), {'junaeb': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sandwich Ave Palta")
        self.assertNotContains(response, "Bebida Energética")


class PanelOperadorSeguridadTest(TestCase):
    """Pruebas de seguridad OWASP A01 y Ley N° 21.459 en el panel y API."""

    def setUp(self):
        self.client = Client()
        self.u_casino = User.objects.create_user(username='operador_casino', password='Password123!')
        self.local_casino = Local.objects.create(nombre="Casino Central", tipo=Local.TIPO_CASINO, activo=True, operador=self.u_casino)

        self.u_ft = User.objects.create_user(username='operador_ft', password='Password123!')
        self.local_ft = Local.objects.create(nombre="Food Truck 2", tipo=Local.TIPO_FOOD_TRUCK, activo=True, operador=self.u_ft)

        self.u_sin_local = User.objects.create_user(username='sin_local', password='Password123!')

        self.prod_casino = Producto.objects.create(
            local=self.local_casino,
            nombre="Cazuela Vacuno",
            precio_regular=3500,
            disponible=True
        )
        self.prod_ft = Producto.objects.create(
            local=self.local_ft,
            nombre="Hamburguesa Mechada",
            precio_regular=4200,
            disponible=True
        )

    def test_panel_requiere_login(self):
        """Acceso no autenticado debe redirigir al login."""
        response = self.client.get(reverse('panel_operador'))
        self.assertEqual(response.status_code, 302)

    def test_usuario_sin_local_recibe_403(self):
        """Usuario autenticado sin local asignado debe recibir HTTP 403 Forbidden."""
        self.client.force_login(self.u_sin_local)
        response = self.client.get(reverse('panel_operador'))
        self.assertEqual(response.status_code, 403)

    def test_aislamiento_horizontal_panel(self):
        """OWASP A01 / Ley 21.459: Cada operador ve exclusivamente su propio catálogo."""
        self.client.force_login(self.u_casino)
        response = self.client.get(reverse('panel_operador'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cazuela Vacuno")
        self.assertNotContains(response, "Hamburguesa Mechada")

    def test_actualizar_stock_propio_exitoso(self):
        """RF03 / HU04: Conmutación asíncrona de stock retorna JSON HTTP 200."""
        self.client.force_login(self.u_casino)
        url = reverse('actualizar_stock', args=[self.prod_casino.pk])
        response = self.client.post(
            url,
            data=json.dumps({'disponible': False}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['disponible'])

        self.prod_casino.refresh_from_db()
        self.assertFalse(self.prod_casino.disponible)

    def test_actualizar_stock_local_ajeno_bloqueado(self):
        """Ley N° 21.459 (Acceso Ilícito): Intento de mutar stock ajeno retorna HTTP 403."""
        self.client.force_login(self.u_casino)
        url = reverse('actualizar_stock', args=[self.prod_ft.pk])
        response = self.client.post(
            url,
            data=json.dumps({'disponible': False}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.prod_ft.refresh_from_db()
        self.assertTrue(self.prod_ft.disponible)


class FormularioOWASPA03Test(TestCase):
    """Validación de saneamiento de entradas contra inyecciones XSS / HTML."""

    def test_saneamiento_tags_nombre_producto(self):
        form = ProductoForm(data={
            'nombre': '<script>alert("hack")</script>Sandwich de Pavo',
            'categoria': 'Sandwiches',
            'precio_regular': 2800,
            'acepta_junaeb': True,
            'disponible': True,
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['nombre'], 'Sandwich de Pavo')

    def test_rechazo_url_insegura(self):
        form = ProductoForm(data={
            'nombre': 'Jugo Natural',
            'categoria': 'Bebidas',
            'precio_regular': 1500,
            'imagen_url': 'javascript:alert(1)',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('imagen_url', form.errors)
