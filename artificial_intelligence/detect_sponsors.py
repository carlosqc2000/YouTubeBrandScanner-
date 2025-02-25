import openai
import json
import os
from dotenv import load_dotenv
import re
import numpy as np

# Cargar API Key de OpenAI desde .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Lista de palabras clave sobre patrocinadores y publicidad en YouTube
KEYWORDS = ["sponsor", "patrocinador", "marca", "publicidad", "anuncio", 
            "empresa", "producto", "afiliado", "descuento", "colaboración", "brand"]

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

def generate_openai_embedding(text):
    """Genera un embedding con OpenAI"""
    response = client.embeddings.create(
    input=text,
    model="text-embedding-3-small"
    )
    return response.data[0].embedding

def is_relevant_question(user_query):
    """Evalúa si una pregunta es relevante basándose en embeddings y palabras clave."""

    # Obtener embedding de la pregunta del usuario
    user_embedding = generate_openai_embedding(user_query)

    # Obtener embeddings de las palabras clave
    keyword_embeddings = [generate_openai_embedding(keyword) for keyword in KEYWORDS]

    # Calcular la similitud de coseno entre la pregunta y cada palabra clave
    similarities = [
        np.dot(user_embedding, keyword_emb) / (np.linalg.norm(user_embedding) * np.linalg.norm(keyword_emb))
        for keyword_emb in keyword_embeddings
    ]

    print(f"📊 Similitudes con palabras clave: {similarities}")

    # Si alguna similitud es mayor a 0.75, consideramos la pregunta como relevante
    return max(similarities) > 0.4

def generate_openai_response(user_query, similar_videos):
    """Genera una respuesta basada en los videos más similares encontrados."""

    # Formatear los videos para que OpenAI los entienda correctamente
    context = "\n".join([
        f"Título: {video['title']}\nCanal: {video['channel_name']}\nPatrocinadores: {', '.join([s['brand_name'] for s in video['sponsors']]) if video['sponsors'] else 'Ninguno'}"
        for video in similar_videos
    ])

    prompt = f"""
    You are an AI assistant that answers questions about sponsors in YouTube videos.

    User question: "{user_query}"

    Based on the information from the database, provide a clear and helpful response. Here are the relevant videos:

    {context}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

def ask_chatgpt(user_message):
    """Genera una respuesta con IA para temas fuera del proyecto."""
    prompt = f"""You are a helpful AI assistant. Answer the following question:

    User: {user_message}
    AI:"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content