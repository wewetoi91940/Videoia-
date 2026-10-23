#!/usr/bin/env python3
"""Montage du test « crue de 1910 » (TikTok 1080 × 1920, ≈ 43 s), dirigé avec la skill tiktok-retention-director.

Entrées : STORYBOARD.md (plans et textes), SCRIPT.md (texte lu), build/voix/l1..l8.wav (voix Kokoro locale).
Étapes : place la voix (coupe de chaque plan sur son premier mot), transcrit la voix (Whisper local) pour dater chaque
mot affiché, mixe musique et bruitages avec le mixeur du projet Marseille (04_audio.mixer : −14 LUFS, crête vraie
≤ −1,5 dBTP, musique ≥ 15 dB sous la voix), découpe les sous-titres (05_composition.sous_titres), écrit index.html.
Sorties : index.html, build/voix.wav, build/mix_master.wav, build/plans_calcules.json, build/audio_mesures.json.
"""
import html
import importlib.util
import json
import re
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import soundfile as sf
from num2words import num2words
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
MARSEILLE = ROOT.parent / "marseille-17-octobre" / "scripts"


def module(chemin):
    spec = importlib.util.spec_from_file_location(chemin.stem.replace("0", "m"), chemin)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


A = module(MARSEILLE / "04_audio.py")
C = module(MARSEILLE / "05_composition.py")
SR = A.SR
FPS = 30
DEBUT = 0.12                  # premier mot
GAPS = {2: .3, 3: .3, 4: .55, 5: .3, 6: .5, 7: .5, 8: .6}   # silence avant chaque ligne
TENUE = 2.2                   # image finale après le dernier mot
AMBIANCE = {1: "ouverture", 2: "contexte", 3: "tension", 4: "arret", 5: "tension", 6: "tension", 7: "chiffres", 8: "fin"}
POULS = {5, 6}
ft, esc = C.ft, C.esc


# ------------------------------------------------------------------------------------------------ lecture
def storyboard():
    s = (ROOT / "STORYBOARD.md").read_text()
    plans = []
    for bloc in re.split(r"\n## Frame ", s)[1:]:
        tete, *lignes = bloc.split("\n")
        p = {"n": int(tete.split()[0]), "titre": tete.split("—", 1)[1].strip()}
        for l in lignes:
            m = re.match(r"- ([a-z_]+): (.*)", l)
            if m:
                p[m.group(1)] = m.group(2).strip()
        p["voiceover"] = p["voiceover"].strip('"')
        plans.append(p)
    return plans


def lignes_lues():
    return [l.strip() for l in re.findall(r"\n\n    (.+)", (ROOT / "SCRIPT.md").read_text())]


def bornes_parole(a, sr, seuil_db=-38):
    """Début et fin de la parole dans un clip (énergie par tranches de 10 ms)."""
    n = int(0.01 * sr)
    e = np.array([np.sqrt(np.mean(a[i:i + n] ** 2)) for i in range(0, len(a) - n, n)])
    ok = np.where(20 * np.log10(e + 1e-9) > 20 * np.log10(e.max()) + seuil_db)[0]
    return ok[0] * 0.01, (ok[-1] + 1) * 0.01


# ---------------------------------------------------------------------------------------- alignement des mots
def normal(t):
    """Mot → lettres prononcées : chiffres en toutes lettres (« 000 » de « 20 000 » se dit « mille »)."""
    t = t.lower().replace("\u2019", "'")
    if t.strip(".,;:") == "000":
        return "mille"
    t = re.sub(r"(\d+),(\d+)", lambda m: f"{m.group(1)} virgule {m.group(2)}", t)
    return re.sub(r"\d+", lambda m: " " + num2words(int(m.group()), lang="fr") + " ", t)


def lettres(t):
    """Chaîne de lettres + index du mot d'origine pour chaque lettre (mots séparés par des espaces)."""
    s, idx = [], []
    for k, w in enumerate(t.split()):
        for ch in normal(w):
            if ch.isalpha():
                s.append(ch)
                idx.append(k)
    return "".join(s), idx


