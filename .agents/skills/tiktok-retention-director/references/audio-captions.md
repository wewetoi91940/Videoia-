# Audio and captions for phone viewing

Providers, voices and commands for TTS, music, sound effects and transcription are owned by `/media-use`
(`../../media-use/audio/references/tts.md`, `captions/authoring.md`, `captions/transcript-handling.md`).
Mixing tools (ducking, voice carve, limiter) are owned by `/hyperframes-audio`. This file sets the targets
for a TikTok short and the caption spec for a 1080 × 1920 phone screen.

## Audio

### Voice

- Narration first: the visuals cut to the voice, not the reverse. Generate the voice (or record it) before
  the final timing of frames.
- Pace: the word budget in `retention-script.md` (≈ 2.6–3.0 words/s in French). Ask the TTS for a steady,
  close, conversational delivery; energy comes from the writing, not from shouting.
- Pronunciation: numbers, dates and proper names are written the way they must be said in the TTS input
  (`huit mètres soixante-deux`, `mille neuf cent dix`), the display text keeps the digits.
- Provider choice: a free local engine (`npx hyperframes tts`, Kokoro, French voice `ff_siwis`, `--lang fr-fr`;
  set `HYPERFRAMES_PYTHON` to a Python that has `kokoro-onnx` and `soundfile`; for French, speed ≈ 0.92 lands near
  2.6 words/s) is always available; a paid or quota-limited provider (HeyGen, Gemini, ElevenLabs …) is used only after the user
  agreed. Say which voice was used in the delivery note and the credits.
- Get word timings (TTS timestamps or `npx hyperframes transcribe <audio> -l fr -m small -e whisper`) — captions,
  cuts and sound effects are placed on them. Read the transcript back: it is also a pronunciation check (homophones
  are fine; a garbled proper name means the TTS input needs a phonetic spelling).

### Music and sound effects

- Music: one bed whose mood follows the story's arc; it rises in pauses and on the end card, and ducks under
  the voice. Royalty-free or generated with a licence that allows publication; never a commercial track.
- Sound effects: few and meaningful — on a cut that changes place or time, on a number that lands, on a
  reveal. Each cue is anchored to the word it illustrates (`sfx: impact on "8,62"`). No crowd, gunshot or
  siren recordings that could pass for audio of a real event.

### Targets (measure, don't assume)

| Measure | Target |
| --- | --- |
| Integrated loudness | −14 LUFS (−16 to −12 accepted) |
| True peak | ≤ −1 dBTP |
| Music under voice, while the voice speaks | ≥ 15 dB lower (aim ≈ 20) |
| Silence | no gap > 1.2 s in the first 10 s; elsewhere only as an intentional held beat |

`node scripts/tiktok_qc.mjs --video …` measures loudness, true peak and silences on the render.

## Captions

Many viewers watch without sound: captions carry the narration, the on-screen text carries the facts.

| Rule | Value on 1080 × 1920 |
| --- | --- |
| Lines per group | 1–2 |
| Characters per line | ≤ 30–32 (≈ 870 px at 52 px serif or 56 px sans) |
| Size | 48–60 px, weight 600–800 |
| Band | y ≈ 1180–1460, centred in x 60–930 (clear of the right rail and the bottom area) |
| Timing | word-timed; a group shows from its first word to ≥ 0.3 s after its last word; ≥ 0.8 s on screen |
| Grouping | break on sentence ends, pauses ≥ 150 ms, never after an article or preposition, never before detached punctuation (`:` `;` `?` `!` `»`) or after an opening `«`, never between a number and its unit (`8,62 mètres`, `13 h 30`) |
| Emphasis | numbers, dates, names in the accent colour or weight; at most one emphasised item per line |
| Contrast | text on a dark box (≥ 85 % opacity) or with a stroke; WCAG ≥ 4.5:1 |
| Exclusivity | one caption group visible at a time; a hard cut-out at the group end |

Build options, in order of preference:

1. **The workflow's own builder** — `/faceless-explainer` `scripts/captions.mjs` reads `STORYBOARD.md` and the
   word timings, and uses the frame preset's caption skin. Set its band to the caption band above.
2. **A registry caption component** — `npx hyperframes catalog --tag caption-style`; `caption-highlight` is the
   TikTok-style word highlight. Mount it as a sub-composition (`/hyperframes-registry`).
3. **Hand-built** — groups as timed clips with spans per line (`/media-use` `captions/authoring.md` gives the
   exit guarantee and the fit-text helper).

Always run the bottom-area and right-rail `check --caption-zone` passes after captions are in place.
