from typing import List, Tuple

def parse_vtt(vtt_text: str) -> List[Tuple[float, float, str]]:
    """
    Minimal VTT parser returning list of (start_sec, end_sec, text).
    """
    lines = [ln.strip("\ufeff") for ln in vtt_text.splitlines()]
    cues = []
    i = 0
    def ts_to_sec(ts: str) -> float:
        # format: HH:MM:SS.mmm
        h, m, rest = ts.split(":")
        s, ms = rest.split(".")
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
    while i < len(lines):
        ln = lines[i].strip()
        i += 1
        if "-->" in ln:
            try:
                start, end = [x.strip() for x in ln.split("-->")]
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    text_lines.append(lines[i].strip())
                    i += 1
                text = " ".join(text_lines)
                cues.append((ts_to_sec(start), ts_to_sec(end), text))
            except Exception:
                continue
    return cues
