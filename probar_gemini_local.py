"""
Script auxiliar para probar la conexión con Gemini y el análisis de quejas
sin necesidad de conectarse a Google Sheets.
Útil para verificar que tu GEMINI_API_KEY funciona correctamente.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from agente_soporte import analizar_con_gemini, GEMINI_API_KEY
from google import genai
import agente_soporte

if __name__ == "__main__":
    print("=" * 60)
    print(" PRUEBA LOCAL DE CLASIFICACIÓN CON GEMINI")
    print("=" * 60)

    # Validar API Key
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    if not api_key or api_key == "TU_API_KEY_AQUI":
        print("\n[AVISO] No has configurado tu GEMINI_API_KEY.")
        print("Edita 'agente_soporte.py' con tu clave real o pásala como variable de entorno:")
        print("  $env:GEMINI_API_KEY='tu_clave_aqui'")
        sys.exit(1)

    try:
        agente_soporte.cliente_gemini = genai.Client(api_key=api_key)
        print("[OK] Cliente de Gemini inicializado con éxito.")
    except Exception as e:
        print(f"[Error] No se pudo inicializar Gemini: {e}")
        sys.exit(1)

    # Casos de prueba de la práctica
    casos = [
        ("Ana", "No entiendo cómo funciona la nueva app, el botón de ayuda no sirve."),
        ("Carlos", "Me atendió un vendedor llamado Juan y fue increíble, ¡resolvió todo! 10/10."),
        ("María", "Mi paquete lleva 2 semanas sin llegar y nadie me da información.")
    ]

    print("\nEvaluando casos de prueba del PDF...\n")
    for nombre, comentario in casos:
        print(f"Cliente: {nombre}")
        print(f"Comentario: \"{comentario}\"")
        try:
            res = analizar_con_gemini(comentario)
            print(f"  -> Clasificación: {res.get('clasificacion')}")
            print(f"  -> Sentimiento:   {res.get('sentimiento')}")
        except Exception as err:
            print(f"  -> Error: {err}")
        print("-" * 50)
