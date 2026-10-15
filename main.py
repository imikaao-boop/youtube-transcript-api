import os
import re
import glob
from fastapi import FastAPI, HTTPException, Query
import yt_dlp

app = FastAPI(title="YouTube Transcript Microservice via yt-dlp")

@app.get("/get-transcript")
def get_transcript(url: str = Query(..., description="YouTube video URL")):
    tmp_dir = "/tmp"
    
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['uk', 'ru', 'en'],
        'subtitlesformat': 'vtt',
        'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            
        # Шукаємо завантажений файл субтитрів у /tmp
        vtt_files = glob.glob(os.path.join(tmp_dir, f"{video_id}.*.vtt"))
        if not vtt_files:
            raise HTTPException(status_code=404, detail="Subtitles not found for this video.")
            
        vtt_file_path = vtt_files[0]
        
        # Парсимо VTT файл у чистий текст
        with open(vtt_file_path, 'r', encoding='utf-8') as f:
            vtt_content = f.read()
            
        # Видаляємо зайві теги часу та службові рядки VTT
        lines = vtt_content.splitlines()
        clean_lines = []
        for line in lines:
            if '-->' in line or line.startswith('WEBVTT') or re.match(r'^\d+$', line.strip()):
                continue
            cleaned = re.sub(r'<[^>]*>', '', line).strip()
            if cleaned and (not clean_lines or cleaned != clean_lines[-1]):
                clean_lines.append(cleaned)
                
        full_text = " ".join(clean_lines)
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        
        # Видаляємо тимчасовий файл
        try:
            os.remove(vtt_file_path)
        except:
            pass

        return {
            "success": True,
            "video_id": video_id,
            "transcript": full_text
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching subtitles: {str(e)}")