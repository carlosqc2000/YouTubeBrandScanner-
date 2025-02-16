from pymongo import MongoClient
import datetime

# Conectar a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["youtube_sponsors"]
collection = db["sponsored_videos"]

def save_to_mongodb(video_id, channel_name, channel_id, published_at, sponsors, title):
    """Guarda los datos en MongoDB, incluyendo el título del video"""
    data = {
        "video_id": video_id,
        "title": title,  # ➡️ Ahora almacenamos el título
        "channel_name": channel_name,
        "channel_id": channel_id,
        "published_at": published_at,
        "sponsors": [
            {"brand_name": sponsor, "detected_at": datetime.datetime.utcnow().isoformat()}
            for sponsor in sponsors
        ]
    }
    collection.insert_one(data)
    print(f"✅ Datos guardados en MongoDB para el video {video_id} - {title}")

def get_all_sponsored_videos():
    """Devuelve todos los videos almacenados en MongoDB"""
    return list(collection.find({}, {"_id": 0}))

