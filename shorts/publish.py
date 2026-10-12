"""Publish a finished master to TikTok and YouTube Shorts through Upload-Post.

Upload-Post (https://docs.upload-post.com) holds the platform OAuth tokens and
audited API access, so one multipart request posts to both platforms publicly.
Credentials come from the environment: UPLOAD_POST_API_KEY (required) and
UPLOAD_POST_USER (optional; auto-detected when the account has one profile).
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

API = "https://api.upload-post.com/api"


class PublishError(RuntimeError):
    pass


def compose_texts(episode: dict, channel: dict) -> dict:
    """Per-platform caption/title/description built from episode metadata."""
    meta = episode["metadata"]
    tags = ["#" + t.lstrip("#") for t in meta.get("hashtags", [])]
    disclaimer = channel["channel"]["disclaimer"]
    caption = meta["caption"].strip()
    tiktok = f"{caption}\n\n{' '.join(tags)}\n{disclaimer}".strip()
    sources = [c["source"] for c in episode.get("claims", []) if c.get("source")]
    sources += [s for s in episode.get("sources", []) if s not in sources]
    desc = [meta.get("description", "").strip() or caption]
    if sources:
        desc.append("Sources:\n" + "\n".join(f"- {s}" for s in sources))
    desc.append(disclaimer)
    desc.append("Script written with AI assistance and checked before publishing; visuals and voice are AI-generated.")
    desc.append(" ".join(tags + ["#Shorts"]))
    title = meta["title"].strip()
    return {
        "tiktok_title": tiktok[:2200],
        "youtube_title": title[:100],
        "youtube_description": "\n\n".join(d for d in desc if d)[:4900],
        "tags": [t.lstrip("#") for t in meta.get("tags", meta.get("hashtags", []))][:15],
    }


def next_slot(channel: dict, now: datetime | None = None) -> str | None:
    """Next configured local posting time as ISO-8601, or None for 'post now'."""
    pub = channel["publishing"]
    if not pub.get("post_time"):
        return None
    tz = ZoneInfo(pub.get("timezone", "UTC"))
    now = now or datetime.now(tz)
    hh, mm = (int(x) for x in pub["post_time"].split(":"))
    slot = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if slot <= now + timedelta(minutes=10):
        slot += timedelta(days=1)
    return slot.isoformat()


class UploadPost:
    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self.api_key = api_key or os.environ.get("UPLOAD_POST_API_KEY", "")
        if not self.api_key:
            raise PublishError("UPLOAD_POST_API_KEY is not set (add it to the environment's secrets)")
        self.http = session or requests.Session()
        self.http.headers["Authorization"] = f"Apikey {self.api_key}"

    def _get(self, path: str, **params) -> dict:
        r = self.http.get(f"{API}{path}", params=params, timeout=60)
        if r.status_code >= 400:
            raise PublishError(f"GET {path} -> {r.status_code}: {r.text[:500]}")
        return r.json()

    def me(self) -> dict:
        return self._get("/uploadposts/me")

    def profiles(self) -> list[dict]:
        return self._get("/uploadposts/users").get("profiles", [])

    def resolve_user(self, configured: str = "") -> str:
        configured = configured or os.environ.get("UPLOAD_POST_USER", "")
        if configured:
            return configured
        profiles = self.profiles()
        if len(profiles) == 1:
            return profiles[0]["username"]
        names = [p.get("username") for p in profiles]
        raise PublishError(f"set publishing.upload_post_user; account has profiles {names}")

    def connected_platforms(self, user: str) -> set[str]:
        for p in self.profiles():
            if p.get("username") == user:
                accounts = p.get("social_accounts") or {}
                return {k for k, v in accounts.items() if v and not (isinstance(v, dict) and v.get("reauth_required"))}
        return set()

    def upload(self, video: Path, fields: list[tuple[str, str]]) -> dict:
        with open(video, "rb") as f:
            r = self.http.post(f"{API}/upload", data=fields, files={"video": (video.name, f, "video/mp4")},
                               timeout=900)
        if r.status_code >= 400:
            raise PublishError(f"upload -> {r.status_code}: {r.text[:800]}")
        return r.json()

    def status(self, request_id: str | None = None, job_id: str | None = None) -> dict:
        params = {"request_id": request_id} if request_id else {"job_id": job_id}
        return self._get("/uploadposts/status", **params)

    def wait(self, request_id: str, timeout: int = 900) -> dict:
        deadline = time.time() + timeout
        while True:
            st = self.status(request_id=request_id)
            if st.get("status") == "completed" or time.time() > deadline:
                return st
            time.sleep(10)


def build_fields(episode: dict, channel: dict, user: str, platforms: list[str],
                 scheduled: str | None) -> list[tuple[str, str]]:
    pub = channel["publishing"]
    texts = compose_texts(episode, channel)
    fields: list[tuple[str, str]] = [("user", user), ("title", texts["youtube_title"])]
    fields += [("platform[]", p) for p in platforms]
    if "tiktok" in platforms:
        tt = pub["tiktok"]
        fields += [("tiktok_title", texts["tiktok_title"]),
                   ("post_mode", tt.get("post_mode", "DIRECT_POST")),
                   ("privacy_level", tt.get("privacy_level", "PUBLIC_TO_EVERYONE")),
                   ("is_aigc", str(bool(tt.get("is_aigc", True))).lower()),
                   ("cover_timestamp", "1000")]
    if "youtube" in platforms:
        yt = pub["youtube"]
        fields += [("youtube_title", texts["youtube_title"]),
                   ("youtube_description", texts["youtube_description"]),
                   ("privacyStatus", yt.get("privacy_status", "public")),
                   ("categoryId", str(yt.get("category_id", "27"))),
                   ("containsSyntheticMedia", str(bool(yt.get("contains_synthetic_media", True))).lower()),
                   ("selfDeclaredMadeForKids", str(bool(yt.get("made_for_kids", False))).lower())]
        fields += [("tags[]", t) for t in texts["tags"]]
    if scheduled:
        fields += [("scheduled_date", scheduled), ("timezone", pub.get("timezone", "UTC"))]
    else:
        fields.append(("async_upload", "true"))
    return fields


def publish(episode: dict, channel: dict, video: Path, dry_run: bool = False,
            post_now: bool = False, client: UploadPost | None = None) -> dict:
    pub = channel["publishing"]
    wanted = [p for p in ("tiktok", "youtube") if pub.get(p, {}).get("enabled")]
    if not wanted:
        raise PublishError("no platform enabled in channel.yaml publishing")
    scheduled = None if post_now else next_slot(channel)
    if dry_run:
        fields = build_fields(episode, channel, user="<profile>", platforms=wanted, scheduled=scheduled)
        return {"dry_run": True, "platforms": wanted, "scheduled_date": scheduled, "fields": fields}

    client = client or UploadPost()
    user = client.resolve_user(pub.get("upload_post_user", ""))
    connected = client.connected_platforms(user)
    platforms = [p for p in wanted if p in connected] if connected else wanted
    missing = sorted(set(wanted) - set(platforms))
    if not platforms:
        raise PublishError(f"none of {wanted} is connected on Upload-Post profile {user!r}")
    fields = build_fields(episode, channel, user, platforms, scheduled)
    response = client.upload(video, fields)
    result = {"provider": "upload_post", "user": user, "platforms": platforms, "skipped_not_connected": missing,
              "scheduled_date": scheduled, "response": response,
              "submitted_at": datetime.now(ZoneInfo("UTC")).isoformat()}
    if response.get("request_id") and not scheduled:
        result["final_status"] = client.wait(response["request_id"])
    return result
