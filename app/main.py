import os
import uuid
import asyncio
from typing import List, Dict, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pathlib import Path

from .transcribe import transcribe_to_vtt_many
from .search_index import SearchIndexManager

# ----- Config -----
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
VTT_DIR = DATA_DIR / "vtts"
STATIC_DIR = BASE_DIR / "frontend"

for d in [DATA_DIR, UPLOAD_DIR, VTT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SUPPORTED_LANGS: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "te": "Telugu",
    "ta": "Tamil",
    "ml": "Malayalam",
    "mr": "Marathi",
    "gu": "Gujarati",
    "bn": "Bengali",
    "pa": "Punjabi",
    "or": "Odia",
    "ur": "Urdu",
}

# ----- App -----
app = FastAPI(title="Keyword Speech Indexing API", version="1.0.0")

# CORS (allow local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend and generated files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/vtts", StaticFiles(directory=str(VTT_DIR)), name="vtts")

index_manager = SearchIndexManager(vtt_root=VTT_DIR)

class UploadResponse(BaseModel):
    video_id: str
    video_url: str
    tracks: List[Dict[str, str]]

@app.get("/api/langs")
def get_langs():
    return SUPPORTED_LANGS

@app.post("/api/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...), langs: Optional[str] = Query(None)):
    # langs: comma-separated list of lang codes; default to all supported
    try:
        if file.content_type is None or not (file.content_type.startswith("video/") or file.filename.lower().endswith((".mp4", ".mkv", ".mov", ".webm", ".wav", ".mp3"))):
            raise HTTPException(status_code=400, detail="Please upload a video or audio file.")
        video_id = str(uuid.uuid4())[:8]
        ext = os.path.splitext(file.filename)[1] or ".mp4"
        save_path = UPLOAD_DIR / f"{video_id}{ext}"
        with save_path.open("wb") as f:
            f.write(await file.read())

        # parse langs
        if langs:
            requested = [code.strip() for code in langs.split(",") if code.strip() in SUPPORTED_LANGS]
            if not requested:
                requested = list(SUPPORTED_LANGS.keys())
        else:
            requested = list(SUPPORTED_LANGS.keys())

        # transcribe & translate -> VTTs
        results = await asyncio.get_event_loop().run_in_executor(
            None, lambda: transcribe_to_vtt_many(str(save_path), VTT_DIR, requested)
        )

        tracks = []
        for code in requested:
            vtt_path = VTT_DIR / f"{video_id}.{code}.vtt"
            if not vtt_path.exists():
                # Maybe transcriber wrote a different name, but we default to this
                # If not found, skip
                continue
            tracks.append({
                "lang": code,
                "label": SUPPORTED_LANGS.get(code, code),
                "url": f"/vtts/{vtt_path.name}"
            })

        # Build search indexes in background (non-blocking)
        asyncio.create_task(index_manager.ensure_indexes_for_video(video_id))

        return UploadResponse(
            video_id=video_id,
            video_url=f"/uploads/{save_path.name}",
            tracks=tracks
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

@app.get("/api/search")
def search_keyword(
    video_id: str = Query(...),
    q: str = Query(..., min_length=1),
    lang: str = Query("en")
):
    lang = lang.lower()
    if lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail=f"Unsupported lang: {lang}")
    # Ensure index exists for this video/lang
    try:
        hits = index_manager.search(video_id, lang, q)
        return {"video_id": video_id, "lang": lang, "q": q, "hits": hits}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

@app.get("/")
def root():
    # Simple redirect target for dev; serve the frontend index
    return JSONResponse({"message": "Backend running. Open frontend at /static/index.html"})
