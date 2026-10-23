# Vertical direction — shot table, TikTok-safe layout, motion vocabulary

## TikTok interface zones (1080 × 1920)

TikTok draws its own interface over the video. Nothing essential (text, faces, the key part of a map or
document) may sit under it. These are deliberate over-estimates — the app's layout changes with versions,
devices and caption length; check on a phone before publishing.

| Zone | Pixels | Fractions (for `check --caption-zone`) | What covers it |
| --- | --- | --- | --- |
| Top bar | y < 160 | `x0=0;y0=0;x1=1;y1=.083` | status bar, "Following / For You", search, LIVE |
| Right rail | x > 940 and 700 < y < 1500 | `x0=.870;y0=.365;x1=1;y1=.781` | avatar, like, comment, save, share, sound disc |
| Bottom area | y > 1480 | `x0=0;y0=.771;x1=1;y1=1` | username, description, sound name, progress bar |
| Side margins | x < 60, x > 1020 | — | rounded corners, cropping on some phones |

The generic Premiere action-safe / title-safe boxes (`/hyperframes-studio` § 4) are looser than this; use
these zones for TikTok. `node scripts/tiktok_qc.mjs --print-checks` prints the three `npx hyperframes check
--caption-zone …` passes that flag any text inside a zone; the QC sheet draws them in red.

## Layout bands (a proven default, adapt per piece)

| Band | y range | Holds |
| --- | --- | --- |
| Header | 170–350 | date or chapter tag (left), part tag (right), a slim timeline or progress device |
| Stage | 360–1220 | the image: archive photo, map, diagram, big number, quote card |
| Source line | ≈ 1232 | `SOURCE …` in small mono, left aligned |
| Captions | 1300–1460 | one or two caption lines, centred in x 60–930 |
| Bottom | > 1480 | leave empty (TikTok's description lands here) |

Full-bleed images may extend under the interface as long as nothing that must be read or recognised sits
there. Keep text blocks inside x 60–930 in the lower half (the right rail starts around x 940).

## Shot table — one row per frame (Step 5)

Write these as bullets on each `STORYBOARD.md` frame (the parser keeps them under `extra`), and mirror the
table in `DIRECTION.md` for review:

| Column | Storyboard key | Content |
| --- | --- | --- |
| Duration | `duration` | seconds; after TTS, the real voice timing wins |
| Narration | `voiceover` | the spoken line (locked copy in `SCRIPT.md`) |
| Image or video | `image` | file or registry block + **source and licence**, or `invented: <what>` / `reconstruction: <what>` |
| Camera | `camera` | `static`, `ken-burns in <focus>`, `ken-burns out`, `pan <dir>`, `punch-in <focus> @<s>`, `reframe <from>→<to>` |
| Animation | `animation` | the reveal: e.g. `number count-up`, `line draw`, `stagger list`, `map highlight`, `type slam` |
| On-screen text | `on_screen` | the words shown (≤ 9 per block), with their role: `title`, `label`, `number`, `quote`, `source` |
| Sound effect | `sfx` | `none` or the cue and the word it lands on: `whoosh on "mais"`, `impact on "8,62"` |
| Transition | `transition_in` | registry names: `cut`, `crossfade`, `blur-crossfade`, `push-slide UP/DOWN/LEFT/RIGHT`, `zoom-through`, `squeeze` |
| Visual changes | `changes` | seconds from the frame start where the picture visibly changes: `0, 1.8, 3.4` |

`retention_lint.mjs` checks that every frame has these keys and that the gaps between visual changes stay
short.

## Mapping to HyperFrames

| Column value | How to build it | Owner |
| --- | --- | --- |
| Ken Burns, punch-in, reframe, pan | animate an inner wrapper (`#id-cam`), never the timed clip | `/hyperframes-keyframes` |
| Reveals (count-up, stagger, line draw, type slam) | pick 1–2 rules or a blueprint | `/hyperframes-animation` `rules-index.md`, `blueprints-index.md` |
| Map highlight | SVG overlay on a real map image (OSM, © contributors) or `/motion-graphics` map category | `/motion-graphics` |
| Named looks (film grain, archive paper, glitch) | `npx hyperframes catalog --query "<look>" --json` before hand-building | `/hyperframes-registry` |
| Archive photo treatment (dust, grade, face hiding) | canonical media treatments | `/media-use` `references/media-treatments.md` |
| Transitions | registry transition names; repeat 2–3 kinds per video | `/hyperframes-animation` |

## Pacing rules

- A visible change every 2–4 s: a cut, a new element, a camera move starting, a number changing. In the first
  10 s, every 1.5–3 s. A frozen picture longer than ~5 s needs a reason (a held beat before a reveal, ≤ 2 s
  of silence).
- Match cuts to the narration: cut on the word that names the new image, not before it.
- One focal point per frame; a second element appears only when the voice names it.
- Repeat the visual grammar (same stage, same transition family) so changes read as progress, not chaos.
- Text on screen holds at least 1.2 s plus 0.3 s per word, and never changes while the voice is mid-word.
- During a crossfade or push, the outgoing shot's texts leave first and the incoming ones arrive after the image
  transition (one text layer per shot): two texts never overlap, even for 0.4 s.
- A label that names a place or a date appears on the word that says it — it is also the cheapest visual change.
- Titles in the header band: at 1080 px wide, 62–66 px keeps a 5–7-word title on one or two lines above the stage.

## Type scale on a phone (1080 × 1920)

| Role | Size | Notes |
| --- | --- | --- |
| Hook / title | 84–120 px, weight 700–800 | ≤ 6 words, 2 lines max |
| Big number or date | 150–230 px condensed | one per frame |
| Body statement | 56–68 px | ≤ 3 lines |
| Labels on maps and photos | 30–36 px uppercase | dark box behind, 1.5 px accent border |
| Captions | 48–60 px | see `audio-captions.md` |
| Source / credit | 15–20 px mono | contrast ≥ 4.5:1, never under the interface |
