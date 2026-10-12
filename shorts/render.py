"""Render an episode: narration timing -> Remotion motion graphics -> mixed, loudness-normalised master.

Inputs in output/<episode-id>/:

    voiceNN.(mp3|wav|m4a)        narration line for scene NN (1-based), required
    sceneNN.(png|jpg|jpeg|webp)  still for an `image` scene without `src`, optional

The Remotion project in video/ draws everything else from code.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from .captions import chunk_words, time_chunks
from .visuals import expand_visual

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".aac", ".ogg")

DEFAULT_THEME = {
    "paper": "#F3EDE2", "card": "#FFFDF8", "ink": "#14213D", "muted": "#5B6478",
    "accent": "#FFD84D", "accentInk": "#14213D", "good": "#2A9D8F", "bad": "#E63946",
}
LOCALES = {"en": "en-US", "de": "de-DE"}


class RenderError(RuntimeError):
    pass


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)
    if proc.returncode != 0:
        tail = "\n".join((proc.stderr or proc.stdout).strip().splitlines()[-30:])
        raise RenderError(f"command failed ({proc.returncode}): {' '.join(cmd[:5])} ...\n{tail}")
    return proc.stdout + proc.stderr


def probe(path: Path) -> dict:
    out = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    return json.loads(out[out.index("{"):])


def duration(path: Path) -> float:
    return float(probe(path)["format"]["duration"])


def speech_bounds(path: Path, total: float) -> tuple[float, float]:
    """Seconds from the start of a take where speech begins and ends."""
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
               "silencedetect=noise=-38dB:d=0.08", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    lead = ends[0] if starts and starts[0] <= 0.02 and ends else 0.0
    trail = total
    if starts and starts[-1] > lead and (len(ends) < len(starts) or ends[-1] >= total - 0.02):
        trail = starts[-1]
    if trail - lead < 0.3:
        return 0.0, total
    return lead, trail


def find_asset(folder: Path, stem: str, exts: tuple[str, ...]) -> Path | None:
    for ext in exts:
        p = folder / f"{stem}{ext}"
        if p.exists():
            return p
    return None


def _pick_music(prod: dict, root: Path, seed: str) -> Path | None:
    folder = root / prod.get("music_dir", "assets/music")
    tracks = sorted(p for p in folder.glob("*") if p.suffix.lower() in AUDIO_EXTS) if folder.exists() else []
    if not tracks:
        return None
    return tracks[int(hashlib.sha256(seed.encode()).hexdigest(), 16) % len(tracks)]


def build_props(episode: dict, channel: dict, series: dict, timings: list[dict], total: float,
                asset_dir: Path) -> dict:
    prod = channel["production"]
    theme = dict(DEFAULT_THEME, **(series.get("theme") or {}))
    scenes = []
    for i, (scene, t) in enumerate(zip(episode["scenes"], timings), 1):
        visual = expand_visual(scene["visual"])
        if visual["type"] == "image" and not visual.get("src"):
            still = find_asset(asset_dir, f"scene{i:02d}", IMAGE_EXTS)
            if still is None:
                raise RenderError(f"scene {i}: image scene needs scene{i:02d}.(png|jpg|webp) in {asset_dir}")
            visual["src"] = still.name
        visual.pop("prompt", None)
        captions = time_chunks(chunk_words(scene["narration"]), t["speech_start"], t["speech_end"])
        scenes.append({"start": round(t["start"], 3), "duration": round(t["end"] - t["start"], 3),
                       "visual": visual, "captions": captions})
    return {
        "fps": prod["fps"], "width": prod["width"], "height": prod["height"], "duration": round(total, 3),
        "locale": LOCALES.get(episode.get("language", "en"), "en-US"),
        "theme": theme,
        "seriesLabel": series.get("label", ""),
        "hookText": episode.get("hook_text", ""),
        "disclaimer": channel["channel"]["disclaimer"],
        "cta": channel["channel"].get("cta", ""),
        "scenes": scenes,
    }


def render_episode(episode: dict, channel: dict, series: dict, asset_dir: Path, root: Path) -> dict:
    """Render output/<id>/final.mp4 and return render facts (path, duration, checks)."""
    prod = channel["production"]
    asset_dir, root = asset_dir.resolve(), root.resolve()
    work = asset_dir / "work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    # 1. Measure narration and lay out the timeline (one scene per narration line).
    voices, takes = [], []
    for i in range(1, len(episode["scenes"]) + 1):
        v = find_asset(asset_dir, f"voice{i:02d}", AUDIO_EXTS)
        if v is None:
            raise RenderError(f"missing narration voice{i:02d}.* in {asset_dir}")
        d = duration(v)
        voices.append(v)
        takes.append((d, *speech_bounds(v, d)))

    pad, hold = prod["scene_pad_seconds"], prod["end_hold_seconds"]
    lengths = [d + pad for d, _, _ in takes]
    lengths[-1] += hold
    total = sum(lengths)
    deficit = prod["min_seconds"] + 0.5 - total
    if deficit > 0:
        if deficit > 4.0:
            raise RenderError(f"narration only fills {total:.1f} s; need > {prod['min_seconds']} s. "
                              "Lengthen the script (lint estimates should catch this).")
        lengths[-1] += deficit
        total += deficit
    timings, t = [], 0.0
    for length, (_, lead, trail) in zip(lengths, takes):
        timings.append({"start": t, "end": t + length, "speech_start": t + lead, "speech_end": t + trail})
        t += length

    # 2. Narration track: each take padded to its scene length, then joined.
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for v in voices:
        cmd += ["-i", str(v)]
    chains = [f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,apad=whole_dur={L:.3f},"
              f"atrim=0:{L:.3f},asetpts=N/SR/TB[a{i}]" for i, L in enumerate(lengths)]
    joined = "".join(f"[a{i}]" for i in range(len(lengths)))
    narration = work / "narration.wav"
    run(cmd + ["-filter_complex", ";".join(chains) + f";{joined}concat=n={len(lengths)}:v=0:a=1[out]",
               "-map", "[out]", "-c:a", "pcm_s16le", str(narration)])

    # 3. Motion graphics via Remotion (silent), using output/<id>/ as the public dir for stills.
    props = build_props(episode, channel, series, timings, total, asset_dir)
    props_path = work / "props.json"
    props_path.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
    video_dir = root / "video"
    if not (video_dir / "node_modules" / ".bin" / "remotion").exists():
        run(["npm", "ci", "--no-audit", "--no-fund"], cwd=video_dir)
    visuals = work / "visuals.mp4"
    concurrency = str(max(1, (os.cpu_count() or 2)))
    run(["npx", "remotion", "render", "src/index.ts", "Short", str(visuals), f"--props={props_path}",
         f"--public-dir={asset_dir}", "--muted", "--codec=h264", "--crf=18", f"--concurrency={concurrency}",
         "--log=error"], cwd=video_dir)

    # 4. Mix narration (+ optional ducked music bed), normalise loudness, mux.
    final = asset_dir / "final.mp4"
    music = _pick_music(prod, root, episode["id"])
    lufs = prod["loudness_lufs"]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(visuals), "-i", str(narration)]
    if music:
        vol = prod.get("music_volume_db", -24)
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        agraph = (f"[1:a]aformat=channel_layouts=stereo,asplit=2[voice][key];"
                  f"[2:a]aformat=channel_layouts=stereo,volume={vol}dB[bed];"
                  f"[bed][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[ducked];"
                  f"[voice][ducked]amix=inputs=2:duration=first:normalize=0,loudnorm=I={lufs}:TP=-1.5:LRA=11[a]")
    else:
        agraph = f"[1:a]aformat=channel_layouts=stereo,loudnorm=I={lufs}:TP=-1.5:LRA=11[a]"
    run(cmd + ["-filter_complex", agraph, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total:.3f}",
               "-movflags", "+faststart", str(final)])

    poster = asset_dir / "poster.jpg"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", "1.0", "-i", str(final),
         "-frames:v", "1", "-q:v", "3", str(poster)])

    checks = qa(final, channel)
    return {
        "path": str(final.relative_to(root)) if final.is_relative_to(root) else str(final),
        "duration": round(duration(final), 2),
        "size_mb": round(final.stat().st_size / 1e6, 2),
        "sha256": hashlib.sha256(final.read_bytes()).hexdigest(),
        "music": music.name if music else None,
        "checks": checks,
    }


def qa(path: Path, channel: dict) -> dict:
    """Hard checks every master must pass before it may be published."""
    prod = channel["production"]
    info = probe(path)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    audio = [s for s in info["streams"] if s["codec_type"] == "audio"]
    num, den = (int(x) for x in video["r_frame_rate"].split("/"))
    dur = float(info["format"]["duration"])
    vol = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    match = re.search(r"mean_volume: (-?[\d.]+) dB", vol)
    mean = float(match.group(1)) if audio and match else -99.0
    checks = {
        "resolution": f"{video['width']}x{video['height']}",
        "fps": round(num / den, 2),
        "duration": round(dur, 2),
        "has_audio": bool(audio),
        "mean_volume_db": mean,
    }
    problems = []
    if (video["width"], video["height"]) != (prod["width"], prod["height"]):
        problems.append(f"resolution {checks['resolution']}")
    if abs(checks["fps"] - prod["fps"]) > 0.5:
        problems.append(f"fps {checks['fps']}")
    if dur <= prod["min_seconds"]:
        problems.append(f"duration {dur:.1f}s is not above {prod['min_seconds']}s")
    if dur > prod["max_seconds"] + 8:
        problems.append(f"duration {dur:.1f}s too long")
    if not audio or mean < -40:
        problems.append("audio missing or near-silent")
    checks["passed"] = not problems
    checks["problems"] = problems
    return checks
