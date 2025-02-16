import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configurar la API Key correctamente
if not OPENAI_API_KEY:
    print("❌ ERROR: La clave OPENAI_API_KEY no está configurada en .env")
else:
    print(f"✅ OPENAI_API_KEY cargada correctamente: {OPENAI_API_KEY[:5]}*****")

client = openai.Client(api_key=OPENAI_API_KEY)

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

        ### Example 1:
        **Description:** "Consigue un **descuento exclusivo** en tu seguro de viaje con **Chapka Direct** usando este enlace: https://www.chapkadirect.es"
        **Expected Output:** ["Chapka Direct"]

        ### Example 2:
        **Description:** "Patrocinado por **Flexispot**, la mejor marca de escritorios ergonómicos. Usa mi código 'Nandez' en https://bit.ly/3UQ6cwD"
        **Expected Output:** ["Flexispot"]

        ### Example 3:
        **Description:** "Gracias a **Tesla** por prestarme el coche para grabar este vídeo."
        **Expected Output:** ["Tesla"]

        ### Example 4 (Avoid Locations):
        **Description:** "Hoy visitamos el **Dubai Atlantis Aquadventure**, un parque acuático en Dubai. La pasamos genial en España."
        **Expected Output:** []

        ### Example 5 (Ensure Discount Codes are Recognized):
        **Description:** "Descuento en tu ESIM con **SAILY**: https://saily.com/nandez Código 'Nandez'"
        **Expected Output:** ["SAILY"]
        
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
        
        try:
            detected_brands = json.loads(raw_output)
            
            if not isinstance(detected_brands, list):
                print("❌ OpenAI did not return a valid list. Forcing reformat...")
                detected_brands = [raw_output]  # Si la respuesta no es JSON, la tratamos como texto
            
            return detected_brands if "No brands detected" not in detected_brands else []
        
        except json.JSONDecodeError:
            print("❌ JSON Decode Error: OpenAI did not return a valid JSON array.")
            return []
    
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return []
