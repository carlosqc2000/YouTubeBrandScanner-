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

# # 📌 Endpoint para recibir y procesar mensajes de WhatsApp
# @app.post("/webhook")
# async def webhook(request: Request):
#     try:
#         incoming_data = await request.json()
        
#         # 📌 Extraer mensaje de WhatsApp
#         for msg in incoming_data.get("messages", []):
#             user_message = msg.get("text", {}).get("body", "")
#             sender_id = msg.get("from", "")

#             # 📌 Consultar MongoDB si la marca existe en la base de datos
#             videos = await retrieve_sponsored_videos(user_message)

#             # 📌 Si no hay datos en MongoDB, preguntar a OpenAI
#             if not videos:
#                 response_message = f"Lo siento, no encontré datos en la base de datos. Intentando con OpenAI..."
#                 ai_response = await generate_response(user_message, context="No hay datos en la base de datos.")
#             else:
#                 response_message = f"📌 Encontré {len(videos)} videos con esa marca."
#                 ai_response = await generate_response(user_message, context=str(videos))

#             # 📌 Responder con OpenAI o MongoDB
#             final_response = ai_response if ai_response else response_message
#             return {"message": final_response}

#     except Exception as e:
#         print(f"❌ Error en webhook: {e}")
#         return {"error": "Error procesando el mensaje"}

# # 📌 Endpoint para consultar marcas patrocinadas por un creador
# @app.get("/creador/{creator_name}")
# async def get_creator_sponsorships(creator_name: str):
#     try:
#         brands = await retrieve_brands_by_creator(creator_name)
#         if brands:
#             return {"creator": creator_name, "sponsored_brands": brands}
#         else:
#             return {"message": "No se encontraron patrocinadores para este creador."}
#     except Exception as e:
#         print(f"❌ Error en la consulta: {e}")
#         return {"error": "Error procesando la solicitud"}

# 📌 Ejecutar el servidor si el script es ejecutado directamente
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000)
