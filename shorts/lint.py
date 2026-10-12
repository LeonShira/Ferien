"""Compliance and quality gate for an episode script.

Errors block rendering and publishing; warnings are printed for the agent to fix
when it can. The rules encode three things:

* platform monetisation policy: education, not advice; no AI "advisor" persona;
  no templated, interchangeable scripts (YouTube "inauthentic content");
* length: TikTok Creator Rewards needs > 60 s, retention drops after ~90 s;
* factual hygiene: every number is either recomputed by `finmath` or sourced.
"""

from __future__ import annotations

import re

from . import finmath, visuals

# Phrases that turn education into advice, hype or a fake credential.
ADVICE_PATTERNS = [
    (r"\byou (should|must|need to) (buy|sell|invest in|put (your|all your) (money|savings) (in|into))\b", "personalised buy/sell instruction"),
    (r"\b(buy|sell|short) (this|these|it) (now|today)\b", "buy/sell call to action"),
    (r"\b(i|we) (recommend|suggest) (buying|selling|investing in)\b", "recommendation to buy or sell"),
    (r"\bguaranteed? (returns?|profits?|income|gains?)\b", "guaranteed returns"),
    (r"\b(risk[- ]free|can'?t lose|no[- ]risk|zero risk) (investment|returns?|profit|money|bet)\b", "risk-free claim"),
    (r"\bget rich (quick|fast)\b(?!.*\b(scheme|scam|myth|promise)s?\b)", "get-rich-quick framing"),
    (r"\b(to the moon|100x|10x your|1000x|next bitcoin|next tesla)\b", "hype language"),
    (r"\bprice target\b", "price target"),
    (r"\b(will|is going to) (double|triple|explode|skyrocket|crash) (by|in|this|next)\b", "price prediction"),
    (r"\bas (a|your) (financial advisor|financial adviser|certified|licensed|cfa|cfp)\b", "claimed credential"),
    (r"\b(i'?m|i am) (a|your) (financial advisor|financial adviser|banker|broker)\b", "claimed credential"),
    (r"(?<![\w])\$[A-Z]{2,5}\b", "ticker symbol"),
    (r"\b(nyse|nasdaq|xetra|lse)\s*:\s*[A-Z]{1,5}\b", "exchange ticker"),
    # German
    (r"\b(du solltest|ihr solltet|sie sollten) (jetzt )?(kaufen|verkaufen|investieren)\b", "Kauf-/Verkaufsempfehlung"),
    (r"\bgarantierte? (rendite|gewinne?|einnahmen)\b", "garantierte Rendite"),
    (r"\b(kauft|kauf|verkauft|verkauf) (jetzt|sofort|heute)\b", "Kauf-/Verkaufsaufruf"),
    (r"\b(kursziel|anlageempfehlung)\b", "Kursziel/Anlageempfehlung"),
    (r"\bschnell reich\b(?!.*\b(masche|betrug|mythos|versprechen)\b)", "schnell-reich-Framing"),
]

# Words in an image prompt that make generators draw garbled text or real IP.
VISUAL_BANNED = [
    (r"\b(logo|logos|watermark|brand name|trademark)\b", "logos/brands"),
    (r"\b(text|caption|headline|label|lettering|words?|numbers?|digits?) (that )?(says?|reading|reads|showing)\b", "rendered text"),
    (r"[\"“”]\s*[\w$€%][^\"“”]*[\"“”]", "quoted text to render"),
    (r"\b(elon musk|warren buffett|jeff bezos|bill gates|trump|biden|powell|lagarde|scholz|merz)\b", "real person"),
    (r"\b(tesla|google|microsoft|nvidia|mastercard|paypal|sparkasse|deutsche bank|coinbase|robinhood|blackrock|vanguard)\b", "real brand"),
]

FILLER = re.compile(r"\b(basically|literally|actually|in this video|let'?s dive in|without further ado|smash that like|don'?t forget to subscribe)\b", re.I)
WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9'’%.,€$-]*")


def words(text: str) -> list[str]:
    return WORD.findall(text or "")


def narration(episode: dict) -> str:
    return " ".join(s.get("narration", "") for s in episode.get("scenes", []))


def estimate_seconds(episode: dict, channel: dict) -> float:
    prod = channel["production"]
    n_words = len(words(narration(episode)))
    n_scenes = len(episode.get("scenes", []))
    return (n_words / prod["words_per_second"]
            + n_scenes * prod["scene_pad_seconds"] + prod["end_hold_seconds"])


def _ngrams(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def _first_sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]


