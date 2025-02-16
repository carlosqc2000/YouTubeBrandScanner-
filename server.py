from flask import Flask, request
import openai
import pymongo
import os
from dotenv import load_dotenv

# Cargar credenciales desde .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGO_URI = "mongodb://localhost:27017/"

# Conectar a MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client["youtube_sponsors"]
collection = db["sponsored_videos"]

# Inicializar Flask
app = Flask(__name__)

@app.route("/")
def home():
    """Página de inicio para comprobar que el servidor está funcionando."""
    return "✅ ¡Servidor Flask funcionando correctamente!"

def retrieve_data_from_mongodb(query):
    """Busca información en MongoDB según la consulta del usuario."""
    search_result = collection.find(
        {"$or": [
            {"channel_name": {"$regex": query, "$options": "i"}},
            {"sponsors.brand_name": {"$regex": query, "$options": "i"}}
        ]},
        {"_id": 0}
    )
    return list(search_result)

def generate_response(user_query):
    """Genera una respuesta usando OpenAI y datos de MongoDB."""
    related_data = retrieve_data_from_mongodb(user_query)

    context = "\n".join([
        f"Canal: {doc['channel_name']}, Video: {doc['video_id']}, Patrocinios: {', '.join([s['brand_name'] for s in doc['sponsors']])}"
        for doc in related_data
    ])

    if not context:
        context = "No encontré información en nuestra base de datos."

    prompt = f"""
    Usuario preguntó: {user_query}
    Información disponible:
    {context}
    
    Genera una respuesta informativa basada en estos datos.
    """

    client = openai.Client(api_key=OPENAI_API_KEY)  
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    return response.choices[0].message.content 

@app.route("/webhook", methods=["POST"])
def webhook():
    """Simula la recepción de un mensaje y devuelve la respuesta."""
    incoming_message = request.get_json()

    if "messages" in incoming_message:
        for msg in incoming_message["messages"]:
            user_message = msg["text"]["body"]
            sender_id = msg["from"]

            # Generar respuesta con GPT y MongoDB
            response_message = generate_response(user_message)

            return {"message": response_message}, 200

    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
