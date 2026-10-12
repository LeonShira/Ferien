"""Caption chunking and timing.

Each narration line is split into 2-4 word chunks, timed in proportion to their
length inside the line's detected speech window. On short chunks that stays
within a few frames of the voice, which is all a short needs.
"""

from __future__ import annotations

import re


def chunk_words(text: str, max_words: int = 3, max_chars: int = 18) -> list[str]:
    """Split narration into short caption chunks, breaking after punctuation."""
    chunks: list[str] = []
    current: list[str] = []
    for word in text.split():
        candidate = " ".join(current + [word])
        if current and (len(current) >= max_words or len(candidate) > max_chars):
            chunks.append(" ".join(current))
            current = []
        current.append(word)
        if re.search(r"[.!?;:,]$", word):
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


def _weight(chunk: str) -> float:
    w = len(re.sub(r"[^\w%€$£]", "", chunk)) + 2
    if re.search(r"[.!?]$", chunk):
        w += 5
    elif re.search(r"[,;:]$", chunk):
        w += 2.5
    return w


def time_chunks(chunks: list[str], start: float, end: float) -> list[dict]:
    total = sum(_weight(c) for c in chunks) or 1.0
    span = max(0.1, end - start)
    out, t = [], start
    for c in chunks:
        d = span * _weight(c) / total
        out.append({"start": round(t, 3), "end": round(t + d, 3), "text": c.rstrip(",;:")})
        t += d
    return out


def chunks_from_words(text: str, times: list[list[float]], offset: float) -> list[dict]:
    """Caption chunks timed from per-word timestamps (see shorts/listen.py)."""
    words = text.split()
    if len(times) != len(words) or not words:
        return []
    out, i = [], 0
    for chunk in chunk_words(text):
        n = len(chunk.split())
        out.append({"start": round(offset + times[i][0], 3), "end": round(offset + times[i + n - 1][1], 3),
                    "text": chunk.rstrip(",;:")})
        i += n
    # Hold each chunk until the next one starts so captions never blink off mid-sentence.
    for a, b in zip(out, out[1:]):
        if b["start"] - a["end"] < 0.6:
            a["end"] = b["start"]
    return out
