import motor.motor_asyncio # type: ignore
import datetime

# Conectar a MongoDB de forma asíncrona
MONGO_URI = "mongodb://localhost:27017/"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["youtube_sponsors"]
collection = db["sponsored_videos"]

async def save_to_mongodb(video_id, channel_name, channel_id, published_at, sponsors, title):
    """Guarda los datos en MongoDB de forma asíncrona, incluyendo el título del video."""
    data = {
        "video_id": video_id,
        "title": title,  # ➡️ Guardamos el título del video
        "channel_name": channel_name,
        "channel_id": channel_id,
        "published_at": published_at,
        "sponsors": [
            {"brand_name": sponsor, "detected_at": datetime.datetime.utcnow().isoformat()}
            for sponsor in sponsors
        ]
    }
    await collection.insert_one(data)  # ✅ Ahora es asíncrono
    print(f"✅ Datos guardados en MongoDB para el video {video_id} - {title}")

