# Daily production runbook

This is the checklist the scheduled agent follows to make and publish one video.
Every step is a command or an MCP tool call. Stop at any failed gate and report it.

## 0. Preflight

```bash
cd video && npm ci --no-audit --no-fund && cd ..   # skip if node_modules exists
python -m shorts doctor
python -m shorts status
```

- Higgsfield `balance`: if credits < `budget.min_balance_reserve` + 10, stop and report
  "Higgsfield credits low" (do not buy anything).
- If `status` shows `budget.max_unpublished_buffer` or more episodes waiting in `rendered`,
  skip production. Try `publish` for the oldest instead, then report.

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
- 9-13 scenes, one sentence or two per scene, 165-200 words total (~65-80 s).
- First sentence <= 14 words and it states the payoff. `hook_text` <= 8 words.
- Narration: plain spoken English with figures as digits ("$5,000", "24%"), no filler.
- Explain, never advise. Use "here's how it works" and "the math shows", never "you should buy, sell or invest".
  Specific products, tickers, coins and price predictions are off-limits.
- Visuals: see `docs/VISUALS.md`. Use `calc` for every number on screen.
- `claims`: one per number or fact in the narration. A `check` recomputes it; otherwise give a `source` URL.
- `metadata`: YouTube `title` <= 90 chars (curiosity, no clickbait lies), TikTok `caption`
  1-2 sentences, `description` one paragraph that states the assumptions, 3-6 `hashtags`, `tags`.

```bash
python -m shorts lint <id>     # must print PASS; fix every ERROR, fix WARNs when sensible
```

## 3. Narration (Higgsfield, ~0.45 credits per line)

```bash
python -m shorts prompts <id>  # exact generate_audio params for every line
```

- Submit `audio_requests` with `generate_audio_batch` **in batches of 3** (bigger batches hit 429 rate limits),
  then `jobs_wait`. Resubmit any `submission_failed` item in the next batch.
- Never change `voice_id`, model or variant: the channel voice is locked in `channel.yaml`.
- Optional `image` scenes: submit `image_requests` with `generate_image_batch` (max 3 per episode).
- Write each result into `assets.scenes[i]` as `audio_url` / `image_url` (with job ids), in scene order.

```bash
python -m shorts fetch <id>
```

## 4. Render and check

```bash
python -m shorts render <id>   # Remotion motion graphics + narration mix + QA, ~3-6 min
```

- QA must pass (1080x1920, 30 fps, > 61 s, audible). On failure fix the cause and re-render.
- Look at `output/<id>/poster.jpg` and a few frames
  (`ffmpeg -ss 12 -i output/<id>/final.mp4 -frames:v 1 output/<id>/check.jpg`, then Read the image).
  Fix overflowing text, overlapping elements or unreadable charts before publishing.

## 5. Publish

```bash
python -m shorts publish <id> --dry-run   # inspect captions and settings
python -m shorts publish <id>             # schedules for publishing.post_time on TikTok + YouTube
```

If `UPLOAD_POST_API_KEY` is not set, skip publishing: the episode stays `rendered` and the
package (`final.mp4`, `post.txt`) waits for the next run that has a key. Also upload `final.mp4`
to Higgsfield (`media_upload` -> curl PUT -> `media_confirm`) and record the hosted URL in
`assets.final_url` so the video can be reviewed or posted from anywhere.

## 6. Record and report

- Note the credits spent (balance before minus after) in the episode as `cost_credits`.
- Commit `content/` changes with a message like `episode: <id>` and push.
- Final message: topic, title, length, credits, publish status (scheduled time or why not),
  and anything that needs a human.

## Hard rules

- Never publish an episode that fails lint or QA.
- Never invent a number or a source. If you can't verify it, cut it.
- Never present the narrator as a financial professional or give personal advice.
- Never post twice for the same topic; check `status` and the episode file first.
- Never buy credits, change plans, or change publishing settings on your own.
