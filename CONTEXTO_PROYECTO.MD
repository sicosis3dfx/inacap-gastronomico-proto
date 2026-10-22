# CONTEXTO Y REGLAS DEL PROYECTO: SISTEMA GASTRONÓMICO INACAP RENCA
**Objetivo para el Agente IA:** Actúa como un Ingeniero de Software Senior experto en Python y Django. Debes construir el prototipo funcional para la Evaluación 3 del "Sistema Centralizado de Publicación y Consulta Gastronómica INACAP Renca", manteniendo la misma arquitectura de despliegue (Vercel + Supabase + WhiteNoise) utilizada previamente por el equipo.

## 1. Stack Tecnológico Obligatorio (Presupuesto Cero / Estudiante)
- **Backend y Frontend:** Python 3.x + Django (Arquitectura MTV con Templates responsivos Mobile-First).
- **Base de Datos (Cloud/IaaS):** PostgreSQL alojado en **Supabase** (NO usar SQLite en producción). Conexión mediante variables de entorno (`.env`).
- **Despliegue (PaaS):** Configuración lista para **Vercel** (`vercel.json`, `wsgi.py`) y manejo de archivos estáticos con **WhiteNoise**.

## 2. Modelo de Datos (Estricto según Diagrama de Clases UML del Informe)
En `models.py` de la app principal (ej. `catalogo` o `locales`), debes implementar exactamente estas entidades:
1. **`Local`**:
   - Atributos: `nombre` (CharField), `tipo` (Choices: 'Casino', 'Food Truck'), `activo` (BooleanField, default=True), `operador` (OneToOneField o ForeignKey al modelo `User` de Django para asegurar aislamiento RBAC).
   - Métodos: `abrir_jornada()`, `cerrar_jornada()`.
2. **`Producto`**:
   - Atributos: `local` (ForeignKey a `Local`), `nombre` (CharField), `precio_regular` (PositiveIntegerField), `acepta_junaeb` (BooleanField, default=False), `disponible` (BooleanField, default=True), `categoria` (CharField), `imagen_url` (URLField o ImageField opcional).
   - Método clave: `cambiar_estado_stock(bool)` para marcar como Agotado.
3. **`MenuDia` (Herencia de Modelo / Especialización de `Producto`)**:
   - Hereda de `Producto`.
   - Atributos adicionales: `plato_entrada` (CharField), `plato_fondo` (CharField), `postre` (CharField), `es_vegano` (BooleanField, default=False).
   - Método: `get_detalle_completo()`.
4. **`PromoFlash`**:
   - Atributos: `local` (ForeignKey a `Local`), `producto` (ForeignKey a `Producto`), `precio_oferta` (PositiveIntegerField), `expira_en` (DateTimeField), `activa` (BooleanField, default=True).
   - Método o propiedad: `desactivar_oferta()` / validación automática si `timezone.now() > expira_en`.

## 3. Funcionalidades Críticas a Implementar (Requerimientos Funcionales)
- **RF01 (Autenticación y Aislamiento RBAC):** Cada encargado de los 4 locales (Casino Central, Food Truck 1, 2 y 3) inicia sesión y SOLO puede ver y editar los productos de su propio local. Impedir mediante código que un local modifique datos de otro (Cumplimiento Ley 21.459 de delitos informáticos / acceso no autorizado).
- **RF02 y RF06 (Catálogo Público sin registro):** Vista principal (`index`) pensada para pantallas de celular donde los estudiantes ven los productos agrupados por local sin necesidad de iniciar sesión. Destacar visualmente la opción vegana del Casino.
- **RF03 (Switch "Agotado" en 1 clic - FUNCIONALIDAD ESTRELLA):** En el panel móvil del encargado, incluir un switch deslizable por cada producto. Al tocarlo, debe enviar una petición (`POST` o `PATCH` vía Fetch/AJAX o formulario rápido) al endpoint para cambiar `disponible=False` en menos de 2 segundos (RNF02) y mostrar el badge rojo "AGOTADO" en el catálogo del estudiante.
- **RF04 (Filtro JUNAEB):** Un botón o switch en la vista del estudiante (`?junaeb=1`) que filtre instantáneamente solo los productos con `acepta_junaeb=True`.
- **RF05 (Promociones Flash):** Mostrar en el catálogo las promociones vigentes con un contador regresivo visual en JavaScript hasta `expira_en`.

## 4. Reglas de Seguridad OWASP (Obligatorias para la Rúbrica)
Deja comentarios explícitos en el código (`# SEGURIDAD OWASP: ...`) en las siguientes secciones para exponerlas ante la profesora:
1. **Prevención de Inyecciones (OWASP A03):** Uso estricto del ORM de Django en consultas y filtros (`?junaeb=1`), más validaciones en formularios (`ModelForm`).
2. **Control de Acceso Roto (OWASP A01):** Uso de `@login_required` y filtrado estricto `Producto.objects.filter(local__operador=request.user)` antes de cualquier edición o cambio de stock.
3. **Fallas Criptográficas y Datos Sensibles (OWASP A02):** Uso de variables de entorno (`.env`) para credenciales de Supabase y `SECRET_KEY`, más protección `{% csrf_token %}` en todas las peticiones de modificación.
4. **Manejo de Errores:** Configuración preparada para no exponer trazas sensibles en producción y uso de `django.contrib.messages` para feedback seguro al usuario. 