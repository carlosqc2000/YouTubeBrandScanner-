import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read API key from .env
API_KEY = os.getenv("GOOGLE_API")

# YouTube Channel ID (Nandez!)
CHANNEL_ID = "UC4DkKqQmgmlOOWi1pUw95JQ"

# YouTube API base URL
BASE_URL = "https://www.googleapis.com/youtube/v3/"

def get_video_ids(api_key, channel_id):
    """Fetch the latest 50 video IDs from a YouTube channel."""
    url = f"{BASE_URL}search?key={api_key}&channelId={channel_id}&part=id&order=date&maxResults=50"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        video_ids = [item["id"]["videoId"] for item in data.get("items", []) if "videoId" in item["id"]]
        return video_ids
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

if __name__ == "__main__":
    if not API_KEY:
        print("Error: API_KEY not found. Make sure it's in the .env file.")
    else:
        print("Fetching the latest 50 video IDs...")
        video_ids = get_video_ids(API_KEY, CHANNEL_ID)
        
        if video_ids:
            print(f"Found {len(video_ids)} videos.")
            print("First 5 video IDs:", video_ids[:5])  # Print only first 5 for testing
        else:
            print("No videos found or there was an issue with the request.")
