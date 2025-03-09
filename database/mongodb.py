from artificial_intelligence.detect_sponsors import generate_openai_embedding
import motor.motor_asyncio # type: ignore
import datetime
from scipy.spatial.distance import cosine
import motor.motor_asyncio
from dateutil import parser
from datetime import datetime, timedelta
import re
from pymongo.errors import DuplicateKeyError

# Conectar a MongoDB de forma asíncrona
MONGO_URI = "mongodb://localhost:27017/"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client["youtube_sponsors"]
collection = db["sponsored_videos"]

async def save_to_mongodb(video_id, channel_name, channel_id, published_at, sponsors, title, description, embedding, collection):
    """Guarda los datos en MongoDB asegurando que cada video sea único usando video_id, sin actualizar si ya existe."""

    video_id = str(video_id).strip()

    data = {
        "video_id": video_id,
        "title": title,
        "channel_name": channel_name,
        "channel_id": channel_id,
        "published_at": published_at,
        "sponsors": [{"brand_name": sponsor} for sponsor in sponsors],
        "description": description,
        "embedding": embedding
    }

    # 🔹 Intentamos actualizar solo si no existe
    result = await collection.update_one(
        {"video_id": video_id},  # Condición de búsqueda
        {"$setOnInsert": data},  # Solo inserta si no existe
        upsert=True  # Permite la inserción solo si no hay coincidencias
    )

    if result.matched_count == 0:
        print(f"✅ Video {video_id} guardado en MongoDB.")
    else:
        print(f"⚠️ El video {video_id} ya existe en MongoDB. Saltando...")

async def channel_exists(channel_name):
    """Verifica si un canal existe en la base de datos."""
    channel = await collection.find_one({"channel_name": channel_name})
    return channel is not None  # Retorna True si el canal existe, False si no

def extract_date_range(user_query):
    """Extrae un rango de fechas basado en la consulta del usuario."""
    now = datetime.utcnow()

    # Detectar "últimos X meses"
    match = re.search(r"últimos (\d+) meses", user_query.lower())
    if match:
        months = int(match.group(1))
        start_date = now - timedelta(days=months * 30)  # Aproximado
        return start_date.isoformat(), now.isoformat()

    # Detectar meses específicos ("marzo", "enero", etc.)
    months_dict = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    for month, num in months_dict.items():
        if month in user_query.lower():
            year = now.year  # Suponemos el año actual
            start_date = datetime(year, num, 1)
            end_date = datetime(year, num + 1, 1) - timedelta(days=1)  # Último día del mes
            return start_date.isoformat(), end_date.isoformat()

    # Detectar "primer video"
    if "primer video" in user_query.lower():
        return "first", "first"  # Indicador especial para buscar el más antiguo

    return None, None  # No se detectó fecha

async def find_similar_videos(user_query, top_n=3):
    """Encuentra los videos más similares a la consulta del usuario basándose únicamente en similitud de coseno."""

    query_embedding = generate_openai_embedding(user_query)  

    # Definir un umbral de similitud mínima para evitar respuestas incorrectas
    THRESHOLD = 0.35  # 🔥 Ajusta este valor si es necesario

    # Obtener todos los videos en la base de datos
    videos = await collection.find({}, {
        "video_id": 1, "title": 1, "embedding": 1, "sponsors": 1, "description": 1, 
        "published_at": 1, "channel_name": 1, "_id": 0
    }).to_list(length=100)

    # Comparar embeddings con la consulta
    similarities = []
    for video in videos:
        if "embedding" in video and video["embedding"]:
            similarity = 1 - cosine(query_embedding, video["embedding"])
            similarities.append((video, similarity))

    # Ordenar por similitud de coseno (de mayor a menor)
    similarities.sort(key=lambda x: x[1], reverse=True)

    # 🔍 Imprimir las similitudes para depuración
    print("\n📊 Similitudes de coseno calculadas:")
    for video, sim in similarities:
        print(f"🎥 Video: {video['title']} - 🔥 Similitud: {sim:.3f}")

    # Si la mejor similitud es menor que el umbral, devolver None
    if similarities and similarities[0][1] < THRESHOLD:
        print("⚠️ Ninguna coincidencia relevante encontrada, devolviendo None.")
        return None

    return [video[0] for video in similarities[:top_n]] if similarities else None

