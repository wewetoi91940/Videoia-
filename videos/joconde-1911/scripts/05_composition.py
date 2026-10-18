#!/usr/bin/env python3
"""Montage : écrit index.html (composition HyperFrames) et les sous-titres (SRT) à partir de la voix réelle.

- plans, durées et ancrages : scripts/plans.json + build/chronologie.json (via chrono.py) ;
- sous-titres : une ligne, ≤ 27 caractères, découpés par groupes de sens, largeur mesurée dans la police réelle ;
- zones sûres : tout texte entre x = 60 et 940 px et entre y = 200 et 1 440 px (contrôlé ici, puis par `hyperframes check`).
Sorties : index.html, build/sous-titres.json, livrables/joconde-1911.srt
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from PIL import ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrono  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAFE = {"x0": 60, "x1": 940, "y0": 200, "y1": 1440}
SUB_FONT = ROOT / "assets/fonts/Oswald-Bold.ttf"
SUB_SIZE = 66
SUB_MAX_CHARS = 27
SUB_MAX_W = SAFE["x1"] - SAFE["x0"] - 40          # 840 px de texte, marge comprise
SUB_Y = 1300
SUB_TAIL = 0.4          # la dernière ligne d'une phrase reste 0,4 s après la voix (dans la pause)
WEAK_END = {"de", "la", "le", "les", "un", "une", "à", "au", "du", "des", "en", "sur", "dans", "par", "pour", "il",
            "qui", "ne", "que", "son", "sa", "ses", "ce", "l'a", "d'une", "d'un", "l'avait", "est", "a", "quatre", "deux"}
LABEL_COLORS = {"ARCHIVE": "#f2ead8", "ILLUSTRATION": "#e0a84a", "CARTE SCHÉMATIQUE": "#7fc4c0"}
VISUELS = {
    "mur_vide": "assets/illustrations/mur_vide.png", "crochets": "assets/illustrations/crochets.png",
    "joconde": "assets/illustrations/joconde.png", "soupcons": "assets/illustrations/soupcons.png",
    "prison": "assets/illustrations/prison.png", "empreinte": "assets/illustrations/empreinte.png",
    "fichier": "assets/illustrations/fichier.png", "chambre": "assets/illustrations/chambre.png",
    "carte": "assets/cartes/carte_paris_florence.png", "arrestation": "assets/illustrations/arrestation.png",
    "vitrine": "assets/illustrations/vitrine.png", "escalier": "assets/illustrations/escalier.png",
    "joconde_detail": "assets/illustrations/joconde_detail.png",
}

font = ImageFont.truetype(str(SUB_FONT), SUB_SIZE)


def text_w(s: str) -> float:
    return font.getlength(s) * 1.01  # +1 % : léger interlettrage CSS


def _attach_punct(words: list[dict]) -> list[dict]:
    out = []
    for w in words:
        if w["mot"] in (":", ";", "?", "!") and out:
            out[-1] = {**out[-1], "mot": out[-1]["mot"] + "\u00a0" + w["mot"], "fin": w["fin"]}
        else:
            out.append(dict(w))
    return out


def _fits(text: str) -> bool:
    return len(text) <= SUB_MAX_CHARS and text_w(text) <= SUB_MAX_W


def carton_cls(text: str) -> str:
    """Un carton tient toujours sur une ligne : corps réduit au-delà de 22 caractères."""
    return "carton long" if len(text) > 22 else "carton"


def chunk_sentence(words: list[dict], sent_end: float) -> list[list[dict]]:
    """Découpe optimale (programmation dynamique) : lignes lisibles (≥ 0,85 s), coupures sur la ponctuation,
    jamais de fin de ligne sur un mot-outil, dans la limite stricte de 27 caractères et 840 px."""
    words = _attach_punct(words)
    n = len(words)
    INF = float("inf")
    best = [0.0] + [INF] * n
    back = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(j):
            text = " ".join(w["mot"] for w in words[i:j])
            if not _fits(text):
                continue
            end = words[j]["debut"] if j < n else sent_end + SUB_TAIL
            dur = end - words[i]["debut"]
            last = words[j - 1]["mot"]
            cost = 0.5 + 40 * max(0.0, 0.85 - dur)
            if j < n:
                cost += 0 if re.search(r"[,;:.?!]$", last) else 1.0
                cost += 50.0 if last.lower().strip(",") in WEAK_END else 0   # quasi interdit
            if best[i] + cost < best[j]:
                best[j], back[j] = best[i] + cost, i
    cuts, j = [], n
    while j > 0:
        cuts.append((back[j], j))
        j = back[j]
    return [words[i:j] for i, j in reversed(cuts)]


def subtitles(tl: dict) -> list[dict]:
    subs = []
    for p in tl["phrases"]:
        chunks = chunk_sentence(p["mots"], p["fin"])
        for i, ch in enumerate(chunks):
            start = ch[0]["debut"]
            end = chunks[i + 1][0]["debut"] if i + 1 < len(chunks) else p["fin"] + SUB_TAIL
            subs.append({"debut": round(start, 3), "fin": round(end, 3), "texte": " ".join(w["mot"] for w in ch), "phrase": p["id"]})
    for i in range(len(subs) - 1):  # pas de chevauchement
        subs[i]["fin"] = min(subs[i]["fin"], subs[i + 1]["debut"])
    subs[0]["debut"] = 0.0          # premier sous-titre visible dès la première image
    subs[-1]["fin"] = tl["duree"]
    for s in subs:
        s["chars"] = len(s["texte"])
        s["largeur_px"] = round(text_w(s["texte"]), 1)
        s["duree"] = round(s["fin"] - s["debut"], 3)
    return subs


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(subs: list[dict], path: Path) -> None:
    lines = []
    for i, s in enumerate(subs, 1):
        lines += [str(i), f"{srt_time(s['debut'])} --> {srt_time(s['fin'])}", s["texte"].replace(" ", " "), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def build(tl: dict, subs: list[dict]) -> str:
    D = tl["duree"]
    carte = json.loads((ROOT / "assets/cartes/carte.json").read_text())
    (px, py), (fx, fy) = carte["villes_px_cadre_1080x1920"]["Paris"], carte["villes_px_cadre_1080x1920"]["Florence"]
    cxm, cym = (px + fx) / 2 + 60, (py + fy) / 2 - 150
    route = f"M{px},{py} Q{cxm:.1f},{cym:.1f} {fx},{fy}"
    shots_html, tween = [], []
    plans = tl["plans"]
    for i, p in enumerate(plans):
        start, dur = p["debut"], p["duree"]
        fade_next = i + 1 < len(plans) and plans[i + 1].get("transition") == "fondu"
        clip_dur = dur + (0.5 if fade_next else 0)
        sid = p["id"].lower()
        inner = [f'<img id="{sid}-img" class="kb" src="{VISUELS[p["visuel"]]}" alt="">']
        if p["visuel"] == "carte":
            inner.append(
                f'<svg id="{sid}-svg" class="overlay" viewBox="0 0 1080 1920" width="1080" height="1920">'
                f'<path id="route" d="{route}" fill="none" stroke="#e0b04c" stroke-width="7" stroke-linecap="round" stroke-dasharray="18 16"/>'
                f'<circle cx="{px}" cy="{py}" r="13" fill="#f2ead8"/>'
                f'<circle id="florence-dot" cx="{fx}" cy="{fy}" r="13" fill="#f2ead8"/>'
                f'<circle id="florence-ring" cx="{fx}" cy="{fy}" r="13" fill="none" stroke="#e0b04c" stroke-width="5"/>'
                f'<text x="{px + 26}" y="{py - 26}" class="city">PARIS</text>'
                f'<text id="florence-label" x="{fx - 26}" y="{fy - 26}" class="city" text-anchor="end">FLORENCE</text></svg>')
        if p.get("revele") and p["visuel"] in ("empreinte", "vitrine"):
            inner.append(f'<div id="{sid}-glow" class="glow glow-{p["visuel"]}"></div>')
        cam = f'<div id="{sid}-cam" class="cam">{"".join(inner)}</div>'
        label_color = LABEL_COLORS[p["type"]]
        allow = " data-layout-allow-overlap data-layout-allow-occlusion" if p.get("transition") == "fondu" or (i + 1 < len(plans) and plans[i + 1].get("transition") == "fondu") else ""  # même étiquette, même place, pendant le fondu
        over = [f'<div class="label"{allow}><span class="dot" style="background:{label_color}"></span>{esc(p["type"])}</div>']
        if p.get("legende"):
            over.append(f'<div class="legende">{esc(p["legende"])}</div>')
        if p.get("carton"):
            over.append(f'<div id="{sid}-carton" class="{carton_cls(p["carton"])}"><span>{esc(p["carton"])}</span></div>')
        if p.get("carton_2"):
            over.append(f'<div id="{sid}-carton2" class="{carton_cls(p["carton_2"]["texte"])}"><span>{esc(p["carton_2"]["texte"])}</span></div>')
        if p.get("carton_fin"):
            over.append(f'<div id="{sid}-cartonfin" class="{carton_cls(p["carton_fin"])}"><span>{esc(p["carton_fin"])}</span></div>')
        shots_html.append(
            f'<section id="{sid}" class="clip shot" data-start="{start}" data-duration="{clip_dur:.4f}" data-track-index="{1 + i % 2}">'
            f'<div id="{sid}-fade" class="fade">{cam}{"".join(over)}</div></section>')
        de, a = p["camera"]["de"], p["camera"]["a"]
        tween.append(f'tl.fromTo("#{sid}-cam", {{scale:{de[0]}, x:{de[1]}, y:{de[2]}}}, '
                     f'{{scale:{a[0]}, x:{a[1]}, y:{a[2]}, duration:{clip_dur:.4f}, ease:"sine.inOut"}}, {start});')
        if p.get("transition") == "fondu":
            tween.append(f'tl.fromTo("#{sid}-fade", {{opacity:0}}, {{opacity:1, duration:0.5, ease:"sine.inOut"}}, {start});')
        if p.get("carton"):
            tween.append(f'tl.fromTo("#{sid}-carton", {{opacity:{1 if i == 0 else 0}, y:{0 if i == 0 else 10}}}, '
                         f'{{opacity:1, y:0, duration:0.3, ease:"power2.out"}}, {start + (0 if i == 0 else 0.1):.3f});')
            if p.get("carton_2"):
                t2 = p["carton_2"]["t"]
                tween.append(f'tl.to("#{sid}-carton", {{opacity:0, duration:0.15, ease:"power1.in"}}, {t2 - 0.15:.3f});')
        if p.get("carton_2"):
            t2 = p["carton_2"]["t"]
            tween.append(f'tl.fromTo("#{sid}-carton2", {{opacity:0, y:10}}, {{opacity:1, y:0, duration:0.3, ease:"power2.out"}}, {t2:.3f});')
        if p.get("carton_fin"):
            tween.append(f'tl.fromTo("#{sid}-cartonfin", {{opacity:0}}, {{opacity:1, duration:0.8, ease:"sine.inOut"}}, {D - 1.0:.3f});')
        if p["visuel"] == "carte":
            tf = p["revele"]["t"]
            tween.append(f'tl.fromTo("#route", {{strokeDashoffset:1400, strokeDasharray:"1400 1400"}}, '
                         f'{{strokeDashoffset:0, duration:{tf - start - 0.2:.3f}, ease:"power1.inOut"}}, {start + 0.2:.3f});')
            tween.append(f'tl.fromTo("#florence-ring", {{attr:{{r:13}}, opacity:1}}, {{attr:{{r:70}}, opacity:0, duration:1.0, ease:"power2.out"}}, {tf:.3f});')
            tween.append(f'tl.fromTo("#florence-label", {{opacity:0}}, {{opacity:1, duration:0.3, ease:"power2.out"}}, {tf - 0.1:.3f});')
        if p.get("revele") and p["visuel"] in ("empreinte", "vitrine"):
            tr = p["revele"]["t"]
            if p["visuel"] == "empreinte":
                tween.append(f'tl.fromTo("#{sid}-glow", {{opacity:0}}, {{opacity:1, duration:0.6, ease:"power2.out"}}, {tr:.3f});')
            else:
                tween.append(f'tl.fromTo("#{sid}-glow", {{xPercent:-120, opacity:1}}, {{xPercent:120, opacity:1, duration:1.1, ease:"sine.inOut"}}, {tr:.3f});')
    subs_html, sub_tw = [], []
    for k, s in enumerate(subs):
        subs_html.append(f'<div id="sub{k}" class="clip sub" data-start="{s["debut"]:.3f}" data-duration="{s["fin"] - s["debut"]:.3f}" '
                         f'data-track-index="9"><span>{esc(s["texte"])}</span></div>')
    return TEMPLATE.format(
        duration=f"{D:.4f}", shots="\n      ".join(shots_html), subs="\n      ".join(subs_html),
        tweens="\n        ".join(tween + sub_tw), sub_y=SUB_Y, safe_x0=SAFE["x0"], safe_x1=SAFE["x1"],
        safe_w=SAFE["x1"] - SAFE["x0"], sub_size=SUB_SIZE,
    )


TEMPLATE = """<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Le vol de la Joconde (1911)</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Oswald"; src: url("assets/fonts/Oswald-Regular.woff2") format("woff2"); font-weight: 400; }}
      @font-face {{ font-family: "Oswald"; src: url("assets/fonts/Oswald-Bold.woff2") format("woff2"); font-weight: 700; }}
      @font-face {{ font-family: "EB Garamond"; src: url("assets/fonts/EBGaramond-Regular.woff2") format("woff2"); font-weight: 400; }}
      @font-face {{ font-family: "EB Garamond"; src: url("assets/fonts/EBGaramond-Bold.woff2") format("woff2"); font-weight: 700; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #0c0b0a; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #0c0b0a; }}
      .clip {{ position: absolute; inset: 0; }}
      .shot {{ overflow: hidden; }}
      .fade {{ position: absolute; inset: 0; }}
      .cam {{ position: absolute; inset: 0; transform-origin: 50% 46%; }}
      .kb {{ position: absolute; inset: 0; width: 1080px; height: 1920px; object-fit: cover; display: block; }}
      .overlay {{ position: absolute; inset: 0; }}
      .city {{ font-family: "Oswald", sans-serif; font-weight: 700; font-size: 46px; letter-spacing: 0.08em; fill: #f2ead8; }}
      .glow {{ position: absolute; inset: 0; pointer-events: none; mix-blend-mode: screen; opacity: 0; }}
      .glow-empreinte {{ background: radial-gradient(circle at 556px 862px, rgba(190, 240, 245, 0.55) 0, rgba(120, 200, 210, 0.18) 260px, rgba(0, 0, 0, 0) 470px); }}
      .glow-vitrine {{ background: linear-gradient(105deg, rgba(255, 255, 255, 0) 38%, rgba(255, 248, 230, 0.22) 50%, rgba(255, 255, 255, 0) 62%); }}
      .label {{ position: absolute; left: {safe_x0}px; top: 200px; display: flex; align-items: center; gap: 12px;
               font-family: "Oswald", sans-serif; font-weight: 700; font-size: 26px; letter-spacing: 0.16em; color: #f2ead8;
               background: rgba(10, 9, 8, 0.62); padding: 8px 16px 9px 14px; border-radius: 4px; }}
      .label .dot {{ display: block; width: 12px; height: 12px; border-radius: 50%; }}
      .legende {{ position: absolute; left: {safe_x0}px; top: 264px; max-width: {safe_w}px; font-family: "EB Garamond", serif;
                 font-size: 30px; line-height: 1.25; color: #efe7d4; background: rgba(10, 9, 8, 0.62); padding: 5px 14px 7px; border-radius: 4px; }}
      .carton {{ position: absolute; left: {safe_x0}px; width: {safe_w}px; top: 340px; text-align: center;
                font-family: "EB Garamond", serif; font-weight: 700; font-size: 50px; letter-spacing: 0.06em; color: #f4ecd8; }}
      .carton span {{ display: inline-block; white-space: nowrap; background: rgba(10, 9, 8, 0.66); padding: 6px 26px 10px; border-radius: 4px; }}
      .carton.long {{ font-size: 42px; letter-spacing: 0.03em; }}
      .sub {{ display: flex; align-items: center; justify-content: center; }}
      .sub span {{ position: absolute; left: {safe_x0}px; width: {safe_w}px; top: {sub_y}px; transform: translateY(-50%);
                  text-align: center; white-space: nowrap; font-family: "Oswald", sans-serif; font-weight: 700; font-size: {sub_size}px;
                  line-height: 1.15; color: #fbf7ee; -webkit-text-stroke: 9px rgba(12, 10, 8, 0.92); paint-order: stroke fill;
                  text-shadow: 0 4px 14px rgba(0, 0, 0, 0.55); }}
      #vignette {{ position: absolute; inset: 0; pointer-events: none;
                   background: radial-gradient(ellipse 80% 64% at 50% 46%, rgba(0, 0, 0, 0) 60%, rgba(0, 0, 0, 0.38) 100%); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{duration}" data-fps="30" data-width="1080" data-height="1920">
      {shots}
      <div id="vignette"></div>
      {subs}
      <audio id="mix" src="build/mix_master.wav" data-start="0" data-duration="{duration}" data-track-index="20"></audio>
    </div>
    <script>
      (function () {{
        const tl = gsap.timeline({{ paused: true }});
        {tweens}
        window.__timelines["main"] = tl;
        tl.seek(0);
      }})();
    </script>
  </body>
</html>
"""


def main() -> None:
    tl = chrono.load()
    subs = subtitles(tl)
    bad = [s for s in subs if s["chars"] > SUB_MAX_CHARS or s["largeur_px"] > SUB_MAX_W]
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/sous-titres.json").write_text(json.dumps(subs, ensure_ascii=False, indent=1))
    (ROOT / "livrables").mkdir(exist_ok=True)
    write_srt(subs, ROOT / "livrables/joconde-1911.srt")
    (ROOT / "index.html").write_text(build(tl, subs), encoding="utf-8")
    print(f"composition : {len(tl['plans'])} plans, {len(subs)} sous-titres, durée {tl['duree']} s")
    for s in subs:
        print(f"  {s['debut']:6.2f}–{s['fin']:6.2f}  {s['chars']:2d} car. {s['largeur_px']:5.0f} px  {s['texte']}")
    if bad:
        sys.exit(f"sous-titres hors limites : {bad}")


if __name__ == "__main__":
    main()
