"""
Práctica: Mi Primer Agente de IA
Construcción de un Agente de Soporte con Python y Gemini

Este script implementa el flujo completo descrito en la práctica:
1. Conexión con Google Sheets usando OAuth 2.0 (gspread).
2. Lectura y filtrado de quejas registradas mediante Google Forms.
3. Análisis inteligente con Gemini (clasificación por departamento y detección de sentimiento).
4. Actualización automática de la hoja de cálculo y marcado de fila ('SI').
5. Programación periódica recurrente usando la librería schedule.
"""

# ==========================================
# Paso 4.2: Sección de Importaciones
# ==========================================
import json
import os
import sys
import time
import schedule
import gspread
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Cargar automáticamente variables de entorno desde el archivo .env
load_dotenv()

# ==========================================
# Paso 4.3: Sección de Configuración
# ==========================================
# Archivo de credenciales OAuth 2.0 descargado de Google Cloud Console
ARCHIVO_CREDENCIALES = os.getenv("ARCHIVO_CREDENCIALES", "client_secrets.json")

# Nombre exacto de la hoja de cálculo vinculada al formulario
NOMBRE_HOJA = os.getenv("NOMBRE_HOJA", "Respuestas de Quejas (Base de Datos)")

# API Key de Gemini obtenida en Google AI Studio (cargada desde .env o variable de entorno)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "TU_API_KEY_AQUI")

# Intervalo en minutos para la ejecución periódica del agente (por defecto 15)
INTERVALO_MINUTOS = int(os.getenv("INTERVALO_MINUTOS", "15"))

# Índices de columnas en Google Sheets (base 1):
# Columna D: Clasificación IA
COL_CLASIFICACION = 4
# Columna E: Sentimiento IA
COL_SENTIMIENTO = 5
# Columna F: Agente Ejecutado
COL_EJECUTADO = 6

# Modelo de Gemini a utilizar (gemini-3.5-flash recomendado)
MODELO_GEMINI = os.getenv("MODELO_GEMINI", "gemini-3.5-flash")

# Variable global para el cliente de Gemini
cliente_gemini = None


# ==========================================
# Paso 4.4: Función: Conectar con Google Sheets
# ==========================================
def conectar_sheets():
    """
    Autentica el script mediante OAuth 2.0 con gspread, abre la hoja de cálculo
    indicada en NOMBRE_HOJA y retorna el objeto de la primera hoja (sheet1).
    """
    try:
        print("[Conexión] Autenticando con Google Sheets vía OAuth 2.0...")
        # gspread utiliza client_secrets.json y guarda el token generado en authorized_user.json
        gc = gspread.oauth(
            credentials_filename=ARCHIVO_CREDENCIALES,
            authorized_user_filename="authorized_user.json"
        )
        print(f"[Conexión] Abriendo hoja de cálculo: '{NOMBRE_HOJA}'...")
        spreadsheet = gc.open(NOMBRE_HOJA)
        hoja = spreadsheet.sheet1
        return hoja
    except Exception as e:
        print(f"[Error de Conexión] No se pudo conectar a Google Sheets: {e}")
        return None


# ==========================================
# Paso 4.5: Función: Analizar con Gemini
# ==========================================
def analizar_con_gemini(comentario):
    """
    Envía el comentario del cliente a la API de Gemini para:
    1. Clasificarlo en: 'Ventas', 'Soporte Técnico' o 'Logística'.
    2. Detectar el sentimiento: 'Positivo', 'Negativo' o 'Neutro'.
    Retorna un diccionario Python con las claves 'clasificacion' y 'sentimiento'.
    """
    instruccion_sistema = (
        "Eres un analista de soporte al cliente experto. Tu única tarea es clasificar el comentario "
        "recibido y detectar su sentimiento. Debes responder EXCLUSIVAMENTE con un objeto JSON válido, "
        "sin explicaciones adicionales, sin texto antes ni después, y sin bloques de formato innecesarios. "
        "El JSON debe tener exactamente esta estructura:\n"
        "{\n"
        '  "clasificacion": "Ventas" | "Soporte Técnico" | "Logística",\n'
        '  "sentimiento": "Positivo" | "Negativo" | "Neutro"\n'
        "}"
    )

    instruccion_usuario = (
        f"Analiza el siguiente comentario o queja de un cliente:\n"
        f"\"{comentario}\"\n\n"
        f"Clasifícalo en una de estas categorías: 'Ventas', 'Soporte Técnico' o 'Logística'.\n"
        f"Determina el sentimiento: 'Positivo', 'Negativo' o 'Neutro'.\n"
        f"Recuerda responder únicamente con el JSON solicitado."
    )

    # Configuración de generación solicitando JSON estricto
    config = types.GenerateContentConfig(
        system_instruction=instruccion_sistema,
        response_mime_type="application/json",
        temperature=0.2
    )

    # Llamada al modelo de Gemini
    respuesta = cliente_gemini.models.generate_content(
        model=MODELO_GEMINI,
        contents=instruccion_usuario,
        config=config
    )

    texto_respuesta = respuesta.text.strip() if respuesta.text else ""

    # Limpiar bloques markdown si vinieran incluidos por formato
    if texto_respuesta.startswith("```json"):
        texto_respuesta = texto_respuesta[7:]
    elif texto_respuesta.startswith("```"):
        texto_respuesta = texto_respuesta[3:]
    if texto_respuesta.endswith("```"):
        texto_respuesta = texto_respuesta[:-3]
    texto_respuesta = texto_respuesta.strip()

    # Parsear y retornar como diccionario nativo de Python
    resultado = json.loads(texto_respuesta)
    return resultado


