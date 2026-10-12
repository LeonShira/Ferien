# Daily production runbook

This is the checklist the scheduled agent follows to make and publish one video.
Every step is a command or an MCP tool call. Stop at any failed gate and report it.

## 0. Preflight

```bash
cd video && npm ci --no-audit --no-fund && cd ..   # skip if node_modules exists
python -m shorts doctor
python -m shorts status
```

- Only if you plan `image` scenes: check the Higgsfield `balance`; if credits are below
  `budget.min_balance_reserve` + 10, write the episode without `image` scenes (do not buy anything).
- If `budget.max_unpublished_buffer` or more episodes are waiting in `rendered`, skip steps 1-4
  (don't spend credits) and go straight to step 5.

## 1. Pick and research the topic

```bash
python -m shorts next          # topic + its series definition (beats, visuals, rules)
python -m shorts new <topic_id>
```

Research the topic on the web. Every factual claim needs an http(s) source, and the
source must say what the script says. Prefer official, academic, central-bank or
regulator sources. If the evidence is weak or disputed, pick the next topic
(`python -m shorts mark <id> skipped`) instead of guessing.

## 2. Write the episode

Edit `content/episodes/<id>.yaml` (format: the pilot `2026-10-12-credit-card-minimum-trap.yaml`).

- Follow the series `beats`, in your own words. Change the hook pattern from the last episodes.
- 9-13 scenes, one or two sentences per scene, 160-190 words total (~65-75 s at the voice's ~2.7 words/s).
- First sentence <= 14 words and it states the payoff. `hook_text` <= 8 words.
- Narration: write for the ear (docs/VOICE.md). Name the currency once, then bare numbers ("150 a month");
  at most 2 figures per line; round when precision doesn't matter; contractions; no filler.
- Explain, never advise. Use "here's how it works" and "the math shows", never "you should buy, sell or invest".
  Specific products, tickers, coins and price predictions are off-limits.
- Visuals: see `docs/VISUALS.md`. Use `calc` for every number on screen.
- `claims`: one per number or fact in the narration. A `check` recomputes it; otherwise give a `source` URL.
- `metadata`: YouTube `title` <= 90 chars (curiosity, no clickbait lies), TikTok `caption`
  1-2 sentences, `description` one paragraph that states the assumptions, 3-6 `hashtags`, `tags`.

```bash
python -m shorts lint <id>     # must print PASS; fix every ERROR, fix WARNs when sensible
```

## 3. Narration (local voice, free)

```bash
python -m shorts voice <id>    # narrates every line in the channel voice, then runs the listening check
```

- The voice is Kokoro, running on this machine: same voice every time, no credits, no account.
- `LISTEN PASS` is a gate. Every line is transcribed and compared with the script; a failed line
  shows what was actually heard. Fix the wording, or add `say:` with a respelling (docs/VOICE.md),
  and run `voice` again.
- Optional `image` scenes (max 3 per episode, ~1.25 credits each): run `python -m shorts prompts <id>`,
  submit the `image_requests` with Higgsfield `generate_image_batch` in batches of 3, `jobs_wait`,
  write each result's URL into `assets.scenes[i].image_url` (scene order), then `python -m shorts fetch <id>`.

## 4. Render and check

```bash
python -m shorts render <id>   # Remotion motion graphics + narration mix + QA, ~3-6 min
```

- QA must pass (1080x1920, 30 fps, > 61 s, audible). On failure fix the cause and re-render.
- Look at `output/<id>/poster.jpg` and a few frames
  (`ffmpeg -ss 12 -i output/<id>/final.mp4 -frames:v 1 output/<id>/check.jpg`, then Read the image).
  Fix overflowing text, overlapping elements or unreadable charts before publishing.

## 5. Publish (exactly one post per run)

Publish the **oldest** episode in `rendered` (`python -m shorts status`), which is today's
only when nothing older is waiting. One post per day keeps the cadence steady.

Each run starts in a fresh container, so an older episode's `output/<id>/final.mp4` won't exist.
Rebuild it first; it costs no credits (the voice is local and any stills' URLs are stored in the episode):
`python -m shorts voice <id> && python -m shorts fetch <id> && python -m shorts render <id>`.

```bash
python -m shorts publish <id> --dry-run   # inspect captions and settings
python -m shorts publish <id>             # schedules for publishing.post_time on TikTok + YouTube
```

If `UPLOAD_POST_API_KEY` is not set, skip publishing: the episode stays `rendered` and the
package (`final.mp4`, `post.txt`) waits for the next run that has a key. Also upload `final.mp4`
to Higgsfield (`media_upload` -> curl PUT -> `media_confirm`) and record the hosted URL in
`assets.final_url` so the video can be reviewed or posted from anywhere.

## 6. Record and report

- If you generated stills, note the credits spent in the episode as `cost_credits`.
- Commit `content/` changes with a message like `episode: <id>` and push.
- Final message: topic, title, length, credits, publish status (scheduled time or why not),
  and anything that needs a human.

## Hard rules

- Never publish an episode that fails lint or QA.
- Never invent a number or a source. If you can't verify it, cut it.
- Never present the narrator as a financial professional or give personal advice.
- Never post twice for the same topic; check `status` and the episode file first.
- Never buy credits, change plans, or change publishing settings on your own.