def correspondance(a, b):
    """Pour chaque caractère de a, l'indice du caractère apparié dans b (interpolé entre deux appariements)."""
    m = [None] * len(a)
    for bl in SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(bl.size):
            m[bl.a + k] = bl.b + k
    connus = [i for i, v in enumerate(m) if v is not None]
    for i in range(len(m)):
        if m[i] is None and connus:
            g = max([c for c in connus if c < i], default=None)
            d = min([c for c in connus if c > i], default=None)
            m[i] = m[g] if d is None else m[d] if g is None else round(m[g] + (m[d] - m[g]) * (i - g) / (d - g))
    return m


def transcrire(wav):
    travail = BUILD / "transcription"
    travail.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["npx", "--yes", "hyperframes@0.8.166", "transcribe", str(wav), "-l", "fr", "-m", "small", "-e",
                        "whisper", "--json", "-d", str(travail)], capture_output=True, text=True)
    if r.returncode or not (travail / "transcript.json").exists():
        sys.exit(f"transcription impossible : {r.stderr[-400:]}")
    return json.loads((travail / "transcript.json").read_text())


def dater_mots(affiche, lu, mots_w, t0, t1):
    """Heure de début de chaque mot affiché : affiché ↔ lu (caractères) ↔ transcription (caractères → mots datés)."""
    mots_w = [w for w in mots_w if w["end"] > t0 - 0.2 and w["start"] < t1 + 0.2]
    wc, wi = lettres(" ".join(w["text"] for w in mots_w))
    lc, _ = lettres(lu)
    ac, ai = lettres(affiche)
    a2l, l2w = correspondance(ac, lc), correspondance(lc, wc) if wc else None
    debuts = {}
    for i, k in enumerate(ai):
        if k in debuts:
            continue
        if l2w:
            j = l2w[a2l[i]]
            w = mots_w[wi[j]]
            # position de la lettre dans son mot transcrit → interpolation dans [start, end]
            pos = wi[:j + 1].count(wi[j]) - 1
            tot = max(1, wi.count(wi[j]))
            debuts[k] = w["start"] + (w["end"] - w["start"]) * pos / tot
        else:
            debuts[k] = t0 + (t1 - t0) * i / max(1, len(ac))
    toks = affiche.split()
    out = []
    for k, tok in enumerate(toks):
        d = debuts.get(k, out[-1]["debut"] if out else t0)
        out.append({"mot": tok, "debut": round(max(t0, min(d, t1)), 3)})
    for a, b in zip(out, out[1:]):
        b["debut"] = max(b["debut"], a["debut"] + 0.05)
        a["fin"] = b["debut"]
    out[-1]["fin"] = round(t1, 3)
    return out


