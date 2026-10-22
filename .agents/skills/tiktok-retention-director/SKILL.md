---
name: tiktok-retention-director
description: >
  Direct a high-retention vertical short (TikTok, Reels, Shorts — 15 to 90 s, 1080x1920) around the
  HyperFrames build: find the strongest true angle of the subject, write five typed hooks and keep the
  best honest one, script beat by beat for retention, write a shot-level direction table (duration,
  narration, image, camera, animation, on-screen text, sound effect, transition), plan voice, music and
  captions inside TikTok's interface-safe area, map the emotional arc frame by frame, then lint the plan and QC
  the render. Use for « vidéo TikTok », « Reels », « Shorts », « hook », « accroche », « rétention », « format
  vertical », « plus d'émotion », « à la mode », « tendance », including
  history and news topics (fact ledger, no invented sources or archives). It directs; the build runs in
  /faceless-explainer (invented visuals) or /general-video (real archives, maps, custom layout). Not for
  captioning existing footage (/embedded-captions) or overlays on a talking head (/talking-head-recut).
---

# TikTok retention director

You direct the piece; existing HyperFrames workflows build it. This skill owns what they do not: the
**hook lab**, the **retention grammar** of the script, the **shot direction table**, **TikTok's
interface-safe layout**, the **retention lint** and the **render QC**. Everything else is reused — read the
owner skill instead of re-deriving it here.

## Reuse map — read the owner, don't duplicate

| Need | Owner | This skill adds |
| --- | --- | --- |
| Routing, `BRIEF.md`, aspect from destination (TikTok → `1080x1920`) | `/hyperframes` (intent layer, `references/brief-contract.md`) | `destination: tiktok`, retention fields in the brief body |
| Story structures, clarity techniques, beat vocabulary, hook strategies | `faceless-explainer/references/story-design.md`, `hyperframes-creative/references/story-spine.md` | the 5-hook lab, the honesty test, short-form beat timing |
| Build with invented visuals (typography, diagrams, data-viz) | `/faceless-explainer` (frame workers, `audio.mjs`, `captions.mjs`, transitions) | direction keys in `STORYBOARD.md` the workers read as narrative |
| Build with real archives, photos, maps, custom layout | `/general-video` + `/hyperframes-core` | vertical layout zones, shot table |
| Motion rules, blueprints, transitions | `/hyperframes-animation` | which motion serves which retention job |
| Camera moves (Ken Burns, punch-in, reframe) | `/hyperframes-keyframes` | camera column vocabulary |
| Named looks, caption components (`caption-highlight` …) | `/hyperframes-registry` (`npx hyperframes catalog`) | — |
| Voice (TTS), music, SFX, transcription, caption authoring, face hiding | `/media-use` (`audio/references/tts.md`, `captions/authoring.md`, `references/media-treatments.md`) | phone-readable caption spec, word budget |
| Mixing, ducking, voice carve | `/hyperframes-audio` | level targets for phone speakers |
| Studio timeline, generic action/title-safe boxes | `/hyperframes-studio` § 4 | TikTok **UI** zones (stricter than title-safe) |
| lint, check, snapshot, render | `/hyperframes-cli` | UI-zone `check` passes, `scripts/tiktok_qc.mjs` |

## Files this skill writes (in `videos/<project>/`)

| File | Content | Template |
| --- | --- | --- |
| `DIRECTION.md` | subject analysis, the 5 hooks and the choice, retention map, QC log | `templates/DIRECTION.md` |
| `STORYBOARD.md` | standard storyboard (`hyperframes/references/storyboard-format.md`) + direction keys per frame | `templates/STORYBOARD.md` |
| `SCRIPT.md` | locked narration (`hyperframes/references/script-format.md`) | — |
| `SOURCES.md` | fact ledger: claim → source → status (history, news, numbers, quotes) | `templates/SOURCES.md` |

