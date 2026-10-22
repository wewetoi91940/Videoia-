#!/usr/bin/env python3
"""Montage de la V2 « crue de 1910 » (TikTok 1080 × 1920, ≈ 52 s) : plus d'émotion, grammaire des formats courts de 2026.

Reprend la chaîne de la V1 (`videos/crue-1910-tiktok/scripts/build.py` : lecture du storyboard, placement de la voix,
transcription Whisper locale, datation des mots) et le mixeur du projet Marseille (−14 LUFS, crête vraie ≤ −1,6 dBTP,
musique ≥ 15 dB sous la voix). Ce qui change, et pourquoi :
- une partition par émotion (tic-tac, coupure, nappe en ré mineur, battement de cœur, piano seul sur les sinistrés,
  passage en fa majeur sur l'entraide, montée et impact sur 8,62 m, tic-tac final qui reboucle sur le début) ;
- sous-titres « pop-on » mot à mot, le mot prononcé en ambre ; titres qui entrent mot par mot sur la voix ;
- archive en carte arrondie sur son propre fond flou (profondeur, deux vitesses de caméra) ; couleur selon l'émotion
  (étalonnage précalculé par `scripts/images.py`) ; flash et tremblement sur le sommet ; lumière chaude du registre
  (`organic-light-leak-overlay`) sur l'entraide.
Entrées : STORYBOARD.md, SCRIPT.md, build/voix/l1..l11.wav, build/img/ (scripts/images.py).
Sorties : index.html, build/voix.wav, build/mix_master.wav, build/plans_calcules.json, build/audio_mesures.json,
livrables/crue-1910-v2.srt.
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfilt

sys.dont_write_bytecode = True    # le module de la V1 est importé : pas de __pycache__ dans son dossier
ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"


def module(chemin):
    spec = importlib.util.spec_from_file_location(chemin.parent.parent.name.replace("-", "_") + "_build", chemin)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


V1 = module(ROOT.parent / "crue-1910-tiktok" / "scripts" / "build.py")
V1.ROOT, V1.BUILD = ROOT, BUILD          # ses lecteurs (storyboard, script, transcription) travaillent ici
A, C = V1.A, V1.C                         # mixeur et sous-titres du projet Marseille
SR, FPS = A.SR, 30
ft, esc = C.ft, C.esc
N = 11
DEBUT = 0.15
GAPS = {2: .55, 3: .35, 4: .5, 5: .35, 6: .4, 7: .6, 8: .9, 9: .6, 10: 1.0, 11: .45}   # silence avant chaque ligne
TENUE = 2.6                                # après le dernier mot : titre, puis le cadran revient (boucle)
AMBRE, GLACE, BLANC = "#ffc247", "#9fdcea", "#f4f1ea"

# ------------------------------------------------------------------------------------------------ musique
NOTE = {"Bb1": 58.27, "D2": 73.42, "F2": 87.31, "A2": 110.0, "Bb2": 116.54, "C3": 130.81, "D3": 146.83,
        "E3": 164.81, "F3": 174.61, "A3": 220.0, "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
        "G4": 392.0, "A4": 440.0, "C5": 523.25, "D5": 587.33, "F5": 698.46}


def nappe(freqs, dur, coupure, seed):
    """Nappe de dents de scie douces (additive), filtrée sous `coupure` Hz : sombre à 300 Hz, chaude à 1 400 Hz."""
    sr = 8000
    m = int(dur * sr) + 1
    t = np.arange(m) / sr
    out = np.zeros(m)
    for i, f in enumerate(freqs):
        for det in (-0.0035, 0.0035):
            ff = f * (1 + det + 0.0011 * (i - 2))
            for k in range(1, 18):
                if ff * k > min(3600, coupure * 3):
                    break
                out += np.sin(2 * np.pi * ff * k * t + seed * 1.7 + i * k) / k
    out *= 0.78 + 0.22 * np.sin(2 * np.pi * (0.06 + 0.01 * seed) * t + seed)
    out = sosfilt(butter(2, coupure, "low", fs=sr, output="sos"), out)
    out = resample_poly(out, SR // sr, 1)
    return out / (np.abs(out).max() + 1e-9)


def piano(f, dur=3.2):
    """Note de piano simple : partiels légèrement inharmoniques, chacun avec sa décroissance, attaque de 4 ms."""
    m = int(dur * SR)
    t = np.arange(m) / SR
    s = np.zeros(m)
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        if fk > 9000:
            break
        s += np.sin(2 * np.pi * fk * t) * np.exp(-t * (0.8 + 0.6 * k)) / k ** 1.15
    s *= np.minimum(1, t / 0.004) * np.clip((dur - t) / 0.3, 0, 1)
    return s / np.abs(s).max()


def montee(dur, seed=3):
    """Montée : souffle filtré qui s'éclaircit + sinus qui glisse vers l'aigu, coupée net à la fin."""
    m = int(dur * SR)
    t = np.arange(m) / SR
    x = t / dur
    bruit = np.random.default_rng(seed).normal(0, 1, m)
    s = A.bp(bruit, 500, 2400) * (1 - x) + A.bp(bruit, 2400, 7000) * x
    s = s / np.abs(s).max() * 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(180 + 900 * x ** 2) / SR)
    return s * x ** 2.2


def souffle(dur=0.6, lo=300, hi=2600, seed=5):
    """Souffle de transition : bruit filtré, enveloppe en cloche centrée sur le milieu."""
    m = int(dur * SR)
    t = np.arange(m) / SR
    s = A.bp(np.random.default_rng(seed).normal(0, 1, m), lo, hi)
    return s / np.abs(s).max() * np.sin(np.pi * t / dur) ** 2


def place_st(L, R, sig, t, g=1.0, ecart=0.0):
    A.place(L, sig * g, t)
    A.place(R, sig * g, t + ecart)


def musique(cues, _seq, _chrono, D):
    n = int(round(D * SR))
    tt = np.arange(n) / SR
    L, R = np.zeros(n), np.zeros(n)
    # 1) nappes : une couleur par émotion, enchaînées en fondus
    secs = cues["sections"]
    for i, (a, notes, coupure, g) in enumerate(secs):
        b = secs[i + 1][0] if i + 1 < len(secs) else D
        if g <= 0:
            continue
        entree = 0.25 if secs[i - 1][3] <= 0 else 0.8      # après un silence (l'arrêt des horloges) : attaque franche
        a0, b0 = max(0.0, a - (0 if entree < 0.5 else 0.8)), min(D, b + 1.2)
        seg = nappe([NOTE[x] for x in notes], b0 - a0, coupure, seed=i) * g
        x = tt[int(a0 * SR):int(a0 * SR) + len(seg)]
        seg = seg[:len(x)] * np.clip((x - a0) / entree, 0, 1) * np.clip((b0 - x) / 1.2, 0, 1)
        place_st(L, R, seg * 0.5, a0, ecart=0.007)
    # 2) battement de cœur (« lub-dub ») pendant l'angoisse
    a, b = cues["coeur"]
    t, k = a, 0
    while t < b:
        g = 0.55 + 0.35 * (t - a) / max(1e-6, b - a)
        place_st(L, R, A.sub_hit(0.45) * g, t)
        place_st(L, R, A.sub_hit(0.35) * g * 0.6, t + 0.27)
        t += 60 / 72
        k += 1
    # 3) piano, cloches, montées, impacts
    bus = np.zeros(n)
    for t, note, v in cues["piano"]:
        A.place(bus, piano(NOTE[note]) * v, t)
    for t, note, v in cues["cloches"]:
        A.place(bus, A.bell(NOTE[note], 3.0) * v, t)
    rev = A.convolve_st(bus, A.reverb_ir(2.6, 11, 4200))
    L += bus * 0.8 + rev[:n, 0] * 0.6
    R += bus * 0.8 + rev[:n, 1] * 0.6
    for a, b in cues["montees"]:
        s = montee(b - a)
        place_st(L, R, s * 0.5, a, ecart=0.004)
    for t, g in cues["impacts"]:
        place_st(L, R, A.sub_hit(1.6) * 0.9 * g, t)
        place_st(L, R, A.bell(NOTE["D3"], 3.0) * 0.12 * g, t, ecart=0.006)
    st = np.stack([L, R], axis=1)
    return st * np.clip((D - tt) / 0.6, 0, 1)[:, None]


def bruitages(cues, D):
    n = int(round(D * SR))
    fx = np.zeros((n, 2))
    for k, (t, sorte) in enumerate(cues["tics"]):
        c = A.tick(seed=k)
        if sorte == "tac":
            c = A.lp(c, 1600) * 0.75
        elif sorte == "declic":
            c = A.lp(c, 3000) * 0.5
        A.place(fx[:, 0], c * 0.9, t)
        A.place(fx[:, 1], c, t + 0.003)
    for k, (t, dur, lo, hi) in enumerate(cues["souffles"]):
        s = souffle(dur, lo, hi, seed=k) * 0.5
        A.place(fx[:, 0], s, max(0.0, t - dur / 2))
        A.place(fx[:, 1], np.roll(s, 220), max(0.0, t - dur / 2))
    return fx


# ----------------------------------------------------------------------------------------------- composition
CSS = """
@font-face { font-family: "Inter"; src: url("assets/fonts/inter-latin-600-normal.woff2") format("woff2"); font-weight: 600; }
@font-face { font-family: "Inter"; src: url("assets/fonts/inter-latin-800-normal.woff2") format("woff2"); font-weight: 800; }
@font-face { font-family: "Inter"; src: url("assets/fonts/inter-latin-900-normal.woff2") format("woff2"); font-weight: 900; }
@font-face { font-family: "Anton"; src: url("assets/fonts/anton-latin-400-normal.woff2") format("woff2"); font-weight: 400; }
@font-face { font-family: "Newsreader"; src: url("assets/fonts/Newsreader-400-italic.woff2") format("woff2"); font-weight: 400; font-style: italic; }
@font-face { font-family: "Oswald"; src: url("assets/fonts/Oswald-Regular.woff2") format("woff2"); font-weight: 400; }
:root { --bg: #07090b; --fg: #f4f1ea; --ambre: #ffc247; --glace: #9fdcea; }
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 100%; height: 100%; overflow: hidden; background: var(--bg); }
#root { position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--bg); color: var(--fg); font-family: "Inter", sans-serif; }
.plan { position: absolute; inset: 0; overflow: hidden; }
.inner { position: absolute; inset: 0; background: var(--bg); }
.fond-cam { position: absolute; inset: -5%; }
.fond-cam img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; display: block; }
.carte { position: absolute; overflow: hidden; border-radius: 34px; background: #000;
         box-shadow: 0 34px 90px rgba(0, 0, 0, 0.62), 0 0 0 2px rgba(255, 255, 255, 0.10); }
