#!/usr/bin/env python3
"""Version TikTok : le documentaire en trois parties verticales (1080 × 1920), tirées du même script, de la même voix
et des mêmes sources. Aucune nouvelle synthèse vocale : la voix est découpée dans build/voix.wav.

Pour chaque partie (séquences consécutives du script) : chronologie décalée, voix découpée, mixage refait par
04_audio.mixer (−14 LUFS, crête vraie ≤ −1,5 dBTP, musique ≥ 15 dB sous la voix), composition HyperFrames verticale
avec sous-titres incrustés (beaucoup regardent TikTok sans le son).
Sorties : build/tiktok/partie-N/ (index.html, mix_master.wav, chronologie.json, plans_calcules.json, audio_mesures.json,
lien « assets » vers les images du projet) et docs/08_tiktok.md (textes de publication).
Zones laissées à l'interface de TikTok : au-dessus de 170 px, sous 1 470 px, à droite de 960 px dans la moitié basse.
"""
import copy
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
SORTIE = BUILD / "tiktok"


def module(nom):
    spec = importlib.util.spec_from_file_location(nom, ROOT / "scripts" / f"{nom}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


C = module("05_composition")     # fonctions du montage 16:9 (temps, typographie, cartons)
A = module("04_audio")           # mixage

W, H = 1080, 1920
FPS = C.FPS
PRE = 2.0            # carton « Partie N/3 » avant la voix (parties 2 et 3)
SUITE = 3.5          # carton « À suivre » après la voix (parties 1 et 2)
PARTIES = [
    {"n": 1, "seqs": [1, 2, 3, 4], "titre": "Avant midi : les premiers pillages"},
    {"n": 2, "seqs": [5, 6, 7, 8, 9], "titre": "De l'hôtel de ville à la nuit"},
    {"n": 3, "seqs": [10, 11, 12], "titre": "Le jour d'après : les bilans"},
]
VUES_V = {"ensemble": "v_ensemble", "prado_castellane": "v_prado_castellane", "matin": "v_matin",
          "canebiere": "v_canebiere", "quadrilatere": "v_quadrilatere", "vieux_port": "v_vieux_port"}
# étiquettes déplacées pour le cadrage vertical : (plan, n° de couche) → réglages
ETIQ_V = {
    ("P08", 0): {"dx": -24, "dy": -84}, ("P12", 0): {"dx": -24, "dy": -84},
    ("P08", 1): {"dx": 24, "dy": -20}, ("P12", 1): {"dx": 24, "dy": -20},
    ("P14", 2): {"dx": -24, "dy": -20},
    ("P15", 1): {"dx": 24, "dy": -20},
}
NOMBRE = re.compile(r"\d+(?:[  ]\d{3})*(?:[  ]h\b(?:[  ]\d{2})?)?")
ft, esc = C.ft, C.esc


# ----------------------------------------------------------------------------------------------- plans verticaux
def plan_carte_v(p: dict, pid: str, vues: dict, T, t0: float, tw: list) -> str:
    v = vues[p["vue"]]
    w, h = v["w"], v["h"]
    svg, labels = [], []
    for k, c in enumerate(p.get("couches", [])):
        ta = T(c["a"]) if "a" in c else t0 + 0.6
        cid = f"{pid}-c{k}"
        etat = c.get("etat", "actif")
        if "ligne" in c:
            for j, seg in enumerate(v["lignes"][c["ligne"]]):
                if len(seg) < 2:
                    continue
                d, L = C.chemin(seg)
                for suf, cls in (("h", "halo"), ("", etat)):   # trait plus court que le blanc : aucun bout arrondi avant le tracé
                    svg.append(f'<path id="{cid}-{j}{suf}" class="hl hl-{cls}" d="{d}" '
                               f'style="stroke-dasharray:{L:.0f} {L + 60:.0f};stroke-dashoffset:{L + 30:.0f}"/>')
                    tw.append(f'tl.fromTo("#{cid}-{j}{suf}",{{strokeDashoffset:{L + 30:.0f}}},{{strokeDashoffset:0,duration:1.4,ease:"power2.inOut"}},{ft(ta):.4f});')
        elif "zone" in c:
            for j, poly in enumerate(v["zone_rues"]):
                d, _ = C.chemin(poly)
                svg.append(f'<path id="{cid}-{j}" class="zone" d="{d} Z"/>')
                tw.append(f'tl.fromTo("#{cid}-{j}",{{opacity:0}},{{opacity:1,duration:0.9,ease:"sine.out"}},{ft(ta):.4f});')
        elif "point" in c:
            x, y = v["points"][c["point"]]
            svg.append(f'<g transform="translate({x:.1f},{y:.1f})"><g id="{cid}-g" opacity="0"><circle id="{cid}-pu" class="pulse" r="12"/>'
                       f'<circle id="{cid}" class="pt pt-{etat}" r="11"/></g></g>')
            # le groupe reste caché jusqu'à l'apparition du point (sinon l'anneau de pulsation se voit avant)
            tw.append(f'tl.fromTo("#{cid}-g",{{opacity:0}},{{opacity:1,duration:0.1}},{ft(ta):.4f});')
            tw.append(f'tl.fromTo("#{cid}",{{scale:0,transformOrigin:"50% 50%"}},{{scale:1,duration:0.5,ease:"back.out(2.2)"}},{ft(ta):.4f});')
            reps = max(0, int((p["_fin"] - ta) / 1.6) - 1)
            tw.append(f'tl.fromTo("#{cid}-pu",{{scale:1,opacity:0.75,transformOrigin:"50% 50%"}},'
                      f'{{scale:3.2,opacity:0,duration:1.6,ease:"sine.out",repeat:{reps}}},{ft(ta):.4f});')
        if c.get("etiquette"):
            if "point" in c:
                x, y = v["points"][c["point"]]
            else:
                ref = c.get("ref")
                seg = max(v["lignes"][c["ligne"]], key=len) if "ligne" in c else v["zone_rues"][0]
                x, y = seg[int(len(seg) * c.get("pos", 0.5))] if ref is None else v["points"][ref]
            dx, dy = c.get("dx", 24), c.get("dy", -18)
            larg = 18.7 * len(c["etiquette"]) + 36
            if dx > 0 and x + dx + larg > w - 40:
                dx = -abs(dx)
            elif dx < 0 and x + dx - larg < 30:
                dx = abs(dx)
            ancre = "right" if dx < 0 else "left"
            style = (f"left:{x + dx:.0f}px" if ancre == "left" else f"right:{w - x - dx:.0f}px") + f";top:{y + dy:.0f}px"
            labels.append(f'<div id="{cid}-lb" class="etiq etiq-{ancre}" style="{style}">{esc(c["etiquette"])}</div>')
            tw.append(f'tl.fromTo("#{cid}-lb",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.5,ease:"power2.out"}},{ft(ta + 0.25):.4f});')
    colonne = ""
    if p.get("colonne") and v.get("panneau"):
        col = p["colonne"]
        x, larg = v["panneau"]
        items = "".join(f'<li id="{pid}-li{k}">{esc(t)}</li>' for k, t in enumerate(col.get("lignes", [])))
        colonne = (f'<div id="{pid}-col" class="colonne-v" style="left:{x}px;width:{larg}px">'
                   f'<div class="col-kicker">{esc(col.get("kicker", ""))}</div><h2 id="{pid}-h">{esc(col.get("titre", ""))}</h2>'
                   f'<ul>{items}</ul></div>')
        tw.append(f'tl.fromTo("#{pid}-col",{{opacity:0,y:24}},{{opacity:1,y:0,duration:0.7,ease:"power3.out"}},{ft(t0 + 0.3):.4f});')
        for k, _ in enumerate(col.get("lignes", [])):
            ta = T(col["a"][k]) if col.get("a") else t0 + 0.7 + 0.35 * k
            tw.append(f'tl.fromTo("#{pid}-li{k}",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.6,ease:"power2.out"}},{ft(ta):.4f});')
    cote = "mob-d" if v.get("panneau") else "mob-g"
    echelle = 200 * v["px_par_m"]
    barre = (f'<div id="{pid}-mob" class="mobilier {cote}"><div class="echelle"><span style="width:{echelle:.0f}px"></span>200 m</div>'
             f'<div class="nord">N</div><div class="attrib">© contributeurs d’OpenStreetMap</div></div>')
    tw.append(f'tl.fromTo("#{pid}-mob",{{opacity:0}},{{opacity:1,duration:0.4}},{ft(t0 + C.FONDU / 2 + 0.05):.4f});')
    return (f'<div class="plateau" style="width:{w}px;height:{h}px">'
            f'<div id="{pid}-cam" class="cam" style="width:{w}px;height:{h}px">'
            f'<img src="{v["image"]}" alt="" style="width:{w}px;height:{h}px"><div class="vignette"></div>'
            f'<svg class="calque" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{"".join(svg)}</svg>'
            f'{"".join(labels)}</div>{barre}{colonne}</div>')


def plan_photo_v(p: dict, pid: str, photos: dict) -> str:
    ph = photos[p["photo"]]
    credit = f'Photo : {ph["auteur"]} · {ph["licence"]} · Wikimedia Commons' + (" · image modifiée (floutage)" if ph.get("modifications") else "")
    return (f'<div class="scene"><div id="{pid}-cam" class="cam"><img class="photo" src="assets/photos/{ph["fichier"]}" alt="" '
            f'style="object-position:{p.get("position", "50% 50%")}"></div><div class="voile"></div></div>'
            f'<div class="mention">LE LIEU EN TEMPS NORMAL · PHOTO D’ILLUSTRATION</div>'
            f'<div class="credit">{esc(credit)}</div>')


def plan_fin_v(p: dict, pid: str, T, t0: float, tw: list) -> str:
    """Les trois colonnes du bilan, l'une après l'autre (en 16:9 elles sont côte à côte)."""
    debuts = [T(c["a"]) if "a" in c else t0 + 0.5 + 6 * k for k, c in enumerate(p["colonnes"])]
    cols = []
    for k, c in enumerate(p["colonnes"]):
        ta = debuts[k]
        items = "".join(f'<li id="{pid}-c{k}i{j}">{esc(t)}</li>' for j, t in enumerate(c["lignes"]))
        cols.append(f'<div id="{pid}-c{k}" class="f-col"><h3>{esc(c["titre"])}</h3><ul>{items}</ul></div>')
        tw.append(f'tl.fromTo("#{pid}-c{k}",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.7,ease:"power3.out"}},{ft(ta):.4f});')
        for j, _ in enumerate(c["lignes"]):
            tj = T(c["a_lignes"][j]) if c.get("a_lignes") else ta + 0.4 + 0.3 * j
            tw.append(f'tl.fromTo("#{pid}-c{k}i{j}",{{opacity:0,x:-14}},{{opacity:1,x:0,duration:0.5,ease:"power2.out"}},{ft(tj):.4f});')
        if k + 1 < len(p["colonnes"]):
            # immediateRender:false : sinon l'état de départ (opacité 1) s'applique dès la construction et la colonne
            # suivante apparaît avant son heure
            tw.append(f'tl.fromTo("#{pid}-c{k}",{{opacity:1}},{{opacity:0,duration:0.35,ease:"sine.in",immediateRender:false}},'
                      f'{ft(debuts[k + 1] - 0.4):.4f});')
    return f'<div class="fond-grille"></div><div class="f-bloc">{"".join(cols)}</div>'


def plan_partie(p: dict, pid: str, t0: float, tw: list) -> str:
    """Carton d'ouverture d'une partie, ou carton « À suivre » annonçant la suivante."""
    note = f'<p id="{pid}-note" class="pt-note">{esc(p["note"])}</p>' if p.get("note") else ""
    tw += [f'tl.fromTo("#{pid}-k",{{opacity:0,y:-10}},{{opacity:1,y:0,duration:0.5}},{ft(t0 + 0.05):.4f});',
           f'tl.fromTo("#{pid}-num",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.6,ease:"expo.out"}},{ft(t0 + 0.15):.4f});',
           f'tl.fromTo("#{pid}-rule",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.8,ease:"power3.inOut"}},{ft(t0 + 0.3):.4f});',
           f'tl.fromTo("#{pid}-h1",{{opacity:0,y:24}},{{opacity:1,y:0,duration:0.7,ease:"power2.out"}},{ft(t0 + 0.4):.4f});']
    if note:
        tw.append(f'tl.fromTo("#{pid}-note",{{opacity:0}},{{opacity:1,duration:0.6}},{ft(t0 + 0.9):.4f});')
    return (f'<div class="fond-grille"></div><div class="ghost" aria-hidden="true" data-t="{p["num"]}/3"></div>'
            f'<div class="pt-bloc"><div id="{pid}-k" class="pt-kicker">{esc(p["kicker"])}</div>'
            f'<div id="{pid}-num" class="pt-num">PARTIE {p["num"]}/3</div><div id="{pid}-rule" class="t-rule"></div>'
            f'<h1 id="{pid}-h1" class="pt-titre">{esc(p["titre"])}</h1>{note}</div>')


def sous_titre_html(texte: str) -> str:
    """Deux lignes au plus ; nombres et heures en couleur d'accent."""
    out = []
    for ligne in C.deux_lignes(texte, 31):
        parts, i = [], 0
        for m in NOMBRE.finditer(ligne):
            parts.append(esc(ligne[i:m.start()]) + f'<span class="st-n">{esc(m.group())}</span>')
            i = m.end()
        parts.append(esc(ligne[i:]))
        out.append(f'<span class="st-r"><span>{"".join(parts)}</span></span>')
    return "".join(out)


# ------------------------------------------------------------------------------------------------- une partie
def partie(P: dict, script: dict, cfg: dict, chrono: dict, vues: dict, photos: dict, voix: np.ndarray) -> dict:
    n, seqs = P["n"], set(P["seqs"])
    ph_part = [p for p in chrono["phrases"] if p["seq"] in seqs]
    dt = 0.0 if n == 1 else PRE - ph_part[0]["debut"]
    ch = dict(chrono, phrases=[dict(p, debut=p["debut"] + dt, fin=p["fin"] + dt,
                                    mots=[dict(m, debut=m["debut"] + dt, fin=m["fin"] + dt) for m in p["mots"]])
                               for p in ph_part])
    ch["voix_fin"] = ch["phrases"][-1]["fin"]
    T = C.Temps(ch)
    voix0, voix_fin = ch["phrases"][0]["debut"], ch["voix_fin"]
    ordre = {p["cle"]: k for k, p in enumerate(chrono["phrases"])}
    dans = {p["cle"] for p in ph_part}

    def etat(a):   # -1 : phrase avant la partie, 0 : dans la partie, 1 : après
        return 0 if a["phrase"] in dans else (-1 if ordre[a["phrase"]] < ordre[ph_part[0]["cle"]] else 1)

    # ---- plans de la partie, version verticale
    plans = []
    if n > 1:
        plans.append({"id": "T0", "type": "partie", "seq": P["seqs"][0], "debut_fixe": 0.0, "musique": "impact",
                      "num": n, "kicker": "Marseille · 17 octobre 2026", "titre": P["titre"]})
    for p in cfg["plans"]:
        if p.get("seq") not in seqs or p["type"] == "credits":
            continue
        p = copy.deepcopy(p)
        if p["type"] == "photo" and p["photo"] not in photos:
            sys.exit(f"photo absente : {p['photo']}")
        if p["type"] == "carte":
            p["vue"] = VUES_V[p["vue"]]
            for k, c in enumerate(p.get("couches", [])):
                c.update(ETIQ_V.get((p["id"], k), {}))
        plans.append(p)
    if n < 3:
        suivante = PARTIES[n]
        plans.append({"id": "SUITE", "type": "suite", "seq": P["seqs"][-1], "duree": SUITE, "num": n + 1,
                      "kicker": "À suivre", "titre": suivante["titre"],
                      "note": "Voix de synthèse · sources à l'écran ; liste complète à la fin de la partie 3"})
    else:
        src = script["sources"]
        utilisees = list(dict.fromkeys(s for ph in script["phrases"] for s in ph.get("sources", []) if s != "OSM"))
        lignes = [f'{src[s]["media"]} ({src[s]["date"]}) — {src[s]["titre"]}' for s in utilisees]
        m = (len(lignes) + 1) // 2
        credits = [p for p in cfg["plans"] if p["type"] == "credits"]
        plans += [{"id": "P56a", "seq": 12, "type": "credits", "duree": 7.0, "kicker": "Sources (1/2) · lues du 17 au 19 octobre 2026",
                   "blocs": [{"titre": "Articles et directs", "lignes": lignes[:m]}]},
                  {"id": "P56b", "seq": 12, "type": "credits", "duree": 7.0, "kicker": "Sources (2/2)",
                   "blocs": [{"titre": "Articles et directs (suite)", "lignes": lignes[m:]}]},
                  dict(credits[-1], duree=7.0)]
    for p in plans:
        p["_debut"] = ft(T(p["ancre"])) if "ancre" in p else p.get("debut_fixe")
    t = None
    for p in plans:       # cartons de fin, sans ancre : après la voix, à la suite
        if p["_debut"] is None:
            p["_debut"] = ft(t if t is not None else voix_fin + C.FIN_APRES_VOIX)
            t = p["_debut"] + p.get("duree", 6)
    for a, b in zip(plans, plans[1:]):
        a["_fin"] = b["_debut"]
    plans[-1]["_fin"] = ft(plans[-1]["_debut"] + plans[-1].get("duree", 6))
    D = plans[-1]["_fin"]
    fin_hud = next((p["_debut"] for p in plans if "ancre" not in p and p["_debut"] > voix0), D)

    TEXTE = {"heure", "citation", "chiffres", "constat", "fin", "titre", "credits", "partie", "suite"}
    for k, p in enumerate(plans):
        p["_creux"] = k > 0 and p["type"] in TEXTE and plans[k - 1]["type"] in TEXTE
    tw, sections = [], []
    for k, p in enumerate(plans):
        pid = p["id"].lower()
        t0, t1 = p["_debut"], p["_fin"]
        suivant = plans[k + 1] if k + 1 < len(plans) else None
        fondu = 0.0 if k == 0 else (C.CREUX if p["_creux"] else p.get("fondu", C.FONDU))
        start = 0.0 if k == 0 else (t0 if p["_creux"] else ft(max(0.0, t0 - fondu / 2)))
        fin_clip = t1 if (suivant is None or suivant["_creux"]) else t1 + suivant.get("fondu", C.FONDU) / 2
        dur = fin_clip - start
        typ = p["type"]
        if typ == "carte":
            corps = plan_carte_v(p, pid, vues, T, t0, tw)
        elif typ == "photo":
            corps = plan_photo_v(p, pid, photos)
        elif typ == "heure":
            corps = C.plan_heure(p, pid)
        elif typ == "citation":
            corps = C.plan_citation(p, pid)
        elif typ == "chiffres":
            corps = C.plan_chiffres(p, pid, T, t0, tw)
        elif typ == "constat":
            corps = C.plan_constat(p, pid)
            if len(p.get("ghost", "")) > 5:   # « 12 → 20 », « ?? H ?? » : plus petits, pour tenir dans la largeur
                corps = corps.replace('class="ghost"', 'class="ghost g-long"', 1)
        elif typ == "fin":
            corps = plan_fin_v(p, pid, T, t0, tw)
        elif typ == "titre":
            corps = C.plan_titre(p, pid)
        elif typ == "credits":
            corps = C.plan_credits(p, pid)
        elif typ in ("partie", "suite"):
            corps = plan_partie(p, pid, t0, tw)
        else:
            sys.exit(f"type de plan inconnu : {typ}")
        corps += C.cartouche(p.get("cartouche"), pid)
        sections.append(f'<section id="{pid}" class="clip plan plan-{typ}" data-start="{start:.4f}" '
                        f'data-duration="{dur:.4f}" data-track-index="{1 + k % 2}"><div id="{pid}-in" class="inner"'
                        f'{" style=\"opacity:0\"" if fondu > 0 else ""}>{corps}</div></section>')
        if fondu > 0:
            tw.append(f'tl.fromTo("#{pid}-in",{{opacity:0}},{{opacity:1,duration:{fondu},ease:"sine.inOut"}},{start:.4f});')
        else:
            tw.append(f'tl.set("#{pid}-in",{{opacity:1}},{start:.4f});')
        if suivant is not None and suivant["_creux"]:
            tw.append(f'tl.fromTo("#{pid}-in",{{opacity:1}},{{opacity:0,duration:{C.CREUX},ease:"sine.in"}},{ft(t1 - C.CREUX):.4f});')
        cam = p.get("camera") or ({"de": [1.0, 0, 0], "a": [1.05, 0, 0]} if typ in ("carte", "photo") else None)
        if cam and typ in ("carte", "photo"):
            (s0, x0, y0), (s1, x1, y1) = cam["de"], cam["a"]
            origine = cam.get("origine", "50% 50%")
            if typ == "carte" and cam.get("foyer"):
                fx, fy = vues[p["vue"]]["points"][cam["foyer"]]
                origine = f"{fx:.0f}px {fy:.0f}px"
            tw.append(f'tl.fromTo("#{pid}-cam",{{scale:{s0},x:{x0},y:{y0},transformOrigin:"{origine}"}},'
                      f'{{scale:{s1},x:{x1},y:{y1},duration:{dur:.3f},ease:"sine.inOut"}},{start:.4f});')
        if p.get("cartouche"):
            tw.append(f'tl.fromTo("#{pid}-cart",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.6,ease:"power3.out"}},{ft(t0 + 0.35):.4f});')
        if typ == "heure":
            tw += [f'tl.fromTo("#{pid}-st",{{opacity:0,y:-12}},{{opacity:1,y:0,duration:0.5,ease:"power2.out"}},{ft(t0 + 0.1):.4f});',
                   f'tl.fromTo("#{pid}-hm",{{opacity:0,x:-40}},{{opacity:1,x:0,duration:0.7,ease:"expo.out"}},{ft(t0 + 0.2):.4f});',
                   f'tl.fromTo("#{pid}-rule",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:0.9,ease:"power3.inOut"}},{ft(t0 + 0.45):.4f});',
                   f'tl.fromTo("#{pid}-evt",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.7,ease:"power2.out"}},{ft(t0 + 0.7):.4f});',
                   f'tl.fromTo("#{pid}-lieu",{{opacity:0}},{{opacity:1,duration:0.6}},{ft(t0 + 1.0):.4f});',
                   f'tl.fromTo("#{pid}-ghost",{{x:0}},{{x:-120,duration:{t1 - t0 + 0.5:.3f},ease:"none"}},{start:.4f});']
        elif typ == "citation":
            tw += [f'tl.fromTo("#{pid}-gl",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.6,ease:"back.out(1.8)"}},{ft(t0 + 0.1):.4f});',
                   f'tl.fromTo("#{pid}-q",{{opacity:0,y:24}},{{opacity:1,y:0,duration:0.8,ease:"power2.out"}},{ft(t0 + 0.3):.4f});',
                   f'tl.fromTo("#{pid}-who",{{opacity:0,x:-20}},{{opacity:1,x:0,duration:0.6,ease:"power3.out"}},{ft(t0 + 0.9):.4f});',
                   f'tl.fromTo("#{pid}-src",{{opacity:0}},{{opacity:1,duration:0.6}},{ft(t0 + 1.2):.4f});']
        elif typ == "constat":
            if p.get("ghost"):
                tw.append(f'tl.fromTo("#{pid}-ghost",{{x:0}},{{x:-120,duration:{dur:.3f},ease:"none"}},{start:.4f});')
            tw.append(f'tl.fromTo("#{pid}-k",{{opacity:0,y:26}},{{opacity:1,y:0,duration:0.8,ease:"power2.out"}},{ft(t0 + 0.2):.4f});')
            if p.get("sous"):
                ta = T(p["sous_a"]) if "sous_a" in p else t0 + 1.2
                tw.append(f'tl.fromTo("#{pid}-s",{{opacity:0}},{{opacity:1,duration:0.7}},{ft(ta):.4f});')
        elif typ == "chiffres":
            tw.append(f'tl.fromTo("#{pid}-t",{{opacity:0,y:-14}},{{opacity:1,y:0,duration:0.6,ease:"power2.out"}},{ft(t0 + 0.15):.4f});')
        elif typ == "titre":
            tw += [f'tl.fromTo("#{pid}-k",{{opacity:0,y:-10}},{{opacity:1,y:0,duration:0.6}},{ft(t0 + 0.2):.4f});',
                   f'tl.fromTo("#{pid}-h1",{{opacity:0,y:30}},{{opacity:1,y:0,duration:1.0,ease:"power3.out"}},{ft(t0 + 0.4):.4f});',
                   f'tl.fromTo("#{pid}-h2",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.9,ease:"power2.out"}},{ft(t0 + 0.9):.4f});',
                   f'tl.fromTo("#{pid}-rule",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:1.2,ease:"power3.inOut"}},{ft(t0 + 1.1):.4f});',
                   f'tl.fromTo("#{pid}-note",{{opacity:0}},{{opacity:1,duration:0.8}},{ft(t0 + 1.6):.4f});',
                   f'tl.fromTo("#{pid}-ghost",{{x:0}},{{x:-160,duration:{dur:.3f},ease:"none"}},{start:.4f});']

    # ---- habillage : jour, numéro de partie, horloge du samedi, sources, sous-titres
    hud = []
    seqd = {s["n"]: s for s in script["sequences"]}
    jours = []
    for p in ch["phrases"]:
        j = seqd[p["seq"]]["jour"]
        if not jours or jours[-1][0] != j:
            jours.append([j, p["debut"]])
    for k, (j, t) in enumerate(jours):
        t_fin = jours[k + 1][1] if k + 1 < len(jours) else fin_hud
        a = ft(max(0.0, t - 0.2)) if k else ft(max(0.0, voix0 - 0.25)) if n > 1 else 0.0
        hud.append(f'<div id="jour{k}" class="clip jour" data-start="{a:.4f}" data-duration="{ft(t_fin) - a:.4f}" '
                   f'data-track-index="5"><span class="j-dot"></span>{esc(j)}</div>')
        tw.append(f'tl.fromTo("#jour{k}",{{opacity:0}},{{opacity:1,duration:0.6}},{a:.4f});')
    a = 0.0 if n == 1 else ft(voix0 - 0.25)
    hud.append(f'<div id="ptag" class="clip partie-tag" data-start="{a:.4f}" data-duration="{ft(fin_hud) - a:.4f}" '
               f'data-track-index="4">PARTIE {n}/3</div>')
    tw.append(f'tl.fromTo("#ptag",{{opacity:0}},{{opacity:1,duration:0.6}},{a:.4f});')

    hz = cfg["horloge"]
    e0, e1 = etat(hz["debut"]), etat(hz["fin"])
    hz_debut = ft(T(hz["debut"])) if e0 == 0 else (ft(voix0 - 0.25) if e0 < 0 else None)
    hz_fin = ft(T(hz["fin"])) if e1 == 0 else (ft(voix_fin + 0.6) if e1 > 0 else None)
    if hz_debut is not None and hz_fin is not None and hz_fin - hz_debut > 3:
        hud.append(f'<div id="horloge" class="clip horloge" data-start="{hz_debut:.4f}" data-duration="{hz_fin - hz_debut:.4f}" '
                   f'data-track-index="6">{C.horloge(hz)}</div>')
        tw.append(f'tl.fromTo("#horloge",{{opacity:0,y:-10}},{{opacity:1,y:0,duration:0.8}},{hz_debut:.4f});')
        for k, m in enumerate(hz["marques"]):
            e = etat(m["revele"])
            if e < 0:
                tw.append(f'tl.set("#hz-m{k}",{{opacity:1}},{hz_debut:.4f});')
            elif e > 0:
                tw.append(f'tl.set("#hz-m{k}",{{opacity:0.22}},{hz_debut:.4f});')
            else:
                tw.append(f'tl.fromTo("#hz-m{k}",{{opacity:0.22}},{{opacity:1,duration:0.6}},{ft(T(m["revele"])):.4f});')
        avant = [c for c in hz["curseur"] if etat(c["a"]) < 0]
        pos = C.h2x(avant[-1]["h"], 30, 790) if avant else None
        if pos is not None:
            tw.append(f'tl.set("#hz-cur",{{x:{pos:.1f}}},{hz_debut:.4f});')
        for c in hz["curseur"]:
            if etat(c["a"]) != 0:
                continue
            x = C.h2x(c["h"], 30, 790)
            if pos is None:
                tw.append(f'tl.set("#hz-cur",{{x:{x:.1f}}},{hz_debut:.4f});')
            else:
                tw.append(f'tl.fromTo("#hz-cur",{{x:{pos:.1f}}},{{x:{x:.1f},duration:1.0,ease:"power2.inOut"}},{ft(T(c["a"])):.4f});')
            pos = x

    src = script["sources"]
    sp = {p["cle"]: p for p in script["phrases"]}
    blocs_src = []
    for p in ch["phrases"]:
        lab = " · ".join(dict.fromkeys(f'{src[i]["media"]} ({src[i]["date"]})' for i in sp[p["cle"]].get("sources", [])))
        if blocs_src and blocs_src[-1][0] == lab:
            continue
        blocs_src.append([lab, p["debut"]])
    for k, (lab, t) in enumerate(blocs_src):
        t_fin = blocs_src[k + 1][1] if k + 1 < len(blocs_src) else min(voix_fin + 0.6, fin_hud)
        if not lab:
            continue
        a = ft(max(0.0, t - 0.1))
        hud.append(f'<div id="src{k}" class="clip sources" data-start="{a:.4f}" data-duration="{ft(t_fin) - a:.4f}" '
                   f'data-track-index="7"><span class="s-k">SOURCE{"S" if "·" in lab else ""}</span>{esc(lab)}</div>')
        tw.append(f'tl.fromTo("#src{k}",{{opacity:0}},{{opacity:1,duration:0.4}},{a:.4f});')

    subs = C.sous_titres(ch, 62)   # deux lignes de 31 caractères
    for k, s in enumerate(subs):
        a, b = ft(s["debut"]), ft(s["fin"])
        hud.append(f'<div id="st{k}" class="clip st" data-start="{a:.4f}" data-duration="{b - a:.4f}" '
                   f'data-track-index="8">{sous_titre_html(s["texte"])}</div>')

    css = (ROOT / "scripts/style.css").read_text() + (ROOT / "scripts/style_tiktok.css").read_text()
    doc = f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>Marseille, 17 octobre · partie {n}/3</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
{css}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{D:.4f}" data-fps="{FPS}" data-width="{W}" data-height="{H}">
      {chr(10).join("      " + s for s in sections).lstrip()}
      {chr(10).join("      " + s for s in hud).lstrip()}
      <div class="grain"></div>
      <audio id="mix" src="mix_master.wav" data-start="0" data-duration="{D:.4f}" data-track-index="20"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + x for x in tw).lstrip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
    d = SORTIE / f"partie-{n}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(doc)
    lien = d / "assets"
    if not lien.is_symlink():
        lien.symlink_to(os.path.relpath(ROOT / "assets", d))
    (d / "meta.json").write_text(json.dumps({"id": f"marseille-17-octobre-tiktok-{n}", "name": f"marseille-17-octobre-tiktok-{n}"}))
    (d / "hyperframes.json").write_text((ROOT / "hyperframes.json").read_text())
    (d / "chronologie.json").write_text(json.dumps(ch, ensure_ascii=False))
    calc = {"duree": D, "voix_debut": voix0, "voix_fin": voix_fin, "decalage": dt, "plans": [
        {"id": p["id"], "type": p["type"], "seq": p.get("seq"), "debut": p["_debut"], "fin": p["_fin"],
         "duree": round(p["_fin"] - p["_debut"], 3), "musique": p.get("musique")} for p in plans]}
    (d / "plans_calcules.json").write_text(json.dumps(calc, ensure_ascii=False, indent=1))

    # ---- son : la même voix, découpée (marges prises dans les silences entre séquences), puis le mixage habituel
    sr = A.SR
    a, b = ph_part[0]["debut"] - 0.25, ph_part[-1]["fin"] + 0.45
    seg = voix[int(round(a * sr)):int(round(b * sr))].copy()
    f = int(0.01 * sr)
    seg[:f] *= np.linspace(0, 1, f)
    seg[-f:] *= np.linspace(1, 0, f)
    v = np.zeros(int(round(D * sr)))
    i = int(round((a + dt) * sr))
    v[i:i + len(seg)] = seg[:len(v) - i]
    if "--sans-son" in sys.argv:   # garde le mixage déjà fait (seul l'habillage a changé)
        res = json.loads((d / "audio_mesures.json").read_text()) if (d / "audio_mesures.json").exists() else {}
    else:
        res = A.mixer(v, ch, calc["plans"], seqd, D, d, avec_stems=False)
        (d / "audio_mesures.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    courts = [f"{p['id']} {p['_fin'] - p['_debut']:.2f}s" for p in plans if p["_fin"] - p["_debut"] < 2.5]
    print(f"partie {n} : {len(plans)} plans, {D:.2f} s ({int(D // 60)} min {D % 60:04.1f} s), {len(subs)} sous-titres"
          + (f" · plans courts : {', '.join(courts)}" if courts else "")
          + (f" · {res['loudness_integree_lufs']} LUFS, crête {res['crete_vraie_dbtp']} dBTP, écart voix/musique "
             f"{res['ecart_voix_musique_db']} dB" if res else ""))
    return {"n": n, "titre": P["titre"], "duree": D, "seqs": P["seqs"], "plans": calc["plans"], "audio": res}


# ------------------------------------------------------------------------------------------------ publication
def publication(script: dict, chrono: dict, infos: list[dict]) -> None:
    src = script["sources"]
    lignes = ["# Publication TikTok — trois parties", "",
              "Format vertical 1080 × 1920, 30 i/s, sous-titres incrustés. Fichiers : "
              "`livrables/marseille-17-octobre_tiktok-partie-N.mp4`.", "",
              "À l'envoi, sur chaque partie : activer l'étiquette **« Contenu généré par IA »** (voix de synthèse) ;",
              "publier dans l'ordre 1, 2, 3, puis les épingler sur le profil ou les grouper dans une playlist.", ""]
    for info in infos:
        seqs = set(info["seqs"])
        ids = list(dict.fromkeys(s for ph in script["phrases"] if ph["seq"] in seqs for s in ph.get("sources", []) if s != "OSM"))
        medias = list(dict.fromkeys(src[s]["media"] for s in ids))
        D = info["duree"]
        lignes += [f"## Partie {info['n']}/3 — {info['titre']} ({int(D // 60)} min {D % 60:02.0f} s)", "",
                   "Légende proposée :", "",
                   "> Marseille, samedi 17 octobre 2026 : " + {
                       1: "comment une journée contre la vie chère a basculé dans le pillage avant midi. "
                          "Heure par heure, d'après la presse locale. Partie 1/3.",
                       2: "l'hôtel de ville forcé, le rassemblement empêché, les pillages jusque dans la nuit. Partie 2/3.",
                       3: "le jour d'après, les bilans qui divergent, ce que l'on sait et ce qui reste ouvert. Partie 3/3.",
                   }[info["n"]],
                   ">",
                   f"> Sources : {' · '.join(medias)}. Aucune image des événements : cartes OpenStreetMap et photos "
                   "des lieux en temps normal. Voix de synthèse.",
                   ">",
                   "> #Marseille #actualité #vieChère #Canebière #chronologie", ""]
    lignes += ["## Rappels", "",
               "- Les heures « direct » sont des heures de mise en ligne d'entrées de direct : le fait peut être antérieur.",
               "- Les chiffres de pilleurs et de commerces restent contestés ; aucun n'est présenté comme établi.",
               "- La liste complète des sources (avec liens) est dans `docs/06_publication.md`.", ""]
    (ROOT / "docs/08_tiktok.md").write_text("\n".join(lignes))


def main() -> None:
    script = json.loads((ROOT / "scripts/script.json").read_text())
    cfg = json.loads((ROOT / "scripts/plans.json").read_text())
    chrono = json.loads((BUILD / "chronologie.json").read_text())
    if chrono.get("brouillon", True):
        sys.exit("Refus : la voix est un brouillon de calage ; la version TikTok utilise la voix livrée.")
    vues = json.loads((ROOT / "assets/carte/vues.json").read_text())["vues"]
    photos = {Path(c["fichier"]).stem: c for c in json.loads((ROOT / "assets/photos/credits.json").read_text())}
    voix, sr = sf.read(BUILD / "voix.wav", dtype="float64")
    assert sr == A.SR
    choix = [int(x) for x in sys.argv[1:] if x.isdigit()] or [P["n"] for P in PARTIES]
    infos = [partie(P, script, cfg, chrono, vues, photos, voix) for P in PARTIES if P["n"] in choix]
    if len(infos) == len(PARTIES):
        publication(script, chrono, infos)
        (SORTIE / "parties.json").write_text(json.dumps(infos, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
