# 🛡️ GUÍA RÁPIDA DE DEMOSTRACIÓN EN VIVO: ERRORES HTTP 4XX
## Presentación Técnica — Calidad, Testing y Ciberseguridad (TI3043)

Esta guía contiene los **comandos listos para copiar y pegar** durante la presentación en vivo ante la Comisión Evaluadora, permitiendo provocar y evidenciar en tiempo real el manejo defensivo de errores **HTTP 4xx** en el prototipo productivo.

---

## 📋 Resumen de Casos a Demostrar

| Turno / Integrante | Código HTTP | Significado | Escenario de Prueba en el Sistema | Estándar / Norma Vinculada |
| :--- | :--- | :--- | :--- | :--- |
| **1° Yoshua Castillo** | **HTTP 404** | **Not Found** | Petición sobre un ID de producto que no existe en la base de datos. | **ISO/IEC 25010** (Tolerancia a fallos) |
| **2° Vicente Sagredo** | **HTTP 405** | **Method Not Allowed** | Envío de un `GET` a un endpoint configurado exclusivamente para `POST`. | **OWASP A05** (Configuración segura) |
| **3° Martín Tapia** | **HTTP 400** | **Bad Request** | Envío de precio de oferta negativo (`-$500`) o inválido en Promo Flash. | **ISO/IEC 27001 A.8.28** (Codificación segura) |
| **4° Angelo Zamora** | **HTTP 403** | **Forbidden** | Ataque IDOR: Operador de un local intenta mutar el stock de otro local. | **OWASP A01** y **Ley N° 21.459 (Art. 2°)** |

---

> 💡 **Nota Previa para la Consola DevTools (F12):**  
> Si Google Chrome o Edge bloquea el pegado con la advertencia de seguridad *Self-XSS*, escribe primero en la consola:  
> `permitir pegado` *(y pulsa Enter)*. Luego ya podrás pegar cualquier snippet libremente.

---

## 1. 🔍 Yoshua Castillo — DEMOSTRACIÓN HTTP 404: NOT FOUND (Recursos Inexistentes)

### ¿Qué demuestra?
El manejo controlado de excepciones cuando un cliente solicita mutar o consultar un identificador que no existe en el catálogo, impidiendo que el servidor lance excepciones internas 500 no controladas.

### 💻 Opción A: Desde la Consola del Navegador (F12)
```javascript
fetch('/api/producto/999999/stock/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': (document.cookie.match(/csrftoken=([^;]+)/) || [])[1]
  },
  body: JSON.stringify({ disponible: true })
}).then(r => {
  console.log("%c🔍 RESPUESTA HTTP " + r.status + " (NOT FOUND)", "color: #0284C7; font-size: 14px; font-weight: bold;");
  console.log("El producto solicitado no existe en la base de datos de INACAP.");
});
```

### 🎙️ Libreto para la Comisión Evaluadora:
> *"Para garantizar la tolerancia a fallos exigida por la norma **ISO/IEC 25010**, el sistema gestiona de manera controlada las solicitudes dirigidas hacia recursos inexistentes mediante la directiva `get_object_or_404`. Como aprecia la Comisión, el servidor responde con un **HTTP 404 Not Found** estructurado, impidiendo fugas de trazas internas o excepciones no controladas en el servidor de producción."*

---

## 2. 🚫 Vicente Sagredo — DEMOSTRACIÓN HTTP 405: METHOD NOT ALLOWED (Verbos HTTP No Permitidos)

### ¿Qué demuestra?
El endpoint asíncrono `/api/producto/<pk>/stock/` está decorado estrictamente con `@require_http_methods(['POST'])`. Si alguien intenta acceder usando `GET` desde el navegador para obtener datos o ejecutar un ataque CSRF por URL, el servidor rechaza el verbo HTTP.

### 💻 Opción A: Desde la Consola del Navegador (F12)
```javascript
fetch('/api/producto/1/stock/', {
  method: 'GET'
}).then(r => {
  console.log("%c🚫 RESPUESTA HTTP " + r.status + " (METHOD NOT ALLOWED)", "color: purple; font-size: 14px; font-weight: bold;");
  console.log("Solo se admiten mutaciones seguras mediante método POST.");
});
```

### 🎙️ Libreto para la Comisión Evaluadora:
> *"Finalmente, para neutralizar vectores de ataque CSRF basados en enlaces forzados, restringimos los verbos HTTP mediante el decorador `@require_http_methods(['POST'])`. Al intentar consumir el servicio transaccional mediante el verbo GET, el servidor rechaza la solicitud devolviendo un código **HTTP 405 Method Not Allowed**, ratificando una arquitectura defensiva en todas sus capas."*

---

## 3. 🛑 Martín Tapia — DEMOSTRACIÓN HTTP 400: BAD REQUEST (Datos Inválidos / Manipulados)

### ¿Qué demuestra?
Que el backend **no confía ciegamente en el frontend**. Si un usuario altera el payload o envía números negativos, el servidor rechaza la transacción y no ensucia la base de datos.

### 💻 Opción A: Desde la Consola del Navegador (F12)
*(Estando con la sesión iniciada en el Panel del Operador o Catálogo)*

