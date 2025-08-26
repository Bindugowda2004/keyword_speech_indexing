# Keyword Speech Indexing — Full Stack (Python + Vanilla Frontend)

 Project to upload an audio/video file, generate subtitles (VTT) in **multiple Indian languages**, play the video with selectable subtitles, and **jump to timestamps by keyword**.


## Features

- 🗂️ Upload audio/video
- 📝 Transcribe with [OpenAI Whisper](local) — choose model via `WHISPER_MODEL` env var
- 🌐 Auto-translate subtitles to 11 Indian languages (via `deep-translator` GoogleTranslate backend)
- 📄 Save per-language `.vtt` files
- 🎯 Keyword search: type a word, jump to its earliest occurrence, see all hits as clickable chips
- 🧩 Clean API (FastAPI) + static frontend
- 🔐 CORS enabled for local dev
- 🔎 Simple VTT parser & word indexer

## Tech

- **Backend:** Python 3.9+, FastAPI, Uvicorn
- **ASR:** `openai-whisper` (requires `ffmpeg` installed on your system)
- **Translate:** `deep-translator` (uses Google Translate unofficially)
- **Frontend:** Plain HTML/CSS/JS (no build step)

## Setup

1. **Install system dependency**
   - **ffmpeg**:  
     - Windows: get a static build from ffmpeg.org and add `bin` to PATH  
     - macOS: `brew install ffmpeg`  
     - Linux (Debian/Ubuntu): `sudo apt-get install ffmpeg`

2. **Create & activate venv (recommended)**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install Python deps**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the backend (dev)**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Open the frontend**
   - Navigate to: `http://127.0.0.1:8000/static/index.html`

## Usage

- Click **Upload & Transcribe**, pick your file.  
- Wait for processing (longer videos take longer).  
- Once ready, the video appears with track(s) for `en` and selected Indian languages.  
- Use the **keyword search** box: type a word (in the same script as the subtitle language), click **Go to first match**, and the player jumps to the first hit. All matches are shown as time chips—click any to jump.

## Notes & Tips

- First run downloads a Whisper model (default `small`). For faster/better accuracy, set env var `WHISPER_MODEL` to one of: `tiny`, `base`, `small`, `medium`, `large`.
- Translation uses `deep-translator`. If translation fails or rate-limits, the English transcript is used as a fallback for that language.
- Generated files are in `data/uploads/` (media) and `data/vtts/` (captions & indexes).
- API quick test:
  ```bash
  curl -F "file=@/path/to/video.mp4" "http://127.0.0.1:8000/api/upload?langs=en,hi,ta"
  curl "http://127.0.0.1:8000/api/search?video_id=abcd1234&lang=hi&q=नमस्ते"
  ```

## File Tree

```
keyword-speech-indexing-fullstack/
├─ app/
│  ├─ __init__.py
│  ├─ main.py                # FastAPI app, upload+search endpoints, serves static & VTTs
│  ├─ transcribe.py          # Whisper transcription + translation + VTT writer
│  ├─ vtt_utils.py           # Minimal VTT parser
│  └─ search_index.py        # Builds/loads word->timestamps index per language
├─ data/
│  ├─ uploads/               # Saved media files
│  └─ vtts/                  # Generated VTTs + indexes
├─ frontend/
│  ├─ index.html
│  ├─ styles.css
│  └─ script.js
├─ requirements.txt
├─ README.md
├─ run_dev.sh
└─ run_dev.bat
```

## Environment Variables

- `WHISPER_MODEL` — set to `tiny|base|small|medium|large` (default `small`)

## Windows / macOS helpers

- **Windows:** double-click `run_dev.bat` after installing dependencies.
- **macOS/Linux:** `bash run_dev.sh`

## Troubleshooting

- `ffmpeg not found` → Install FFmpeg and ensure it is on your PATH.
- `CUDA not available` → Whisper will fall back to CPU. For GPU, install PyTorch with CUDA.
- Translations missing → ensure internet access; `pip install deep-translator`.
- If your video language is not English, Whisper still transcribes in the original language. The search works on the chosen subtitle language (word must match script/casing).

## License

MIT — use freely in your capstone with attribution.

## author
{ Bindu (https://github.com/Bindugowda2004)}
