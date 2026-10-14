# Growth and monetisation plan

## The honest money picture

Platform payouts only start after eligibility, and both bars are high for a new channel:

| Program | Bar | Pays (finance niche, estimates) |
|---|---|---|
| TikTok Creator Rewards | 10k followers, 100k views / 30 days, videos > 1 min | ~$1.50-3.00 per 1,000 qualified views from US viewers; ~$0.40-1.00 from German/EU viewers |
| YouTube Shorts (YPP) | 1k subscribers + 10M Shorts views in 90 days | ~$0.15-0.40 per 1,000 views |
| YouTube long-form (YPP) | 1k subscribers + 4,000 watch hours | ~$10-25 per 1,000 views |

So **month 1 earns about nothing from the platforms**: the month buys data and an audience.
Rates are third-party estimates (sources below); real numbers come from your own analytics.

What 1 month of reach is worth once eligible, for scale:

| Reach | TikTok (US-heavy) | TikTok (EU-heavy) | YouTube Shorts |
|---|---|---|---|
| 500k views | $750-1,500 | $200-500 | $75-200 |
| 2M views | $3,000-6,000 | $800-2,000 | $300-800 |

## Revenue levers, in the order they become available

1. **Own digital product in the bio link** (from day 1). A "money math" spreadsheet
   (debt payoff, compound growth, inflation) built from `shorts/finmath.py`, sold for €9-19.
   It matches the content, isn't advice, and keeps most of the price. This is the only lever that
   can pay in month 1.
2. **Email list** (from day 1). Free weekly "one money idea" mail; it becomes the asset you own if
   a platform changes its rules.
3. **TikTok Creator Rewards** (at 10k followers). Videos must stay > 60 s; one tracker reports > 2 min
   videos earn ~45% more per view.
4. **Long-form YouTube** (when Shorts have an audience). Stitch related shorts into 8-12 minute
   explainers ("10 money myths, tested"). Long-form RPM is roughly 25-100x Shorts RPM and counts toward the
   4,000 watch hours.
5. **Sponsorships** (5-10k+ followers). Only categories that fit the no-advice line (budgeting
   tools, books, courses), always disclosed.

Avoid: affiliate links to brokers, crypto exchanges or specific investments. They conflict with
"education, not advice", draw platform restrictions on financial promotion and, in Germany, regulator
attention (BaFin's finfluencer guidance).

## "Shoot and forget": one workshop, one month on autopilot

```
Workshop (60-90 min, together)        Batch run (2-4 h, unattended)      30 days (nothing runs)      Day 30
───────────────────────────────       ──────────────────────────────     ──────────────────────      ──────
decide name, language, voice           write + voice + render 60 videos   Upload-Post publishes       report: views,
idea sprint: 100 ideas -> keep 60-70   every one through lint, listen,    2 per day at fixed times    follows, retention by
review 3 pilot videos, tune            QA gates                           (TikTok + YouTube Shorts)   series / hook / length
press go                               upload all 60 with publish dates                               -> plan month 2
```

Every video is uploaded to Upload-Post with its own publish date (it accepts dates up to a year
ahead), so nothing has to run during the month: no Routine, no session, no risk of a failed day.

### Run the month as an experiment

Sixty posts are enough to learn something if they vary on purpose:

| Variable | Split |
|---|---|
| Series | all six, about 10 each |
| Length | 45 at 65-80 s, 15 at ~2 min |
| Slot | 12:30 vs 19:00 (local) |
| Hook style | number-first vs question vs story |

The day-30 report ranks each variable by views per post, follower gain and watch-through,
and month 2 doubles down on the winners.

### Decisions for the workshop

- **Language and account region.** English reaches the bigger, better-paying audience. TikTok
  tends to show a new account's videos first to viewers in the account's own country, though.
  The free voice has no German; German narration would need ElevenLabs (~$5-6/mo).
- **Voice** from `output/voice-samples/` (default af_heart).
- **Name, handles, bio, and an Impressum page** if monetising from Germany.
- **Posting times** (default 12:30 and 19:00 Berlin).

### To build before the workshop (not built yet)

- `shorts plan-batch N`: picks N topics balanced across series and the experiment splits.
- `shorts schedule-batch`: books 2 slots per day and uploads every rendered video with its date.
- Parallel production: the batch split across several cloud sessions so 60 videos take hours, not
  a day.
- `shorts report`: day-30 analytics from Upload-Post, grouped by series, length, slot and hook.

## Running costs

About €20 a month: Upload-Post Basic (€13-19). The narration voice is free, and the Claude Max plan
you already have covers the writing. Higgsfield is only used for optional illustrations.

## Sources

- TikTok RPM, finance: https://ttcalculator.net/learn/finance-creators-earnings/
- TikTok RPM Q1 2026 (length effect): https://ttcalculator.net/blog/q1-2026-tiktok-rpm-report/
- Creator Rewards guide 2026: https://www.shortsync.app/resources/tiktok-creator-rewards-program-2026
- YouTube finance RPM: https://outlierkit.com/blog/youtube-rpm-finance-niche
- Shorts pay 2026: https://www.shortsync.app/resources/how-much-do-youtube-shorts-pay-2026
