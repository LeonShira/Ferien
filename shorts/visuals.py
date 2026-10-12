"""Scene visual specs: validation and computed numbers.

Any number on screen can be given as a calculation instead of a literal:

    to: {calc: payoff_interest, args: {balance: 5000, apr: 0.24, monthly_payment: 150}}
    series: [{label: "7 %", calc: {calc: future_value, args: {...}, vary: years, from: 0, to: 40, step: 5}}]

`expand_visual` replaces those with values from `finmath`, so charts and counters
show recomputed figures rather than numbers typed into a script.
"""

from __future__ import annotations

import copy
import math

from . import finmath

# type -> (required keys, optional keys). Mirrors video/src/scenes/index.tsx.
SCHEMA: dict[str, tuple[set[str], set[str]]] = {
    "title": ({"text"}, {"sub", "emoji", "accentWords"}),
    "big_number": ({"to"}, {"from", "prefix", "suffix", "decimals", "label", "sub", "emoji"}),
    "quote": ({"text"}, {"by"}),
    "list": ({"items"}, {"title"}),
    "emoji": ({"emojis"}, {"label", "flow"}),
    "line_chart": ({"series"}, {"title", "prefix", "suffix", "decimals", "xSuffix"}),
    "bar_compare": ({"bars"}, {"title", "prefix", "suffix", "decimals"}),
    "ring": ({"value"}, {"title", "label", "decimals", "bad"}),
    "dot_grid": ({"total", "highlight"}, {"title", "label", "cols", "bad"}),
    "myth_fact": ({"myth", "fact"}, {"mythLabel", "factLabel"}),
    "split_compare": ({"left", "right"}, {"title"}),
    "timeline": ({"events"}, {"title"}),
    "image": (set(), {"src", "prompt", "label", "motion"}),
    "custom": ({"component"}, set()),
}
COMMON = {"type", "motion"}


def _compute(spec: dict) -> float:
    fn = finmath.CALCULATORS.get(spec.get("calc"))
    if fn is None:
        raise ValueError(f"unknown calculator {spec.get('calc')!r}")
    value = float(fn(**(spec.get("args") or {}))) * float(spec.get("scale", 1))
    if math.isinf(value) or math.isnan(value):
        raise ValueError(f"{spec['calc']} returned {value}")
    digits = spec.get("round")
    return round(value, int(digits)) if digits is not None else value


def _series_points(spec: dict) -> list[list[float]]:
    vary = spec["vary"]
    start, stop, step = float(spec["from"]), float(spec["to"]), float(spec.get("step", 1))
    points, x = [], start
    while x <= stop + 1e-9:
        args = dict(spec.get("args") or {}, **{vary: x})
        points.append([round(x, 4), round(_compute({**spec, "args": args}), 2)])
        x += step
    return points


def _is_calc(v) -> bool:
    return isinstance(v, dict) and "calc" in v


def expand_visual(visual: dict) -> dict:
    """Return a copy of `visual` with every calc replaced by its computed value."""
    v = copy.deepcopy(visual)
    for key in ("to", "from", "value", "total", "highlight"):
        if _is_calc(v.get(key)):
            v[key] = _compute(v[key])
    for bar in v.get("bars") or []:
        if _is_calc(bar.get("value")):
            bar["value"] = _compute(bar["value"])
    for s in v.get("series") or []:
        if _is_calc(s.get("calc")):
            s["points"] = _series_points(s.pop("calc"))
    return v


def text_of(visual: dict) -> list[str]:
    """Every human-readable string in a visual (for the compliance lint)."""
    out: list[str] = []

    def walk(x, key=""):
        if isinstance(x, str) and key not in ("type", "src", "prompt", "component", "motion", "calc"):
            out.append(x)
        elif isinstance(x, dict):
            for k, val in x.items():
                walk(val, k)
        elif isinstance(x, list):
            for val in x:
                walk(val, key)

    walk(visual)
    return out


def validate(visual) -> list[str]:
    if not isinstance(visual, dict) or "type" not in visual:
        return ["visual must be a mapping with a `type`"]
    t = visual["type"]
    if t not in SCHEMA:
        return [f"unknown visual type {t!r}; use one of {sorted(SCHEMA)}"]
    required, optional = SCHEMA[t]
    problems = [f"{t}: missing {k}" for k in sorted(required - visual.keys())]
    unknown = set(visual) - required - optional - COMMON
    if t != "custom" and unknown:
        problems.append(f"{t}: unknown keys {sorted(unknown)}")
    if t == "image" and not (visual.get("src") or visual.get("prompt")):
        problems.append("image: needs `prompt` (to generate) or `src` (existing file)")
    try:
        expanded = expand_visual(visual)
    except (ValueError, TypeError, KeyError) as e:
        return problems + [f"{t}: calculation failed: {e}"]
    if t == "line_chart":
        for s in expanded.get("series", []):
            if len(s.get("points") or []) < 2:
                problems.append("line_chart: every series needs >= 2 points (or a calc with vary/from/to)")
    if t == "bar_compare" and not 2 <= len(expanded.get("bars", [])) <= 5:
        problems.append("bar_compare: use 2-5 bars")
    if t == "list" and not 2 <= len(expanded.get("items", [])) <= 5:
        problems.append("list: use 2-5 items")
    if t == "timeline" and not 2 <= len(expanded.get("events", [])) <= 5:
        problems.append("timeline: use 2-5 events")
    if t == "ring" and not 0 <= float(expanded.get("value", 0)) <= 100:
        problems.append("ring: value must be 0-100")
    if t == "dot_grid" and int(expanded.get("total", 0)) > 400:
        problems.append("dot_grid: total must be <= 400")
    return problems
