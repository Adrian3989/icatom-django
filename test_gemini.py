import os
from dotenv import load_dotenv
from google import genai

def probar_conexion():
    # 1. Cargar las variables de entorno del archivo .env
    # Esto busca un archivo llamado '.env' en el mismo directorio donde se ejecuta el script
    load_dotenv()

    # 2. Obtener la API Key
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("❌ Error: No se encontró la variable GEMINI_API_KEY en tu archivo .env.")
        print("Asegúrate de tener un archivo llamado '.env' en la raíz con la línea:")
        print("GEMINI_API_KEY=tu_clave_real_sin_comillas")
        return

    # Imprimir los primeros y últimos caracteres para comprobar que se lee limpia
    # sin comillas accidentales
    print(f"🔑 API Key detectada: {api_key[:6]}...{api_key[-4:]}")
    if api_key.startswith('"') or api_key.startswith("'"):
        print("⚠️ Alerta: Tu API Key en el archivo .env empieza con comillas. Por favor, retíralas.")

    try:
        # 3. Inicializar el cliente oficial de Gemini
        print("🔌 Conectando con el cliente de Gemini...")
        client = genai.Client(api_key=api_key)

        # 4. Realizar una petición básica de prueba
        print("📡 Enviando petición de prueba a Gemini...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hola, responde únicamente con la palabra 'Conexión Exitosa con .env' si recibes esto correctamente."
        )

        print("\n================ RESULTADO ================")
        print(f"Respuesta de la IA: {response.text.strip()}")
        print("===========================================")
        print("🎉 ¡Todo configurado correctamente!")

    except Exception as e:
        print("\n❌ Error al intentar conectar con la API de Gemini:")
        print(f"Detalle del error: {str(e)}")

if __name__ == "__main__":
    probar_conexion()