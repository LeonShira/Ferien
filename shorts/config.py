"""Paths and channel configuration."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "content"
EPISODES_DIR = CONTENT_DIR / "episodes"
OUTPUT_DIR = ROOT / "output"
TOPICS_FILE = CONTENT_DIR / "topics.yaml"
SERIES_FILE = CONTENT_DIR / "series.yaml"
CHANNEL_FILE = ROOT / "channel.yaml"


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=100)
    os.replace(tmp, path)


def load_channel(path: Path | None = None) -> dict:
    return load_yaml(path or CHANNEL_FILE)


def episode_path(episode_id: str) -> Path:
    return EPISODES_DIR / f"{episode_id}.yaml"


def episode_output_dir(episode_id: str) -> Path:
    return OUTPUT_DIR / episode_id
