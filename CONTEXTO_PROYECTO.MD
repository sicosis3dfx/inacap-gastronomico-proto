# DIRECTRICES TÉCNICAS Y CONTEXTO DEL SISTEMA: EVALUACIÓN 3
**Proyecto:** Sistema Centralizado de Publicación y Consulta Gastronómica — INACAP Sede Renca.  
**Módulo Django Principal:** `gastronomia`  
**Rol del Agente IA:** Actúa como Ingeniero de Software Full-Stack Senior en Python/Django. Tu objetivo es transformar la base del repositorio clonado en el prototipo funcional operativo exigido para la Evaluación 3, manteniendo estricta fidelidad con los diagramas UML, requerimientos y matriz de trazabilidad del informe técnico previo. Toda la lógica, vistas, modelos y plantillas deben estructurarse bajo la aplicación `gastronomia`.

---

## 1. Alcance Funcional y Requerimientos del Sistema

El sistema administra la oferta gastronómica de cuatro locales: Casino Central, Food Truck 1, Food Truck 2 y Food Truck 3.

- **RF01 - Autenticación y Perfiles Independientes (RBAC):** Inicio de sesión exclusivo e independiente para cada encargado de local. Un operador autenticado solo puede gestionar su propio catálogo; el sistema debe bloquear cualquier acceso o edición sobre locales ajenos (Aislamiento lógico y cumplimiento Ley N° 21.459).
- **RF02 - Gestión de Catálogo y Menús:** Publicación de alternativas de almuerzo y líneas de productos. El Casino Central publica 3 alternativas diarias (2 tradicionales y 1 opción vegana destacada). Los Food Trucks administran sus productos por categoría, precio y fotografía.
- **RF03 - Actualización de Stock (Funcionalidad Crítica Prioritaria):** Control directo mediante switch interactivo en la interfaz móvil del encargado para marcar productos como "Agotado" en 1 clic. La actualización debe persistir en la base de datos Supabase (PostgreSQL) y reflejarse en el catálogo público en menos de 2 segundos (RNF02).
- **RF04 - Filtrado JUNAEB:** Mecanismo en la vista del estudiante (`?junaeb=1` o filtro en interfaz) que oculta instantáneamente los productos que no acepten pago con tarjeta de beneficio estudiantil.
- **RF05 - Promociones Flash:** Programación de ofertas con precio rebajado y temporizador regresivo que finaliza y desactiva la oferta automáticamente al expirar el tiempo establecido.
- **RF06 - Consulta Pública del Catálogo:** Navegación pública, responsiva (Mobile-First) y centralizada para los estudiantes sin requerir registro de cuenta ni inicio de sesión.

---

## 2. Modelo de Dominio (Diagrama de Clases UML del Informe)

En el archivo `gastronomia/models.py`, se deben implementar exactamente las siguientes entidades, respetando atributos, relaciones de herencia y métodos públicos:

### Clase `Local`
- **Atributos:**
  - `id_local`: Clave primaria autoincremental.
  - `nombre`: CharField.
  - `tipo`: CharField con opciones choices ('Casino', 'Food Truck').
  - `activo`: BooleanField (default=True).
  - `operador`: OneToOneField a `auth.User` de Django para aislamiento estricto por usuario.
- **Métodos:**
  - `abrir_jornada()`: void (establece `activo=True`).
  - `cerrar_jornada()`: void (establece `activo=False`).

### Clase `Producto`
- **Atributos:**
  - `id_producto`: Clave primaria autoincremental.
  - `local`: ForeignKey a `Local` (relación "administra", related_name='productos').
  - `nombre`: CharField.
  - `precio_regular`: PositiveIntegerField.
  - `acepta_junaeb`: BooleanField (default=False).
  - `disponible`: BooleanField (default=True).
  - `categoria`: CharField opcional.
  - `imagen_url`: URLField opcional.
- **Métodos:**
  - `cambiar_estado_stock(bool)`: void (actualiza el campo `disponible`).

### Clase `MenuDia` (Especialización / Herencia de `Producto`)
- **Herencia:** Hereda directamente de `Producto`.
- **Atributos propios:**
  - `plato_entrada`: CharField.
  - `plato_fondo`: CharField.
  - `postre`: CharField.
  - `es_vegano`: BooleanField (default=False).
- **Métodos:**
  - `get_detalle_completo()`: string (retorna cadena formateada con entrada, fondo y postre).

