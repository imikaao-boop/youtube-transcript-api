import re
from fastapi import FastAPI, HTTPException, Query
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

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
    
    try:
        # Створюємо об'єкт API і напряму забираємо субтитри для вказаних мов
        api = YouTubeTranscriptApi()
        fetched_data = api.fetch(video_id, languages=['uk', 'ru', 'en'])
        
        # Витягуємо самі тексти
        transcript_data = fetched_data.data
        used_lang = getattr(fetched_data, 'language_code', 'unknown')

    except (TranscriptsDisabled, NoTranscriptFound):
        raise HTTPException(status_code=404, detail="Subtitles are disabled or not found for this video.")
    except Exception as e:
        # Запасний варіант спроби отримати без вказання мови (автовизначення)
        try:
            api = YouTubeTranscriptApi()
            # Отримуємо перші доступні
            transcript_list = api.list(video_id)
            for transcript in transcript_list:
                transcript_data = transcript.fetch()
                used_lang = transcript.language_code
                break
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Could not fetch transcript: {str(err)}")

    # Скріплюємо всі шматочки тексту в один суцільний рядок
    full_text = " ".join([item['text'] for item in transcript_data])
    full_text = re.sub(r'\s+', ' ', full_text).strip()

    return {
        "success": True,
        "video_id": video_id,
        "language": used_lang,
        "transcript": full_text
    }