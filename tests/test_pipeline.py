import copy
import math
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from shorts import backlog, captions, finmath, lint, publish, visuals
from shorts.config import EPISODES_DIR, load_channel, load_yaml

PILOT = EPISODES_DIR / "2026-10-12-credit-card-minimum-trap.yaml"


@pytest.fixture
def channel():
    return load_channel()


@pytest.fixture
def pilot():
    return load_yaml(PILOT)


# finmath -----------------------------------------------------------------

def test_doubling_and_rule_of_72():
    assert finmath.doubling_years(0.07) == pytest.approx(10.24, abs=0.01)
    assert finmath.rule_of_72(0.08) == pytest.approx(9.0)


def test_card_payoff():
    assert finmath.payoff_months(5000, 0.24, 150) == 56
    assert finmath.payoff_months(5000, 0.24, 300) == 21
    assert finmath.payoff_interest(5000, 0.24, 300) == pytest.approx(1143.34, abs=0.01)
    assert math.isinf(finmath.payoff_months(5000, 0.24, 100))  # interest-only never clears
    assert finmath.remaining_balance(5000, 0.24, 300, 21) == 0.0


def test_loans_and_odds():
    assert finmath.loan_payment(20000, 0.06, 60) == pytest.approx(386.66, abs=0.01)
    assert finmath.odds_one_in(49, 6) == 13_983_816
    assert finmath.future_value(1000, 0.0, 10, 100) == pytest.approx(13000)


def test_verify_claim():
    ok, actual, _ = finmath.verify_claim({"calc": "doubling_years", "args": {"rate": 0.07}, "expect": 10.2})
    assert ok and actual == pytest.approx(10.24, abs=0.01)
    ok, _, _ = finmath.verify_claim({"calc": "doubling_years", "args": {"rate": 0.07}, "expect": 12})
    assert not ok
    ok, _, msg = finmath.verify_claim({"calc": "nope", "expect": 1})
    assert not ok and "unknown calculator" in msg


# visuals -----------------------------------------------------------------

def test_expand_visual_computes_numbers():
    v = {"type": "big_number", "to": {"calc": "payoff_interest",
         "args": {"balance": 5000, "apr": 0.24, "monthly_payment": 150}, "round": 0}}
    assert visuals.expand_visual(v)["to"] == 3322
    chart = {"type": "line_chart", "series": [{"label": "a", "calc": {"calc": "remaining_balance",
             "args": {"balance": 5000, "apr": 0.24, "monthly_payment": 300}, "vary": "months", "from": 0, "to": 22, "step": 2}}]}
    pts = visuals.expand_visual(chart)["series"][0]["points"]
    assert pts[0] == [0, 5000] and pts[-1][1] == 0


def test_validate_visual():
    assert visuals.validate({"type": "big_number", "to": 5}) == []
    assert "unknown visual type" in visuals.validate({"type": "hologram"})[0]
    assert any("missing myth" in p for p in visuals.validate({"type": "myth_fact", "fact": "x"}))
    assert any("2-5 bars" in p for p in visuals.validate({"type": "bar_compare", "bars": [{"label": "a", "value": 1}]}))
    assert any("prompt" in p for p in visuals.validate({"type": "image"}))


# lint --------------------------------------------------------------------

def test_pilot_passes(pilot, channel):
    errors, _ = lint.lint_episode(pilot, channel)
    assert errors == []
    assert channel["production"]["min_seconds"] < lint.estimate_seconds(pilot, channel) <= channel["production"]["max_seconds"]


@pytest.mark.parametrize("line", [
    "You should buy this stock now before it explodes.",
    "This is a guaranteed return of 12% a year.",
    "As a financial advisor, I recommend buying gold.",
    "$TSLA is going to the moon.",
    "Du solltest jetzt kaufen.",
])
def test_advice_language_blocks(pilot, channel, line):
    ep = copy.deepcopy(pilot)
    ep["scenes"][3]["narration"] = line
    errors, _ = lint.lint_episode(ep, channel)
    assert errors


def test_wrong_number_blocks(pilot, channel):
    ep = copy.deepcopy(pilot)
    ep["claims"][2]["check"]["expect"] = 40
    errors, _ = lint.lint_episode(ep, channel)
    assert any("failed recomputation" in e for e in errors)


