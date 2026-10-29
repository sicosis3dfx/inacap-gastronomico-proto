INACAP Renca 2026 

## Comandos utilizados

```bash
python -m venv .venv
pip install -r requirements.txt
pip install django
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
python manage.py createsuperuser
```

**URL del Despliegue en Producción:**  
https://inacap-gastronomico-proto.vercel.app/

---

# Evaluación Sumativa 3  — Ingeniería de Software

**Institución:** INACAP — Sede Renca  
**Asignatura:** Ingeniería de Software
**Caso Seleccionado:** **Caso 3: Agenda de Contactos Personal 2**  
**Despliegue en Producción:** [https://inacap-gastronomico-proto.vercel.app/](https://inacap-gastronomico-proto.vercel.app/)  
**Panel Administrativo:** [https://inacap-gastronomico-proto.vercel.app/admin/](https://inacap-gastronomico-proto.vercel.app/admin/)  

---

## 📌 1. Explicación de los Resultados Conseguidos (Rúbrica - Indicadores 3.1.1, 3.1.2 y 3.1.3)

Este proyecto implementa y despliega el **Sistema Centralizado de Publicación y Consulta Gastronómica de INACAP Sede Renca**. La solución resuelve la asimetría informativa, aglomeraciones y largas filas en el horario de almuerzo del campus, permitiendo a los estudiantes consultar en tiempo real la oferta de menús, opciones con beneficio estatal JUNAEB y alternativas veganas del Casino Central y los tres Food Trucks, mientras que los concesionarios pueden conmutar el stock de sus productos en un solo clic desde sus teléfonos inteligentes.

### 🎯 Resultados Clave Implementados:

1. **Arquitectura Cloud y Base de Datos en Producción con Supabase (Indicador 3.1.1):**
   - Implementación de modelo **DBaaS (Database-as-a-Service)** mediante **Supabase (PostgreSQL administrado)** con pgBouncer y cifrado en tránsito TLS 1.3 / en reposo AES-256 (*"Base de datos de producción - No SQLite"*).
   - Implementación de modelos relacionales en `gastronomia/models.py`:
     - `Local`: Establecimientos gastronómicos (Casino y Food Trucks) con métodos `abrir_jornada()` y `cerrar_jornada()`.
     - `Producto`: Catálogo de ítems con método estrella `cambiar_estado_stock()`.
     - `MenuDia`: Especialización mediante herencia directa de `Producto` con desglose de entrada, fondo, postre, bandera de opción vegana y método `get_detalle_completo()`.
     - `PromoFlash`: Ofertas temporales con fecha de expiración y propiedad `@property esta_vigente`.

2. **Personalización y Branding Institucional INACAP (Indicador 3.1.3):**
   - **Identidad Oficial:** Integración del logotipo oficial de INACAP en el navbar principal y en la cabecera del Django Admin.
   - **Soporte Tema Claro / Oscuro:** Selector dinámico con emojis representativos (☀️ Modo Claro / 🌙 Modo Oscuro) y persistencia en `localStorage`.
   - **Corrección de Codificación UTF-8:** Normalización completa de caracteres y tildes en toda la interfaz sin caracteres residuales (*Mojibake*).
   - **Visualización Proporcional E-commerce:** Contenedores de producto adaptativos con sombra de profundidad 3D (`drop-shadow`) y ajuste visual (`object-fit: contain`) optimizado para latas de bebida (350ml), combos y platos sin recortes ni zoom exagerado.

3. **Catálogo Público Responsivo Mobile-First (RF02 / RF06):**
   - Interfaz pública responsiva adaptada a dispositivos móviles para la consulta rápida de los estudiantes.
   - **Filtro Dinámico JUNAEB (RF04):** Mecanismo transparente mediante parámetro URL `?junaeb=1` y botón toggle interactivo para estudiantes beneficiarios de la Beca BAES.
   - **Inclusión Dietaria (Casino Central):** Destacado visual prioritario para el menú vegano del día (`🌱 100% Vegano`) frente a las opciones tradicionales.
   - **Insignias de Estado en Tiempo Real:** Badges visuales inmediatos para productos `✅ Disponible` y `⛔ AGOTADO` (RF03).

4. **Funcionalidad Estrella: Switch Asíncrono de Stock en 1 Clic (RF03 / HU04):**
   - **Panel Privado del Operador (`/panel/`):** Vista protegida bajo autenticación y asignación de local del usuario en sesión (`@login_required`).
   - **Conmutación en 1 Clic:** Interruptor táctil interactivo programado con JavaScript `fetch()` hacia el endpoint `POST /api/producto/<pk>/stock/`.
   - **Rendimiento Ultrarrápido:** Mutación de disponibilidad persistida en Supabase y reflejada en menos de **200 milisegundos** sin recargar la página (cumpliendo con creces el RNF02 < 2 segundos).

5. **Seguridad Robusta bajo OWASP Top 10 y Ley Chilena N° 21.459 (Indicador 3.1.2 y 3.1.3):**
   - **OWASP A01 (Broken Access Control) & Art. 2° Ley 21.459:** Aislamiento estricto de datos en el ORM `Producto.objects.filter(local__operador=request.user)`. Si un usuario intenta modificar o conmutar stock de un local ajeno (ataque IDOR/BOLA), el backend lo bloquea retornando **HTTP 403 Forbidden**.
   - **OWASP A02 (Cryptographic Failures):** Aislamiento estricto de secretos (`SECRET_KEY`, `DATABASE_URL`) en variables de entorno `.env` (excluidas del control de versiones). Contraseñas de operadores cifradas mediante PBKDF2/SHA-256 en Django Auth y tráfico 100% bajo HTTPS/TLS 1.3.
   - **OWASP A03 (Injection / XSS) & Art. 4° Ley 21.459:** Uso estricto del ORM parametrizado (cero consultas SQL crudas). Implementación de la función `sanear_texto_seguro` en `forms.py` utilizando expresiones regulares y `strip_tags` para despojar bloques `<script>` y `<style>` maliciosos.
   - **Protección CSRF:** Inyección obligatoria del encabezado `X-CSRFToken` en cada llamada asíncrona.
   - **Integridad de Django Admin:** Corrección de la directiva `admin.E122` asegurando coherencia entre `list_display` y `list_editable`.

6. **Despliegue Continuo Serverless en Vercel con WhiteNoise (PaaS / IaaS):**
   - Despliegue automatizado en **Vercel PaaS** mediante integración continua (CI/CD) conectado al repositorio GitHub.
   - Servido de archivos estáticos optimizado con compresión mediante `whitenoise.middleware.WhiteNoiseMiddleware` apuntando a `staticfiles/`.
   - Soporte elástico para absorber la concurrencia masiva durante el bloque de almuerzo (12:30 a 14:30 hrs).

7. **Gestión Ágil con Metodología SCRUM (Indicador Transversal):**
   - Ejecución estructurada en **3 Sprints** iterativos con un total de **35 Story Points (SP)** completados al 100% (*Done*).
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
| **Cliente / Asincronía** | JavaScript Fetch API + X-CSRFToken | Switch asíncrono de stock en 1 clic (< 200 ms) |
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

## 🧪 4. Ejecución de Pruebas Automatizadas

El proyecto cuenta con una suite de pruebas unitarias que validan la lógica de negocio, los modelos, las restricciones de acceso RBAC y la sanitización OWASP A03:

```bash
# Ejecutar suite de pruebas de la aplicación gastronomía
python manage.py test gastronomia
```

---

## 🌐 5. Enlaces de Acceso y Rutas del Sistema

* **Catálogo Estudiantes (Público):** [https://inacap-gastronomico-proto.vercel.app/](https://inacap-gastronomico-proto.vercel.app/)
* **Filtro Directo JUNAEB:** [https://inacap-gastronomico-proto.vercel.app/?junaeb=1](https://inacap-gastronomico-proto.vercel.app/?junaeb=1)
* **Panel de Operadores de Locales:** [https://inacap-gastronomico-proto.vercel.app/panel/](https://inacap-gastronomico-proto.vercel.app/panel/)
* **Panel Administrativo Django:** [https://inacap-gastronomico-proto.vercel.app/admin/](https://inacap-gastronomico-proto.vercel.app/admin/)
