import openai
import json
import os
from dotenv import load_dotenv
import re

# Cargar API Key de OpenAI desde .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Verificar que la API Key está configurada
if not OPENAI_API_KEY:
    print("❌ ERROR: La clave OPENAI_API_KEY no está configurada en .env")
else:
    print(f"✅ OPENAI_API_KEY cargada correctamente: {OPENAI_API_KEY[:5]}*****")

def detect_sponsors_openai(description):
    """Detecta marcas patrocinadoras en una descripción de video."""
    
    if not description:
        print("🔍 No description provided.")
        return []

    prompt = f"""
        Extract and return a list of **brand names, product names, company mentions, and sponsorship-related entities** from the following YouTube description.  
        Ensure the output is always a **valid JSON array** (e.g., ["Nike", "Apple"]).  

        **Exclusions:**  
        - **DO NOT** include personal names, content creators, or geographic locations (e.g., Spain, Dubai).  
        - **DO NOT** include **social media platforms** (e.g., Instagram, Twitter, Discord, Twitch, YouTube).  

        **Inclusions:**  
        - Include all brands associated with **discount codes, affiliate links, or sponsorship mentions**.  
        - Recognize brands **even if they are indirectly referenced**.  

        ### Example:
        **Description:** "Consigue un **descuento exclusivo** en tu seguro de viaje con **Chapka Direct** usando este enlace: https://www.chapkadirect.es"
        **Expected Output:** ["Chapka Direct"]
        
        ---
        **Description:** {description}
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        raw_output = response.choices[0].message.content.strip()
        print(f"🔍 OpenAI Raw Output BEFORE JSON Parsing: {raw_output}")  # Depuración

        # Limpiar la salida de OpenAI si hay texto extra
        cleaned_output = re.sub(r'^\*\*Output:\*\*\s*', '', raw_output)

        try:
            detected_brands = json.loads(cleaned_output)
            return detected_brands if isinstance(detected_brands, list) else []
        
        except json.JSONDecodeError:
            print("❌ JSON Decode Error: OpenAI did not return a valid JSON array.")
            return []
    
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return []

async def generate_response(user_query, context):
    """Genera una respuesta para el chatbot utilizando OpenAI."""
    
    prompt = f"""
    Usuario preguntó: {user_query}
    Información disponible:
    {context}
    
    Genera una respuesta informativa basada en estos datos.
    """

    try:
        response = await openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return "Hubo un error al generar la respuesta. Inténtalo nuevamente más tarde."
