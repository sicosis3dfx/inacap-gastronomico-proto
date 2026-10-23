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

## 📌 1. Explicación de los Resultados Conseguidos (Rúbrica - Indicador 4)

Este proyecto representa la consolidación y evolución de la **Agenda de Contactos Personal**, implementando una **solución productiva completa en la nube (PaaS en Vercel)** respaldada por una base de datos relacional en **Supabase (PostgreSQL gestionado, No SQLite)**, arquitectura MTV (Modelo-Template-Vista), interfaz administrativa avanzada con control de acceso basado en roles (RBAC) y sincronización con dispositivos móviles mediante estándares universales vCard (.vcf).

### 🎯 Resultados Clave Implementados:
1. **Base de Datos en Producción con Supabase (Indicador 1):**
   - Configuración y migración integral del esquema relacional directamente en **Supabase (PostgreSQL en la nube)**, cumpliendo con el requerimiento estricto de la evaluación (*"Base de datos de producción - No SQLite"*).
   - Ejecución verificada de migraciones (`makemigrations` y `migrate`) para los modelos del sistema, sesiones y control de autenticación.

2. **Personalización y Branding de Django Admin (Indicadores 2 y 10):**
   - **Identidad Institucional:** Títulos de sitio, encabezados y favicon personalizados (`Agenda de Contactos | INACAP`).
   - **Soporte Tema Claro / Oscuro:** Selector en cabecera con persistencia en `localStorage`.
   - **Diferenciación Visual de Roles (RBAC):** Insignias de color para clasificar visualmente `👑 Superusuario`, `🛡️ Staff` y `👤 Usuario normal`.
   - **Acciones Masivas en Admin:** Exportación directa a CSV compatible con Excel y normalización masiva de nombres en formato título.
   - **Filtros Avanzados (`SimpleListFilter`):** Segmentación por dominio de correo (Gmail, INACAP, Outlook/Hotmail, Otros).
   - **Internacionalización y Textos:** Interfaz 100% en español sin textos residuales en inglés.

3. **CRUD Completo con Validaciones Robustas (Indicador 3):**
   - Operaciones completas de Crear, Listar, Ver Detalle, Editar y Eliminar contactos.
   - Validación personalizada de número móvil chileno (`+56 9 XXXX XXXX` o `9XXXXXXXX`) y validación estricta de estructura de correo electrónico.
   - Eliminación masiva de contactos seleccionados con confirmación previa y conteo auditado.

4. **Experiencia de Usuario (UX/UI) y Feedback (Indicador 5):**
   - **Paginación Inteligente:** Listados paginados a 12 contactos por página con navegación fluida y preservación de filtros de búsqueda (`?page=X&q=...`).
   - **Mensajes Flash:** Notificaciones visuales (`messages.success`, `messages.warning`, `messages.error`) tras cada acción realizada.

5. **Seguridad y Variables de Entorno (Indicador 6):**
   - Aislamiento completo de credenciales de conexión de Supabase (`host`, `database`, `user`, `password`, `port`) a través de variables de entorno seguras (`.env` excluido del control de versiones).

6. **Despliegue en PaaS con WhiteNoise (Indicadores 7 y 8):**
   - Empaquetado y servido de archivos estáticos optimizado con compresión mediante `whitenoise.middleware.WhiteNoiseMiddleware`.
   - Configuración serverless con `vercel.json` y `wsgi.py` para despliegue continuo de alto rendimiento.

7. **Integración Móvil vCard (.vcf Bidireccional - Indicador 9):**
   - **Importación desde Smartphone:** Procesador nativo en Django que permite subir archivos `.vcf` exportados de Android/iPhone, parseando nombres, teléfonos, correos y direcciones hacia la base de datos sin duplicados.
   - **Exportación a Celular:** Descarga individual y por lote seleccionado en formato `.vcf` directamente importable en la agenda nativa de cualquier smartphone.

---

## 🛠️ 2. Arquitectura Tecnológica

| Componente | Tecnología / Servicio |
| :--- | :--- |
| **Lenguaje** | Python 3.13 |
| **Framework Web** | Django 6.1 (Arquitectura MTV) |
| **Base de Datos** | Supabase (PostgreSQL PaaS en la nube - No SQLite) |
| **Hosting / PaaS** | Vercel Serverless WSGI |
| **Servidor de Estáticos** | WhiteNoise 6.9 |
| **Control de Versiones** | Git + GitHub Desktop |
| **Formato Móvil** | vCard 2.1 / 3.0 / 4.0 (.vcf) |

---

## 🧪 3. Ejecución de Pruebas Automatizadas

El proyecto incluye un conjunto de pruebas unitarias que verifican el correcto funcionamiento de las vistas, validaciones y modelos:

```bash
python manage.py test contactos
```

---

## 🌐 4. Enlaces de Acceso

* **Aplicación Web:** [https://ti3041-p2-c3-2026p-u1.vercel.app/](https://ti3041-p2-c3-2026p-u1.vercel.app/)
* **Panel de Administración:** [https://ti3041-p2-c3-2026p-u1.vercel.app/admin/](https://ti3041-p2-c3-2026p-u1.vercel.app/admin/)
