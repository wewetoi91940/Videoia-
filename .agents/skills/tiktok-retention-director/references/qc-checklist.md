# QC checklist — before delivering a TikTok short

Run in this order; fix, then re-run only the failed item. Log each result in `DIRECTION.md` § QC
(item · measured value · verdict · fix).

## 1. Plan (before building)

| Check | How | Pass |
| --- | --- | --- |
| Retention plan | `node scripts/retention_lint.mjs --storyboard STORYBOARD.md` | no error; warnings read and either fixed or explained |
| Emotion map | the same lint (`emotion:` per frame) | ≥ 3 emotions from 30 s, none held > 3 frames or > 45 % of the time, a contrast in the second half |
| Sources | every claim in narration and on screen has a `SOURCES.md` row | no orphan claim |
| Hook honesty | `hooks.md` honesty test on the chosen hook | five yes |

## 2. Composition (before rendering)

| Check | How | Pass |
| --- | --- | --- |
| Lint | `npx hyperframes lint` | 0 errors |
| (long timelines) | a check that stops with "did not finish within its deadline" | rerun with `--timeout 30000` |
| Layout, contrast, runtime | `npx hyperframes check --at-transitions` (samples every transition seam too) | 0 errors |
| TikTok interface zones | the three passes from `node scripts/tiktok_qc.mjs --print-checks` | no `caption_zone_collision` on text that must be read |
| Hook frames | `npx hyperframes snapshot --at 0,0.5,1.5` | the first frame shows the subject and the hook text; nothing under the top bar |
| Every frame | `npx hyperframes snapshot --at <frame midpoints>` | one focal point, text readable at phone size, no overlap |

## 3. Render (after rendering)

`node scripts/tiktok_qc.mjs --video renders/<file>.mp4 --target <seconds> --sheet renders/qc-sheet.jpg`

| Check | Pass |
| --- | --- |
| Format | 1080 × 1920, 30 fps (24–60 accepted), H.264, yuv420p, AAC audio |
| Duration | within ±15 % of the target |
| Loudness | −16 to −12 LUFS integrated, true peak ≤ −1 dBTP |
| Dead air | no silence > 1.2 s in the first 10 s; elsewhere only intentional |
| Frozen picture | no static stretch > 5 s |
| Black | no black frame at the start; none elsewhere unless intended |
| QC sheet | open the sheet: frames at 0 s, 0.5 s, 1.5 s, then evenly spaced, with TikTok's zones in red — no text or face under red |

## 4. Watch it like a viewer

Once, with sound, at full speed; once without sound. Note the second where attention drops: a sentence that
adds nothing, a picture that stays too long, a word you did not understand, a caption you could not finish
reading. Fix those, then re-render.

| Defect | Typical fix |
| --- | --- |
| Hook understood only with sound | stronger on-screen text, first image that shows the subject |
| Dead time between two beats | trim the pause, move the next cut onto the first word |
| Information too dense | split the beat, move a number on screen, cut a clause |
| Caption under the interface | move the caption band up, shorten lines |
| Music masks the voice | duck deeper (≥ 15 dB under the voice), cut low-mids of the bed |
| Payoff weak or late | answer the hook's question in one line, on screen and in voice |
| Two texts superimposed during a fade, or text "under" the incoming shot | put each shot's texts in one layer that fades out at the start of the transition and in at its end |
| A number and its unit split across two captions ("8,62 / mètres") | keep units with their number when grouping captions |