.cam { position: absolute; inset: 0; }
.cam img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; display: block; }
.kick { position: absolute; left: 70px; top: 176px; font-weight: 800; font-size: 25px; letter-spacing: 0.16em; padding: 5px 16px 6px;
        border: 2px solid currentColor; border-radius: 999px; background: rgba(7, 9, 11, 0.55); }
.titre { position: absolute; left: 70px; top: 224px; width: 900px; font-weight: 900; font-size: 72px; line-height: 1.02;
         letter-spacing: -0.02em; color: var(--fg); text-shadow: 0 6px 30px rgba(0, 0, 0, 0.55); }
.titre .w { display: inline-block; }
.titre.serif { font-family: "Newsreader", serif; font-style: italic; font-weight: 400; font-size: 80px; line-height: 0.98; letter-spacing: -0.01em; }
.titre.big { font-family: "Anton", sans-serif; font-weight: 400; font-size: 124px; line-height: 1; letter-spacing: 0.005em; }
.titre .acc { color: var(--ambre); }
.lab { position: absolute; font-weight: 800; font-size: 29px; letter-spacing: 0.06em; text-transform: uppercase; color: #fff;
       background: rgba(8, 10, 12, 0.86); border-left: 6px solid var(--ambre); padding: 7px 16px 9px; border-radius: 4px; }
