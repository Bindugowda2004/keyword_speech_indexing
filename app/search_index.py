import json
from pathlib import Path
from typing import Dict, List, Tuple
from .vtt_utils import parse_vtt

class SearchIndexManager:
    """
    Builds and caches word->timestamps indexes from VTT.
    Index format: { "word": [start_seconds,...] }
    """
    def __init__(self, vtt_root: Path):
        self.vtt_root = Path(vtt_root)
        self.cache: Dict[str, Dict[str, Dict[str, List[float]]]] = {}
        # cache[video_id][lang] -> index dict
    
    def _index_path(self, video_id: str, lang: str) -> Path:
        return self.vtt_root / f"{video_id}.{lang}.index.json"

    def _vtt_path(self, video_id: str, lang: str) -> Path:
        return self.vtt_root / f"{video_id}.{lang}.vtt"

    async def ensure_indexes_for_video(self, video_id: str):
        # Build for all langs present in manifest, if missing
        manifest_path = self.vtt_root / f"{video_id}.manifest.json"
        if not manifest_path.exists():
            return
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for lang in manifest.get("langs", []):
            _ = self._get_or_build(video_id, lang)

    def _get_or_build(self, video_id: str, lang: str) -> Dict[str, List[float]]:
        vid_cache = self.cache.setdefault(video_id, {})
        if lang in vid_cache:
            return vid_cache[lang]
        idx_path = self._index_path(video_id, lang)
        if idx_path.exists():
            idx = json.loads(idx_path.read_text(encoding="utf-8"))
            vid_cache[lang] = idx
            return idx
        vtt_path = self._vtt_path(video_id, lang)
        if not vtt_path.exists():
            raise FileNotFoundError(f"VTT not found for video={video_id} lang={lang}")
        cues = parse_vtt(vtt_path.read_text(encoding="utf-8"))
        idx: Dict[str, List[float]] = {}
        for start, end, text in cues:
            # Simple tokenization
            for raw in text.split():
                word = "".join([c.lower() for c in raw if c.isalnum()])
                if not word:
                    continue
                idx.setdefault(word, []).append(start)
        # Deduplicate & sort
        for w in list(idx.keys()):
            idx[w] = sorted(set(round(t, 2) for t in idx[w]))
        # persist
        idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=0), encoding="utf-8")
        vid_cache[lang] = idx
        return idx

    def search(self, video_id: str, lang: str, q: str) -> List[float]:
        idx = self._get_or_build(video_id, lang)
        key = "".join([c.lower() for c in q if c.isalnum()])
        return idx.get(key, [])
