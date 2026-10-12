# Money, Explained: automated finance-education shorts

A pipeline that researches, writes, animates, narrates and publishes 60-90 second
vertical videos to **TikTok** and **YouTube Shorts**, once a day, run by a scheduled
Claude session.

- **Motion graphics drawn from code** (Remotion): counters, charts, comparisons, myth/fact
  reveals, timelines. No video-generation credits, and every number on screen is computed.
- **Narration** by a local open-source voice (Kokoro), free and identical every time, checked by a
  speech-recognition pass that must hear exactly the script. ElevenLabs is a one-line switch.
- **Compliance gate** before every render: education not advice, every number recomputed or
  sourced, length > 61 s for TikTok Creator Rewards, variety checks against templated content.
- **Publishing** through Upload-Post, with AI-content labels on both platforms.

```bash
python -m shorts status                       # backlog and recent episodes
python -m shorts lint <episode>               # compliance + fact checks
python -m shorts render <episode>             # output/<episode>/final.mp4
python -m shorts publish <episode> --dry-run  # see exactly what would be posted
python -m pytest tests                        # 25 tests
```

| Doc | For |
|---|---|
| [docs/SETUP.md](docs/SETUP.md) | The few steps only you can do (accounts, Upload-Post key) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How it fits together, costs, design decisions |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | What the daily agent does, step by step |
| [docs/VISUALS.md](docs/VISUALS.md) | Scene types and computed numbers for script writing |
| [docs/VOICE.md](docs/VOICE.md) | Writing narration that sounds like a person |