# ==========================================
# Paso 4.6: Función: Agente Principal
# ==========================================
def ejecutar_agente():
    """
    Orquesta el ciclo completo del agente:
    - Conecta con Google Sheets.
    - Lee todas las filas registradas.
    - Filtra las filas pendientes (columna F sin 'SI').
    - Analiza cada comentario con Gemini.
    - Escribe los resultados en las columnas D, E y F de Sheets.
    """
    print("\n" + "=" * 55)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando ciclo de revisión del Agente...")
    print("=" * 55)

    # 1. Conectar a Google Sheets
    hoja = conectar_sheets()
    if hoja is None:
        print("[Alerta] No se pudo acceder a la hoja. Se reintentará en el próximo ciclo programado.")
        return

    # 2. Leer todas las filas
    try:
        filas = hoja.get_all_values()
    except Exception as e:
        print(f"[Error] Falló la lectura de filas en la hoja: {e}")
        return

    # Si la hoja solo tiene encabezados o está vacía
    if len(filas) <= 1:
        print("[Info] No hay respuestas de clientes para procesar.")
        return

    filas_procesadas = 0

    # Omitir fila 1 (encabezados) y usar base 1 de Google Sheets (comenzando en fila 2)
    for indice_fila, fila in enumerate(filas[1:], start=2):
        # 3. Filtrar: verificar si la columna F (índice 5 en lista de Python) ya tiene 'SI'
        ya_ejecutado = len(fila) >= 6 and fila[5].strip().upper() == "SI"
        if ya_ejecutado:
            continue

        # Extraer nombre (columna B / índice 1) y comentario (columna C / índice 2)
        nombre = fila[1].strip() if len(fila) > 1 and fila[1].strip() else "Anónimo"
        comentario = fila[2].strip() if len(fila) > 2 else ""

        if not comentario:
            print(f"[Fila {indice_fila}] Comentario vacío para '{nombre}'. Omitiendo...")
            continue

        print(f"\n[Fila {indice_fila}] Nueva queja detectada:")
        print(f"  - Cliente: {nombre}")
        print(f"  - Comentario: \"{comentario}\"")

        # 4. Analizar con Gemini
        try:
            resultado = analizar_con_gemini(comentario)
            clasificacion = resultado.get("clasificacion", "No clasificado")
            sentimiento = resultado.get("sentimiento", "Neutro")

            print(f"  -> Clasificación detectada: {clasificacion}")
            print(f"  -> Sentimiento detectado: {sentimiento}")

            # 5. Escribir resultados en Google Sheets
            hoja.update_cell(indice_fila, COL_CLASIFICACION, clasificacion)
            hoja.update_cell(indice_fila, COL_SENTIMIENTO, sentimiento)
            hoja.update_cell(indice_fila, COL_EJECUTADO, "SI")

            print(f"  -> [OK] Resultados guardados exitosamente en Google Sheets.")
            filas_procesadas += 1

        except json.JSONDecodeError as err_json:
            print(f"[Error JSON en Fila {indice_fila}] Gemini no retornó un JSON válido: {err_json}")
            print("Continuando con la siguiente fila...")
        except Exception as err:
            print(f"[Error en Fila {indice_fila}] Ocurrió un error al procesar la queja: {err}")
            print("Continuando con la siguiente fila...")

    if filas_procesadas == 0:
        print("[Info] No se encontraron nuevas quejas pendientes de procesar.")
    else:
        print(f"\n[Ciclo Completado] Se procesaron {filas_procesadas} nueva(s) fila(s) con éxito.")


# ==========================================
# Paso 4.7: Punto de Entrada del Script
# ==========================================
if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("      AGENTE DE SOPORTE INTELIGENTE (Python + Gemini)")
    print("#" * 60)

    # 1. Validar la API Key de Gemini
    if not GEMINI_API_KEY or GEMINI_API_KEY == "TU_API_KEY_AQUI":
        print("\n[ERROR CRÍTICO] La variable 'GEMINI_API_KEY' aún contiene el texto de marcador.")
        print("Por favor, abre 'agente_soporte.py' y asigna tu API Key obtenida de Google AI Studio,")
        print("o establécela en tu sistema con: $env:GEMINI_API_KEY='tu_clave'")
        sys.exit(1)

    # 2. Validar que el archivo de credenciales de Google Sheets exista
    if not os.path.exists(ARCHIVO_CREDENCIALES):
        print(f"\n[ERROR CRÍTICO] No se encontró el archivo '{ARCHIVO_CREDENCIALES}' en la carpeta:")
        print(f"  {os.path.abspath(ARCHIVO_CREDENCIALES)}")
        print("Por favor, descarga el archivo JSON de Google Cloud Console (ID de cliente OAuth 2.0),")
        print(f"renómbralo exactamente como '{ARCHIVO_CREDENCIALES}' y colócalo en esta carpeta.")
        sys.exit(1)

    # 3. Inicializar el cliente global de Gemini
    try:
        cliente_gemini = genai.Client(api_key=GEMINI_API_KEY)
        print("[Gemini] Cliente de Gemini inicializado correctamente.")
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar el cliente de Gemini: {e}")
        sys.exit(1)

    # 4. Ejecutar inmediatamente la primera vez al arrancar
    print("\n[Inicio] Ejecutando primera revisión inmediata del agente...")
    ejecutar_agente()

    # 5. Programar ejecuciones automáticas periódicas con schedule
    schedule.every(INTERVALO_MINUTOS).minutes.do(ejecutar_agente)
    print(f"\n[Programador] Agente activo. Revisará la hoja automáticamente cada {INTERVALO_MINUTOS} minutos.")
    print("Presiona Ctrl+C en cualquier momento para detener el agente.\n")

    # 6. Mantener el script corriendo en bucle infinito
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n[Finalizado] Agente detenido manualmente por el usuario. ¡Hasta luego!")
