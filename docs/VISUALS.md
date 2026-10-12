# Scene visual reference

Every scene in an episode has one narration line and one `visual`. The visual is
drawn by code in `video/src/scenes/`, so text and numbers are always crisp and exact.
`python -m shorts lint` validates every visual against this list (`shorts/visuals.py`).

## Computed numbers

Wherever a visual takes a number, you can pass a calculation instead of a literal.
The renderer computes it with `shorts/finmath.py`, so the screen can't drift from the math:

```yaml
to: {calc: payoff_interest, args: {balance: 5000, apr: 0.24, monthly_payment: 150}, round: 0}
value: {calc: divide, args: {a: 100, b: 150}, scale: 100, round: 0}   # 66.7 -> 67 (%)
```

Line-chart series take a calculation that varies one argument:

```yaml
series:
- label: 7 % a year
  calc: {calc: future_value, args: {principal: 0, rate: 0.07, monthly_contribution: 200}, vary: years, from: 0, to: 40, step: 2}
```

Calculators: `future_value`, `total_contributed`, `doubling_years`, `rule_of_72`, `real_value`,
`loan_payment`, `payoff_months`, `payoff_interest`, `remaining_balance`, `effective_annual_rate`,
`percent_change`, `combinations`, `odds_one_in`, `expected_value`, `add`, `subtract`, `multiply`, `divide`.
Rates are fractions (`0.07` = 7 %).

## Scene types

| type | required | optional | use it for |
|---|---|---|---|
| `title` | `text` | `sub`, `emoji`, `accentWords` | the hook scene, chapter breaks |
| `big_number` | `to` | `from`, `prefix`, `suffix`, `decimals`, `label`, `sub`, `emoji` | one striking figure that counts up |
| `line_chart` | `series` (each `label` + `points` or `calc`) | `title`, `prefix`, `suffix`, `decimals`, `xSuffix` | growth or decay over time |
| `bar_compare` | `bars` (2-5 of `label`, `value`, `highlight`) | `title`, `prefix`, `suffix`, `decimals` | comparing outcomes |
| `ring` | `value` (0-100) | `title`, `label`, `decimals`, `bad` | a share or percentage |
| `dot_grid` | `total` (<= 400), `highlight` | `title`, `label`, `cols`, `bad` | odds, "N in 100" |
| `split_compare` | `left`, `right` (`title`, `emoji`, `rows`, `highlight`) | `title` | two choices side by side |
| `myth_fact` | `myth`, `fact` | `mythLabel`, `factLabel` | correcting a belief |
| `list` | `items` (2-5) | `title` | steps, red flags, takeaways |
| `timeline` | `events` (2-5 of `year`, `label`) | `title` | history stories |
| `quote` | `text` | `by` | a sourced quote |
| `emoji` | `emojis` | `label`, `flow` (arrows between, default true) | flows like 💳 → 💸 → 🏦 |
| `image` | `prompt` or `src` | `label`, `motion` (`zoom_in`, `zoom_out`, `pan`) | illustrated moments (costs ~1.25 credits) |
| `custom` | `component` | anything | a bespoke scene written for one episode |

## Rules of thumb

- At least 3 different types per episode; never the same type twice in a row.
- Keep on-screen text short: titles under ~30 characters, list items under ~40.
- Text on screen must say the same thing as the narration, not something new.
- `image` prompts describe a scene, never text, logos, real people or brands.

## Writing a custom scene

1. Add `video/src/custom/MyScene.tsx` exporting a component with props `{v, durationInFrames}`.
   Use `useCurrentFrame()`, `useShort()` for theme colours, and `BOX` from `../util` for the safe area.
2. Register it in `video/src/custom/index.ts`: `export const custom = {MyScene};`
3. Use it: `visual: {type: custom, component: MyScene, ...your params}`.
4. Check it: `cd video && npx tsc -p . && npx remotion still src/index.ts Short out/check.png --frame=60 --props=../output/<id>/work/props.json`.
