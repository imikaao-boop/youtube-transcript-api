import re
from fastapi import FastAPI, HTTPException, Query
from youtube_transcript_api import YouTubeTranscriptApi

app = FastAPI(title="YouTube Transcript Microservice")

def extract_video_id(url_or_id: str) -> str:
    if len(url_or_id) == 11 and not " " in url_or_id:
        return url_or_id
        
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
            
    return url_or_id

@app.get("/get-transcript")
def get_transcript(url: str = Query(..., description="YouTube video URL or Video ID")):
    video_id = extract_video_id(url)
    
    # Список мов, які пробуємо отримати по черзі
    languages = ['uk', 'ru', 'en']
    
    transcript_data = None
    used_lang = None

    for lang in languages:
        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            used_lang = lang
            break
        except Exception:
            continue
            
    # Якщо з заданих мов нічого не знайшлося, спробуємо отримати хоч якісь доступні (наприклад, автогенеровані)
    if not transcript_data:
        try:
            # Отримуємо список усіх доступних субтитрів для відео
            transcript_list = YouTubeTranscriptApi.list(video_id)
            for tr in transcript_list:
                transcript_data = tr.fetch()
                used_lang = tr.language_code
                break
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Subtitles not found for this video: {str(e)}")

    if not transcript_data:
        raise HTTPException(status_code=404, detail="Subtitles are disabled or not found for this video.")

    # Скріплюємо всі шматочки тексту в один суцільний рядок
    full_text = " ".join([item['text'] for item in transcript_data])
    full_text = re.sub(r'\s+', ' ', full_text).strip()

    return {
        "success": True,
        "video_id": video_id,
        "language": used_lang,
        "transcript": full_text
    }