def lint_episode(episode: dict, channel: dict, previous: list[dict] | None = None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    prod = channel["production"]
    scenes = episode.get("scenes") or []

    for key in ("id", "series", "topic_id", "language", "scenes", "metadata"):
        if not episode.get(key):
            errors.append(f"missing field: {key}")
    if errors:
        return errors, warnings

    if not 6 <= len(scenes) <= 16:
        errors.append(f"{len(scenes)} scenes; use 6-16 (a new visual every 4-10 s keeps retention up)")
    types = [s.get("visual", {}).get("type") for s in scenes if isinstance(s.get("visual"), dict)]
    if len(set(types)) < 3:
        errors.append(f"only {len(set(types))} distinct visual types; use at least 3 so the video doesn't feel templated")
    for a, b in zip(types, types[1:]):
        if a == b and a not in ("image", "custom"):
            warnings.append(f"two {a} scenes in a row; alternate visual types")
            break

    # Advice / hype language anywhere the viewer will read or hear it.
    meta = episode["metadata"]
    spoken_and_shown = [("scene %d narration" % (i + 1), s.get("narration", "")) for i, s in enumerate(scenes)]
    spoken_and_shown += [("scene %d visual" % (i + 1), text) for i, s in enumerate(scenes)
                         if isinstance(s.get("visual"), dict) for text in visuals.text_of(s["visual"])]
    spoken_and_shown += [("hook_text", episode.get("hook_text", "")), ("title", meta.get("title", "")),
                         ("caption", meta.get("caption", "")), ("description", meta.get("description", ""))]
    for where, text in spoken_and_shown:
        for pattern, label in ADVICE_PATTERNS:
            flags = 0 if label in ("ticker symbol", "exchange ticker") else re.I
            if re.search(pattern, text or "", flags):
                errors.append(f"{where}: {label}: {text!r}")

    # Per-scene narration shape.
    for i, s in enumerate(scenes, 1):
        n = len(words(s.get("narration", "")))
        if n == 0:
            errors.append(f"scene {i}: empty narration")
        elif n > 30:
            errors.append(f"scene {i}: {n} words; split it (max 30 words per scene so visuals keep changing)")
        visual = s.get("visual")
        errors += [f"scene {i}: {p}" for p in visuals.validate(visual)]
        prompt = visual.get("prompt", "") if isinstance(visual, dict) else ""
        for pattern, label in VISUAL_BANNED:
            if re.search(pattern, prompt or "", re.I):
                errors.append(f"scene {i} image prompt: {label} (generators garble text; real brands and people are off-limits)")
        if FILLER.search(s.get("narration", "")):
            warnings.append(f"scene {i}: filler phrase: {FILLER.search(s['narration']).group(0)!r}")

    # Hook: the first spoken sentence must land fast.
    hook = _first_sentence(scenes[0].get("narration", ""))
    if len(words(hook)) > 14:
        errors.append(f"hook is {len(words(hook))} words; the first sentence must be <= 14 words")
    hook_text = episode.get("hook_text", "")
    if not hook_text:
        errors.append("missing hook_text (on-screen title for the first seconds)")
    elif len(words(hook_text)) > 8:
        errors.append("hook_text must be <= 8 words")

    # Length window.
    est = estimate_seconds(episode, channel)
    if est < prod["min_seconds"] + 2:
        errors.append(f"estimated {est:.0f} s; need >= {prod['min_seconds'] + 2} s so the final cut clears "
                      f"{prod['min_seconds']} s (add a concrete example, not filler)")
    if est > prod["max_seconds"]:
        errors.append(f"estimated {est:.0f} s; keep it <= {prod['max_seconds']} s")

    # Repetition inside the script.
    tokens = [w.lower().strip(".,!?") for w in words(narration(episode))]
    seen: dict[tuple[str, ...], int] = {}
    for gram in (tuple(tokens[i:i + 5]) for i in range(len(tokens) - 4)):
        seen[gram] = seen.get(gram, 0) + 1
    repeats = [" ".join(g) for g, c in seen.items() if c > 1]
    if repeats:
        warnings.append(f"repeated 5-word phrases: {repeats[:3]}")

    # Templated-channel guard: compare against recent episodes.
    for prev in previous or []:
        if prev.get("id") == episode.get("id"):
            continue
        prev_hook = _first_sentence((prev.get("scenes") or [{}])[0].get("narration", ""))
        a = set(w.lower() for w in words(hook))
        b = set(w.lower() for w in words(prev_hook))
        if a and b and len(a & b) / len(a | b) > 0.6:
            errors.append(f"hook is near-identical to {prev['id']}; vary the opening (YouTube flags templated channels)")
        prev_tokens = [w.lower().strip(".,!?") for w in words(narration(prev))]
        shared = _ngrams(tokens, 6) & _ngrams(prev_tokens, 6)
        if len(shared) > 3:
            warnings.append(f"shares {len(shared)} six-word phrases with {prev['id']}; rephrase")

    # Placeholders from the template must not survive.
    if "TODO" in repr(episode):
        errors.append("template placeholders (TODO) are still in the episode")

    # Claims: every number is either recomputed or sourced.
    claims = episode.get("claims") or []
    has_numbers = bool(re.search(r"\d", narration(episode)))
    if has_numbers and not claims:
        errors.append("narration contains numbers but no claims are declared")
    for i, c in enumerate(claims, 1):
        if c.get("check"):
            ok, _, msg = finmath.verify_claim(c["check"])
            if not ok:
                errors.append(f"claim {i} failed recomputation: {msg}")
        elif not c.get("source", "").startswith("http"):
            errors.append(f"claim {i} ({c.get('statement', '')[:50]!r}) needs a `check` or an http(s) `source`")

    # Metadata.
    title = meta.get("title", "")
    if not title:
        errors.append("metadata.title missing (YouTube requires it)")
    elif len(title) > 90:
        errors.append(f"metadata.title is {len(title)} chars; keep <= 90 so it isn't truncated")
    caption = meta.get("caption", "")
    if not caption:
        errors.append("metadata.caption missing (TikTok caption)")
    elif len(caption) > 2000:
        errors.append("metadata.caption exceeds TikTok's limit")
    tags = meta.get("hashtags") or []
    if not 3 <= len(tags) <= 6:
        warnings.append(f"{len(tags)} hashtags; 3-6 targeted tags beat a wall of tags")
    if any(" " in t for t in tags):
        errors.append("hashtags may not contain spaces")

    return errors, warnings
