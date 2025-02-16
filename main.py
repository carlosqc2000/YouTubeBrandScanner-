from youtube.youtube_api import *
from artificial_intelligence.detect_sponsors import detect_sponsors_openai
from database.mongodb import save_to_mongodb

# Configuración
youtube_handle = "@LolaLoliitaaa" #"@ItzNandez"
channel_id, channel_name = get_channel_id_and_name(GOOGLE_API_KEY, youtube_handle)

if channel_id:
    latest_videos = get_latest_non_short_videos(GOOGLE_API_KEY, channel_id, max_results=20)

    for video in latest_videos:
        description = get_video_description(GOOGLE_API_KEY, video["videoId"])
        print(description)
        sponsors = detect_sponsors_openai(description) if description else []
        print(sponsors)
        save_to_mongodb(
                video_id=video["videoId"],
                channel_name=channel_name,
                channel_id=channel_id,
                published_at=video["publishTime"],
                sponsors=sponsors,
                title=video["title"]
            )