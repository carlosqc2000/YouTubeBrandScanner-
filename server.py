from fastapi import FastAPI, Request
import uvicorn
import os
from dotenv import load_dotenv
from youtube.youtube_api import get_channel_id_and_name, get_latest_non_short_videos, get_video_description
from artificial_intelligence.detect_sponsors import detect_sponsors_openai, generate_response
from database.mongodb import save_to_mongodb

# Cargar variables de entorno
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

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
    
    latest_videos = get_latest_non_short_videos(GOOGLE_API_KEY, channel_id, max_results=20)
    
    if not latest_videos:
        return {"message": f"No se encontraron videos recientes de más de 120s en {channel_name}."}
    
    processed_videos = []
    for video in latest_videos:
        description = get_video_description(GOOGLE_API_KEY, video["videoId"])
        
        sponsors = detect_sponsors_openai(description) if description else []

        await save_to_mongodb(
            video_id=video["videoId"],
            channel_name=channel_name,
            channel_id=channel_id,
            published_at=video["publishTime"],
            sponsors=sponsors,
            title=video["title"]
            )
        processed_videos.append({
            "video_id": video["videoId"],
            "title": video["title"],
            "published_at": video["publishTime"],
            "sponsors": sponsors
        })
    
    return {"message": "✅ Procesamiento completado", "channel": channel_name, "videos": processed_videos}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
