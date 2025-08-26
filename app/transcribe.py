import os
from pathlib import Path
from typing import List, Dict, Any
import json

# External deps: whisper, torch, deep_translator (or openai)
# We attempt to import; if missing, we raise a helpful error.
try:
    import whisper
except Exception as e:
    whisper = None

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

SUPPORTED_LANGS = ["en","hi","kn","te","ta","ml","mr","gu","bn","pa","or","ur"]

def format_timestamp(seconds: float) -> str:
    ms = int(round((seconds - int(seconds)) * 1000))
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = int(seconds) // 3600
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

def write_vtt(segments: List[Dict[str, Any]], out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, seg in enumerate(segments, 1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg["text"].strip().replace("-->", "→")
            f.write(f"{start} --> {end}\n{text}\n\n")

def translate_segments(segments: List[Dict[str, Any]], target_lang: str) -> List[Dict[str, Any]]:
    if target_lang == "en":
        return segments
    if GoogleTranslator is None:
        raise RuntimeError("Translation requires 'deep-translator'. Install via: pip install deep-translator")
    translator = GoogleTranslator(source='auto', target=target_lang)
    out = []
    # Batch translation for performance: join texts with a delimiter, translate, then split.
    delim = " ||| "
    joined = delim.join([s["text"] for s in segments])
    translated = translator.translate(joined)
    parts = [p.strip() for p in translated.split("|||")]
    if len(parts) != len(segments):
        # Fallback to per-line translation
        parts = []
        for s in segments:
            parts.append(translator.translate(s["text"]))
    for s, t in zip(segments, parts):
        out.append({"start": s["start"], "end": s["end"], "text": t})
    return out

def transcribe_core(audio_path: str) -> List[Dict[str, Any]]:
    if whisper is None:
        raise RuntimeError("Whisper not installed. Install via: pip install -U openai-whisper && ensure ffmpeg is installed.")
    model_name = os.environ.get("WHISPER_MODEL", "small")
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, task="transcribe")  # keeps original language if supported
    segments = []
    for seg in result.get("segments", []):
        segments.append({"start": float(seg["start"]), "end": float(seg["end"]), "text": seg["text"]})
    if not segments and result.get("text"):
        # Whole-file fallback
        segments = [{"start": 0.0, "end": 0.01, "text": result["text"]}]
    return segments

def transcribe_to_vtt_many(media_path: str, vtt_dir: Path, langs: List[str]) -> Dict[str, str]:
    """
    Returns a dict of {lang_code: vtt_path_str}
    """
    p = Path(media_path)
    video_id = p.stem  # may include uuid from API
    base_segments = transcribe_core(media_path)

    out = {}
    for code in langs:
        if code not in SUPPORTED_LANGS:
            continue
        if code == "en":
            segs = base_segments
        else:
            try:
                segs = translate_segments(base_segments, code)
            except Exception as e:
                # If translation fails, write English as a placeholder for that language
                segs = base_segments
        vtt_path = vtt_dir / f"{video_id}.{code}.vtt"
        write_vtt(segs, vtt_path)
        out[code] = str(vtt_path)
    # Also write a manifest for indexing
    manifest = {
        "video_id": video_id,
        "media_file": os.path.basename(media_path),
        "langs": list(out.keys())
    }
    with (vtt_dir / f"{video_id}.manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return out
