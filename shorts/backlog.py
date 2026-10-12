"""Topic backlog: pick the next topic with series rotation."""

from __future__ import annotations

from datetime import date

from .config import EPISODES_DIR, SERIES_FILE, TOPICS_FILE, load_yaml, save_yaml


def load_topics() -> list[dict]:
    return load_yaml(TOPICS_FILE)["topics"]


def save_topics(topics: list[dict]) -> None:
    save_yaml(TOPICS_FILE, {"topics": topics})


def load_series() -> dict:
    return {s["id"]: s for s in load_yaml(SERIES_FILE)["series"]}


def load_episodes() -> list[dict]:
    if not EPISODES_DIR.exists():
        return []
    eps = [load_yaml(p) for p in sorted(EPISODES_DIR.glob("*.yaml"))]
    return [e for e in eps if e]


def next_topic(topics: list[dict] | None = None, episodes: list[dict] | None = None) -> dict | None:
    """Highest-priority open topic whose series differs from the last two episodes."""
    topics = topics if topics is not None else load_topics()
    episodes = episodes if episodes is not None else load_episodes()
    recent = [e.get("series") for e in sorted(episodes, key=lambda e: e.get("id", ""))[-2:]]
    open_topics = [t for t in topics if t.get("status", "todo") == "todo"]
    if not open_topics:
        return None
    open_topics.sort(key=lambda t: -int(t.get("priority", 2)))
    for t in open_topics:
        if t["series"] not in recent:
            return t
    return open_topics[0]


def set_status(topic_id: str, status: str, episode_id: str | None = None) -> dict:
    topics = load_topics()
    for t in topics:
        if t["id"] == topic_id:
            t["status"] = status
            if episode_id:
                t["episode"] = episode_id
            save_topics(topics)
            return t
    raise KeyError(f"unknown topic {topic_id}")


def new_episode_id(topic_id: str, day: date | None = None) -> str:
    return f"{(day or date.today()).isoformat()}-{topic_id}"
