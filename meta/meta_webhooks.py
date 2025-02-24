from fastapi import APIRouter, Request
import os
import openai
from pymongo import MongoClient
import requests

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Configuración de WhatsApp API
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializar clientes
router = APIRouter()
client = MongoClient(MONGO_URI)
db = client["youtube_sponsors"]
collection = db["sponsored_videos"]

openai.api_key = OPENAI_API_KEY

@router.post("/webhook")
async def whatsapp_webhook(request: Request):
    """ Maneja mensajes entrantes de WhatsApp a través de Webhooks de Meta """
    try:
        data = await request.json()
        messages = data.get("entry", [])[0].get("changes", [])[0].get("value", {}).get("messages", [])

        if not messages:
            return {"message": "No hay mensajes"}

        for message in messages:
            sender_id = message["from"]
            text = message["text"]["body"]

            # Procesar mensaje y obtener respuesta
            response_text = await process_message(text)

            # Enviar respuesta a WhatsApp
            send_whatsapp_message(sender_id, response_text)

        return {"message": "Procesado correctamente"}
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

async def process_message(text):
    """ Busca información en MongoDB y usa OpenAI para generar respuesta """
    
    # 1️⃣ Buscar información en MongoDB
    query = {"$or": [
        {"title": {"$regex": text, "$options": "i"}},
        {"sponsors.brand_name": {"$regex": text, "$options": "i"}}
    ]}
    results = list(collection.find(query))

    if not results:
        return "No encontré información relevante en la base de datos."

    # 2️⃣ Construir contexto con datos de MongoDB
    context = "\n".join([f"{r['title']} fue patrocinado por {', '.join([s['brand_name'] for s in r['sponsors']])}" for r in results])

    # 3️⃣ Generar respuesta con OpenAI
    prompt = f"""Tienes acceso a información sobre patrocinadores de YouTube. 
    Un usuario te pregunta sobre: {text}. 
    Usa la siguiente información para responder:
    
    {context}
    
    Si no tienes suficiente información, responde de forma natural y profesional."""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    return response["choices"][0]["message"]["content"]

