from fastapi import FastAPI, Request
import uvicorn
import os
import requests
from dotenv import load_dotenv
from youtube.youtube_api import get_channel_id_and_name, get_latest_non_short_videos, get_video_description
from artificial_intelligence.detect_sponsors import ask_chatgpt, detect_sponsors_openai, generate_openai_embedding, generate_openai_response, is_relevant_question
from database.mongodb import find_similar_videos, save_to_mongodb, collection  
from pydantic import BaseModel

# Cargar variables de entorno
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # Token para verificar el webhook

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "🚀 FastAPI está funcionando correctamente!"}

@app.get("/procesar/{youtube_handle}")
async def process_youtube_channel(youtube_handle: str):
    """Obtiene videos recientes de un canal, detecta patrocinadores y guarda los datos en MongoDB."""

    channel_id, channel_name = get_channel_id_and_name(GOOGLE_API_KEY, youtube_handle)
    if not channel_id:
        return {"error": "No se encontró el canal. Verifica el nombre."}
    
    latest_videos = get_latest_non_short_videos(GOOGLE_API_KEY, channel_id, max_results=50)
    
    if not latest_videos:
        return {"message": f"No se encontraron videos recientes de más de 120s en {channel_name}."}
    
    processed_videos = []
    for video in latest_videos:
        video_id = video["videoId"]

        # 🔹 Verificar si el video ya existe en MongoDB antes de usar IA
        existing_video = await collection.find_one({"video_id": video_id})
        if existing_video:
            print(f"⚠️ El video {video_id} ya existe en MongoDB. Saltando IA...")
            continue  # Saltar predicción y pasar al siguiente video

        # 🔥 Ahora hacemos la predicción solo si el video no estaba en MongoDB
        description = get_video_description(GOOGLE_API_KEY, video_id)
        sponsors = detect_sponsors_openai(description) if description else []
        text_to_embed = f"""
        Canal: {channel_name}
        Título: {video["title"]}
        Patrocinios: {', '.join(sponsors) if sponsors else 'None'}
        """
        embedding = generate_openai_embedding(text_to_embed)

        # Guardar en MongoDB ahora que tenemos la predicción
        await save_to_mongodb(
            video_id=video_id,
            channel_name=channel_name,
            channel_id=channel_id,
            published_at=video["publishTime"],
            sponsors=sponsors,
            title=video["title"],
            description=description,
            embedding=embedding,
            collection=collection
        )

        processed_videos.append({
            "video_id": video_id,
            "title": video["title"],
            "published_at": video["publishTime"],
            "sponsors": sponsors
        })
    
    return {"message": "✅ Procesamiento completado", "channel": channel_name, "videos": processed_videos}

class ChatMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat_simulation(user_input: ChatMessage):    
    user_query = user_input.message
    similar_videos = await find_similar_videos(user_query)  # 🔍 Buscar videos similares
    
    if similar_videos is None:
        return {"response": "No encontré información relevante para tu consulta. ¿Puedes reformular tu pregunta?"}
    
    openai_response = generate_openai_response(user_query, similar_videos)  
    
    return {"response": openai_response}

### 🔹 WHATSAPP WEBHOOK 🔹 ###

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Verifica el webhook con Meta"""
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge", 0))
    return {"error": "Verificación fallida"}

@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    """Recibe mensajes de WhatsApp y responde automáticamente con IA"""
    data = await request.json()

    if "entry" in data:
        for entry in data["entry"]:
            for change in entry["changes"]:
                if "messages" in change["value"]:
                    for message in change["value"]["messages"]:
                        sender_id = message["from"]
                        message_text = message.get("text", {}).get("body", "")

                        print(f"📩 Mensaje recibido: {message_text}")

                        # Verificar si la pregunta es relevante con embeddings
                        is_relevant = is_relevant_question(message_text)
                        print(f"🔍 Es relevante? {is_relevant}")  # 📌 Depuración

                        if is_relevant:
                            print("✅ Buscando en la base de datos...")
                            similar_videos = await find_similar_videos(message_text) or []
                            response_text = generate_openai_response(message_text, similar_videos)
                        else:
                            print("🤖 Usando ChatGPT para responder...")
                            response_text = ask_chatgpt(message_text)

                        print(f"📤 Enviando respuesta: {response_text}")  # 📌 Depuración Final
                        send_whatsapp_message(sender_id, response_text)

    return {"status": "ok"}

def send_whatsapp_message(recipient_id, message):
    """Envía un mensaje a WhatsApp y muestra la respuesta de la API."""
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "text": {"body": message}
    }

    response = requests.post(url, headers=headers, json=payload)
    
    print(f"📤 Enviando mensaje a {recipient_id}: {message}")  # Verificar que el mensaje se genera
    print(f"🔍 Respuesta de WhatsApp API: {response.status_code} - {response.json()}")  # Verificar la API
    
    return response.json()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
