import requests
import os
from dotenv import load_dotenv
import isodate

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API")

def get_channel_id_and_name(api_key, handle):
    """Obtener el ID y nombre de un canal a partir de su handle."""
    url = f"https://www.googleapis.com/youtube/v3/channels?part=id,snippet&forHandle={handle}&key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["id"], data["items"][0]["snippet"]["title"]
    
    print("❌ No se pudo encontrar el canal:", handle)
    return None, None

def is_probable_short(video_id, api_key):
    """Determina si un video es un Short basado en su duración."""
    url = f"https://www.googleapis.com/youtube/v3/videos?key={api_key}&id={video_id}&part=contentDetails"
    response = requests.get(url)

    try:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            duration_iso = data["items"][0]["contentDetails"]["duration"]
            duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())

            if duration_seconds < 180:  # Filtrar videos de menos de 180 segundos
                return True
    except Exception as e:
        print(f"❌ Error obteniendo duración del video {video_id}: {e}")

    return False

def get_latest_non_short_videos(api_key, channel_id, max_results=10):
    """Obtener los últimos videos de un canal excluyendo Shorts."""
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet,id&order=date&type=video&maxResults={max_results * 3}"
    response = requests.get(url)

    video_list = []
    try:
        data = response.json()
        if "items" in data:
            for item in data["items"]:
                video_id = item["id"].get("videoId")
                if not video_id:
                    continue

                if is_probable_short(video_id, api_key):
                    continue  # Omitir Shorts

                video_info = {
                    "videoId": video_id,
                    "title": item["snippet"]["title"],
                    "publishTime": item["snippet"]["publishedAt"]
                }
                video_list.append(video_info)

                if len(video_list) >= max_results:
                    break
    except Exception as e:
        print(f"❌ Error obteniendo videos: {e}")

    return video_list

def get_video_description(api_key, video_id):
    """Obtener la descripción de un video."""
    url = f"https://www.googleapis.com/youtube/v3/videos?key={api_key}&id={video_id}&part=snippet"
    response = requests.get(url)

    try:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["snippet"]["description"]
    except Exception as e:
        print(f"❌ Error obteniendo la descripción del video: {e}")

    return None