# ----------------------------------------------------------------------------------------------- composition
CSS = """
@font-face { font-family: "Newsreader"; src: url("assets/fonts/Newsreader-400.woff2") format("woff2"); font-weight: 400; }
@font-face { font-family: "Newsreader"; src: url("assets/fonts/Newsreader-600.woff2") format("woff2"); font-weight: 600; }
@font-face { font-family: "Newsreader"; src: url("assets/fonts/Newsreader-800.woff2") format("woff2"); font-weight: 800; }
@font-face { font-family: "Oswald"; src: url("assets/fonts/Oswald-Regular.woff2") format("woff2"); font-weight: 400; }
@font-face { font-family: "Oswald"; src: url("assets/fonts/Oswald-Bold.woff2") format("woff2"); font-weight: 700; }
:root { --bg: #0f0d0a; --fg: #f1e7d3; --mut: #b9ad97; --acc: #e3a93f; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 100%; height: 100%; overflow: hidden; background: var(--bg); }
#root { position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--bg); color: var(--fg); font-family: "Newsreader", serif; }
.plan { position: absolute; inset: 0; overflow: hidden; }
.inner { position: absolute; inset: 0; background: var(--bg); }
.scene { position: absolute; left: 0; top: 360px; width: 1080px; height: 860px; overflow: hidden; background: #000; }
.cam { position: absolute; inset: 0; }
.cam img { position: absolute; left: 0; top: 0; width: 100%; height: 100%; object-fit: cover; display: block; }
.ombre { position: absolute; left: 0; right: 0; bottom: 0; height: 240px; background: rgba(8, 7, 5, 0.55); }
.calque { position: absolute; inset: 0; }
.puce { position: absolute; left: 40px; top: 24px; font-family: "Oswald"; font-size: 22px; letter-spacing: 0.16em; color: var(--bg);
        background: var(--acc); padding: 3px 12px 5px; }
.credit { position: absolute; left: 40px; bottom: 18px; max-width: 880px; font-family: "Oswald"; font-size: 19px; letter-spacing: 0.04em;
          color: #f1e7d3; background: rgba(10, 9, 7, 0.78); padding: 3px 10px 4px; }
.entete { position: absolute; left: 60px; top: 178px; width: 900px; }
.kicker { font-family: "Oswald"; font-size: 26px; letter-spacing: 0.2em; color: var(--mut); }
.titre { font-weight: 800; font-size: 62px; line-height: 1.02; margin-top: 4px; }
.titre em { font-style: normal; color: var(--acc); }
.tampon { font-family: "Oswald"; font-weight: 700; font-size: 84px; line-height: 1; color: var(--acc); margin-top: 6px; letter-spacing: 0.02em; }
.etiquette { position: absolute; font-family: "Oswald"; font-size: 34px; letter-spacing: 0.05em; text-transform: uppercase;
             color: var(--fg); background: rgba(12, 10, 7, 0.88); border: 1.5px solid rgba(227, 169, 63, 0.75); padding: 6px 16px 8px; }
.chiffre { position: absolute; left: 40px; bottom: 60px; font-family: "Oswald"; font-weight: 700; font-size: 180px; line-height: 1;
           color: var(--acc); }
.chiffre small { display: block; font-size: 44px; font-weight: 400; color: var(--fg); letter-spacing: 0.04em; margin-top: 8px; }
.document { position: absolute; left: 170px; top: 24px; width: 740px; height: 529px; background: #e9dfca; padding: 10px; }
.document img { width: 100%; height: 100%; object-fit: contain; display: block; }
.horloge { position: absolute; left: 240px; top: 40px; width: 600px; height: 600px; }
.schema { position: absolute; left: 60px; top: 680px; width: 900px; display: flex; align-items: center; gap: 24px; }
.boite { font-family: "Oswald"; font-size: 32px; letter-spacing: 0.04em; color: var(--fg); border: 2px solid var(--acc); padding: 10px 18px 12px; }
.fleche { font-family: "Oswald"; font-size: 44px; color: var(--acc); }
.sources { position: absolute; left: 60px; top: 1232px; max-width: 880px; font-family: "Oswald"; font-size: 20px; letter-spacing: 0.04em;
           color: var(--fg); background: rgba(12, 10, 7, 0.8); padding: 5px 12px; }
.sources b { color: var(--acc); font-weight: 400; letter-spacing: 0.14em; margin-right: 10px; }
.st { position: absolute; left: 50px; top: 1306px; width: 890px; text-align: center; }
.st-r { display: block; margin-bottom: 6px; }
.st-r span { font-weight: 600; font-size: 54px; line-height: 1.2; color: var(--fg); background: rgba(10, 9, 7, 0.9); padding: 2px 14px 6px;
             -webkit-box-decoration-break: clone; box-decoration-break: clone; }
.st-r .st-n { color: var(--acc); background: none; padding: 0; font-size: inherit; }
.fin-carte { position: absolute; left: 0; right: 0; bottom: 0; height: 330px; background: rgba(12, 10, 7, 0.9); padding: 28px 40px; }
.fc-titre { font-family: "Oswald"; font-weight: 700; font-size: 40px; color: var(--acc); letter-spacing: 0.04em; margin-bottom: 14px; }
.fin-carte p { font-family: "Oswald"; font-size: 23px; line-height: 1.35; color: var(--fg); margin-bottom: 8px; }
.fin-carte b { color: var(--acc); font-weight: 400; letter-spacing: 0.12em; margin-right: 8px; }
.grain { position: absolute; inset: 0; pointer-events: none; background-image: url("assets/grain.png"); opacity: 0.06; }
"""
NOMBRE = re.compile(r"\d+(?:[  ]\d{3})*(?:,\d+)?")


