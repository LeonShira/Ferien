# Architecture

```
                   ┌──────────────── Claude Routine: one fresh cloud session per day ─────────────────┐
                   │                                                                                    │
 content/          │  1 pick topic      python -m shorts next / new                                     │
  topics.yaml ────►│  2 research+write  Claude writes content/episodes/<id>.yaml (script, visuals,      │
  series.yaml      │                    claims, metadata)                                               │
                   │  3 gate            python -m shorts lint   (advice language, length, facts, variety)│
                   │  4 narration       python -m shorts voice: Kokoro on the session's CPU, then a     │
                   │                    Whisper "listening check" that must hear exactly the script     │
                   │  5 render          python -m shorts render                                         │
                   │                     ├─ ffmpeg: measure takes, build narration track               │
                   │                     ├─ Remotion (video/): motion graphics from code, captions      │
                   │                     └─ ffmpeg: mix, -14 LUFS, mux, QA (1080x1920, 30 fps, >61 s)   │
                   │  6 publish         python -m shorts publish → Upload-Post API                      │
                   │                     ├─ TikTok  (Content Posting API, AI label on)                  │
                   │                     └─ YouTube Shorts (Education, synthetic-media disclosure)      │
                   │  7 record          commit episode YAML (status, cost, publish ids), push           │
                   └────────────────────────────────────────────────────────────────────────────────────┘
```

## Why this shape

| Decision | Reason |
|---|---|
| Motion graphics drawn by code (Remotion) instead of generated video | No generation credits, exact numbers and text, renders in minutes, runs on the Claude plan you already pay for. |
| Local voice (Kokoro-82M, Apache-2.0) | Free, ~1 min per video on CPU, and the same voice every time. Generating lines separately on a cloud TTS gave audibly different deliveries. Qwen3-TTS and Chatterbox were benchmarked too: both run 8-17x slower than real time on this CPU (samples in `output/voice-samples/`). ElevenLabs direct is a one-line switch (`tts.provider`) if you want the top quality tier. |
| Listening check (faster-whisper) | No one listens to an unattended run. Every take is transcribed and must match the script (it caught "$5,000" being read as "dollar five thousand"). The word timestamps also sync the captions exactly. |
| Every on-screen number is a `calc` | Charts and counters are computed by `shorts/finmath.py`, and lint recomputes every spoken number, so a typo can't become a wrong figure. |
| Upload-Post for posting | One API for TikTok and YouTube. It holds audited platform access, so videos post publicly. A self-made YouTube API app stays private-only until Google audits it, and TikTok works the same way. |
| > 61 s, <= 90 s | TikTok Creator Rewards only pays for videos over one minute; Shorts allow up to 3 minutes. |
| Faceless narrator, six rotating series, lint against repetition | YouTube's July 2026 monetisation guidance excludes templated/repetitive content and "AI personas giving advice on finance". The channel explains, never advises, and has no fake expert on camera. |
| AI labels on (`is_aigc`, `containsSyntheticMedia`) | Both platforms require disclosure of AI-generated media. Unlabelled AI content risks strikes and demonetisation. |

## Files

| Path | What it is |
|---|---|
| `channel.yaml` | Channel identity, voice, render and publishing settings, budget guards |
| `content/series.yaml` | The six formats: beats, colours, preferred visuals, rules |
| `content/topics.yaml` | Topic backlog with priorities and research notes |
| `content/episodes/*.yaml` | One file per video: script, visuals, claims, metadata, assets, render and publish results |
| `shorts/` | Python CLI: lint, finmath, visuals, captions, render, publish, backlog |
| `video/` | Remotion project: scene library (`src/scenes`), overlays, per-episode custom scenes |
| `output/<id>/` | Working files and `final.mp4` (git-ignored) |
| `docs/RUNBOOK.md` | The step-by-step the daily agent follows |
| `docs/VISUALS.md` | Scene vocabulary for script writers |

## Costs per video

| Item | Cost |
|---|---|
| Script, research, motion design, render | included in the Claude Max plan (cloud session) |
| Narration | free (local Kokoro); or ElevenLabs Starter ~$5-6/mo for ~30 videos |
| Optional illustrated stills | ~1.25 Higgsfield credits each (history/scam episodes, max 3) |
| Posting | Upload-Post Basic, $24/mo or $16/mo billed annually: unlimited posts, includes TikTok |

## Extending

- **Another language:** Kokoro has no German voice. For German, switch `tts.provider` to `elevenlabs`
  (multilingual) or add Qwen3-TTS (supports German; slow on CPU). Set `channel.language: de`.
  Number formats switch automatically. Run a separate channel by copying `channel.yaml`.
- **More platforms:** Upload-Post also posts Instagram Reels. Add it to `shorts/publish.py`'s platform list.
- **Analytics loop:** Upload-Post's `/analytics/{profile}` endpoint can feed view counts back into
  topic priorities (planned; not built yet).
- **Voice:** listen to `output/voice-samples/` and set `tts.kokoro.voice`, or switch providers.
