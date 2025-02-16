import motor.motor_asyncio
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

async def get_all_sponsored_videos():
    """Devuelve todos los videos almacenados en MongoDB de forma asíncrona."""
    videos = await collection.find({}, {"_id": 0}).to_list(length=100)  # ✅ Ahora es asíncrono
    return videos

async def retrieve_data_from_mongodb(query):
    """Detecta si la consulta es sobre una marca o un canal y realiza la búsqueda en MongoDB de manera más precisa."""

    print(f"🔍 Buscando en MongoDB con la query: {query}")  # Depuración

    # 🔹 Buscar si la consulta se refiere a un YouTuber
    if "qué marcas ha patrocinado" in query.lower():
        youtuber_name = query.split("a")[-1].strip()
        print(f"🎯 Búsqueda específica por YouTuber: {youtuber_name}")

        search_result = await collection.find(
            {"channel_name": {"$regex": youtuber_name, "$options": "i"}},
            {"_id": 0, "channel_name": 1, "sponsors.brand_name": 1}
        ).to_list(length=100)

    # 🔹 Buscar si la consulta se refiere a una marca
    elif "qué videos tienen patrocinio de" in query.lower():
        brand_name = query.split("de")[-1].strip()
        print(f"🎯 Búsqueda específica por Marca: {brand_name}")

        search_result = await collection.find(
            {"sponsors": {"$elemMatch": {"brand_name": {"$regex": brand_name, "$options": "i"}}}},
            {"_id": 0}
        ).to_list(length=100)

    else:
        # 🔹 Si no se detecta canal o marca, usar búsqueda estándar
        search_result = await collection.find(
            {"$or": [
                {"sponsors": {"$elemMatch": {"brand_name": {"$regex": query, "$options": "i"}}}},
                {"channel_name": {"$regex": query, "$options": "i"}}
            ]},
            {"_id": 0}
        ).to_list(length=100)

    return search_result
