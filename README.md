# Práctica: Mi Primer Agente de IA — Python y Gemini

Guía completa y estructurada del proyecto basada en el documento oficial `Practica_Agente_Soporte_Python (1).pdf`.

---

## 📋 Resumen del Funcionamiento

El objetivo de esta práctica es construir un **agente de inteligencia artificial** que funcione de manera autónoma con el siguiente flujo:

```
[ Google Forms ]        --> Entrada del usuario (queja o sugerencia)
       ↓
[ Google Sheets ]       --> Base de datos que almacena las respuestas
       ↓
[ Script Python ]       --> El Agente: lee quejas nuevas y las procesa
       ↓
[ Gemini AI API ]       --> Clasifica (Ventas / Soporte / Logística) y detecta sentimiento (Positivo / Negativo / Neutro)
       ↓
[ Google Sheets ]       --> Escribe los resultados en las columnas D y E, y marca la columna F con 'SI'
```

---

## 📦 Librerías y Dependencias

Las librerías requeridas ya están instaladas en tu entorno de Python:
- `gspread`: Lectura y escritura en Google Sheets.
- `google-auth` / `google-auth-oauthlib`: Autenticación con credenciales OAuth 2.0 de Google.
- `google-genai`: SDK oficial para conectar con la API de Gemini (`gemini-2.5-flash`).
- `schedule`: Planificador para ejecutar el agente periódicamente cada 15 minutos.

Si requieres reinstalarlas en cualquier momento:
```bash
pip install gspread google-auth google-genai schedule
```

---

## 🛠️ Guía Paso a Paso para Completar la Práctica

### **FASE 1: Preparar la Entrada y la Salida (Google Forms y Sheets)**

