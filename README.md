# Sistema Centralizado de Publicación y Consulta Gastronómica — INACAP Sede Renca

**Institución:** Universidad Tecnológica de Chile INACAP — Sede Renca  
**Asignatura:** TI3043 — Ingeniería de Software  
**Docente Guía:** Oscarina Sanabria  
**Equipo de Desarrollo:** Yoshua Castillo · Martín Tapia · Vicente Sagredo · Angelo Zamora  
**Repositorio GitHub:** [https://github.com/sicosis3dfx/inacap-gastronomico-proto/](https://github.com/sicosis3dfx/inacap-gastronomico-proto/)  
**Despliegue en Producción:** [https://inacap-gastronomico-proto.vercel.app/](https://inacap-gastronomico-proto.vercel.app/)  
**Panel Administrativo:** [https://inacap-gastronomico-proto.vercel.app/admin/](https://inacap-gastronomico-proto.vercel.app/admin/)  

---

## 💻 Instalación y Despliegue Local

```bash
# Creación y activación del entorno virtual
python -m venv .venv
# En Windows: .venv\Scripts\activate
# En Linux/macOS: source .venv/bin/activate

# Instalación de dependencias
pip install -r requirements.txt

# Aplicación de migraciones a la base de datos
python manage.py makemigrations
python manage.py migrate

# Creación de superusuario y arranque del servidor local
python manage.py createsuperuser
python manage.py runserver
```

## 📌 1. Arquitectura y Resultados Implementados del Proyecto

Este proyecto implementa y despliega el **Sistema Centralizado de Publicación y Consulta Gastronómica de INACAP Sede Renca**. La solución resuelve la asimetría informativa, aglomeraciones y largas filas en el horario de almuerzo del campus, permitiendo a los estudiantes consultar en tiempo real la oferta de menús, opciones con beneficio estatal JUNAEB y alternativas veganas del Casino Central y los tres Food Trucks, mientras que los concesionarios pueden conmutar el stock de sus productos en un solo clic desde sus teléfonos inteligentes.

### 🎯 Resultados Clave Implementados:

1. **Arquitectura Cloud y Base de Datos en Producción con Supabase:**
   - Implementación de modelo **DBaaS (Database-as-a-Service)** mediante **Supabase (PostgreSQL administrado)** con pgBouncer y cifrado en tránsito TLS 1.3 / en reposo AES-256 (*"Base de datos de producción - No SQLite"*).
   - Implementación de modelos relacionales en `gastronomia/models.py`:
     - `Local`: Establecimientos gastronómicos (Casino y Food Trucks) con métodos `abrir_jornada()` y `cerrar_jornada()`.
     - `Producto`: Catálogo de ítems con método estrella `cambiar_estado_stock()`.
     - `MenuDia`: Especialización mediante herencia directa de `Producto` con desglose de entrada, fondo, postre, bandera de opción vegana y método `get_detalle_completo()`.
     - `PromoFlash`: Ofertas temporales con fecha de expiración, propiedad `@property esta_vigente`, `@property porcentaje_descuento` y `@property monto_ahorro` (100% alineado al Diagrama de Clases UML 2.5).

2. **Personalización y Branding Institucional INACAP:**
   - **Identidad Oficial:** Integración del logotipo oficial de INACAP en el navbar principal y en la cabecera del Django Admin.
   - **Diseño Institucional Limpio y Profesional:** Paleta cromática oficial de INACAP (Rojo Institucional `#b91c1c`, Azul Marino `#0f172a`, Verde JUNAEB `#1b5e20` y Naranja Flash `#d84315`), con tipografía moderna `Plus Jakarta Sans` y contrastes certificados para accesibilidad WCAG.
   - **Corrección de Codificación UTF-8:** Normalización completa de caracteres y tildes en toda la interfaz sin caracteres residuales (*Mojibake*).
   - **Visualización Proporcional E-commerce:** Contenedores de producto adaptativos con sombra de profundidad 3D (`drop-shadow`) y ajuste visual (`object-fit: contain`) optimizado para latas de bebida (350ml), combos y platos sin recortes ni zoom exagerado.

3. **Catálogo Público Responsivo Mobile-First con Filtrado Asíncrono (RF02 / RF06):**
   - **Filtrado Dinámico Asíncrono (SPA-like con Fetch API):** Búsqueda por texto en tiempo real con debounce, filtro por local y botón conmutable JUNAEB sin recargar la página completa, sincronizando la URL mediante `history.replaceState`.
   - **Conmutador de Vistas Dual (Cuadrícula Completa / Lista Simplificada):** Permite a los estudiantes alternar con 1 clic entre una vista rica en imágenes (por defecto) y una vista condensada de alta velocidad para consulta rápida en horas punta, con transición suave y persistencia en `localStorage`.
   - **Botón Flotante Inteligente "Volver Arriba":** Acceso rápido al inicio del catálogo activado dinámicamente mediante sensor de scroll con transiciones suaves.
   - **Filtro Dinámico JUNAEB (RF04):** Mecanismo transparente mediante parámetro URL `?junaeb=1` y botón toggle interactivo (activar/desactivar en un toque) para estudiantes beneficiarios de la Beca BAES.
   - **Inclusión Dietaria (Casino Central):** Destacado visual prioritario para el menú vegano del día (`🌱 100% Vegano`) frente a las opciones tradicionales.
   - **Insignias de Estado en Tiempo Real:** Badges visuales inmediatos para productos `✅ Disponible`, `⛔ AGOTADO` (RF03) e insignia animada `⚡ PROMO FLASH` (RF05).

4. **Funcionalidad Estrella: Switch Asíncrono de Stock en 1 Clic (RF03 / HU04):**
   - **Panel Privado del Operador (`/panel/`):** Vista protegida bajo autenticación y asignación de local del usuario en sesión (`@login_required`).
   - **Conmutación en 1 Clic Mobile-First:** Interruptor táctil ergonómico con etiquetas visuales proporcionales (`DISPONIBLE` / `AGOTADO`), programado con JavaScript `fetch()` hacia el endpoint `POST /api/producto/<pk>/stock/`.
   - **Rendimiento Ultrarrápido:** Mutación de disponibilidad persistida en Supabase y reflejada en menos de **200 milisegundos** sin recargar la página (cumpliendo con creces el RNF02 < 2 segundos).

5. **Módulo de Gestión de Promociones Flash de Alto Impacto (RF05):**
   - **Autonomía Operativa Descentralizada:** Cada encargado de local puede formular, editar y activar ofertas relámpago directamente desde su panel operativo (`/panel/`), eliminando la dependencia previa de la administración central.
   - **Configuración de Precios y Temporizador Programado:** Permite ajustar el precio regular, fijar el precio de oferta con descuento y definir la duración de vigencia (30 min, 1 hr, 2 hrs, 3 hrs o jornada completa).
   - **Endpoint Asíncrono Seguro (`POST /api/producto/<pk>/promo-flash/`):** Activación y desactivación en 1 clic mediante llamadas asíncronas con la API `fetch()`, calculando automáticamente la estampa temporal de expiración (`expira_en`) con retroalimentación Toast inmediata.
   - **Showcase de Precios de Alto Impacto:**
     - Tarjeta destacada con cápsula comparativa de precios: Precio Normal tachado con etiqueta de referencia, flecha de flujo promocional (`➔`), y Precio de Oferta en tipografía de alto impacto (`2.1rem`, Font-weight 900) con etiqueta `🔥 Oferta Flash`.
     - Insignia dinámica de descuento porcentual (`-XX% DTO`) y píldora de ahorro exacto (`Ahorras $X.XXX`), modeladas formalmente como `@property porcentaje_descuento` y `@property monto_ahorro` en la clase `PromoFlash`.
     - Marquesina superior responsiva con temporizador en vivo de expiración.
   - **Métricas en Vivo del Turno:** Chip dinámico en el panel del operador que monitoriza el total de ofertas flash vigentes en tiempo real.

6. **Seguridad Robusta bajo OWASP Top 10 y Ley Chilena N° 21.459:**
   - **OWASP A01 (Broken Access Control) & Art. 2° Ley 21.459:** Aislamiento estricto de datos en el ORM `Producto.objects.filter(local__operador=request.user)`. Si un usuario intenta modificar o conmutar stock de un local ajeno (ataque IDOR/BOLA), el backend lo bloquea retornando **HTTP 403 Forbidden**.
   - **Estandarización RBAC con Grupos Institucionales:** Implementación del rol `Encargados de Locales Permisos Aislados`, centralizando los permisos mínimos necesarios (`add/change/view` sobre productos, menús y promociones flash) mientras que la lógica de `get_queryset()` y `formfield_for_foreignkey()` en `admin.py` y `views.py` confina el acceso únicamente a los registros del local asignado.
   - **OWASP A02 (Cryptographic Failures):** Aislamiento estricto de secretos (`SECRET_KEY`, `DATABASE_URL`) en variables de entorno `.env` (excluidas del control de versiones). Contraseñas de operadores cifradas mediante PBKDF2/SHA-256 en Django Auth y tráfico 100% bajo HTTPS/TLS 1.3.
   - **OWASP A03 (Injection / XSS) & Art. 4° Ley 21.459:** Uso estricto del ORM parametrizado (cero consultas SQL crudas). Implementación de la función `sanear_texto_seguro` en `forms.py` utilizando expresiones regulares y `strip_tags` para despojar bloques `<script>` y `<style>` maliciosos.
   - **Protección CSRF:** Inyección obligatoria del encabezado `X-CSRFToken` en cada llamada asíncrona.
   - **Integridad de Django Admin:** Corrección de la directiva `admin.E122` asegurando coherencia entre `list_display` y `list_editable`.

7. **Despliegue Continuo Serverless en Vercel con WhiteNoise (PaaS / IaaS):**
   - Despliegue automatizado en **Vercel PaaS** mediante integración continua (CI/CD) conectado al repositorio GitHub.
   - Servido de archivos estáticos optimizado con compresión mediante `whitenoise.middleware.WhiteNoiseMiddleware` apuntando a `staticfiles/`.
   - Soporte elástico para absorber la concurrencia masiva durante el bloque de almuerzo (12:30 a 14:30 hrs).

8. **Gestión Ágil con Metodología SCRUM (Sprint 1 al Sprint 4):**
   - Ejecución estructurada en **4 Sprints** iterativos con un total acumulado de **56 Story Points (SP)** completados al 100% (*Done*).
   - **Sprint 4 enfocado en Testing Integral, Hardening de Seguridad (OWASP / ISO 27001) y Calidad de Software (ISO 25010).**
   - Tablero Kanban en **Trello Workspace** con control de Definition of Done (DoD), criterios de aceptación y matrices de trazabilidad.

---

## 🛠️ 2. Arquitectura Tecnológica Cloud

| Capa / Componente | Tecnología / Plataforma | Rol en el Sistema |
| :--- | :--- | :--- |
| **Lenguaje** | Python 3.13 | Lógica de negocio y backend |
| **Framework Web** | Django 6.1 (MTV) | Controladores, ORM, formularios seguros y templates |
| **Base de Datos (DBaaS)** | Supabase (PostgreSQL Cloud) | Persistencia relacional dedicada con TLS 1.3 y pgBouncer |
| **Plataforma Cloud (PaaS)** | Vercel Serverless WSGI | Alojamiento serverless elástico con escalamiento automático |
| **Distribución de Estáticos** | WhiteNoise 6.9 | Compresión y entrega de CSS, JS e imágenes institucionales |
| **Cliente / Asincronía** | JavaScript Fetch API + X-CSRFToken | Switch asíncrono de stock en 1 clic (< 200 ms) y gestión de Promociones Flash en vivo |
| **Seguridad y Cifrado** | OWASP Top 10 + PBKDF2 / TLS 1.3 | Sanitización de entradas, RBAC y blindaje anti-IDOR |
| **Control de Versiones** | Git + GitHub | Integración y despliegue continuo (CI/CD) |
| **Gestión de Proyecto** | Marco Ágil SCRUM (Trello) | Sprints, estimación en Planning Poker y control de DoD |

---

## 👥 3. Equipo de Desarrollo y Asignación de Roles SCRUM

| Integrante | Rol SCRUM | Responsabilidad Técnica Principal |
| :--- | :--- | :--- |
| **Angelo Zamora** | Product Owner / Cloud Dev | Priorización de Backlog, aprovisionamiento DBaaS Supabase, despliegue Vercel y modelos ORM |
| **Martín Tapia** | Scrum Master / Backend Security | Gestión de Sprints, vistas/endpoints en `views.py`, blindaje OWASP y Ley N° 21.459 |
| **Yoshua Castillo** | Frontend / UX Developer | Maquetación Mobile-First, estilos institucionales, JavaScript asíncrono y filtro JUNAEB |
| **Vicente Sagredo** | QA Tester / Dev Core | Diseño de matrices de prueba, verificación de latencia asíncrona (< 200 ms) y control de DoD |

---

## 🧪 4. Batería de Pruebas Automatizadas (Testing Suite)

El proyecto cuenta con una suite integral de **21 pruebas automatizadas** desarrolladas sobre el framework nativo de pruebas de Django (`unittest.TestCase` y `Client`), garantizando calidad de software, seguridad de la información y eficiencia de desempeño:

### 🚀 Comandos de Ejecución

```bash
# Opción 1: Ejecución rápida directa con script interactivo (Recomendado)
python ejecutar_pruebas.py

# Opción 2: Ejecución mediante el runner oficial de Django con salida detallada
python manage.py test --settings=mi_proyecto.test_settings -v 2
```

> **Nota de Rendimiento:** La suite utiliza una configuración de base de datos aislada en memoria (`SQLite :memory:`), permitiendo ejecutar las 21 pruebas en menos de **0.20 segundos** sin alterar la base de datos de producción Supabase y garantizando un 100% de tasa de éxito (`OK`).

### 📋 Cobertura de las Pruebas Implementadas (`gastronomia/tests.py`)

1. **Pruebas de Lógica de Dominio y Modelos (RF01, RF03, RF05):**
   - Ciclo de apertura y cierre de jornada operativa en `Local` (`abrir_jornada()`, `cerrar_jornada()`).
   - Conmutación booleana inmediata de stock en `Producto` (`cambiar_estado_stock()`).
   - Concatenación estructurada de platos en `MenuDia` (`get_detalle_completo()`).
   - Verificación dinámica de vigencia temporal en `PromoFlash` (`esta_vigente`, cálculo con fechas futuras y expiradas).

2. **Pruebas Funcionales y Vistas Públicas (RF02, RF04, RF06):**
   - Acceso anónimo al catálogo público sin requerir inicio de sesión (HTTP 200).
   - Filtrado booleano en tiempo real por beneficio estatal JUNAEB (`?junaeb=1`), verificando la exclusión de productos no adheridos.

3. **Pruebas de Ciberseguridad OWASP Top 10 y Ley Chilena N° 21.459:**
   - **OWASP A01 (Broken Access Control / IDOR):** Bloqueo estricto con **HTTP 403 Forbidden** ante intentos no autorizados de un operador para modificar stock o promociones de un local ajeno.
   - **Aislamiento Horizontal de Panel:** Verificación de que cada encargado visualiza exclusivamente los productos asociados a su establecimiento.
   - **OWASP A03 (Injection / XSS):** Sanitización automática de etiquetas maliciosas `<script>` mediante `strip_tags` y rechazo estricto de esquemas no seguros (`javascript:`) en campos de URL.

4. **Pruebas de Control de Acceso Basado en Roles (RBAC / ISO 27001):**
   - Validación del grupo formal `Encargados de Locales Permisos Aislados`.
   - Verificación del Principio de Mínimo Privilegio: asignación de permisos de modelo (`add`, `change`, `view` en Producto y PromoFlash) sin privilegios globales (`is_staff=False`, `is_superuser=False`).

5. **Pruebas de la API de Promociones Flash (RF05):**
   - Activación de oferta relámpago con cálculo programado de fecha de expiración y precio rebajado (`POST /api/producto/<pk>/promo-flash/`).
   - Desactivación manual inmediata de promociones activas.
   - Validación de robustez ante datos corruptos o valores numéricos inválidos (HTTP 400 Bad Request ante ofertas negativas o iguales a cero).

6. **Pruebas de Rendimiento y Latencia (ISO/IEC 25010):**
   - Medición estricta del tiempo de respuesta del servidor en endpoints asíncronos críticos (`/api/producto/<pk>/stock/` y `/api/producto/<pk>/promo-flash/`), certificando una latencia inferior a **200 milisegundos** (latencia media observada: ~2.8 ms).

---

## 🌐 5. Enlaces de Acceso y Rutas del Sistema

* **Catálogo Estudiantes (Público):** [https://inacap-gastronomico-proto.vercel.app/](https://inacap-gastronomico-proto.vercel.app/)
* **Filtro Directo JUNAEB:** [https://inacap-gastronomico-proto.vercel.app/?junaeb=1](https://inacap-gastronomico-proto.vercel.app/?junaeb=1)
* **Panel de Operadores de Locales:** [https://inacap-gastronomico-proto.vercel.app/panel/](https://inacap-gastronomico-proto.vercel.app/panel/)
* **Panel Administrativo Django:** [https://inacap-gastronomico-proto.vercel.app/admin/](https://inacap-gastronomico-proto.vercel.app/admin/)
* **Endpoint API Stock (Asíncrono):** `POST /api/producto/<id>/stock/`
* **Endpoint API Promo Flash (Asíncrono):** `POST /api/producto/<id>/promo-flash/`