The direction keys are ordinary storyboard bullets (the parser keeps unknown keys under `extra`), so
`/faceless-explainer` and `/general-video` read the same file without change.

## Process

Run the steps in order; each gate must hold before the next step. Language of every viewer-facing word =
the brief's `language` (French narration for a French brief).

### Step 0 — Brief

A fresh request goes through `/hyperframes` first (intent layer → `BRIEF.md`). Set `destination: tiktok`,
`aspect: 1080x1920`, `length`, `audience`, `language`, and `workflow`: `faceless-explainer` when every
visual is invented, `general-video` when real archives / photos / maps carry the story. An existing
`BRIEF.md` is read, never re-asked. **Gate:** `BRIEF.md` exists with those fields.

### Step 1 — Subject analysis

List 5–10 candidate facts from the material. Score each 0–2 on **surprise**, **stakes or emotion**,
**visual potential**, **verifiability**; keep the top one as the *core surprise* and name the *payoff*
(the answer or reveal the end delivers). For history or news, fill `SOURCES.md` **before** writing
hooks (Step 9 rules apply from here). **Gate:** `DIRECTION.md` § Analysis names audience, core surprise,
payoff, and every candidate fact has a source line in `SOURCES.md`.

### Step 2 — Hook lab → `references/hooks.md`

Write **five** hooks, one per type: curiosity, contradiction, surprising fact, suspense, unexpected
consequence. Each = spoken line (≤ 12 words FR / 10 EN) + first-frame visual + on-screen text (≤ 6 words).
Run the honesty test on each (true, sourced, paid off inside the video, no bait). Pick one with the
selection rubric and write why. **Gate:** five typed hooks, the honesty test, the choice and its reason in
`DIRECTION.md` § Hooks.

### Step 3 — Script → `references/retention-script.md`

Scale the beat map to the length (hook at 0–2 s, minimal context by ~6 s, one new piece of information per
beat, payoff in the last seconds). Every sentence must add a fact, open a question, answer one or show a
consequence; cut introductions, recaps, filler. Respect the word budget. Write the frames into
`STORYBOARD.md` and the locked lines into `SCRIPT.md`. **Gate:** every frame has `beat_role` and
`new_info`; the word count fits the budget.

### Step 4 — Retention plan and emotion map → `references/emotion-and-trends.md`

Open loops (`open_loop: Q1 — …`) are each closed later (`closes: Q1`); re-hooks around one third and two
thirds; a visual change every 2–4 s (`changes:` per frame), never a still frame longer than ~5 s unless it
is a held beat before a reveal. Comprehension beats speed: a new name, date or number gets on-screen
support; no cut lands inside a key word. Give every frame an `emotion:` (one word from the vocabulary + a
note): at least three emotions from 30 s, none held more than three frames, a contrast in the second half, a
quiet beat near the peak — each emotion carried by a sourced fact, never by an invented detail. **Gate:**
`node scripts/retention_lint.mjs --storyboard STORYBOARD.md` reports no error and no emotion warning.

### Step 5 — Visual direction → `references/vertical-direction.md`

Fill the shot table for every frame: duration, narration, image or video (with source and licence),
camera, animation, on-screen text, sound effect, transition — each chosen to carry the frame's emotion
(carrier table in `references/emotion-and-trends.md`: colour, camera, type, transition). Use HyperFrames vocabulary (keyframes,
animation rules, registry transitions) and place everything inside the TikTok safe layout. Search the
registry (`npx hyperframes catalog --query …`) before hand-building any named look. **Gate:** no frame
misses a column; every image has a source and a licence or is labelled as invented / reconstruction.

### Step 6 — Audio → `references/audio-captions.md` § Audio

Clear narration (TTS through `/media-use`; ask before any paid provider; speed and pause set per line from its
emotion), a score that follows the emotion map, well under the voice,
sound effects on the words they illustrate, mix to about −14 LUFS with true peak ≤ −1 dBTP
(`/hyperframes-audio` for ducking). **Gate:** word timings exist (TTS timestamps or
`npx hyperframes transcribe`).

