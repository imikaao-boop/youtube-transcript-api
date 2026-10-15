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
        # Спочатку намагаємося отримати субтитри через список доступних мов
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        transcript = None
        for lang in ['uk', 'ru', 'en']:
            try:
                transcript = transcript_list.find_transcript([lang])
                break
            except:
                continue
                
        if not transcript:
            for t in transcript_list:
                transcript = t
                break
                
        if not transcript:
            raise HTTPException(status_code=404, detail="Subtitles not found for this video.")

        transcript_data = transcript.fetch()
        used_lang = transcript.language_code

    except (TranscriptsDisabled, NoTranscriptFound):
        raise HTTPException(status_code=404, detail="Subtitles are disabled or not found for this video.")
    except Exception:
        # Резервний варіант прямого завантаження
        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=['uk', 'ru', 'en'])
            used_lang = "auto/fallback"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not fetch transcript: {str(e)}")

    # Скріплюємо всі шматочки тексту в один суцільний рядок
    full_text = " ".join([item['text'] for item in transcript_data])
    full_text = re.sub(r'\s+', ' ', full_text).strip()

    return {
        "success": True,
        "video_id": video_id,
        "language": used_lang,
        "transcript": full_text
    }