def sous_titre_html(texte):
    out = []
    for ligne in C.deux_lignes(texte, 31):
        parts, i = [], 0
        for m in NOMBRE.finditer(ligne):
            parts.append(esc(ligne[i:m.start()]) + f'<span class="st-n">{esc(m.group())}</span>')
            i = m.end()
        parts.append(esc(ligne[i:]))
        out.append(f'<span class="st-r"><span>{"".join(parts)}</span></span>')
    return "".join(out)


def horloge_svg():
    traits = []
    for k in range(60):
        a = k * 6
        long_ = 36 if k % 5 == 0 else 14
        larg = 7 if k % 5 == 0 else 3
        traits.append(f'<line x1="300" y1="{30}" x2="300" y2="{30 + long_}" stroke="#2a241b" stroke-width="{larg}" '
                      f'transform="rotate({a} 300 300)"/>')
    return ('<svg class="horloge" viewBox="0 0 600 600" width="600" height="600">'
            '<circle cx="300" cy="300" r="290" fill="#efe5cf" stroke="#e3a93f" stroke-width="10"/>'
            + "".join(traits) +
            '<line x1="300" y1="300" x2="300" y2="150" stroke="#2a241b" stroke-width="14" stroke-linecap="round" transform="rotate(300 300 300)"/>'
            '<line x1="300" y1="300" x2="300" y2="90" stroke="#2a241b" stroke-width="9" stroke-linecap="round" transform="rotate(60 300 300)"/>'
            '<g id="f4-sec"><line x1="300" y1="340" x2="300" y2="70" stroke="#b5481f" stroke-width="4"/>'
            '<circle cx="300" cy="300" r="12" fill="#b5481f"/></g></svg>')