.lab.glace { border-left-color: var(--glace); }
.credit { position: absolute; left: 18px; bottom: 16px; max-width: 880px; font-weight: 600; font-size: 17px; line-height: 1.3;
          color: #eef1f2; background: rgba(6, 8, 10, 0.8); padding: 4px 10px 5px; border-radius: 6px; }
.chip { position: absolute; right: 70px; top: 410px; font-weight: 800; font-size: 19px; letter-spacing: 0.18em; color: #111;
        background: var(--glace); padding: 5px 12px 6px; border-radius: 6px; }
.calque { position: absolute; inset: 0; }
.nombre { position: absolute; left: 70px; top: 224px; font-family: "Anton", sans-serif; font-size: 146px; line-height: 1; color: var(--ambre);
          text-shadow: 0 8px 40px rgba(0, 0, 0, 0.6); }
.nombre small { font-family: "Inter", sans-serif; font-weight: 900; font-size: 50px; color: var(--fg); margin-left: 18px; letter-spacing: -0.01em; }
.boite { position: absolute; left: 250px; top: 440px; width: 580px; text-align: center; font-weight: 900; font-size: 36px; letter-spacing: 0.04em;
         color: var(--fg); background: rgba(8, 10, 12, 0.88); border: 3px solid var(--glace); border-radius: 14px; padding: 18px 10px 20px; }
.tampon { position: absolute; left: 600px; top: 528px; font-weight: 900; font-size: 34px; letter-spacing: 0.12em; color: #ff5a4f;
          border: 5px solid #ff5a4f; border-radius: 8px; padding: 4px 14px 6px; background: rgba(8, 10, 12, 0.78); transform: rotate(-9deg); }
.devise { position: absolute; left: 0; right: 0; bottom: 0; padding: 18px 26px 22px; background: linear-gradient(to top, rgba(6, 8, 10, 0.94), rgba(6, 8, 10, 0.78)); }
.devise b { display: block; font-family: "Newsreader", serif; font-style: italic; font-weight: 400; font-size: 46px; color: var(--ambre); }
.devise span { display: block; font-weight: 600; font-size: 25px; line-height: 1.3; color: var(--fg); margin-top: 4px; }
.sources-fin { position: absolute; left: 18px; right: 18px; bottom: 16px; font-weight: 600; font-size: 17px; line-height: 1.35; color: #eef1f2;
               background: rgba(6, 8, 10, 0.84); padding: 6px 12px 7px; border-radius: 8px; }
.sources-fin b { color: var(--ambre); font-weight: 800; letter-spacing: 0.1em; margin-right: 6px; }
.st { position: absolute; left: 60px; top: 1262px; width: 870px; text-align: center; font-weight: 900; font-size: 66px; line-height: 1.1;
      letter-spacing: -0.01em; word-spacing: 0.14em; color: #fff;
      text-shadow: 0 0 2px #000, 3px 3px 0 #000, -3px 3px 0 #000, 3px -3px 0 #000, -3px -3px 0 #000, 0 4px 0 #000, 0 8px 26px rgba(0, 0, 0, 0.7); }
.st .m { display: inline-block; }
#flash { position: absolute; inset: 0; background: #fff; opacity: 0; pointer-events: none; }
.grain { position: absolute; inset: 0; pointer-events: none; background-image: url("assets/grain.png"); opacity: 0.07; }
"""


MOIS = {"janvier", "février", "mars"}
FIN_PHRASE = (".", "!", "?", "…", ",", ":")


def lies(a, b):
    """Deux mots qui ne se séparent pas d'un groupe à l'autre."""
    na, nb = C.norm(a), C.norm(b)
    return (na in C.FAIBLES or a == "«" or b in C.FERMANTS
            or (any(c.isdigit() for c in a) and (nb in C.UNITES or nb in MOIS or nb == "000"))
            or (na in MOIS and nb.isdigit()))


def groupes(phrases, max_mots=3, max_car=20):
    """Sous-titres courts (1 à 3 mots, ≤ 20 caractères) pour l'affichage mot à mot : coupe après une ponctuation,
    jamais après un mot-outil, ni entre un nombre et son unité, ni dans une date (« 21 janvier 1910 »)."""
    out = []
    for p in phrases:
        u = []
        for m in p["mots"]:
            if m["mot"] in C.FERMANTS and u:
                u[-1] = {**u[-1], "mot": u[-1]["mot"] + "\u00a0" + m["mot"], "fin": m["fin"]}
            else:
                u.append(dict(m))
        i = 0
        while i < len(u):
            j, long = i, 0
            while j < len(u):
                w = u[j]["mot"]
                if j > i and (j - i >= max_mots or long + 1 + len(w) > max_car):
                    break
                long += len(w) + (j > i)
                j += 1
                if w.endswith(FIN_PHRASE) and not (j < len(u) and lies(w, u[j]["mot"])):
                    break
            k = j
            while 0 < k < len(u) and k - 1 > i and lies(u[k - 1]["mot"], u[k]["mot"]):
                k -= 1
            if k < len(u) and lies(u[k - 1]["mot"], u[k]["mot"]):     # impossible de reculer : on prolonge
                while k < len(u) and lies(u[k - 1]["mot"], u[k]["mot"]):
                    k += 1
            j = k
            out.append({"debut": u[i]["debut"], "fin": u[j - 1]["fin"], "unites": [(x["mot"], x["debut"]) for x in u[i:j]],
                        "texte": C.typo(" ".join(x["mot"] for x in u[i:j]))})
            i = j
    for a, b in zip(out, out[1:]):
        a["fin"] = min(max(a["fin"] + 0.25, a["debut"] + 0.7), b["debut"] - 0.04)
    out[-1]["fin"] += 0.4
    return out


def cadran(cid, taille, figee=None):
    """Cadran d'horloge publique dessiné en code (illustration) ; `figee` = rotation fixe de la trotteuse."""
    traits = "".join(
        f'<line x1="300" y1="32" x2="300" y2="{32 + (38 if k % 5 == 0 else 15)}" stroke="#1d1a15" stroke-width="{8 if k % 5 == 0 else 3}" '
        f'transform="rotate({k * 6} 300 300)"/>' for k in range(60))
    sec = (f'<g id="{cid}-sec"{f" transform=\"rotate({figee} 300 300)\"" if figee is not None else ""}>'
           '<line x1="300" y1="345" x2="300" y2="74" stroke="#c4372d" stroke-width="5"/><circle cx="300" cy="300" r="13" fill="#c4372d"/></g>')
    return (f'<svg viewBox="0 0 600 600" width="{taille}" height="{taille}" style="display:block">'
            '<circle cx="300" cy="300" r="292" fill="#f1e9d6" stroke="#cdb98e" stroke-width="12"/>'
            '<circle cx="300" cy="300" r="276" fill="none" stroke="#1d1a15" stroke-width="2" opacity="0.35"/>' + traits +
            '<line x1="300" y1="300" x2="300" y2="152" stroke="#1d1a15" stroke-width="15" stroke-linecap="round" transform="rotate(305 300 300)"/>'
            '<line x1="300" y1="300" x2="300" y2="88" stroke="#1d1a15" stroke-width="9" stroke-linecap="round" transform="rotate(60 300 300)"/>'
            + sec + '</svg>')


def main():
    plans = V1.storyboard()
    lus = V1.lignes_lues()
    assert len(plans) == len(lus) == N, (len(plans), len(lus))

    # ---- voix : chaque ligne après la précédente ; chaque plan coupe sur son premier mot (repris de la V1)
    clips, pos, parole = [], [], []
    fin_prec = None
    for k in range(1, N + 1):
        a, sr = sf.read(BUILD / f"voix/l{k}.wav", dtype="float64")
        a = resample_poly(a, SR, sr) if sr != SR else a
        on, off = V1.bornes_parole(a, SR)
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
    wav = BUILD / "voix.wav"
    ancien = sf.read(wav)[0] if wav.exists() else None
    if ancien is None or len(ancien) != len(v) or np.abs(ancien - v).max() > 1e-4:
        sf.write(wav, v, SR, subtype="PCM_24")

    # ---- mots datés (Whisper local, relancé seulement si la voix a changé) → sous-titres
    tr = BUILD / "transcription/transcript.json"
    mots_w = json.loads(tr.read_text()) if tr.exists() and tr.stat().st_mtime > wav.stat().st_mtime else V1.transcrire(wav)
    phrases = []
    for k, (p, lu) in enumerate(zip(plans, lus), 1):
        t0, t1 = parole[k - 1]
        mots = V1.dater_mots(p["voiceover"], lu, mots_w, t0, t1)
        phrases.append({"cle": f"l{k}", "seq": k, "texte": p["voiceover"], "debut": t0, "fin": t1, "mots": mots})
    chrono = {"phrases": phrases, "voix_fin": parole[-1][1]}
    subs = groupes(phrases)
    (ROOT / "livrables").mkdir(exist_ok=True)
    (ROOT / "livrables/crue-1910-v2.srt").write_text(C.srt(subs))

    def T(n, mot, rang=1, fin=False):
        cands = [m for m in phrases[n - 1]["mots"] if C.norm(m["mot"]).startswith(C.norm(mot))]
        if len(cands) < rang:
            sys.exit(f"ancre introuvable : {mot!r} dans le plan {n}")
        return cands[rang - 1]["fin" if fin else "debut"]

    starts = [0.0] + [ft(parole[k][0] - 0.06) for k in range(1, N)]
    fins = starts[1:] + [D]
    tw, sec = [], []

    # ---- temps forts
    t_stop = T(1, "s'arrêter") + 0.12
    pas = [round(x, 3) for x in np.arange(0.0, t_stop - 0.3, 1.0)]          # la trotteuse avance d'un pas par seconde
    t_inst = T(1, "Au")
    t862 = T(9, "8,62")
    t_boucle = ft(D - 1.7)
    pas_fin = [ft(D - 1.0)]                                                    # un pas : -12° → -6°, puis la boucle repart à 0°

    # ---- son
    cues = {
        "sections": [(0.0, [], 0, 0), (t_stop, ["D2", "A2", "D3", "F3"], 420, 1.0), (starts[3], ["D2", "A2", "D3", "E3", "Bb2"], 520, 1.0),
                     (starts[4], ["D2", "A2", "D3", "F3"], 240, 1.1), (starts[5], ["D2", "A2", "D3", "E3", "Bb2"], 520, 1.0),
                     (starts[6], ["D3", "F3", "A3"], 700, 0.35), (starts[7], ["F2", "C3", "F3", "A3", "C4"], 1400, 1.0),
                     (starts[8], ["D2", "A2", "D3", "F3"], 520, 0.9), (t862, ["D2", "A2", "D3", "F3", "A3"], 900, 1.1),
                     (starts[9], ["Bb1", "F2", "D3", "F3"], 700, 0.9), (starts[10], ["D2", "A2", "D3", "F3"], 650, 0.8),
                     (t_boucle, [], 0, 0)],
        "coeur": (T(4, "quais"), starts[6] - 0.3),
        "piano": [(starts[6] + 0.1 + 0.8 * i, n_, 0.55) for i, n_ in enumerate(["A4", "F4", "E4", "D4"])]
                 + [(starts[6] + 0.1, "D3", 0.35)]
                 + [(starts[7] + 0.15 + 0.55 * i, n_, 0.6) for i, n_ in enumerate(["C5", "A4", "F4", "G4", "A4", "C5"])]
                 + [(starts[7] + 0.15, "F3", 0.4), (starts[7] + 1.8, "C4", 0.35)]
                 + [(starts[9] + 0.2 + 1.3 * i, n_, 0.45) for i, n_ in enumerate(["F4", "D4", "A3", "D4"])]
                 + [(starts[10] + 0.2 + 1.1 * i, n_, 0.4) for i, n_ in enumerate(["A4", "G4", "F4"])],
        "cloches": [(starts[7] + 0.4, "F5", 0.10), (starts[7] + 2.6, "C5", 0.08)],
        "montees": [(starts[3] - 0.2, T(4, "début", fin=True) + 0.05), (starts[8] + 0.2, t862)],
        "impacts": [(t_stop, 1.0), (T(4, "début", fin=True) + 0.05, 0.8), (T(6, "20"), 0.7), (t862, 1.2), (T(10, "nul"), 0.5)],
        "tics": [(t, "tic") for t in pas] + [(t + 0.5, "tac") for t in pas if t + 0.5 < t_stop - 0.1]
                + [(t_inst + 0.12 * i, "declic") for i in range(5)]
                + [(t, "tic") for t in pas_fin] + [(pas_fin[0] + 0.5, "tac")],
        "souffles": [(starts[1], 0.7, 250, 2200), (starts[3], 0.6, 300, 2600), (starts[4], 0.8, 150, 1200), (starts[7], 1.0, 400, 3000),
                     (T(3, "arrête"), 0.9, 600, 4000)],
    }
    A.music, A.bruitages = musique, bruitages
    A.GAP_TARGET_DB, A.RISE_DB = 20.0, 15.0     # la musique remonte dans les silences (émotion) et reste ≥ 15 dB sous la voix
    mesures = A.mixer(v, chrono, cues, {}, D, BUILD, avec_stems=False)
    (BUILD / "audio_mesures.json").write_text(json.dumps(mesures, ensure_ascii=False, indent=1))

    # ---- composition
    # Chaque plan a UN calque de texte (et chaque carte photo le sien) : pendant une transition, les textes du plan
    # sortant partent avant que ceux du plan entrant arrivent (leçon de la V1). Les éléments animés vivent dedans.
    def titre(pid, texte, cls="", temps=None, t0=0.0, gap=0.08, statique=False, acc=()):
        """Titre mot à mot : chaque mot entre quand il est dit (temps[i]) ; sinon 0,12 s après le précédent."""
        mots = texte.split(" ")
        spans = " ".join("<br>" if m == "|" else f'<span class="w{" acc" if i in acc else ""}" id="{pid}-w{i}">{esc(m)}</span>'
                         for i, m in enumerate(mots))
        if not statique:
            prec = None
            for i in range(len(mots)):
                t = temps[i] if temps and i < len(temps) and temps[i] is not None else (prec + 0.12 if prec is not None else t0 + gap * i)
                prec = t
                tw.append(f'tl.fromTo("#{pid}-w{i}",{{opacity:0,y:38,scale:1.1}},{{opacity:1,y:0,scale:1,duration:0.3,ease:"back.out(2.2)"}},{ft(t):.4f});')
        return f'<div id="{pid}" class="titre {cls}">{spans}</div>'

    def paraitre(sel, t, dy=14, d=0.35):
        tw.append(f'tl.fromTo("{sel}",{{opacity:0,y:{dy}}},{{opacity:1,y:0,duration:{d},ease:"power3.out"}},{ft(t):.4f});')

    def compteur(sel, val, t, dur, fmt, n=14):
        for s_ in range(n + 1):
            x = val * (1 - (1 - s_ / n) ** 3)
            tw.append(f'tl.set("{sel}",{{textContent:"{fmt(x)}"}},{ft(t + dur * s_ / n):.4f});')

    def carte(pid, img, box, pos_img="50% 50%", credit="", extra="", contenu=None):
        x, y, w, h = box
        corps = contenu or f'<img src="build/img/{img}.jpg" alt="" style="object-position:{pos_img}">'
        cr = f'<div class="credit">{esc(credit)}</div>' if credit else ""
        return (f'<div id="{pid}-carte" class="carte" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
                f'<div id="{pid}-cam" class="cam" data-layout-allow-overflow>{corps}</div><div class="calque txt">{extra}{cr}</div></div>')

    def kick(texte, couleur=GLACE):
        return f'<div class="kick" style="color:{couleur}">{esc(texte)}</div>'

    def lab(pid, texte, x, y, glace=False):
        return f'<div id="{pid}" class="lab{" glace" if glace else ""}" style="left:{x}px;top:{y}px">{esc(texte)}</div>'

    FOND = {1: "saint-lazare", 2: "saints-peres", 3: "panorama", 4: "passy", 5: "saint-michel", 6: "daumesnil", 7: "gymnase",
            8: "petit-journal", 9: "plan-1910", 10: "repere-celestins", 11: "repere-celestins"}
    BOX = (70, 400, 940, 770)
    fondus = {k: {"zoom-through": 0.45, "push-slide UP": 0.5, "crossfade": 0.6}.get(p.get("transition_in", "cut"), 0.0)
              for k, p in enumerate(plans, 1)}
    fondus[7], fondus[1] = 0.8, 0.0
    CHIP = '<div class="chip">ILLUSTRATION</div>'

    for k, p in enumerate(plans, 1):
        pid, t0, t1 = f"f{k}", starts[k - 1], fins[k - 1]
        trans, fondu = p.get("transition_in", "cut"), fondus[k]
        debut = ft(max(0.0, t0 - fondu / 2)) if fondu else t0
        fin_clip = t1 + (fondus[k + 1] / 2 if k < N else 0.0)
        ta = ft(debut + fondu)                      # premier instant où le plan est installé
        fond = f'<div id="{pid}-fc" class="fond-cam"><img src="build/img/{FOND[k]}-fond.jpg" alt=""></div>'
        scene, texte = "", ""                        # scene : images ; texte : le calque de texte du plan
        if k == 1:
            scene = (f'<div id="f1-cam" class="cam"><div style="position:absolute;left:240px;top:420px">{cadran("f1", 600)}</div>'
                     + "".join(f'<div id="f1-p{i}" style="position:absolute;left:{105 + 170 * i}px;top:1068px">{cadran(f"f1p{i}", 130, figee=6 * (len(pas) - 1))}</div>'
                               for i in range(5)) + "</div>")
            texte = kick("PARIS · 21 JANVIER 1910") + CHIP + titre("f1-t", "Les horloges de Paris s’arrêtent", statique=True, acc={4})
            for n_, t in enumerate(pas):
                tw.append(f'tl.set("#f1-sec",{{rotation:{6 * n_},svgOrigin:"300 300"}},{ft(t):.4f});')
            r = 6 * (len(pas) - 1)
            tw += [f'tl.to("#f1-sec",{{rotation:{r + 3},svgOrigin:"300 300",duration:0.08}},{ft(t_stop - 0.1):.4f});',
                   f'tl.to("#f1-sec",{{rotation:{r},svgOrigin:"300 300",duration:0.12,ease:"power2.out"}},{ft(t_stop - 0.02):.4f});',
                   f'tl.fromTo("#f1-t-w4",{{color:"{BLANC}"}},{{color:"{AMBRE}",duration:0.15}},{ft(t_stop - 0.05):.4f});',
                   f'tl.fromTo("#f1-cam",{{scale:1}},{{scale:1.1,transformOrigin:"50% 38%",duration:0.5,ease:"power3.out"}},{ft(t_stop):.4f});']
            for i in range(5):
                tw.append(f'tl.fromTo("#f1-p{i}",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.25,ease:"back.out(2)"}},{ft(t_inst + 0.12 * i):.4f});')
        elif k == 2:
            scene = carte(pid, "saints-peres", BOX, "50% 50%", "Bateau coincé sous le pont des Saints-Pères, 21 janvier 1910 · Agence Rol · BnF · domaine public",
                          extra=lab("f2-l1", "PONT DES SAINTS-PÈRES", 28, 30, True) + lab("f2-l2", "LA SEINE MONTE", 28, 96))
            texte = kick("IMAGINE") + titre("f2-t", "21 janvier 1910", "big", [T(2, "21"), T(2, "janvier"), T(2, "1910")])
            paraitre("#f2-l1", ta + 0.2)
            paraitre("#f2-l2", T(2, "monte"))
        elif k == 3:
            scene = ('<div id="f3-cam" class="cam">'
                     '<svg style="position:absolute;left:0;top:0" width="1080" height="1200" viewBox="0 0 1080 1200">'
                     '<path id="f3-tuyau" d="M540 532 L540 704" fill="none" stroke="#9fdcea" stroke-width="16" stroke-linecap="round" '
                     'stroke-dasharray="2 26" stroke-dashoffset="0" opacity="0"/></svg>'
                     f'<div style="position:absolute;left:310px;top:700px">{cadran("f3", 460, figee=6 * (len(pas) - 1))}</div></div>')
            texte = (kick("POURQUOI ?") + CHIP.replace('class="chip"', 'class="chip" style="top:1186px;right:auto;left:70px"') + '<div class="boite">USINE D’AIR COMPRIMÉ</div><div id="f3-tp" class="tampon">ARRÊTÉE</div>'
                     + titre("f3-t", "Paris a perdu l’heure", "serif", [T(3, "Paris"), None, T(3, "perdu"), T(3, "l'heure")]))
            tw += [f'tl.fromTo("#f3-tp",{{opacity:0,scale:1.6}},{{opacity:1,scale:1,duration:0.22,ease:"power4.in"}},{ft(T(3, "arrête")):.4f});',
                   # l'air circule de l'usine vers le cadran (pointillés qui avancent), puis s'arrête et devient gris
                   f'tl.fromTo("#f3-tuyau",{{opacity:0}},{{opacity:1,duration:0.2}},{ft(T(3, "fait")):.4f});',
                   f'tl.fromTo("#f3-tuyau",{{strokeDashoffset:0}},{{strokeDashoffset:-84,duration:0.9,ease:"none"}},{ft(T(3, "fait")):.4f});',
                   f'tl.to("#f3-tuyau",{{stroke:"#5b6266",duration:0.3}},{ft(T(3, "horloges")):.4f});',
                   f'tl.fromTo("#f3-cam",{{scale:1}},{{scale:1.12,transformOrigin:"50% 72%",duration:1.4,ease:"power2.inOut"}},{ft(T(3, "Paris")):.4f});']
        elif k == 4:
            fond = ('<div id="f4-fc" class="fond-cam"><img src="build/img/passy-fond.jpg" alt="">'
                    '<img id="f4-f2" src="build/img/rue-leblanc-fond.jpg" alt="" style="opacity:0"></div>')
            scene = carte(pid, "passy", BOX, contenu='<img src="build/img/passy.jpg" alt="" style="object-position:35% 50%">'
                                                     '<img id="f4-i2" src="build/img/rue-leblanc.jpg" alt="" style="opacity:0">',
                          extra=lab("f4-l1", "23 JANVIER · QUAI DE PASSY", 28, 30, True) + lab("f4-l2", "RUE LEBLANC · 15E", 28, 30, True)
                          + '<div id="f4-c1" class="credit">Passerelles au quai de Passy, janvier 1910 · carte postale ND Phot. · domaine public</div>'
                          + '<div id="f4-c2" class="credit" style="opacity:0">Rue Leblanc (15e), janvier 1910 · Agence Rol · BnF · domaine public</div>')
            texte = kick("ET ENSUITE ?") + titre("f4-t", "Ce n’est que le début", "", [T(4, "Ce"), T(4, "n'est"), T(4, "que"), T(4, "le"), T(4, "début")])
            tr_ = T(4, "rues")
            paraitre("#f4-l1", T(4, "23"))
            tw += [f'tl.set(["#f4-i2","#f4-f2","#f4-c2"],{{opacity:1}},{ft(tr_):.4f});', f'tl.set(["#f4-l1","#f4-c1"],{{opacity:0}},{ft(tr_):.4f});',
                   f'tl.fromTo("#f4-l2",{{opacity:0}},{{opacity:1,duration:0.2}},{ft(tr_ + 0.05):.4f});',
                   f'tl.fromTo("#f4-i2",{{scale:1.14}},{{scale:1.0,duration:{t1 - tr_ + 0.4:.3f},ease:"sine.out"}},{ft(tr_):.4f});']
        elif k == 5:
            scene = carte(pid, "saint-michel", BOX, "50% 50%", "La gare Saint-Michel envahie par les eaux, 1910 · carte postale ELD · domaine public",
                          extra=lab("f5-l1", "GARE SAINT-MICHEL", 28, 30, True))
            texte = kick("SOUS TERRE") + titre("f5-t", "Métro et gares sous l’eau", "", [T(5, "métro"), T(5, "et"), T(5, "gares"), None, None])
            paraitre("#f5-l1", ta + 0.2)
        elif k == 6:
            scene = carte(pid, "daumesnil", BOX, "60% 50%", "Avenue Daumesnil inondée, 1910 · carte postale AHK · domaine public",
                          extra=lab("f6-l1", "EAU GLACÉE", 28, 30, True) + lab("f6-l2", "SOUILLÉE PAR LES ÉGOUTS", 28, 96, True))
            texte = kick("L’EAU") + '<div id="f6-n" class="nombre"><span id="f6-v">0</span><small>immeubles</small></div>'
            paraitre("#f6-l1", T(6, "glacée"))
            paraitre("#f6-l2", T(6, "égouts"))
            t20 = T(6, "20")
            tw.append(f'tl.fromTo("#f6-n",{{opacity:0,scale:0.8}},{{opacity:1,scale:1,transformOrigin:"0% 50%",duration:0.3,ease:"back.out(2)"}},{ft(t20 - 0.05):.4f});')
            compteur("#f6-v", 20000, t20, 0.6, lambda x: f"{int(round(x / 100) * 100):,}".replace(",", " "))
        elif k == 7:
            scene = carte(pid, "gymnase", BOX, "50% 50%", "Gymnase de la rue Saint-Lambert transformé en dortoir pour les sinistrés, janvier 1910 · A. Taride · domaine public",
                          extra=lab("f7-l1", "UN DORTOIR POUR LES SINISTRÉS", 28, 30))
            texte = kick("LES SINISTRÉS", BLANC)
            paraitre("#f7-l1", ta + 0.6)
        elif k == 8:
            scene = carte(pid, "petit-journal", (190, 390, 700, 800), "50% 100%", "",
                          extra='<div id="f8-dv" class="devise"><b>Fluctuat nec mergitur</b><span>« Il est battu par les flots, mais ne sombre pas » · '
                                'devise de Paris, en une du <i>Petit Journal</i>, 13 février 1910 · domaine public</span></div>')
            texte = kick("ALORS…", AMBRE) + titre("f8-t", "Paris s’entraide", "serif", [T(8, "Paris"), T(8, "s'entraide")])
            tw.append(f'tl.fromTo("#f8-cam img",{{objectPosition:"50% 100%"}},{{objectPosition:"50% 0%",duration:{t1 - debut + 0.4:.3f},ease:"sine.inOut"}},{debut:.4f});')
            paraitre("#f8-dv", T(8, "passerelles"), dy=30, d=0.5)
        elif k == 9:
            scene = carte(pid, "plan-1910", (70, 420, 940, 672), "50% 50%", "« Les inondations à Paris », plan de 1910 · Héliotypie E. Le Deley · domaine public",
                          extra=lab("f9-l1", "PONT D’AUSTERLITZ", 28, 560))
            texte = kick("LE SOMMET · 28 JANVIER", AMBRE) + '<div id="f9-n" class="nombre"><span id="f9-v">0,00</span><small>mètres</small></div>'
            tw += [f'tl.fromTo("#f9-cam",{{scale:1}},{{scale:2.5,transformOrigin:"8% 12%",duration:0.9,ease:"power3.inOut"}},{ft(t862 - 0.75):.4f});',
                   f'tl.fromTo("#flash",{{opacity:0}},{{opacity:0.85,duration:0.0666}},{ft(t862):.4f});',
                   f'tl.to("#flash",{{opacity:0,duration:0.35,ease:"power2.out"}},{ft(t862) + 2 / FPS:.4f});',
                   f'tl.fromTo("#f9-n",{{opacity:0,scale:1.3}},{{opacity:1,scale:1,transformOrigin:"0% 50%",duration:0.3,ease:"power4.out"}},{ft(t862):.4f});']
            for i, dx in enumerate([-12, 10, -7, 5, -2, 0]):      # tremblement : un pas toutes les deux images
                tw.append(f'tl.to("#f9-carte",{{x:{dx},duration:0.0666,ease:"none"}},{ft(t862) + 2 * i / FPS:.4f});')
            compteur("#f9-v", 8.62, t862, 0.5, lambda x: f"{x:.2f}".replace(".", ","))
            paraitre("#f9-l1", T(9, "pont"))
        elif k == 10:
            scene = carte(pid, "repere-celestins", BOX, "30% 62%", "Repère de crue, port des Célestins (Paris 4e), photo de 2010 · Mu · CC BY-SA 3.0 · Wikimedia Commons",
                          extra=lab("f10-l1", "PORT DES CÉLESTINS · PARIS 4E", 28, 30, True))
            texte = (kick("AUJOURD’HUI", BLANC) + titre("f10-ta", "Toujours gravé", "serif", [T(10, "encore"), T(10, "gravé")])
                     + titre("f10-tb", "Plus faible… | mais pas nul", "serif", statique=True, acc={3, 4, 5}))
            paraitre("#f10-l1", ta + 0.3)
            tw += [f'tl.to("#f10-ta",{{opacity:0,duration:0.15}},{ft(T(10, "faible") - 0.2):.4f});',
                   f'tl.fromTo("#f10-tb",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.3,ease:"power3.out"}},{ft(T(10, "faible")):.4f});',
                   f'tl.fromTo("#f10-tb .acc",{{opacity:0,scale:1.4}},{{opacity:1,scale:1,duration:0.25,ease:"power4.in"}},{ft(T(10, "nul") - 0.2):.4f});']
        elif k == 11:
            scene = carte(pid, "repere-celestins", BOX, "30% 62%", "",
                          extra='<div class="sources-fin"><b>SOURCES</b>Wikipédia · Météo Paris · Paris Zigzag — <b>IMAGES</b>Agence Rol/BnF, cartes postales 1910, '
                                '<i>Le Petit Journal</i>, E. Le Deley (domaine public) · Mu (CC BY-SA 3.0) — <b>VOIX</b>synthèse (Kokoro)</div>')
            texte = kick("SUR LES QUAIS", AMBRE) + titre("f11-t", "Cherche le trait de 1910", "serif",
                                                          [T(11, "cherche"), None, T(11, "trait"), None, T(11, "1910")], acc={4})
        if k in (2, 4, 5, 6, 7, 8, 9, 10):    # parallaxe : le fond dérive lentement, la carte zoome plus vite
            tw.append(f'tl.fromTo("#{pid}-fc",{{scale:1.04}},{{scale:1.12,duration:{fin_clip - debut:.3f},ease:"none"}},{debut:.4f});')
            cam = {2: (1.0, 1.12, "62% 45%"), 4: (1.0, 1.1, "40% 50%"), 5: (1.0, 1.14, "45% 55%"), 6: (1.0, 1.1, "55% 55%"),
                   7: (1.0, 1.12, "45% 62%"), 10: (1.0, 1.16, "28% 60%")}.get(k)
            if cam:
                tw.append(f'tl.fromTo("#{pid}-cam",{{scale:{cam[0]}}},{{scale:{cam[1]},transformOrigin:"{cam[2]}",duration:{t1 - debut + 0.3:.3f},ease:"sine.inOut"}},{debut:.4f});')
            tw.append(f'tl.fromTo("#{pid}-carte",{{y:14}},{{y:-14,duration:{fin_clip - debut:.3f},ease:"sine.inOut"}},{debut:.4f});')
        if k == 11:
            tw.append(f'tl.fromTo("#f11-cam",{{scale:1.16}},{{scale:1.55,transformOrigin:"27% 61%",duration:{t_boucle - t0:.3f},ease:"sine.inOut"}},{t0:.4f});')
        sec.append(f'<section id="{pid}" class="clip plan" data-start="{debut:.4f}" data-duration="{fin_clip - debut:.4f}" data-track-index="{1 + k % 2}">'
                   f'<div id="{pid}-in" class="inner"{" style=\"opacity:0\"" if fondu else ""}>{fond}{scene}<div class="calque txt">{texte}</div></div></section>')
        if fondu:
            # textes : ceux du plan sortant partent au début de la transition, ceux du plan entrant arrivent à sa fin
            tw.append(f'tl.fromTo("#f{k - 1}-in .txt",{{opacity:1}},{{opacity:0,duration:0.15,immediateRender:false}},{debut:.4f});')
            tw.append(f'tl.fromTo("#{pid}-in .txt",{{opacity:0}},{{opacity:1,duration:0.2}},{ta:.4f});')
            if trans == "zoom-through":
                tw.append(f'tl.fromTo("#{pid}-in",{{opacity:0,scale:1.3}},{{opacity:1,scale:1,duration:{fondu},ease:"power3.out"}},{debut:.4f});')
                tw.append(f'tl.fromTo("#f{k - 1}-in",{{scale:1}},{{scale:1.25,duration:{fondu},ease:"power2.in",immediateRender:false}},{debut:.4f});')
            elif trans == "push-slide UP":
                tw.append(f'tl.fromTo("#{pid}-in",{{opacity:1,y:1920}},{{opacity:1,y:0,duration:{fondu},ease:"power3.inOut"}},{debut:.4f});')
                tw.append(f'tl.fromTo("#f{k - 1}-in",{{y:0}},{{y:-1920,duration:{fondu},ease:"power3.inOut",immediateRender:false}},{debut:.4f});')
            else:
                tw.append(f'tl.fromTo("#{pid}-in",{{opacity:0}},{{opacity:1,duration:{fondu},ease:"sine.inOut"}},{debut:.4f});')
        else:
            tw.append(f'tl.set("#{pid}-in",{{opacity:1}},{debut:.4f});')

    # ---- boucle : le cadran du début revient ; la trotteuse fait un pas (−12° → −6°), puis la vidéo repart à 0°
    sec.append(f'<section id="boucle" class="clip plan" data-start="{t_boucle:.4f}" data-duration="{D - t_boucle:.4f}" data-track-index="3">'
               f'<div id="boucle-in" class="inner" style="opacity:0"><div class="fond-cam"><img src="build/img/saint-lazare-fond.jpg" alt=""></div>'
               f'<div style="position:absolute;left:240px;top:420px">{cadran("bc", 600, figee=-12)}</div></div></section>')
    tw.append(f'tl.fromTo("#boucle-in",{{opacity:0}},{{opacity:1,duration:0.5,ease:"sine.inOut"}},{t_boucle:.4f});')
    tw.append(f'tl.fromTo("#f11-in .txt",{{opacity:1}},{{opacity:0,duration:0.3,immediateRender:false}},{t_boucle:.4f});')
    for t in pas_fin:
        tw.append(f'tl.set("#bc-sec",{{rotation:-6,svgOrigin:"300 300"}},{t:.4f});')

    # ---- lumière chaude (bloc du registre) sur l'entraide
    t_leak = ft(starts[7] - 0.2)
    leak = (f'<div id="leak" data-composition-id="organic-light-leak-overlay" data-composition-src="compositions/organic-light-leak-overlay.html" '
            f'data-start="{t_leak:.4f}" data-duration="3.6" data-width="1080" data-height="1920" data-track-index="9" style="opacity:0.6"></div>')

    # ---- sous-titres pop-on : chaque mot apparaît quand il est dit, le mot dit en ambre
    hud = []
    for g, s in enumerate(subs):
        unites = [list(x) for x in s["unites"]]
        lignes = C.deux_lignes(" ".join(u[0] for u in unites), 17)
        coupe = len(lignes[0].split(" ")) if len(lignes) > 1 else len(unites)
        html = ""
        for i, (mot, t) in enumerate(unites):
            html += ("<br>" if i == coupe else (" " if i else "")) + f'<span class="m" id="s{g}m{i}">{esc(mot)}</span>'
            nxt_m = unites[i + 1][1] if i + 1 < len(unites) else s["fin"] - 0.05
            tw.append(f'tl.fromTo("#s{g}m{i}",{{color:"#ffffff",scale:1}},{{color:"{AMBRE}",scale:1.04,duration:0.08}},{ft(max(s["debut"], t)):.4f});')
            tw.append(f'tl.to("#s{g}m{i}",{{color:"#ffffff",scale:1,duration:0.08}},{ft(max(t + 0.1, nxt_m)):.4f});')
        tw.append(f'tl.fromTo("#st{g}",{{scale:0.86,opacity:0}},{{scale:1,opacity:1,duration:0.12,ease:"back.out(2.5)"}},{ft(s["debut"]):.4f});')
        a, b = ft(s["debut"]), ft(s["fin"])
        hud.append(f'<div id="st{g}" class="clip st" data-start="{a:.4f}" data-duration="{b - a:.4f}" data-track-index="8">{html}</div>')

    doc = f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Crue de 1910 · TikTok V2</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>{CSS}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{D:.4f}" data-fps="{FPS}" data-width="1080" data-height="1920">
      {chr(10).join("      " + s for s in sec).lstrip()}
      {leak}
      {chr(10).join("      " + s for s in hud).lstrip()}
      <div id="flash" data-layout-allow-occlusion></div>
      <div class="grain"></div>
      <audio id="mix" src="build/mix_master.wav" data-start="0" data-duration="{D:.4f}" data-track-index="20"></audio>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + x for x in tw).lstrip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    (ROOT / "index.html").write_text(doc)
    calc = {"duree": D, "plans": [{"n": k, "debut": starts[k - 1], "fin": fins[k - 1], "duree": round(fins[k - 1] - starts[k - 1], 2),
                                   "parole": parole[k - 1]} for k in range(1, N + 1)],
            "sous_titres": len(subs), "ancres": {"arret": t_stop, "8,62": t862, "boucle": t_boucle}}
    (BUILD / "plans_calcules.json").write_text(json.dumps(calc, ensure_ascii=False, indent=1))
    print(f"index.html : {D:.2f} s, {len(subs)} sous-titres · durées des plans : "
          + ", ".join(f"{c['duree']}" for c in calc["plans"]) + f" · {mesures['loudness_integree_lufs']} LUFS, "
          f"crête {mesures['crete_vraie_dbtp']} dBTP, écart voix/musique {mesures['ecart_voix_musique_db']} dB "
          f"(court terme min {mesures['ecart_court_terme_db']['min']} dB)")


if __name__ == "__main__":
    main()