def test_unsourced_claim_blocks(pilot, channel):
    ep = copy.deepcopy(pilot)
    ep["claims"].append({"statement": "Most people carry a balance"})
    errors, _ = lint.lint_episode(ep, channel)
    assert any("needs a `check`" in e for e in errors)


def test_short_script_blocks(pilot, channel):
    ep = copy.deepcopy(pilot)
    ep["scenes"] = ep["scenes"][:6]
    errors, _ = lint.lint_episode(ep, channel)
    assert any("estimated" in e for e in errors)


def test_template_placeholders_block(channel):
    template = load_yaml(EPISODES_DIR.parent / "episode_template.yaml")
    errors, _ = lint.lint_episode(template, channel)
    assert any("TODO" in e for e in errors)


def test_copycat_hook_blocks(pilot, channel):
    other = copy.deepcopy(pilot)
    other["id"] = "2026-10-01-other"
    errors, _ = lint.lint_episode(pilot, channel, previous=[other])
    assert any("near-identical" in e for e in errors)


# captions ----------------------------------------------------------------

def test_caption_chunks_cover_speech():
    chunks = captions.chunk_words("Paying $150 a month on a $5,000 card takes almost five years. Here's why.")
    assert all(len(c.split()) <= 3 for c in chunks)
    timed = captions.time_chunks(chunks, 0.2, 4.0)
    assert timed[0]["start"] == pytest.approx(0.2)
    assert timed[-1]["end"] == pytest.approx(4.0, abs=0.01)
    assert all(a["end"] == pytest.approx(b["start"], abs=0.002) for a, b in zip(timed, timed[1:]))


# publish -----------------------------------------------------------------

def test_compose_texts(pilot, channel):
    texts = publish.compose_texts(pilot, channel)
    assert channel["channel"]["disclaimer"] in texts["tiktok_title"]
    assert channel["channel"]["disclaimer"] in texts["youtube_description"]
    assert "#Shorts" in texts["youtube_description"]
    assert "consumerfinance.gov" in texts["youtube_description"]
    assert len(texts["youtube_title"]) <= 100


def test_build_fields(pilot, channel):
    fields = dict(publish.build_fields(pilot, channel, "me", ["tiktok", "youtube"], "2026-10-13T18:30:00+02:00"))
    assert fields["is_aigc"] == "true"
    assert fields["containsSyntheticMedia"] == "true"
    assert fields["categoryId"] == "27"
    assert fields["scheduled_date"] == "2026-10-13T16:30:00Z"
    assert "timezone" not in fields


def test_next_slot(channel):
    tz = ZoneInfo(channel["publishing"]["timezone"])
    morning = datetime(2026, 10, 13, 9, 0, tzinfo=tz)
    evening = datetime(2026, 10, 13, 20, 0, tzinfo=tz)
    assert publish.next_slot(channel, morning).startswith("2026-10-13T18:30")
    assert publish.next_slot(channel, evening).startswith("2026-10-14T18:30")


def test_publish_dry_run(pilot, channel, tmp_path):
    result = publish.publish(pilot, channel, tmp_path / "final.mp4", dry_run=True)
    assert result["platforms"] == ["tiktok", "youtube"]


def test_publish_requires_key(monkeypatch):
    monkeypatch.delenv("UPLOAD_POST_API_KEY", raising=False)
    with pytest.raises(publish.PublishError):
        publish.UploadPost()


# backlog -----------------------------------------------------------------

def test_next_topic_rotates_series():
    topics = [{"id": "a", "series": "the-math", "priority": 3, "status": "todo"},
              {"id": "b", "series": "money-history", "priority": 1, "status": "todo"}]
    recent = [{"id": "2026-10-01-x", "series": "the-math"}]
    assert backlog.next_topic(topics, recent)["id"] == "b"
    assert backlog.next_topic(topics, [])["id"] == "a"


def test_backlog_and_series_are_consistent():
    series = backlog.load_series()
    topics = backlog.load_topics()
    assert len({t["id"] for t in topics}) == len(topics)
    assert {t["series"] for t in topics} <= set(series)
    for s in series.values():
        for v in s["visuals"]:
            assert v in visuals.SCHEMA