def main():
    plans = storyboard()
    lus = lignes_lues()
    assert len(plans) == len(lus) == 8, (len(plans), len(lus))

    # ---- voix : chaque ligne placée après la précédente ; chaque plan coupe sur son premier mot
    clips, pos, parole = [], [], []
    fin_prec = None
    for k in range(1, 9):
        a, sr = sf.read(BUILD / f"voix/l{k}.wav", dtype="float64")
        a = resample_poly(a, SR, sr) if sr != SR else a
        on, off = bornes_parole(a, SR)
        debut_parole = DEBUT if k == 1 else fin_prec + GAPS[k]
        p0 = debut_parole - on
        clips.append(a)
        pos.append(p0)
        parole.append((round(debut_parole, 3), round(p0 + off, 3)))
        fin_prec = p0 + off
    D = ft(parole[-1][1] + TENUE)
    v = np.zeros(int(round(D * SR)))
    for a, p0 in zip(clips, pos):
        i = int(round(p0 * SR))
        j = max(0, -i)
        v[max(0, i):max(0, i) + len(a) - j] += a[j:len(v) - max(0, i) + j]
    sf.write(BUILD / "voix.wav", v, SR, subtype="PCM_24")

    # ---- mots datés (transcription locale) → sous-titres
    mots_w = transcrire(BUILD / "voix.wav")
    phrases = []
    for k, (p, lu) in enumerate(zip(plans, lus), 1):
        t0, t1 = parole[k - 1]
        mots = dater_mots(p["voiceover"], lu, mots_w, t0, t1)
        phrases.append({"cle": f"l{k}", "seq": k, "texte": p["voiceover"], "debut": t0, "fin": t1, "mots": mots})
    chrono = {"phrases": phrases, "voix_fin": parole[-1][1]}
    subs = C.sous_titres(chrono, 62)

    def T(n, mot, rang=1):
        cands = [m for m in phrases[n - 1]["mots"] if C.norm(m["mot"]).startswith(C.norm(mot))]
        if len(cands) < rang:
            sys.exit(f"ancre introuvable : {mot!r} dans le plan {n}")
        return cands[rang - 1]["debut"]

    starts = [0.0] + [ft(parole[k][0] - 0.06) for k in range(1, 8)]
    fins = starts[1:] + [D]

    # ---- son : mixeur du projet Marseille (nappe par ambiance, tics d'horloge, coup sourd, coupure)
    t_stop = T(4, "s'arrêtent")
    repères = [{"type": "x", "debut": 0.0, "musique": "impact"},
               {"type": "heure", "debut": T(1, "horloges")}]
    t = starts[3] + 0.3
    while t + 0.5 < t_stop - 0.2:
        repères.append({"type": "heure", "debut": round(t, 3)})
        t += 1.0
    repères += [{"type": "x", "debut": t_stop, "musique": "coupure"},
                {"type": "x", "debut": T(7, "8,62"), "musique": "impact"},
                {"type": "heure", "debut": T(8, "arrêtée")}]
    seqs = {k: {"ambiance": AMBIANCE[k], "pouls": k in POULS} for k in range(1, 9)}
    mesures = A.mixer(v, chrono, repères, seqs, D, BUILD, avec_stems=False)
    (BUILD / "audio_mesures.json").write_text(json.dumps(mesures, ensure_ascii=False, indent=1))

    # ---- composition
    tw, sec = [], []
    sources = {1: "Wikipédia · Météo Paris", 2: "Wikipédia · Météo Paris · Paris Zigzag", 3: "Wikipédia · Météo Paris",
               4: "Wikipédia · Météo Paris", 5: "Wikipédia · Paris Zigzag", 6: "Wikipédia · Météo Paris",
               7: "Wikipédia · Paris Zigzag", 8: "Wikipédia · Paris Zigzag"}
    for k, p in enumerate(plans, 1):
        pid, t0, t1 = f"f{k}", starts[k - 1], fins[k - 1]
        trans = p.get("transition_in", "cut")
        fondu = 0.0 if k == 1 or trans == "cut" else 0.4
        debut = ft(max(0.0, t0 - fondu / 2)) if fondu else t0
        fin_clip = t1 + (0.2 if k < 8 and plans[k].get("transition_in", "cut") != "cut" else 0.0)
        corps, img = "", ""     # img : images sous la caméra ; corps : textes (un calque, effacé avant chaque fondu)
        if k == 1:
            entete = '<div class="kicker">PARIS · JANVIER 1910</div><div class="titre">La Seine arrête les <em id="f1-em">horloges</em></div>'
            # visible dès la première image ; le mot s'allume quand la voix le dit
            tw.append(f'tl.fromTo("#f1-em",{{color:"#f1e7d3"}},{{color:"#e3a93f",duration:0.25}},{ft(T(1, "horloges")):.4f});')
        else:
            kick, tamp = {2: ("PARIS", "JANVIER 1910"), 3: ("LA SEINE MONTE", "20 JANVIER"), 4: ("LE LENDEMAIN", "21 JANVIER"),
                          5: ("JANVIER 1910", "LA SEINE DÉBORDE"), 6: ("PARIS INONDÉ", "EN BARQUE"),
                          7: ("LE SOMMET", "28 JANVIER"), 8: ("AUJOURD'HUI", "LE TRAIT DE 1910")}[k]
            entete = f'<div class="kicker">{esc(kick)}</div><div id="{pid}-tp" class="tampon">{esc(tamp)}</div>'
            if k != 8:
                tw.append(f'tl.fromTo("#{pid}-tp",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{ft(t0 + 0.1):.4f});')
        image = {1: "saint-lazare", 2: "panorama", 3: "saints-peres", 5: "rue-leblanc", 6: "passy", 8: "repere-celestins"}.get(k)
        credit = {1: "Gare Saint-Lazare, 28 janvier 1910 · Agence Rol · BnF · domaine public",
                  2: "Vue depuis la tour de l'horloge de la gare de Lyon, 29 janvier 1910 · Héliotypie E. Le Deley · domaine public",
                  3: "Bateau coincé sous le pont des Saints-Pères, 21 janvier 1910 · Agence Rol · BnF · domaine public",
                  5: "Rue Leblanc (15e), janvier 1910 · Agence Rol · BnF · domaine public",
                  6: "Passerelles au quai de Passy, janvier 1910 · carte postale ND Phot. · domaine public",
                  7: "« Les inondations à Paris », plan de 1910 · Héliotypie E. Le Deley · domaine public",
                  8: "Repère de crue, port des Célestins (Paris 4e) · photo Mu, 2010 · CC BY-SA 3.0 · Wikimedia Commons"}.get(k, "")
        if image:
            pos_img = {2: "0% 50%", 6: "100% 50%", 8: "50% 60%"}.get(k, "50% 50%")
            img += (f'<div class="cam" id="{pid}-cam"><img src="assets/photos/{image}.jpg" alt="" style="object-position:{pos_img}"></div>'
                    f'<div class="ombre"></div>')
            corps += f'<div class="puce">{"ARCHIVE · 1910" if k != 8 else "AUJOURD’HUI"}</div>'
        if k == 4:
            img += ('<div class="cam" id="f4-cam">' + horloge_svg() +
                    '<div class="schema"><div id="f4-b1" class="boite">USINE D’AIR COMPRIMÉ</div><div id="f4-fl" class="fleche">→</div>'
                    '<div id="f4-b2" class="boite">HORLOGES PUBLIQUES</div></div></div>')
            corps += '<div class="puce">ILLUSTRATION</div>'
            # aiguille des secondes : un pas par seconde jusqu'à « s'arrêtent », puis plus rien
            n, t = 0, t0
            while t < t_stop - 0.05:
                tw.append(f'tl.set("#f4-sec",{{rotation:{n * 6},svgOrigin:"300 300"}},{ft(t):.4f});')
                n, t = n + 1, t + 1.0
            tw += [f'tl.fromTo("#f4-b1",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:0.5}},{ft(T(4, "l'usine")):.4f});',
                   f'tl.fromTo("#f4-fl",{{opacity:0}},{{opacity:1,duration:0.3}},{ft(T(4, "fait")):.4f});',
                   f'tl.fromTo("#f4-b2",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:0.5}},{ft(T(4, "horloges")):.4f});']
        if k == 7:
            img += f'<div class="cam" id="{pid}-cam"><div class="document"><img src="assets/photos/plan-1910.jpg" alt=""></div></div>'
            corps += '<div class="puce">ARCHIVE · 1910</div>'
            corps += (f'<div id="f7-ch" class="chiffre"><span id="f7-n">8,62 m</span><small>PONT D’AUSTERLITZ · 28 JANVIER</small></div>'
                      f'<div id="f7-j" class="etiquette" style="right:150px;top:640px">45 JOURS DE CRUE</div>')
            t862 = T(7, "8,62")
            tw += [f'tl.fromTo("#f7-ch",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{ft(t862 - 0.1):.4f});',
                   f'tl.fromTo("#f7-j",{{opacity:0}},{{opacity:1,duration:0.4}},{ft(T(7, "45")):.4f});']
        if k == 6:
            corps += ('<div id="f6-ch" class="chiffre">20 000<small>IMMEUBLES TOUCHÉS</small></div>'
                      '<div id="f6-m" class="etiquette" style="left:40px;top:90px">MÉTRO INONDÉ</div>')
            corps += '<div id="f6-p" class="etiquette" style="left:40px;top:160px">PASSERELLES · QUAI DE PASSY</div>'
            tw += [f'tl.fromTo("#f6-ch",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{ft(t0 + 0.05):.4f});',
                   f'tl.fromTo("#f6-m",{{opacity:0}},{{opacity:1,duration:0.4}},{ft(T(6, "métro")):.4f});',
                   f'tl.fromTo("#f6-p",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.4}},{ft(T(6, "passerelles")):.4f});']
        if k == 2:
            corps += ('<div id="f2-e" class="etiquette" style="left:40px;top:80px">HIVER PLUVIEUX</div>'
                      '<div id="f2-s" class="etiquette" style="left:40px;top:150px">SOLS GORGÉS D’EAU</div>')
            tw += [f'tl.fromTo("#f2-e",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.5}},{ft(T(2, "pluvieux")):.4f});',
                   f'tl.fromTo("#f2-s",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.5}},{ft(T(2, "gorgés")):.4f});']
        if k == 3:
            corps += '<div id="f3-e" class="etiquette" style="left:40px;top:80px">PONT DES SAINTS-PÈRES</div>'
            tw.append(f'tl.fromTo("#f3-e",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.4}},{ft(T(3, "ponts")):.4f});')
        if k == 8:
            entete = ('<div class="kicker">AUJOURD’HUI</div><div id="f8-t" class="titre">Cherchez « <em>1910</em> » sur les murs</div>')
            tw.append(f'tl.fromTo("#f8-t",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.6,ease:"power3.out"}},{ft(T(8, "Cherchez")):.4f});')
            corps += '<div id="f8-e" class="etiquette" style="left:40px;top:80px">PORT DES CÉLESTINS · PARIS 4E</div>'
            tw.append(f'tl.fromTo("#f8-e",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.4}},{ft(T(8, "1910")):.4f});')
            corps += ('<div id="f8-fin" class="fin-carte"><div class="fc-titre">Crue de la Seine · janvier 1910</div>'
                      '<p><b>SOURCES</b> Wikipédia (« Crue de la Seine de 1910 ») · Météo Paris · Paris Zigzag</p>'
                      '<p><b>IMAGES</b> Agence Rol / BnF, E. Le Deley, ND Phot. (domaine public) · Mu (CC BY-SA 3.0)</p>'
                      '<p><b>VOIX</b> synthèse vocale (Kokoro)</p></div>')
            tw.append(f'tl.fromTo("#f8-fin",{{opacity:0}},{{opacity:1,duration:0.5}},{ft(T(8, "arrêtée") + 0.5):.4f});')
        if credit:
            corps += f'<div class="credit">{esc(credit)}</div>'
        cam = {1: (1.0, 1.08, "50% 50%"), 2: (1.0, 1.0, "50% 50%"), 3: (1.0, 1.18, "50% 35%"), 4: (1.0, 1.0, "50% 40%"),
               5: (1.12, 1.0, "50% 50%"), 6: (1.04, 1.12, "40% 40%"), 7: (1.0, 1.1, "50% 0%"), 8: (1.0, 1.22, "50% 62%")}[k]
        if k in (1, 3, 5, 6, 7, 8):
            tw.append(f'tl.fromTo("#{pid}-cam",{{scale:{cam[0]},transformOrigin:"{cam[2]}"}},{{scale:{cam[1]},duration:{t1 - debut + 0.2:.3f},ease:"sine.inOut"}},{debut:.4f});')
        if k == 2:   # panoramique : la vue de la gare de Lyon défile de gauche à droite
            tw.append(f'tl.fromTo("#f2-cam img",{{objectPosition:"0% 50%"}},{{objectPosition:"100% 50%",duration:{t1 - debut + 0.2:.3f},ease:"none"}},{debut:.4f});')
        if k == 4:
            tw.append(f'tl.fromTo("#f4-cam",{{scale:1}},{{scale:1.1,transformOrigin:"50% 32%",duration:1.2,ease:"power2.inOut"}},{ft(t_stop - 0.1):.4f});')
        scene = f'<div class="scene">{img}<div class="calque txt">{corps}</div></div>'
        sec.append(f'<section id="{pid}" class="clip plan" data-start="{debut:.4f}" data-duration="{fin_clip - debut:.4f}" data-track-index="{1 + k % 2}">'
                   f'<div id="{pid}-in" class="inner"{" style=\"opacity:0\"" if fondu else ""}>'
                   f'<div class="entete txt">{entete}</div>{scene}'
                   f'<div class="sources txt"><b>SOURCES</b>{esc(sources[k])}</div></div></section>')
        if fondu:
            # textes : ceux du plan sortant partent au début du fondu, ceux du plan entrant arrivent à sa fin
            # (jamais deux textes superposés pendant la transition)
            tw.append(f'tl.fromTo("#f{k - 1}-in .txt",{{opacity:1}},{{opacity:0,duration:0.15,immediateRender:false}},{debut:.4f});')
            tw.append(f'tl.fromTo("#{pid}-in .txt",{{opacity:0}},{{opacity:1,duration:0.2}},{ft(debut + fondu):.4f});')
            if trans == "zoom-through":
                tw.append(f'tl.fromTo("#{pid}-in",{{opacity:0,scale:1.08}},{{opacity:1,scale:1,duration:{fondu},ease:"power2.out"}},{debut:.4f});')
            elif trans.startswith("push-slide"):
                tw.append(f'tl.fromTo("#{pid}-in",{{opacity:0,x:160}},{{opacity:1,x:0,duration:{fondu},ease:"power2.out"}},{debut:.4f});')
            else:
                tw.append(f'tl.fromTo("#{pid}-in",{{opacity:0}},{{opacity:1,duration:{fondu},ease:"sine.inOut"}},{debut:.4f});')
        else:
            tw.append(f'tl.set("#{pid}-in",{{opacity:1}},{debut:.4f});')

    hud = []
    for k, s in enumerate(subs):
        a, b = ft(s["debut"]), ft(s["fin"])
        hud.append(f'<div id="st{k}" class="clip st" data-start="{a:.4f}" data-duration="{b - a:.4f}" data-track-index="8">{sous_titre_html(s["texte"])}</div>')

    doc = f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Crue de 1910 · TikTok</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{D:.4f}" data-fps="{FPS}" data-width="1080" data-height="1920">
      {chr(10).join("      " + s for s in sec).lstrip()}
      {chr(10).join("      " + s for s in hud).lstrip()}
      <div class="grain"></div>
      <audio id="mix" src="build/mix_master.wav" data-start="0" data-duration="{D:.4f}" data-track-index="20"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + x for x in tw).lstrip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    (ROOT / "index.html").write_text(doc)
    calc = {"duree": D, "plans": [{"n": k, "debut": starts[k - 1], "fin": fins[k - 1], "duree": round(fins[k - 1] - starts[k - 1], 2),
                                   "parole": parole[k - 1]} for k in range(1, 9)],
            "sous_titres": len(subs), "ancres": {"horloges": T(1, "horloges"), "s'arrêtent": t_stop}}
    (BUILD / "plans_calcules.json").write_text(json.dumps(calc, ensure_ascii=False, indent=1))
    print(f"index.html : {D:.2f} s, {len(subs)} sous-titres · durées des plans : "
          + ", ".join(f"{c['duree']}" for c in calc["plans"]) + f" · {mesures['loudness_integree_lufs']} LUFS, "
          f"crête {mesures['crete_vraie_dbtp']} dBTP, écart voix/musique {mesures['ecart_voix_musique_db']} dB")


if __name__ == "__main__":
    main()