```javascript
fetch('/api/producto/1/promo-flash/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': (document.cookie.match(/csrftoken=([^;]+)/) || [])[1]
  },
  body: JSON.stringify({ action: 'activar', precio_oferta: -500, duracion_minutos: 30 })
}).then(r => r.json().then(data => {
  console.log("%c🛑 RESPUESTA HTTP " + r.status + " (BAD REQUEST)", "color: red; font-size: 14px; font-weight: bold;");
  console.log("Mensaje estructurado devuelto:", data);
}));
```

### 🖥️ Opción B: Desde la Terminal PowerShell
```powershell
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.test_settings'); django.setup(); from django.test import Client; from django.contrib.auth.models import User; u = User.objects.create_user('demo_op'); c = Client(); c.force_login(u); r = c.post('/api/producto/1/promo-flash/', {'precio_oferta': -500}, content_type='application/json'); print('--> ESTADO HTTP:', r.status_code, r.json())"
```

### 🎙️ Libreto para la Comisión Evaluadora:
> *"Ahora, en este escenario simulamos un intento de manipulación transaccional enviando un valor anómalo e inconsistente (precio de oferta negativo de -$500). Como se puede observar en la respuesta de la consola, el sistema no delega la seguridad exclusivamente en la interfaz gráfica, sino que el backend intercepta el payload y responde con un **HTTP 400 Bad Request**, garantizando el principio de integridad transaccional bajo el **Control A.8.28 de la norma internacional ISO/IEC 27001**."*

---

## 4. 🔒 Angelo Zamora — DEMOSTRACIÓN HTTP 403: FORBIDDEN (Aislamiento IDOR / Anti-Hackeo)

### ¿Qué demuestra?
La mitigación de la vulnerabilidad crítica **OWASP Top 10 A01 (Broken Access Control)** y el cumplimiento del **Artículo 2° de la Ley Chilena N° 21.459 de Delitos Informáticos** (acceso ilícito a sistemas informáticos). Un operador jamás puede modificar los productos de un local competidor.

> ⚠️ **Regla Clave para provocar el 403:**  
> El producto **DEBE EXISTIR** en la base de datos, pero debe pertenecer al local de otro operador.  
> * Si estás logueado en el **Casino Central** (`operador_casino`), prueba alterando el **Producto ID 14** (*Café Espresso de Food Truck 1*).
> * Si estás logueado en un **Food Truck**, prueba alterando el **Producto ID 1** (*Cazuela de Vacuno del Casino*).
> *(Si usas un ID que no existe como el 99, Django arrojará 404 Not Found en lugar de 403).*

### 💻 Opción A: Desde la Consola del Navegador (F12)
*(Estando logueado en el Panel del Operador con la cuenta del Casino)*

```javascript
fetch('/api/producto/14/stock/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': (document.cookie.match(/csrftoken=([^;]+)/) || [])[1]
  },
  body: JSON.stringify({ disponible: false })
}).then(async r => {
  const data = r.headers.get('content-type')?.includes('application/json') ? await r.json() : await r.text();
  console.log("%c🔒 RESPUESTA HTTP " + r.status + " (FORBIDDEN)", "color: orange; font-size: 14px; font-weight: bold;");
  console.log("Detalle de Bloqueo Legal (Ley 21.459 / OWASP A01):", data);
});
```

### 🖥️ Opción B: Ejecución del Test Automatizado CP-12
```powershell
.\.venv\Scripts\python.exe manage.py test gastronomia.tests.PanelOperadorSeguridadTest.test_actualizar_stock_local_ajeno_bloqueado --settings=mi_proyecto.test_settings -v 2
```

### 🎙️ Libreto para la Comisión Evaluadora:
> *"Estimada Comisión, a continuación evidenciamos la mitigación de la vulnerabilidad crítica **OWASP Top 10 A01 (Broken Access Control)** y la adherencia al **Artículo 2° de la Ley Chilena N° 21.459 sobre Delitos Informáticos**. Simulamos un ataque IDOR donde un operador autenticado intenta alterar de forma ilícita el stock de un establecimiento ajeno (Producto ID 14 de Food Truck 1). El ORM de Django evalúa la pertenencia relacional (`local.operador == request.user`) y deniega inmediatamente la transacción devolviendo un **HTTP 403 Forbidden** con tipificación legal explícita."*

---

## ⚡ BATERÍA COMPLETA: EJECUTAR TODOS LOS TESTS DE SEGURIDAD EN 1 COMANDO

Si la docente pide verificar que todas estas pruebas de seguridad y código de estado están integradas formalmente en el código del proyecto, solo ejecuta en la terminal:

```powershell
python ejecutar_pruebas.py
```

O para filtrar solo las pruebas de seguridad y códigos de estado:
```powershell
.\.venv\Scripts\python.exe manage.py test gastronomia.tests.PanelOperadorSeguridadTest gastronomia.tests.PromocionesFlashAPITest --settings=mi_proyecto.test_settings -v 2
```

---
*Documento preparado para la defensa final — INACAP Sede Renca 2026*