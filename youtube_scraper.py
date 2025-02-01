import os
import requests
import json
import openai
from dotenv import load_dotenv

# Load API Keys from .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API")
OPENAI_API_KEY = os.getenv("OPENAI_API")

if not API_KEY or not OPENAI_API_KEY:
    print("❌ ERROR: Missing API keys. Check your .env file!")
    exit()

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)  # ✅ OpenAI v1.0.0+ format

def get_channel_id_and_name(api_key, handle):
    """Fetch the YouTube Channel ID and Name using a @handle (e.g., @ItzNandez)."""
    url = f"https://www.googleapis.com/youtube/v3/channels?part=id,snippet&forHandle={handle}&key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            return data["items"][0]["id"], data["items"][0]["snippet"]["title"]
    
    print("❌ Error: Could not find channel ID for handle:", handle)
    return None, None

def get_latest_normal_videos(api_key, channel_id, max_results=5):
    """Fetch the latest publicly visible videos, filtering out Shorts and videos under 120s."""
    url = f"https://www.googleapis.com/youtube/v3/search?key={api_key}&channelId={channel_id}&part=snippet,id&order=date&type=video&maxResults={max_results * 3}"
    response = requests.get(url)

    normal_videos = []
    try:
        data = response.json()
        if "items" in data:
            for item in data["items"]:
                video_data = get_video_details(api_key, item["id"]["videoId"])
                
                # ✅ Solo incluir videos de 120+ segundos y NO Shorts
                if video_data and video_data["privacyStatus"] == "public":
                    if video_data["duration_seconds"] >= 120 and not is_probable_short(video_data):
                        normal_videos.append(video_data)

                if len(normal_videos) == max_results:
                    break
    except Exception as e:
        print(f"❌ Error parsing video ID response: {e}")

    return normal_videos

def get_video_details(api_key, video_id):
    """Fetch full details (title, description, privacy status, duration) for a single video."""
    url = f"https://www.googleapis.com/youtube/v3/videos?key={api_key}&id={video_id}&part=snippet,status,contentDetails"
    response = requests.get(url)

    try:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            item = data["items"][0]
            return {
                "videoId": item["id"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "publishTime": item["snippet"]["publishedAt"],
                "privacyStatus": item["status"]["privacyStatus"],
                "duration_seconds": parse_duration(item["contentDetails"]["duration"]),
                "tags": item["snippet"].get("tags", [])
            }
    except Exception as e:
        print(f"❌ Error parsing video details response: {e}")

    return None

def parse_duration(duration):
    """Convert YouTube's ISO 8601 duration format (PTxHxMxS) into seconds."""
    import isodate
    try:
        return int(isodate.parse_duration(duration).total_seconds())
    except Exception as e:
        print(f"❌ Error parsing duration: {e}")
        return 0

def is_probable_short(video):
    """Check if a video is likely a YouTube Short."""
    title = video["title"].lower()
    description = video["description"].lower()
    tags = [tag.lower() for tag in video.get("tags", [])]

    if "#shorts" in title or "#shorts" in description or "shorts" in tags:
        return True

    if video["duration_seconds"] < 120:  # ✅ Cambiado de 60 a 120 segundos
        return True

    return False

def detect_sponsors_openai(description):
    """Use OpenAI to extract brand sponsorships from the description."""
    
    if not description:
        print("🔍 No description provided.")
        return []

    prompt = f"""
    Extract brand names, company mentions, or sponsorships from the following YouTube description.  
    Only return relevant **brand names** in a JSON **list format** (like ["Brand 1", "Brand 2"]).  
    If no brands are detected, return an empty list [].

    ---
    **Example 1:**  
    Description: "Sponsored by NordVPN! Get 10% off with code TECH10: https://nordvpn.com/mychannel"  
    The output will be: ["NordVPN"]

    ---
    **Example 2:**  
    Description: "Discount for travel insurance: https://www.chapkadirect.es/index.php?action=produit&id=877&app=nandez"  
    The output will be: ["Chapka Insurance"]

    ---
    Now analyze this description and extract sponsors:
    Description: {description}
    """

    try:
        print("\n🟢 Sending prompt to OpenAI...\n", prompt)

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        raw_output = response.choices[0].message.content
        print("\n🔵 OpenAI Response (Raw):\n", raw_output)

        # ✅ Eliminar "✅ Output:" si está presente en la respuesta
        cleaned_output = raw_output.replace("✅ Output:", "").strip()

        # ✅ Parsear el JSON correctamente
        detected_brands = json.loads(cleaned_output)

        print("\n🟡 Parsed Sponsorships:\n", detected_brands)

        return detected_brands if isinstance(detected_brands, list) else []
    except json.JSONDecodeError:
        print("❌ OpenAI returned an invalid format:", cleaned_output)
        return []
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return []

def save_to_json(channel_name, videos):
    """Save the extracted video data to a JSON file named after the channel."""
    filename = f"{channel_name.replace(' ', '_')}.json"

    with open(filename, "w", encoding="utf-8") as json_file:
        json.dump({"channel_name": channel_name, "videos": videos}, json_file, indent=4, ensure_ascii=False)

    print(f"📁 Data saved to {filename}")

if __name__ == "__main__":
    # youtube_handle = "@ItzNandez"  
    youtube_handle = "@LolaLoliitaaa"
    CHANNEL_ID, CHANNEL_NAME = get_channel_id_and_name(API_KEY, youtube_handle)

    if CHANNEL_ID:
        print(f"✅ Found Channel ID: {CHANNEL_ID}")
        print(f"📌 Channel Name: {CHANNEL_NAME}")

        latest_videos = get_latest_normal_videos(API_KEY, CHANNEL_ID, max_results=5)
        
        if latest_videos:
            videos_data = []

            for video in latest_videos:
                sponsors = detect_sponsors_openai(video['description'])
                video_info = {
                    "title": video['title'],
                    "videoId": video['videoId'],
                    "published_at": video['publishTime'],
                    "duration_seconds": video['duration_seconds'],
                    "description": video['description'],
                    "sponsorships": sponsors
                }
                videos_data.append(video_info)

            save_to_json(CHANNEL_NAME, videos_data)

        else:
            print("❌ No recent full-length public videos found.")