#### 1.1 Crear el Formulario de Quejas
1. Ingresa a [forms.google.com](https://forms.google.com) con tu cuenta de Google (Gmail).
2. Crea un nuevo formulario y asígnale el título:
   ```text
   Formulario de Quejas y Sugerencias
   ```
3. Agrega dos preguntas:
   - **Pregunta 1:** `Tu Nombre` *(Tipo: Respuesta corta, campo opcional)*.
   - **Pregunta 2:** `Describe tu queja, sugerencia o comentario.` *(Tipo: Párrafo, campo obligatorio)*.

#### 1.2 Crear la Base de Datos (Google Sheets)
1. En el formulario, haz clic en la pestaña **Respuestas**.
2. Haz clic en el ícono verde de **Google Sheets** ("Vincular con Hojas de cálculo").
3. Elige **"Crear una nueva hoja de cálculo"** y nómbrala exactamente:
   ```text
   Respuestas de Quejas (Base de Datos)
   ```
4. Se abrirá la hoja de cálculo. Google Forms generará automáticamente las columnas A, B y C. 
5. Agrega manualmente los encabezados en la **Fila 1** para las columnas D, E y F:

| Columna | Encabezado exacto a escribir | ¿Quién lo llena? |
|:---:|:---|:---|
| **A** | Marca temporal | Google Forms (automático) |
| **B** | Tu Nombre | Google Forms (automático) |
| **C** | Describe tu queja... | Google Forms (automático) |
| **D** | **Clasificación IA** | El agente de Python |
| **E** | **Sentimiento IA** | El agente de Python |
| **F** | **Agente Ejecutado** | El agente de Python (escribe `SI`) |

#### 1.3 Enviar un Dato de Prueba
1. En el formulario, haz clic en el icono del ojo (**Vista previa**).
2. Envía una queja de prueba:
   - **Nombre:** `Cliente de Prueba`
   - **Comentario:** `Mi pedido llegó tarde y la caja estaba rota. Muy mal servicio.`
3. Verifica que la fila 2 de la hoja de cálculo contenga estos datos en las columnas A, B y C.

---

### **FASE 2: Configurar el Acceso a Google Sheets (OAuth 2.0)**

#### 2.1 a 2.3 Crear Proyecto y Habilitar APIs
1. Ingresa a [console.cloud.google.com](https://console.cloud.google.com) con tu cuenta de Gmail.
2. En la barra superior, haz clic en el selector de proyectos y luego en **"Proyecto nuevo"**.
3. Asigna el nombre `Agente de Soporte` y haz clic en **Crear**. Asegúrate de tener este proyecto seleccionado.
4. Ve al menú lateral **APIs y servicios** → **Biblioteca**.
5. Busca y habilita las siguientes dos APIs:
   - **Google Sheets API** → Clic en *Habilitar*.
   - **Google Drive API** → Clic en *Habilitar*.

#### 2.4 Pantalla de Consentimiento OAuth
1. Ve a **APIs y servicios** → **Pantalla de consentimiento de OAuth** (OAuth consent screen).
2. Selecciona **External** (Externo) y haz clic en **Crear**.
3. Completa los campos obligatorios:
   - Nombre de la aplicación: `AgenteSoporte`
   - Correo electrónico de asistencia al usuario: tu propio correo Gmail.
   - Datos de contacto del desarrollador: tu propio correo Gmail.
4. Haz clic en **Guardar y continuar** en los pasos siguientes.
5. En la sección **Test users** (Usuarios de prueba):
   - Haz clic en **+ Add Users**.
   - Escribe tu propio correo de Gmail y haz clic en **Guardar**. *(Paso crucial para evitar el error access_denied 403)*.

#### 2.5 Descargar `client_secrets.json`
1. Ve a **APIs y servicios** → **Credenciales**.
2. Haz clic en **+ Crear credenciales** → **ID de cliente de OAuth 2.0**.
3. En Tipo de aplicación, selecciona **Aplicación de escritorio** (Desktop app).
4. Asigna cualquier nombre (ej. `agente-soporte`) y haz clic en **Crear**.
5. En la ventana emergente, haz clic en **Descargar JSON**.
6. Renombra el archivo descargado exactamente a:
   ```text
   client_secrets.json
   ```
7. Muévelo a esta carpeta del proyecto junto a `agente_soporte.py`.

---

### **FASE 3: Obtener la API Key de Gemini y Configurar `.env`**

1. Ingresa a [aistudio.google.com/app/api-keys](https://aistudio.google.com/app/api-keys).
2. Haz clic en **"Crear clave de API"**.
3. Selecciona tu proyecto `Agente de Soporte` o crea una clave rápida.
4. Copia la clave generada (tendrá un formato similar a `AIzaSy...`).
5. Abre el archivo **`.env`** en la raíz del proyecto y reemplaza el marcador con tu clave real:
   ```env
   GEMINI_API_KEY=AIzaSy...
   ```
   *(El script carga automáticamente los valores desde `.env` usando `python-dotenv`).*

---

### **FASE 4: El Código del Agente (`agente_soporte.py`)**

El código ya está completamente implementado y estructurado en [agente_soporte.py](file:///c:/Users/wilme/OneDrive/Desktop/8vo/des%20de%20ag%20int/Practica%201%20u2/agente_soporte.py):
- **`conectar_sheets()`**: Maneja el handshake OAuth 2.0 con `gspread`.
- **`analizar_con_gemini(comentario)`**: Invoca a `gemini-2.5-flash` con instrucciones del sistema estrictas en JSON.
- **`ejecutar_agente()`**: Lee la hoja, filtra filas con columna F vacía, consulta a Gemini y actualiza las columnas D, E y F.
- **Punto de Entrada**: Valida archivos, corre una primera revisión y agenda ejecuciones automáticas cada 15 minutos.

---

### **FASE 5: Ejecución y Pruebas**

#### 5.1 Ejecución
En la terminal de PowerShell, ejecuta:
```powershell
python agente_soporte.py
```

> **Nota:** La primera vez que se ejecute, se abrirá automáticamente tu navegador web para que inicies sesión con tu cuenta de Google y otorgues permisos a la aplicación. Se creará automáticamente el archivo `authorized_user.json` y no volverá a pedir autenticación.

#### 5.2 Casos de Prueba Sugeridos en el PDF
Envía desde tu Google Form los siguientes casos para verificar la respuesta del agente:

| Nombre | Comentario de prueba | Clasificación esperada | Sentimiento esperado |
|:---|:---|:---:|:---:|
| **Ana** | *No entiendo cómo funciona la nueva app, el botón de ayuda no sirve.* | `Soporte Técnico` | `Negativo` |
| **Carlos** | *Me atendió un vendedor llamado Juan y fue increíble, ¡resolvió todo! 10/10.* | `Ventas` | `Positivo` |
| **María** | *Mi paquete lleva 2 semanas sin llegar y nadie me da información.* | `Logística` | `Negativo` |

---

## 🔍 Solución de Errores Comunes

| Error en consola | Causa probable | Solución |
|:---|:---|:---|
| `FileNotFoundError: client_secrets.json` | El archivo no está en la carpeta del script. | Colocar `client_secrets.json` en la misma carpeta que `agente_soporte.py`. |
| `Error 403: access_denied` | Tu correo no está agregado como usuario de prueba. | En Google Cloud Console → *OAuth consent screen* → *Test users*, agrega tu correo. |
| `SpreadsheetNotFound` | El nombre de la hoja no coincide. | Verifica que la hoja se llame exactamente `Respuestas de Quejas (Base de Datos)`. |
| `API key not valid (Gemini)` | Clave mal copiada o con espacios. | Copia nuevamente tu clave desde Google AI Studio. |