### Clase `PromoFlash`
- **Atributos:**
  - `id_promo`: Clave primaria autoincremental.
  - `local`: ForeignKey a `Local` (relación "genera", related_name='promociones').
  - `producto`: ForeignKey a `Producto`.
  - `precio_oferta`: PositiveIntegerField.
  - `expira_en`: DateTimeField.
  - `activa`: BooleanField (default=True).
- **Métodos:**
  - `desactivar_oferta()`: void (cambia `activa=False`).
  - Propiedad `esta_vigente`: valida `activa and timezone.now() < self.expira_en`.

---

## 3. Dinámica y Comportamiento del Sistema

### Diagrama de Secuencia (RF03 / HU04 - Actualización de Stock)
El flujo operativo debe cumplir las siguientes interacciones:
1. El encargado conmuta el switch de disponibilidad en la interfaz móvil.
2. La interfaz envía una petición asíncrona (`POST` o `PATCH` vía Fetch a `/api/producto/<id>/stock/`) indicando `disponible=false`.
3. La API/Vista valida la sesión (`@login_required`), verifica pertenencia del producto al local del usuario y ejecuta el `UPDATE` en Supabase (PostgreSQL).
4. La base de datos almacena el estado y el backend retorna una respuesta JSON HTTP 200.
5. El switch en la vista móvil del encargado cambia a inactivo/rojo.
6. La vista pública de los estudiantes, al consultar el catálogo (`GET /`), renderiza el ítem con el badge distintivo "AGOTADO".

### Diagrama de Estados (Ciclo de Vida del Ítem)
Los productos deben respetar los siguientes estados y transiciones:
- `Registrado / Inactivo`: Producto persistido con local cerrado.
- `Disponible`: Activado tras apertura de jornada.
- `Agotado`: Al acabarse el stock físico mediante conmutación del switch.
- `EnPromoFlash`: Estado activo cuando posee una oferta relámpago vigente vinculada.
- `Descontinuado`: Retirado definitivamente de la carta del local.

---

## 4. Requisitos de Seguridad OWASP y Ley Chilena N° 21.459

Todo el código generado debe documentar explícitamente su cumplimiento normativo mediante comentarios en el código:

1. **A01: Broken Access Control & Ley 21.459 (Acceso Ilícito):**
   - Vistas operativas protegidas con `@login_required`.
   - Restricción estricta de consultas a nivel de base de datos: `Producto.objects.filter(local__operador=request.user)`. Ningún usuario puede alterar registros de otro local.
2. **A03: Injection:**
   - Consultas y filtros (`?junaeb=1`, `?local=X`) construidos exclusivamente mediante el ORM de Django. Queda prohibido el uso de consultas SQL crudas o concatenadas.
3. **A02: Cryptographic Failures & Manejo de Secretos:**
   - Las variables sensibles de conexión a Supabase y la `SECRET_KEY` deben residir en variables de entorno leídas desde `.env`.
   - Uso obligatorio de la etiqueta `{% csrf_token %}` en formularios y envío de la cabecera `X-CSRFToken` en peticiones Fetch/AJAX.

---

## 5. Hoja de Ruta para la Refactorización en `gastronomia`

1. **Persistencia y Modelos (`gastronomia/models.py` y `gastronomia/admin.py`):**
   - Implementar las clases `Local`, `Producto`, `MenuDia` y `PromoFlash` con sus métodos.
   - Configurar `gastronomia/admin.py` registrando todos los modelos. En `ProductoAdmin` y `MenuDiaAdmin`, incluir `disponible` tanto en `list_display` como en `list_editable` para evitar excepciones `admin.E122`.
   - Personalizar encabezados en Admin:
     - `admin.site.site_header = "Sistema Gastronómico INACAP Renca"`
     - `admin.site.site_title = "Portal Gastronómico"`
2. **Lógica de Control (`gastronomia/views.py`, `gastronomia/urls.py`):**
   - Retirar los parsers de archivos vCard (`.vcf`) del proyecto anterior.
   - Implementar:
     - `catalogo_estudiantes`: Vista pública que lista productos por local con filtro booleano JUNAEB.
     - `panel_operador`: Vista privada para el encargado donde lista los productos de su local.
     - `actualizar_stock`: Endpoint rápido para conmutar `disponible` en un clic.
3. **Capa Visual (`gastronomia/templates/gastronomia/`):**
   - Reutilizar el sistema de estilos institucionales de INACAP y WhiteNoise.
   - Diseñar las tarjetas de producto en formato Mobile-First, visualizando precios, badges de JUNAEB, etiqueta de menú vegano y los switches deslizables de disponibilidad.