### Step 7 — Captions → `references/audio-captions.md` § Captions

Word-timed groups, at most two lines of ~30 characters, inside the caption band (y ≈ 1180–1460 on
1080×1920), one group at a time, numbers and names emphasised, nothing under the TikTok interface.
**Gate:** captions built (or explicitly skipped with a reason) and checked by the UI-zone passes.

### Step 8 — Build, QC, fix → `references/qc-checklist.md`

Build through the brief's workflow. Then: `npx hyperframes lint`, `npx hyperframes check --at-transitions`, the three
UI-zone passes (`node scripts/tiktok_qc.mjs --print-checks`), snapshots of the hook (0.5 s, 1.5 s) and of
every frame, render, then `node scripts/tiktok_qc.mjs --video renders/<file>.mp4 --target <s> --sheet
renders/qc-sheet.jpg` and look at the sheet (UI zones drawn in red). Fix every defect and re-run the failed
check; log results in `DIRECTION.md` § QC. **Gate:** lint and check without error, QC without error, sheet
inspected, defects fixed or explicitly accepted with a reason.

### Step 9 — Reliability → `references/reliability.md` (applies from Step 1)

Facts are sourced in `SOURCES.md`; established facts and hypotheses are worded differently on screen and in
narration; no invented source, quote, statistic, archive image or footage; reconstructions and AI images
are labelled; media are public domain, free-licensed or authorised, and credited on screen.

## Rules that never bend

- The hook's promise is paid off inside the video; no misleading claim, no fake urgency.
- No invented fact, source, quote, archive or "photo of the event"; an illustration says it is one.
- Comprehension wins over pace; a viewer who missed the sound still follows (captions + on-screen text).
- Nothing essential under TikTok's interface (top bar, right rail, bottom caption area).
- The voice stays intelligible: music ≥ 15 dB under the voice while it speaks.
- Ask before spending paid credits (TTS, image or music generation) when a free local engine exists.

## Commands

```bash
node <SKILL_DIR>/scripts/retention_lint.mjs --storyboard STORYBOARD.md [--lang fr] [--json]
node <SKILL_DIR>/scripts/tiktok_qc.mjs --print-checks                 # UI-zone `hyperframes check` commands
node <SKILL_DIR>/scripts/tiktok_qc.mjs --video renders/video.mp4 --target 45 --sheet renders/qc-sheet.jpg
node --test <SKILL_DIR>/scripts/*.test.mjs                           # the scripts' own tests
```

`retention_lint.mjs` reuses the storyboard parser shipped with `/faceless-explainer`
(`scripts/lib/storyboard.mjs`); `tiktok_qc.mjs` needs `ffmpeg` and `ffprobe` on the PATH.

| Read | When |
| --- | --- |
| `references/hooks.md` | Step 2 |
| `references/retention-script.md` | Steps 3–4 |
| `references/emotion-and-trends.md` | Steps 4–7: emotion map, carriers, current short-form grammar, honesty limits, measured build notes |
| `references/vertical-direction.md` | Step 5, layout of every frame |
| `references/audio-captions.md` | Steps 6–7 |
| `references/qc-checklist.md` | Step 8 |
| `references/reliability.md` | Steps 1 and 9, any history / news / number / quote |
| `templates/` | starting `DIRECTION.md`, `STORYBOARD.md`, `SOURCES.md` |

Worked examples in this repository: `videos/crue-1910-tiktok/` (45 s, history, public-domain archives, local voice) —
its `DIRECTION.md` shows the five hooks, the retention map, the shot table and the QC log with every defect found
and how it was fixed; `videos/crue-1910-v2/` (52 s, same subject) adds the emotion map, word-by-word captions,
card-over-blur depth, colour by emotion, a scored soundtrack and a loop ending.
