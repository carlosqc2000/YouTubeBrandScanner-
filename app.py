import gradio as gr
from youtube_scraper import get_channel_id_and_name, get_latest_normal_videos, detect_sponsors_openai
import os
from dotenv import load_dotenv

# Cargar claves API
env_loaded = load_dotenv()
API_KEY = os.getenv("GOOGLE_API")

def search_brands(youtube_handle):
    """ Busca los patrocinios en los videos recientes de un canal de YouTube."""
    channel_id, channel_name = get_channel_id_and_name(API_KEY, youtube_handle)
    if not channel_id:
        return "Error: No se encontró el canal. Verifica el nombre."
    
    videos = get_latest_normal_videos(API_KEY, channel_id, max_results=5)
    
    if not videos:
        return f"No se encontraron videos recientes de más de 120s en {channel_name}."
    
    results = []
    for video in videos:
        sponsors = detect_sponsors_openai(video['description'])
        video_info = f"🎥 {video['title']}\n📅 {video['publishTime']}\n🔗 https://www.youtube.com/watch?v={video['videoId']}\nPatrocinios detectados: {', '.join(sponsors) if sponsors else 'Ninguno'}\n"
        results.append(video_info)
    
    return "\n\n".join(results)

# Crear interfaz
iface = gr.Interface(
    fn=search_brands,
    inputs=gr.Textbox(label="Ingrese el handle de YouTube (ej. @ItzNandez)"),
    outputs=gr.Textbox(label="Resultados de la búsqueda"),
    title="🔎 YouTube Brands Search",
    description="Busca marcas patrocinadoras en los videos recientes de un canal de YouTube.",
)

# Ejecutar la aplicación
if __name__ == "__main__":
    iface.launch()
