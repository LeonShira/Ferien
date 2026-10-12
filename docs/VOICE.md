# Writing for the ear

The narration is heard once, at speaking speed, by someone scrolling. Write it the way
a sharp friend would explain it out loud, not the way a spreadsheet reads.
`python -m shorts lint` enforces the mechanical rules below; the rest is judgement.

## Rules the lint enforces

| Rule | Why |
|---|---|
| Name the currency at most **3 times** per script (`$`, `€`, `£`, dollars, euros, pounds) | Say it once to set the context, then "150 a month". Nobody says "dollars" twenty times. |
| At most **2 figures per line** | A third number in one breath doesn't land. Put it on screen instead. |
| First sentence <= 14 words | The hook has about two seconds. |
| No filler ("basically", "in this video", "let's dive in") | It costs seconds and sounds scripted. |

## Style

- **Set the scene once, then talk normally.** "Say you owe $5,000 on a card at 24%." After that it's
  "150 a month", "the balance", "that interest".
- **Round when precision doesn't matter.** "About 3,300 in interest" beats "$3,322.09". The screen can show
  the exact figure; the voice gives the gist. Declare rounded claims with a wider `tolerance` (e.g. `0.05`).
- **Don't read the screen aloud.** The chart says "Balance left"; the voice says why it matters.
- **Contractions and plain words.** "You're done in 21 months", not "The debt is extinguished after 21 months."
- **Vary the rhythm.** Mix a short punch ("Sounds responsible.") with a longer explanation.
- **Spell out abbreviations** the first time or avoid them ("interest rate", not "APR").
- **One question per script, max.** Rhetorical questions get tired fast.
- **End on a thought, not a pitch.** One sentence of takeaway, then the follow line.

## Before and after

| Before (pilot v1) | After |
|---|---|
| Keep paying $150 every month, and it takes 56 months to clear. | At that pace, it takes 56 months to reach zero. |
| Total interest: $3,322. You pay back $8,322 for $5,000 of stuff. | All in, that's about 3,300 in interest. |
| Double it to $300 a month, and you're done in 21 months, with $1,143 of interest. | Now pay 300 a month instead. Same card, same rate. You're done in 21 months. |

## Pronunciation

If the voice mispronounces a word, add `say:` to the scene with a respelled version
(`say: "the rye stones of Yap"`). Captions still show `narration`, so keep the words the same and
change only spelling.
