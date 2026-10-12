"""Narration: one consistent voice for every line of an episode.

Providers (channel.yaml `tts.provider`):

* ``kokoro``: open-source Kokoro-82M (Apache-2.0) running on the CPU of the session.
  Free, no account, and the same voice every time because the voice is a fixed
  style vector. Model files (~350 MB) are cached in ~/.cache/shorts-tts.
* ``elevenlabs``: ElevenLabs API, ELEVENLABS_API_KEY in the environment. The whole
  script is sent as ONE request so delivery stays consistent, then split per scene
  using the character timestamps ElevenLabs returns.

Both write output/<id>/voiceNN.wav, which the renderer consumes unchanged.
"""

from __future__ import annotations

import base64
import os
import re
import subprocess
from pathlib import Path

import requests

CACHE = Path(os.environ.get("SHORTS_TTS_CACHE", Path.home() / ".cache" / "shorts-tts"))
KOKORO_FILES = {
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
LANG = {"en": "en-us", "en-gb": "en-gb"}


class TTSError(RuntimeError):
    pass


CURRENCY_WORDS = {"$": ("dollar", "dollars"), "€": ("euro", "euros"), "£": ("pound", "pounds")}
MONEY = re.compile(r"([$€£])\s?(\d[\d,]*(?:\.\d+)?)(\s?(?:thousand|million|billion|trillion)\b)?", re.I)


def normalize_for_speech(text: str) -> str:
    """Rewrite symbols the way people say them: "$5,000" -> "5,000 dollars".

    Local engines read a leading currency symbol literally ("dollar five thousand").
    """
    def money(m: re.Match) -> str:
        one, many = CURRENCY_WORDS[m.group(1)]
        number, scale = m.group(2), (m.group(3) or "")
        word = one if number == "1" and not scale else many
        return f"{number}{scale} {word}"

    return MONEY.sub(money, text)


def spoken_lines(episode: dict) -> list[str]:
    """What the voice says per scene: `say` (pronunciation respelling) or `narration`."""
    return [normalize_for_speech((s.get("say") or s["narration"]).strip()) for s in episode["scenes"]]


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    tmp.replace(dest)


def _clear_takes(out_dir: Path) -> None:
    for old in out_dir.glob("voice[0-9][0-9].*"):
        old.unlink()


def kokoro(episode: dict, cfg: dict, out_dir: Path) -> list[Path]:
    try:
        import soundfile as sf
        from kokoro_onnx import Kokoro
    except ImportError as e:
        raise TTSError("kokoro-onnx is not installed; run scripts/session-setup.sh") from e
    for name, url in KOKORO_FILES.items():
        if not (CACHE / name).exists():
            _download(url, CACHE / name)
    engine = Kokoro(str(CACHE / "kokoro-v1.0.onnx"), str(CACHE / "voices-v1.0.bin"))
    voice = cfg.get("voice", "am_michael")
    lang = cfg.get("lang") or LANG.get(episode.get("language", "en"), "en-us")
    _clear_takes(out_dir)
    paths = []
    for i, text in enumerate(spoken_lines(episode), 1):
        samples, sr = engine.create(text, voice=voice, speed=float(cfg.get("speed", 1.0)), lang=lang)
        path = out_dir / f"voice{i:02d}.wav"
        sf.write(path, samples, sr)
        paths.append(path)
    return paths


def elevenlabs(episode: dict, cfg: dict, out_dir: Path) -> list[Path]:
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key:
        raise TTSError("ELEVENLABS_API_KEY is not set (add it to the environment's secrets)")
    lines = spoken_lines(episode)
    # One request for the whole script keeps the delivery consistent; the
    # character timestamps tell us where each scene's line starts and ends.
    text, spans, pos = "", [], 0
    for line in lines:
        if text:
            text += " "
            pos += 1
        spans.append((pos, pos + len(line)))
        text += line
        pos += len(line)
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['voice_id']}/with-timestamps",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": key},
        json={"text": text, "model_id": cfg.get("model_id", "eleven_multilingual_v2"),
              "voice_settings": {"stability": cfg.get("stability", 0.6),
                                 "similarity_boost": cfg.get("similarity_boost", 0.8),
                                 "style": cfg.get("style", 0.0), "use_speaker_boost": True,
                                 "speed": cfg.get("speed", 1.0)}},
        timeout=300)
    if r.status_code >= 400:
        raise TTSError(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    data = r.json()
    full = out_dir / "narration_full.mp3"
    full.write_bytes(base64.b64decode(data["audio_base64"]))
    align = data["alignment"]
    starts, ends = align["character_start_times_seconds"], align["character_end_times_seconds"]
    if len(starts) != len(text):
        raise TTSError("ElevenLabs alignment does not match the submitted text; cannot split by scene")
    # Cut halfway through each pause so no syllable is clipped.
    bounds = [0.0]
    for (_, a_end), (b_start, _) in zip(spans, spans[1:]):
        bounds.append((ends[a_end - 1] + starts[b_start]) / 2)
    bounds.append(ends[-1] + 0.3)
    _clear_takes(out_dir)
    paths = []
    for i, (t0, t1) in enumerate(zip(bounds, bounds[1:]), 1):
        path = out_dir / f"voice{i:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(full),
                        "-ss", f"{t0:.3f}", "-to", f"{t1:.3f}", "-ar", "44100", "-ac", "1", str(path)], check=True)
        paths.append(path)
    return paths


PROVIDERS = {"kokoro": kokoro, "elevenlabs": elevenlabs}


def synthesize(episode: dict, channel: dict, out_dir: Path) -> list[Path]:
    tts = channel["tts"]
    provider = tts["provider"]
    if provider not in PROVIDERS:
        raise TTSError(f"unknown tts.provider {provider!r}; use one of {sorted(PROVIDERS)}")
    out_dir.mkdir(parents=True, exist_ok=True)
    return PROVIDERS[provider](episode, tts.get(provider) or {}, out_dir)
