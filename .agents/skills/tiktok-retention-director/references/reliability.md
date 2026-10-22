# Reliability — history, news, numbers, quotes, media rights

Applies from Step 1 to delivery, to any factual claim: a date, a number, a name, a quote, a cause.

## The fact ledger (`SOURCES.md`)

One row per claim used anywhere (narration, on-screen text, caption, hook, description):

| Claim (as used) | Source (title, publisher, date, URL) | Status | Notes |
| --- | --- | --- | --- |

Status vocabulary:

- `established` — stated by at least one reliable source and contradicted by none found (two independent
  sources for anything surprising, contested or numeric);
- `estimate` — a figure given as an estimate; attribute it in the script ("selon la préfecture",
  "d'après les historiens") and on screen ("≈", "selon …");
- `disputed` — sources disagree; the video says so or does not use the claim;
- `hypothesis` — an interpretation; worded as one ("peut-être", "selon une hypothèse") and never in the hook.

A claim with no source row is not used. Read the source itself (not a search snippet) before marking it
`established`; respect `robots.txt` and paywalls; keep the URL.

## Wording on screen and in narration

- Established: plain statement. Estimate: attributed and approximate. Disputed: both versions or not at all.
  Hypothesis: conditional, attributed.
- Dates and hours: never invented or "made precise" (a period stays a period: "fin janvier", not "28 janvier
  à 14 h" unless sourced).
- Quotes: verbatim from the source, attributed (who, when, where); a paraphrase is not shown between quotation
  marks.
- No invented dialogue, inner thoughts or "eyewitness" lines for real people.

## Images, footage, music

- Prefer, in order: public-domain archives (Wikimedia Commons PD, Gallica, Library of Congress, national
  archives), free licences (CC0, CC BY, CC BY-SA — credit author and licence on screen), the user's own
  material, OpenStreetMap maps (© OpenStreetMap contributors, ODbL), invented graphics.
- Check the licence on the file page itself; avoid NC/ND for a publication that may be monetised.
- Wikimedia: read the `File:` page (author, date, source, licence), then download a standard thumbnail width
  (`…/thumb/<h>/<hh>/<name>/1280px-<name>`, or 960 / 500) with a descriptive User-Agent; originals and rapid series of
  requests are refused with HTTP 429. When `upload.wikimedia.org` answers 429, the same path on
  `https://thumb.wikimedia.org/wikipedia/commons/thumb/…` has worked; space requests out and keep the files. Keep the
  page URL in `SOURCES.md`.
- Text read inside an archive (a motto, a printed caption, a sign) can be shown verbatim with its translation and
  source; a caption reported by a secondary source but absent from your copy of the image is not quoted.
- Never present an image as showing an event it does not show. A photo of the place in another period is
  labelled ("le lieu aujourd'hui", "photo d'illustration"); a reconstruction or an AI image is labelled
  ("reconstitution", "image générée") and never imitates a real archive.
- Private persons recognisable in recent photos: blur faces (`/media-use` media treatments). Archive photos
  more than a century old: keep as published, credited.
- Music and sound effects: generated or licensed for publication; no sound that could pass for a recording of
  the event.
- Credit line on every borrowed image (author · licence · source), plus a sources card or description text.

## TikTok labels

When narration or images are AI-generated, the upload must use TikTok's "AI-generated content" label; say
so in the delivery note. The description lists the main sources.
