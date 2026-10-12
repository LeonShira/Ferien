"""Command line for the shorts pipeline.

    python -m shorts doctor                 check tools, fonts, config, secrets
    python -m shorts status                 backlog, buffer and recent episodes
    python -m shorts next                   print the next topic (JSON)
    python -m shorts new <topic_id>         create content/episodes/<date>-<topic>.yaml from the template
    python -m shorts lint <episode_id>      compliance + length + fact checks (exit 1 on errors)
    python -m shorts prompts <episode_id>   print the Higgsfield image/TTS requests for the episode (JSON)
    python -m shorts fetch <episode_id>     download generated assets into output/<id>/
    python -m shorts render <episode_id>    build output/<id>/final.mp4 and run QA
    python -m shorts publish <episode_id> [--dry-run] [--now]
    python -m shorts mark <topic_id> <status>
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import requests

from . import backlog, lint, publish, render
from .config import (EPISODES_DIR, ROOT, episode_output_dir, episode_path, load_channel, load_yaml,
                     save_yaml)

TEMPLATE = ROOT / "content" / "episode_template.yaml"


def _load_episode(episode_id: str) -> dict:
    path = episode_path(episode_id)
    if not path.exists():
        sys.exit(f"no episode file {path.relative_to(ROOT)}")
    return load_yaml(path)


def _save_episode(ep: dict) -> None:
    save_yaml(episode_path(ep["id"]), ep)


def cmd_doctor(_args) -> int:
    ok = True

    def report(good: bool, msg: str) -> None:
        nonlocal ok
        ok &= good
        print(("ok   " if good else "FAIL ") + msg)

    for tool in ("ffmpeg", "ffprobe"):
        report(shutil.which(tool) is not None, f"{tool} on PATH")
    channel = load_channel()
    fonts = subprocess.run(["fc-list", ":family"], capture_output=True, text=True).stdout if shutil.which("fc-list") else ""
    for font in ("Inter", "Inter Display", "Noto Color Emoji"):
        report(font.lower() in fonts.lower(), f"font {font!r} installed")
    filters = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    for f in ("loudnorm", "sidechaincompress", "silencedetect"):
        report(f" {f} " in filters, f"ffmpeg filter {f}")
    report((ROOT / "video" / "node_modules" / ".bin" / "remotion").exists(),
           "video/node_modules installed (run: cd video && npm ci)")
    for f in ("topics.yaml", "series.yaml", "episode_template.yaml"):
        report((ROOT / "content" / f).exists(), f"content/{f}")
    provider = channel["publishing"]["provider"]
    if provider == "upload_post":
        has_key = bool(os.environ.get("UPLOAD_POST_API_KEY"))
        print(("ok   " if has_key else "WARN ") + "UPLOAD_POST_API_KEY set"
              + ("" if has_key else " (videos will be rendered and packaged, not posted)"))
        if has_key:
            try:
                client = publish.UploadPost()
                me = client.me()
                user = client.resolve_user(channel["publishing"].get("upload_post_user", ""))
                print(f"ok   Upload-Post plan {me.get('plan')!r}, profile {user!r}, "
                      f"connected: {sorted(client.connected_platforms(user)) or 'none'}")
            except publish.PublishError as e:
                report(False, f"Upload-Post: {e}")
    return 0 if ok else 1


def cmd_status(_args) -> int:
    topics = backlog.load_topics()
    episodes = backlog.load_episodes()
    by_status: dict[str, int] = {}
    for t in topics:
        by_status[t.get("status", "todo")] = by_status.get(t.get("status", "todo"), 0) + 1
    print(f"topics: {len(topics)} {by_status}")
    buffer = [e["id"] for e in episodes if e.get("status") == "rendered"]
    print(f"rendered, waiting to post: {len(buffer)} {buffer}")
    for e in episodes[-7:]:
        pub = e.get("publish") or {}
        print(f"  {e['id']:<48} {e.get('status', '?'):<10} {pub.get('scheduled_date') or ''}")
    nxt = backlog.next_topic(topics, episodes)
    print(f"next topic: {nxt['id'] if nxt else 'BACKLOG EMPTY - add topics'}")
    return 0


def cmd_next(_args) -> int:
    t = backlog.next_topic()
    if not t:
        print(json.dumps({"error": "backlog empty"}))
        return 1
    series = backlog.load_series()[t["series"]]
    print(json.dumps({"topic": t, "series": series}, indent=2, ensure_ascii=False))
    return 0


def cmd_new(args) -> int:
    topics = {t["id"]: t for t in backlog.load_topics()}
    topic = topics.get(args.topic_id)
    if not topic:
        sys.exit(f"unknown topic {args.topic_id}")
    ep_id = backlog.new_episode_id(args.topic_id, date.fromisoformat(args.date) if args.date else None)
    path = episode_path(ep_id)
    if path.exists() and not args.force:
        sys.exit(f"{path.relative_to(ROOT)} exists (use --force)")
    ep = load_yaml(TEMPLATE)
    channel = load_channel()
    ep.update({"id": ep_id, "series": topic["series"], "topic_id": topic["id"],
               "language": channel["channel"]["language"], "status": "draft"})
    _save_episode(ep)
    backlog.set_status(topic["id"], "in_progress", ep_id)
    print(path.relative_to(ROOT))
    return 0


def cmd_lint(args) -> int:
    ep = _load_episode(args.episode_id)
    channel = load_channel()
    previous = [e for e in backlog.load_episodes() if e.get("id") != ep["id"]][-20:]
    errors, warnings = lint.lint_episode(ep, channel, previous)
    est = lint.estimate_seconds(ep, channel)
    print(f"estimated length: {est:.1f} s, {len(lint.words(lint.narration(ep)))} words, {len(ep.get('scenes', []))} scenes")
    for w in warnings:
        print("WARN  " + w)
    for e in errors:
        print("ERROR " + e)
    print("PASS" if not errors else f"FAIL ({len(errors)} errors)")
    return 1 if errors else 0


def cmd_prompts(args) -> int:
    """Emit ready-to-submit generation requests so every run uses identical settings."""
    ep = _load_episode(args.episode_id)
    hf = load_channel()["higgsfield"]
    style = " ".join(hf["style_formula"].split())
    images, audio = [], []
    for i, s in enumerate(ep["scenes"], 1):
        v = s.get("visual") or {}
        if v.get("type") == "image" and v.get("prompt") and not v.get("src"):
            images.append({"index": i, "params": {
                "model": hf["image_model"], "aspect_ratio": "1:1", "resolution": hf["image_resolution"],
                "prompt": f"{v['prompt'].strip()}. Style: {style}",
                "medias": [{"role": "image_references", "value": hf["style_reference_media_id"]}]}})
        audio.append({"index": i, "params": {
            "model": hf["tts_model"], "variant": hf["tts_variant"],
            "voice_id": hf["voice"]["id"], "voice_type": hf["voice"]["type"],
            "prompt": s["narration"].strip()}})
    print(json.dumps({"image_requests": images, "audio_requests": audio}, indent=2, ensure_ascii=False))
    return 0


def _download(url: str, dest_stem: Path) -> Path:
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))
    ext = Path(urlparse(url).path).suffix.lower()
    if not ext or len(ext) > 5:
        ext = mimetypes.guess_extension(r.headers.get("content-type", "").split(";")[0]) or ".bin"
    out = dest_stem.with_suffix(ext)
    out.write_bytes(r.content)
    return out


def cmd_fetch(args) -> int:
    ep = _load_episode(args.episode_id)
    out = episode_output_dir(ep["id"])
    out.mkdir(parents=True, exist_ok=True)
    assets = ep.get("assets", {}).get("scenes") or []
    if len(assets) != len(ep["scenes"]):
        sys.exit(f"assets.scenes has {len(assets)} entries for {len(ep['scenes'])} scenes")
    for i, a in enumerate(assets, 1):
        for key, stem in (("image_url", f"scene{i:02d}"), ("audio_url", f"voice{i:02d}")):
            if a.get(key):
                path = _download(a[key], out / stem)
                print(f"{key:<10} scene {i:02d} -> {path.relative_to(ROOT)}")
    ep["status"] = "assets"
    _save_episode(ep)
    return 0


def cmd_render(args) -> int:
    ep = _load_episode(args.episode_id)
    channel = load_channel()
    errors, _ = lint.lint_episode(ep, channel)
    if errors and not args.skip_lint:
        print("\n".join("ERROR " + e for e in errors))
        sys.exit("lint failed; fix the script before rendering")
    out = episode_output_dir(ep["id"])
    series = backlog.load_series().get(ep["series"], {})
    try:
        info = render.render_episode(ep, channel, series, out, ROOT)
    except render.RenderError as e:
        ep["status"] = "failed"
        ep["error"] = str(e)[:2000]
        _save_episode(ep)
        print(str(e))
        return 1
    texts = publish.compose_texts(ep, channel)
    (out / "post.txt").write_text(
        f"TIKTOK CAPTION\n{texts['tiktok_title']}\n\nYOUTUBE TITLE\n{texts['youtube_title']}\n\n"
        f"YOUTUBE DESCRIPTION\n{texts['youtube_description']}\n", encoding="utf-8")
    ep["render"] = info
    ep.pop("error", None)
    ep["status"] = "rendered" if info["checks"]["passed"] else "failed"
    _save_episode(ep)
    print(json.dumps(info, indent=2))
    return 0 if info["checks"]["passed"] else 1


def cmd_publish(args) -> int:
    ep = _load_episode(args.episode_id)
    channel = load_channel()
    if ep.get("status") != "rendered" and not args.dry_run:
        sys.exit(f"episode status is {ep.get('status')!r}; only 'rendered' episodes that passed QA can be published")
    errors, _ = lint.lint_episode(ep, channel)
    if errors:
        sys.exit("lint errors; refusing to publish:\n" + "\n".join(errors))
    video = episode_output_dir(ep["id"]) / "final.mp4"
    if not video.exists() and not args.dry_run:
        sys.exit(f"missing {video}")
    if channel["publishing"]["provider"] == "none":
        print("publishing.provider is 'none'; package is in output/ for manual posting")
        return 0
    try:
        result = publish.publish(ep, channel, video, dry_run=args.dry_run, post_now=args.now)
    except publish.PublishError as e:
        print(f"publish failed: {e}")
        return 1
    if args.dry_run:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    ep["publish"] = result
    ep["status"] = "scheduled" if result.get("scheduled_date") else "published"
    _save_episode(ep)
    backlog.set_status(ep["topic_id"], "done", ep["id"])
    print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
    return 0


def cmd_mark(args) -> int:
    print(backlog.set_status(args.topic_id, args.status))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="shorts", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("next").set_defaults(fn=cmd_next)
    s = sub.add_parser("new")
    s.add_argument("topic_id")
    s.add_argument("--date")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_new)
    for name, fn in (("lint", cmd_lint), ("prompts", cmd_prompts), ("fetch", cmd_fetch)):
        s = sub.add_parser(name)
        s.add_argument("episode_id")
        s.set_defaults(fn=fn)
    s = sub.add_parser("render")
    s.add_argument("episode_id")
    s.add_argument("--skip-lint", action="store_true")
    s.set_defaults(fn=cmd_render)
    s = sub.add_parser("publish")
    s.add_argument("episode_id")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--now", action="store_true", help="post immediately instead of the next configured slot")
    s.set_defaults(fn=cmd_publish)
    s = sub.add_parser("mark")
    s.add_argument("topic_id")
    s.add_argument("status", choices=["todo", "in_progress", "done", "skipped"])
    s.set_defaults(fn=cmd_mark)
    args = p.parse_args(argv)
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
