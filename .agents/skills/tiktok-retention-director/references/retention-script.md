# Retention script — beat map, word budget, open loops

Structures (concept / how-to / listicle / story), clarity techniques and beat vocabulary are owned by
`../../faceless-explainer/references/story-design.md`; use them. This file adds the short-form constraints:
when each beat lands, how many words fit, and how curiosity is kept open until the end.

## Beat map — a guide scaled to the length, not a fixed grid

| Length | Hook | Minimal context | Body | Re-hooks | Payoff |
| --- | --- | --- | --- | --- | --- |
| 15 s | 0–1.5 s | ≤ 3 s, often merged into the hook | 2–3 beats | — | last 2 s |
| 30 s | 0–2 s | 2–5 s | 3–4 beats | ≈ 15 s | last 3–4 s |
| 45 s | 0–2 s | 2–6 s | 4–5 beats | ≈ 15 s and ≈ 30 s | last 4–6 s |
| 60 s | 0–2 s | 2–7 s | 5–6 beats | every ≈ 15 s | last 5–7 s |
| 90 s | 0–2 s | 2–8 s | 6–8 beats | every ≈ 15–20 s | last 6–8 s — or split into parts |

Adapt to the subject: a story with one big reveal can hold its payoff to the last line; a listicle pays off a
little at every item and keeps the strongest item last. What never moves: the hook is first, context is
minimal, and the end delivers what the hook promised.

`beat_role` values used in `STORYBOARD.md`: `hook`, `context`, `development`, `turn` (a reversal or
re-hook), `reveal`, `conclusion`. Map them onto the shared `type` enum as `story-design.md` explains
(`hook` → `hook`, `context` → `pain_point` or `product_intro`, `development` → `feature_showcase` or
`social_proof`, `turn` → `pain_point`, `reveal` → `benefit_highlight`, `conclusion` → `branding` or `cta`).

## Every sentence earns its place

Each spoken sentence does at least one of: **adds a fact**, **opens a question**, **answers one**, **shows a
consequence**. Delete any sentence that does none. Then delete:

- greetings, channel names, "in this video / dans cette vidéo", "today we'll see / aujourd'hui on va voir";
- announcements of what comes next instead of the thing itself ("let me explain", "je vous explique");
- recaps of what was just said; synonyms repeated for rhythm; adjectives that only intensify;
- the call to action at the start (a follow request, if any, belongs after the payoff, in one short line).

Prefer connectors that carry tension — *mais*, *alors*, *sauf que*, *résultat*, *pourtant* / *but*, *so*,
*except*, *which means* — over *et puis* / *and then*. Short sentences, concrete nouns, active verbs, numbers
said the way people say them.

## Word budget

| Language | Comfortable pace | 15 s | 30 s | 45 s | 60 s |
| --- | --- | --- | --- | --- | --- |
| French | 2.6–3.0 words/s | 35–42 | 70–85 | 105–125 | 140–170 |
| English | 2.4–2.8 words/s | 32–40 | 65–80 | 100–120 | 135–160 |

Leave ≈ 10 % of the length for breathing room: held beats before a reveal, the end card, sound effects.
`retention_lint.mjs` warns above 3.2 words/s (FR) or 3.0 (EN) per frame — faster than that, phone viewers
stop understanding.

## Open loops and re-hooks

- An **open loop** is a question the viewer now wants answered ("but why didn't the water go down?").
  Declare it on the frame that opens it — `open_loop: Q1 — <question>` — and on the frame that answers it —
  `closes: Q1`. Every loop opened must be closed; the lint checks it.
- Keep one loop open at all times after the hook, and never more than two (more is confusion, not suspense).
- A **re-hook** (`beat_role: turn`) lands near each third of the video: a reversal, a new stake, a number
  that changes the scale. It is information, not a slogan.
- The **payoff** answers the hook's question explicitly, in words and on screen. A final line may loop back
  to the first image (a callback) — it rewards rewatching, which TikTok counts.

## Comprehension guard

- Context in ≤ 6 s means: who / where / when, and why it matters — no more.
- A name, date, place or number that matters appears on screen when it is said.
- One idea per beat; when two facts compete, keep the one the payoff needs.
- Never cut inside a key word or during the last word of a sentence that carries the information.

## Frame fields written in this step

`beat_role`, `new_info` (one sentence: what this beat adds), `voiceover`, `duration`, and when relevant
`open_loop`, `closes`, `hook_type` (first frame: `curiosity | contradiction | surprising_fact | suspense |
unexpected_consequence`). Step 4 adds `changes:`; Step 5 adds the visual columns. Template:
`../templates/STORYBOARD.md`.
