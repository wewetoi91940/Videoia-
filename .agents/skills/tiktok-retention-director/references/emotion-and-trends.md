# Emotion map and current short-form grammar

Read at Step 4 (emotion map), Step 5 (visual carriers), Steps 6–7 (voice, music, captions). Worked example:
`videos/crue-1910-v2/` — the same 1910 flood as `videos/crue-1910-tiktok/`, rebuilt with an emotional arc and the
grammar below after the request « plus d'émotion… dans la mode de 2026 ».

## 1. The emotion map (one emotion per frame)

Retention is not only information; viewers stay for a change of feeling. Give every frame an `emotion:` key
(first word from the vocabulary, then a short note) and check the arc before building:

`curiosity` · `unease` · `tension` · `shock` · `dread` · `sadness` · `empathy` · `warmth` · `hope` · `relief` ·
`pride` · `awe` · `wonder` · `humor` · `joy` · `anger` · `nostalgia` · `gravity` · `reflection` · `connection`

```
- emotion: unease — a familiar sound stops
```

Rules (`retention_lint.mjs` checks the first three):

- at least three different emotions in a piece of 30 s or more, five or more around 60 s;
- no emotion held for more than three frames in a row or for more than ~45 % of the running time;
- a contrast in the second half (fear → warmth, loss → pride, tension → relief): the turn people remember;
- the emotion comes **from a sourced fact or a real image**, never from an invented detail, dialogue or sound;
- a quiet beat (fewer words, music thinned out, one image) before or after the strongest moment;
- tragedy with victims: empathy and respect, no thrill, no jokes, no "satisfying" framing of suffering.

A typical history/news arc: unease (hook) → tension (context) → shock (reveal) → dread (escalation) →
empathy (people) → warmth (solidarity) → awe (peak number) → gravity / reflection (today) → connection (a gesture
the viewer can make).

## 2. Carriers — how each layer expresses the emotion

Write the carriers in the frame's shot keys (`camera`, `animation`, `sfx`, plus `grade:` if you use one).

| Layer | Tension / dread | Empathy / sadness | Warmth / hope | Awe / shock | Reflection |
| --- | --- | --- | --- | --- | --- |
| Voice (local TTS speed, French Kokoro) | 0.95–1.0, short sentences | 0.85, one short sentence | 0.92 | 0.9, number said slowly | 0.9, a full stop before the last clause |
| Pause before the line | 0.3–0.5 s | 0.6 s | 0.9 s (music swells) | 0.6 s, riser under it | 1.0 s after the peak |
| Music | low drone, minor, filter ≈ 300–500 Hz, heartbeat ~70 bpm | the bed drops out, a solo piano motif | major mode, brighter (filter ≈ 1.4 kHz), soft bell | riser → impact (sub + bell), cut to silence | sparse piano, low pad |
| Sound effects | ticks, a cut to silence, low thuds | none | none or a soft chime | whoosh into the cut, impact on the number | one soft hit on the key word |
| Colour (grade) | cold, desaturated teal | soft neutral | warm amber | high contrast, paper or flash | natural colour (today) |
| Camera | slow push-in, slight drift | very slow push toward faces | tilt toward the hopeful detail | fast punch-in, 2-frame shake | slow reframe toward the object |
| Type | heavy sans (Inter 900), words slam in on the voice | no title — one label | editorial serif italic | condensed display number (Anton) + count-up | serif italic, two short lines |
| Transition | zoom-through, push (going underground: push up) | slow crossfade (0.8 s) | crossfade + light leak | hard cut + white flash | crossfade |

## 3. Short-form grammar of 2025–2026 (conventions, not facts)

These are observed conventions of vertical shorts at the time of writing; check a few current videos in the niche
before a new series, they change fast.

- **Second-person, present-tense opening** (« Imagine : … », POV): immersion without invention. The on-screen date
  is visible from frame 0 so a present-tense hook is never mistaken for news.
- **Word-by-word captions**: groups of 1–3 words (≤ 20 characters), the whole group shown at once, centred, the
  word being said in the accent colour; break after punctuation, never inside a date or a number + unit.
- **Kinetic titles**: each title word enters when the voice says it (≈ 0.3 s, slight overshoot).
- **Depth without matting**: the archive as a rounded card over its own blurred, darkened copy; the background
  drifts slower than the card (parallax).
- **Colour follows the emotion** (section 2), so the arc reads even without sound.
- **One "impact" moment**: count-up number + white flash + 2-frame shake + sub hit, used once.
- **Sound design as storytelling**: ticks, cut to silence, heartbeat, riser → impact, whoosh on transitions.
- **Loop ending**: the last second returns to the first image/sound (the clock ticks again), so a replay feels
  continuous.
- **A quiet beat**: one image, one line, music thinned out — the moment people comment on.

## 4. Honesty limits of emotional editing

- Dramatise the **form** (rhythm, sound, colour, framing), never the **content**: no invented quote, thought,
  number, sound of the event (crowds, sirens, screams) or "reconstructed" archive.
- "Imagine…" introduces sourced facts only; no fictional character, no invented dialogue.
- A quote shown on screen is verbatim and attributed. Text read **in** an archive image (a motto, a caption) can be
  shown with its translation and source; a caption reported elsewhere but not visible in your copy is not quoted.
- Risk statements today stay measured and sourced ("plus faible… mais pas nul" from a cited source), never fear-bait.

## 5. Build notes measured on the worked example

| Situation | What happened | Do this |
| --- | --- | --- |
| `data-color-grading` (shader grade) on an `<img>` | a 2 s test took 3 min 23 s to render (44 s plain composition: 3 min 33 s) | for long pieces, bake the grade into the image files (duotone + contrast in Python), keep the shader for short pieces |
| `npx hyperframes remove-background` on 1910 postcards | matte empty or a fragment (alpha coverage 0–5 %) | check the alpha coverage on a coloured plate before using a cutout; use card + blurred background instead |
| registry `organic-light-leak-overlay` in 1080 × 1920 | authored 1920 × 1080: covered only the top of the frame | set the block's `data-width`/`data-height` and `html, body` size to 1080 × 1920; host `style="opacity:0.6"` for archives |
| `check` on ~1 000 tweens | "Check did not finish within its deadline" | `npx hyperframes check --timeout 30000` |
| pop-on captions (words hidden until said) | layout reserved for hidden words: text looked off-centre | show the whole group, colour the active word |
| active word scaled 1.08 | the scaled word covered the space ("compriméqui") | `word-spacing: 0.14em`, scale ≤ 1.04 |
| a stamp over a text box | covered the word it stamped | put stamps beside or under the text, never on it |
| Whisper read-back "cruse", "garces" | the phonemes were right (`ʁy aʁɛt`, `ɡaʁ sə nwa`); check with espeak before rewriting a line | `phonemize(text, language="fr-fr", backend="espeak")` |
