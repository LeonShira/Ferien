"""Listen to the narration: transcribe every take and compare it with the script.

A TTS engine can mispronounce a symbol ("dollar five thousand"), skip a word or
garble a name, and nobody hears it in an unattended run. This module transcribes
each take with Whisper (faster-whisper, base.en, CPU) and

* flags lines whose transcript drifts from the script (word error rate), and
* returns per-word timestamps, which the renderer uses to sync captions exactly.

Results are written to output/<id>/alignment.json.
"""

from __future__ import annotations

import difflib
import json
import re
import subprocess
from pathlib import Path

from .render import AUDIO_EXTS, find_asset

WARN_WER = 0.15
ERROR_WER = 0.30
NUMBER_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}


def norm(word: str) -> str:
    w = word.lower().replace(",", "").replace("’", "'")
    w = re.sub(r"[^\w%'.]", "", w).strip(".'")
    w = w.replace("%", "")
    return NUMBER_WORDS.get(w, w)


def tokens(text: str) -> list[str]:
    return [t for t in (norm(w) for w in re.split(r"[\s\-–—/]+", text)) if t]


def wer(ref: list[str], hyp: list[str]) -> float:
    if not ref:
        return 0.0 if not hyp else 1.0
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
    return d[-1] / len(ref)


def _load_pcm(path: Path):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(path), "-f", "f32le",
                          "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def word_times(script_text: str, heard: list[dict]) -> list[tuple[float, float]]:
    """Timestamps for each word of `script_text`, transferred from the transcript.

    Words are matched in order; words Whisper heard differently get times
    interpolated from their matched neighbours.
    """
    words = script_text.split()
    a = [norm(w) for w in words]
    b = [norm(h["word"]) for h in heard]
    times: list[tuple[float, float] | None] = [None] * len(words)
    for blk in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            times[blk.a + k] = (heard[blk.b + k]["start"], heard[blk.b + k]["end"])
    if not heard:
        return []
    first, last = heard[0]["start"], heard[-1]["end"]
    known = [i for i, t in enumerate(times) if t]
    for i, t in enumerate(times):
        if t:
            continue
        before = max((k for k in known if k < i), default=None)
        after = min((k for k in known if k > i), default=None)
        t0 = times[before][1] if before is not None else first
        t1 = times[after][0] if after is not None else last
        lo = before if before is not None else -1
        hi = after if after is not None else len(words)
        span = (t1 - t0) / (hi - lo)
        times[i] = (t0 + span * (i - lo - 1), t0 + span * (i - lo))
    return times  # type: ignore[return-value]


def listen(episode: dict, out_dir: Path, model_name: str = "base.en") -> dict:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    lines = []
    for i, scene in enumerate(episode["scenes"], 1):
        take = find_asset(out_dir, f"voice{i:02d}", AUDIO_EXTS)
        if take is None:
            raise FileNotFoundError(f"missing voice{i:02d}.* in {out_dir}")
        segments, _ = model.transcribe(_load_pcm(take), beam_size=5, word_timestamps=True,
                                       language=episode.get("language", "en")[:2])
        heard: list[dict] = []
        for w in (w for s in segments for w in (s.words or [])):
            # Whisper splits "5,000" into "5" + ",000" and "24%" into "24" + "%"; a token
            # without a leading space continues the previous word.
            if heard and not w.word.startswith(" "):
                heard[-1]["word"] += w.word
                heard[-1]["end"] = round(w.end, 3)
            else:
                heard.append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
        text = " ".join(h["word"] for h in heard)
        rate = wer(tokens(scene["narration"]), tokens(text))
        lines.append({"scene": i, "heard": text, "wer": round(rate, 3),
                      "words": [list(t) for t in word_times(scene["narration"], heard)]})
    result = {"model": model_name, "lines": lines}
    (out_dir / "alignment.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result


def problems(result: dict, episode: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for line, scene in zip(result["lines"], episode["scenes"]):
        msg = f"scene {line['scene']}: heard {line['heard']!r} for {scene['narration']!r} (WER {line['wer']:.0%})"
        if line["wer"] > ERROR_WER:
            errors.append(msg)
        elif line["wer"] > WARN_WER:
            warnings.append(msg)
    return errors, warnings
