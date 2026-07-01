from google import genai
from google.genai import types
from django.conf import settings
import PIL.Image
import json

def diagnosticar_planta(imagen_path):
    # Lista de modelos a intentar en orden de preferencia (todos con capas gratuitas generosas)
    # Si el primero falla por cuota o región, intentará con el siguiente.
    modelos_disponibles = [
        "gemini-2.5-flash",  # El modelo más actual, rápido y con mejor cobertura
        "gemini-1.5-flash",  # El modelo de respaldo clásico ultra-estable
    ]
    
    ultimo_error = ""

    for model_name in modelos_disponibles:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            imagen = PIL.Image.open(imagen_path)

            prompt = """
            Eres un ingeniero agrónomo experto en enfermedades de cultivos de tomate.
            Analiza esta imagen y determina si muestra una planta de tomate enferma.

            Si NO es una planta de tomate, debes responder con esta estructura:
            {"es_valida": false, "mensaje": "La imagen no corresponde a una planta de tomate."}

            Si ES una planta de tomate, debes responder con esta estructura:
            {
                "es_valida": true,
                "enfermedad": "nombre de la enfermedad",
                "severidad": "leve" o "moderado" o "grave",
                "confianza": número entre 0.0 y 1.0,
                "sintomas": "descripción de los síntomas visibles",
                "tratamiento": "tratamiento recomendado detallado"
            }
            """

            # Forzamos a la API a responder estrictamente en formato JSON
            response = client.models.generate_content(
                model=model_name,
                contents=[prompt, imagen],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )

            # Si la petición fue exitosa, procesamos el JSON
            resultado = json.loads(response.text)
            return resultado

        except json.JSONDecodeError:
            # Si el modelo respondió pero no pudimos parsear el JSON
            return {
                "es_valida": True,
                "enfermedad": "No determinada",
                "severidad": "leve",
                "confianza": 0.3,
                "sintomas": "No se pudo estructurar el diagnóstico correctamente.",
                "tratamiento": "Consulte con el ingeniero agrónomo."
            }
        except Exception as e:
            # Si da un error de API (como el 429 de cuota), guardamos el error e intentamos el siguiente modelo
            ultimo_error = str(e)
            continue  # Salta al siguiente modelo en el bucle

    # Si salimos del bucle es porque todos los modelos fallaron
    return {
        "error": True,
        "mensaje": f"No se pudo conectar con el servicio de IA tras probar varios modelos. Último error: {ultimo_error}"
    }