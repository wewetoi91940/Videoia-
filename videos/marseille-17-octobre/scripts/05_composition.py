#!/usr/bin/env python3
"""Montage : index.html (HyperFrames) et sous-titres, calés sur la voix réelle.

Entrées : scripts/script.json (phrases, séquences, sources), scripts/plans.json (plans ancrés sur des mots),
          build/chronologie.json (temps de chaque mot), assets/carte/vues.json, assets/photos/credits.json.
Sorties : index.html, build/plans_calcules.json (début/fin de chaque plan), build/marseille-17-octobre.srt.

Chaque plan commence sur un mot de la voix ; il dure jusqu'au plan suivant. Les plans entrent en fondu
par-dessus le précédent (aucun plan n'est transparent). Les débuts sont arrondis à l'image inférieure.
"""
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
FPS = 30
W, H = 1920, 1080
FONDU = 0.5          # durée du fondu enchaîné entre deux plans
FIN_APRES_VOIX = 1.0

STATUTS = {
    "publiee": "HEURE PUBLIÉE",
    "periode": "PÉRIODE · HEURE EXACTE NON PUBLIÉE",
    "prevue": "HEURE PRÉVUE, PAS CELLE D’UN FAIT",
    "depeche": "HEURE DE PUBLICATION D’UNE DÉPÊCHE",
    "jour": "DATE PUBLIÉE · HEURE NON PUBLIÉE",
    "direct": "SIGNALÉ EN DIRECT À CETTE HEURE · LE FAIT PEUT ÊTRE ANTÉRIEUR",
    "unique": "HEURE PUBLIÉE PAR UNE SEULE SOURCE",
}
H_DEBUT, H_FIN = 6, 27      # horloge du samedi : de 6 h à 3 h du matin


def ft(t: float) -> float:
    """Temps de l'image la plus proche, jamais au-dessus de n/FPS (sinon le plan démarre une image trop tard)."""
    return (round(t * FPS) * 10000 // FPS) / 10000


def typo(s: str) -> str:
    """Typographie française à l'écran : apostrophe courbe, espaces fines insécables devant ; : ? ! et dans « »."""
    s = s.replace("'", "’")
    s = re.sub(r"\s*([;:?!])", " \\1", s)
    s = re.sub(r"«\s*", "« ", s)
    s = re.sub(r"\s*»", " »", s)
    return s


def esc(s: str) -> str:
    return html.escape(typo(s), quote=True)


def norm(w: str) -> str:
    return re.sub(r"[^\wÀ-ÿ'’-]", "", w).lower().replace("’", "'")


class Temps:
    """Résout les ancres {phrase, mot, n, decalage, apres} en secondes sur la voix réelle."""

    def __init__(self, chrono: dict):
        self.ph = {p["cle"]: p for p in chrono["phrases"]}
        self.ordre = [p["cle"] for p in chrono["phrases"]]
        self.fin_voix = chrono["voix_fin"]

    def __call__(self, a: dict) -> float:
        p = self.ph.get(a["phrase"])
        if p is None:
            sys.exit(f"ancre inconnue : phrase {a['phrase']!r}")
        if a.get("apres"):
            t = p["fin"]
        elif "mot" in a:
            cible = norm(a["mot"])
            cands = [m for m in p["mots"] if norm(m["mot"]) == cible or norm(m["mot"]).split("'")[-1] == cible]
            if len(cands) < a.get("n", 1):
                sys.exit(f"ancre introuvable : mot {a['mot']!r} dans {a['phrase']!r} ({p['texte']})")
            t = cands[a.get("n", 1) - 1]["debut"]
        else:
            t = p["debut"]
        return t + float(a.get("decalage", 0.0))


# ----------------------------------------------------------------------------------------------- éléments
def cartouche(c: dict | None, pid: str) -> str:
    if not c:
        return ""
    statut = c.get("statut")
    chip = f'<div class="statut st-{statut}">{esc(STATUTS[statut])}</div>' if statut else ""
    heure = f'<div class="c-heure">{esc(c["heure"])}</div>' if c.get("heure") else ""
    return (f'<div id="{pid}-cart" class="cartouche">{chip}{heure}'
            f'<div class="c-lieu">{esc(c["lieu"])}</div></div>')


def chemin(pts: list) -> tuple[str, float]:
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    long = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
    return d, long


def plan_carte(p: dict, pid: str, vues: dict, T: Temps, t0: float, tw: list) -> str:
    v = vues[p["vue"]]
    w, h = v["w"], v["h"]
    panneau = w != W
    svg, labels = [], []
    for k, c in enumerate(p.get("couches", [])):
        ta = T(c["a"]) if "a" in c else t0 + 0.6
        cid = f"{pid}-c{k}"
        etat = c.get("etat", "actif")
        if "ligne" in c:
            for j, seg in enumerate(v["lignes"][c["ligne"]]):
                if len(seg) < 2:
                    continue
                d, L = chemin(seg)
                for suf, cls in (("h", "halo"), ("", etat)):
                    svg.append(f'<path id="{cid}-{j}{suf}" class="hl hl-{cls}" d="{d}" '
                               f'style="stroke-dasharray:{L:.0f};stroke-dashoffset:{L:.0f}"/>')
                    tw.append(f'tl.fromTo("#{cid}-{j}{suf}",{{strokeDashoffset:{L:.0f}}},{{strokeDashoffset:0,duration:1.4,ease:"power2.inOut"}},{ft(ta):.4f});')
        elif "zone" in c:
            for j, poly in enumerate(v["zone_rues"]):
                d, _ = chemin(poly)
                svg.append(f'<path id="{cid}-{j}" class="zone" d="{d} Z"/>')
                tw.append(f'tl.fromTo("#{cid}-{j}",{{opacity:0}},{{opacity:1,duration:0.9,ease:"sine.out"}},{ft(ta):.4f});')
        elif "point" in c:
            x, y = v["points"][c["point"]]
            svg.append(f'<g transform="translate({x:.1f},{y:.1f})"><circle id="{cid}-pu" class="pulse" r="12"/>'
                       f'<circle id="{cid}" class="pt pt-{etat}" r="11"/></g>')
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
            larg = 17.5 * len(c["etiquette"]) + 34
            if dx > 0 and x + dx + larg > w - 30:
                dx = -abs(dx)
            elif dx < 0 and x + dx - larg < 30:
                dx = abs(dx)
            ancre = "right" if dx < 0 else "left"
            style = (f"left:{x + dx:.0f}px" if ancre == "left" else f"right:{w - x - dx:.0f}px") + f";top:{y + dy:.0f}px"
            labels.append(f'<div id="{cid}-lb" class="etiq etiq-{ancre}" style="{style}">{esc(c["etiquette"])}</div>')
            tw.append(f'tl.fromTo("#{cid}-lb",{{opacity:0,y:10}},{{opacity:1,y:0,duration:0.5,ease:"power2.out"}},{ft(ta + 0.25):.4f});')
    gauche = left = ""
    if panneau:
        left = f"left:{W - w}px;"
        col = p.get("colonne", {})
        items = "".join(f'<li id="{pid}-li{k}">{esc(t)}</li>' for k, t in enumerate(col.get("lignes", [])))
        gauche = (f'<div class="colonne"><div class="col-kicker">{esc(col.get("kicker", ""))}</div>'
                  f'<h2 id="{pid}-h">{esc(col.get("titre", ""))}</h2><ul>{items}</ul></div>')
        tw.append(f'tl.fromTo("#{pid}-h",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.7,ease:"power3.out"}},{ft(t0 + 0.3):.4f});')
        for k, _ in enumerate(col.get("lignes", [])):
            ta = T(col["a"][k]) if col.get("a") else t0 + 0.7 + 0.35 * k
            tw.append(f'tl.fromTo("#{pid}-li{k}",{{opacity:0,y:16}},{{opacity:1,y:0,duration:0.6,ease:"power2.out"}},{ft(ta):.4f});')
    echelle = 200 * v["px_par_m"]
    barre = (f'<div id="{pid}-mob" class="mobilier"><div class="echelle"><span style="width:{echelle:.0f}px"></span>200 m</div>'
             f'<div class="nord">N</div><div class="attrib">© contributeurs d’OpenStreetMap</div></div>')
    # le mobilier de carte n'apparaît qu'après le fondu : pas de doublon avec celui de la carte précédente
    tw.append(f'tl.fromTo("#{pid}-mob",{{opacity:0}},{{opacity:1,duration:0.4}},{ft(t0 + FONDU / 2 + 0.05):.4f});')
    return (f'<div class="plateau" style="{left}width:{w}px;height:{h}px">'
            f'<div id="{pid}-cam" class="cam" style="width:{w}px;height:{h}px">'
            f'<img src="{v["image"]}" alt="" style="width:{w}px;height:{h}px"><div class="vignette"></div>'
            f'<svg class="calque" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{"".join(svg)}</svg>'
            f'{"".join(labels)}</div>{barre}</div>{gauche}')


def plan_photo(p: dict, pid: str, photos: dict) -> str:
    ph = photos[p["photo"]]
    credit = f'Photo : {ph["auteur"]} · {ph["licence"]} · Wikimedia Commons' + (" · image modifiée (floutage)" if ph.get("modifications") else "")
    pos = p.get("position", "50% 50%")
    return (f'<div id="{pid}-cam" class="cam"><img class="photo" src="assets/photos/{ph["fichier"]}" alt="" '
            f'style="object-position:{pos}"></div><div class="voile"></div>'
            f'<div class="mention">LE LIEU EN TEMPS NORMAL · PHOTO D’ILLUSTRATION</div>'
            f'<div class="credit">{esc(credit)}</div>')


def plan_heure(p: dict, pid: str) -> str:
    pre = f'<div class="h-pre">{esc(p["prefixe"])}</div>' if p.get("prefixe") else ""
    return (f'<div class="fond-grille"></div><div id="{pid}-ghost" class="ghost" aria-hidden="true" data-t="{esc(p["heure"])}"></div>'
            f'<div class="h-bloc"><div id="{pid}-st" class="statut st-{p["statut"]}">{esc(STATUTS[p["statut"]])}</div>'
            f'{pre}<div id="{pid}-hm" class="h-main{" h-long" if len(p["heure"]) > 7 else ""}">{esc(p["heure"])}</div>'
            f'<div id="{pid}-rule" class="h-rule"></div>'
            f'<p id="{pid}-evt" class="h-evt">{esc(p["evenement"])}</p>'
            f'<div id="{pid}-lieu" class="h-lieu">{esc(p.get("lieu", ""))}</div></div>')


def plan_citation(p: dict, pid: str) -> str:
    return (f'<div class="fond-grille"></div><div class="q-bloc"><div id="{pid}-gl" class="q-gl">«</div>'
            f'<blockquote id="{pid}-q">{esc(p["texte"])}</blockquote>'
            f'<div id="{pid}-who" class="q-who">{esc(p["qui"])}</div>'
            f'<div id="{pid}-src" class="q-src">{esc(p["source"])}</div></div>')


def plan_chiffres(p: dict, pid: str, T: Temps, t0: float, tw: list) -> str:
    vmax = max(r.get("valeur", 0) for r in p["lignes"]) or 1
    rows = []
    for k, r in enumerate(p["lignes"]):
        ta = T(r["a"]) if "a" in r else t0 + 0.8 + 0.5 * k
        pct = 100 * r.get("valeur", 0) / vmax
        barre = (f'<div class="barre"><span id="{pid}-b{k}" style="width:{pct:.2f}%"></span></div>'
                 if "valeur" in r and p.get("barres", True) else "")
        rows.append(f'<div id="{pid}-r{k}" class="ligne"><div class="l-val{" l-long" if len(r["affiche"]) > 8 else ""}">{esc(r["affiche"])}</div>'
                    f'<div class="l-txt"><div class="l-lib">{esc(r["libelle"])}</div>{barre}'
                    f'<div class="l-src">{esc(r.get("source", ""))}</div></div></div>')
        tw.append(f'tl.fromTo("#{pid}-r{k}",{{opacity:0,x:-28}},{{opacity:1,x:0,duration:0.6,ease:"power3.out"}},{ft(ta):.4f});')
        if barre:
            tw.append(f'tl.fromTo("#{pid}-b{k}",{{scaleX:0,transformOrigin:"0% 50%"}},{{scaleX:1,duration:1.0,ease:"power2.out"}},{ft(ta + 0.2):.4f});')
    note = f'<div id="{pid}-note" class="ch-note">{esc(p["note"])}</div>' if p.get("note") else ""
    if note:
        ta = T(p["note_a"]) if "note_a" in p else t0 + 1.5 + 0.5 * len(rows)
        tw.append(f'tl.fromTo("#{pid}-note",{{opacity:0}},{{opacity:1,duration:0.6}},{ft(ta):.4f});')
    return (f'<div class="fond-grille"></div><div class="ch-bloc"><div class="ch-kicker">{esc(p.get("kicker", ""))}</div>'
            f'<h2 id="{pid}-t">{esc(p["titre"])}</h2>{"".join(rows)}{note}</div>')


def plan_constat(p: dict, pid: str) -> str:
    sous = f'<p id="{pid}-s" class="k-sous">{esc(p["sous"])}</p>' if p.get("sous") else ""
    ghost = f'<div id="{pid}-ghost" class="ghost" aria-hidden="true" data-t="{esc(p["ghost"])}"></div>' if p.get("ghost") else ""
    return (f'<div class="fond-grille"></div>{ghost}<div class="k-bloc"><div class="k-kicker">{esc(p.get("kicker", ""))}</div>'
            f'<p id="{pid}-k" class="k-txt">{esc(p["texte"])}</p>{sous}</div>')


def plan_fin(p: dict, pid: str, T: Temps, t0: float, tw: list) -> str:
    cols = []
    for k, c in enumerate(p["colonnes"]):
        ta = T(c["a"]) if "a" in c else t0 + 0.5 + k
        items = "".join(f'<li id="{pid}-c{k}i{j}">{esc(t)}</li>' for j, t in enumerate(c["lignes"]))
        cols.append(f'<div id="{pid}-c{k}" class="f-col"><h3>{esc(c["titre"])}</h3><ul>{items}</ul></div>')
        tw.append(f'tl.fromTo("#{pid}-c{k}",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.7,ease:"power3.out"}},{ft(ta):.4f});')
        for j, _ in enumerate(c["lignes"]):
            tj = T(c["a_lignes"][j]) if c.get("a_lignes") else ta + 0.4 + 0.3 * j
            tw.append(f'tl.fromTo("#{pid}-c{k}i{j}",{{opacity:0,x:-14}},{{opacity:1,x:0,duration:0.5,ease:"power2.out"}},{ft(tj):.4f});')
    return f'<div class="fond-grille"></div><div class="f-bloc">{"".join(cols)}</div>'


def plan_titre(p: dict, pid: str) -> str:
    return (f'<div class="fond-grille"></div><div id="{pid}-ghost" class="ghost ghost-titre" aria-hidden="true" data-t="17.10"></div>'
            f'<div class="t-bloc"><div id="{pid}-k" class="t-kicker">{esc(p["kicker"])}</div>'
            f'<h1 id="{pid}-h1">{esc(p["titre"])}</h1><h2 id="{pid}-h2">{esc(p["sous_titre"])}</h2>'
            f'<div id="{pid}-rule" class="t-rule"></div><p id="{pid}-note" class="t-note">{esc(p["note"])}</p></div>')


def plan_credits(p: dict, pid: str) -> str:
    blocs = "".join(f'<div class="cr-bloc"><h3>{esc(b["titre"])}</h3>'
                    + "".join(f'<p>{esc(l)}</p>' for l in b["lignes"]) + "</div>" for b in p["blocs"])
    return f'<div class="cr-page"><div class="cr-kicker">{esc(p.get("kicker", "SOURCES"))}</div><div class="cr-cols">{blocs}</div></div>'


# --------------------------------------------------------------------------------------------- horloge
def h2x(hm: str, x0: float, x1: float) -> float:
    h, m = (hm.split(":") + ["0"])[:2]
    t = int(h) + int(m) / 60
    return x0 + (x1 - x0) * (t - H_DEBUT) / (H_FIN - H_DEBUT)


def horloge(cfg: dict) -> str:
    x0, x1, y = 30, 790, 38
    parts = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" class="hz-axe"/>']
    for hh in range(H_DEBUT, H_FIN + 1, 3):
        x = h2x(f"{hh}:00", x0, x1)
        parts.append(f'<line x1="{x:.1f}" y1="{y - 6}" x2="{x:.1f}" y2="{y + 6}" class="hz-tick"/>'
                     f'<text x="{x:.1f}" y="{y + 30}" class="hz-txt">{hh % 24} h</text>')
    for k, m in enumerate(cfg["marques"]):
        a = h2x(m["de"], x0, x1)
        if m["type"] == "periode":
            b = h2x(m["a"], x0, x1)
            parts.append(f'<rect id="hz-m{k}" x="{a:.1f}" y="{y - 9}" width="{b - a:.1f}" height="18" class="hz-periode"/>')
        elif m["type"] == "prevue":
            parts.append(f'<circle id="hz-m{k}" cx="{a:.1f}" cy="{y}" r="8" class="hz-prevue"/>')
        elif m["type"] == "direct":
            parts.append(f'<line id="hz-m{k}" x1="{a:.1f}" y1="{y - 11}" x2="{a:.1f}" y2="{y + 11}" class="hz-direct"/>')
        else:
            parts.append(f'<circle id="hz-m{k}" cx="{a:.1f}" cy="{y}" r="8" class="hz-publiee"/>')
    parts.append(f'<g id="hz-cur"><line x1="0" y1="{y - 22}" x2="0" y2="{y + 14}" class="hz-cur"/>'
                 f'<path d="M-7,{y - 30} L7,{y - 30} L0,{y - 20} Z" class="hz-curtri"/></g>')
    legende = ('<div class="hz-leg"><span class="lg lg-publiee"></span>heure publiée'
               '<span class="lg lg-periode"></span>période approximative'
               '<span class="lg lg-prevue"></span>heure prévue'
               '<span class="lg lg-direct"></span>signalé en direct</div>')
    return f'<svg class="hz" viewBox="0 0 820 80" width="820" height="80">{"".join(parts)}</svg>{legende}'


# ------------------------------------------------------------------------------------------- sous-titres
FAIBLES = set("le la les l' un une des de du d' et ou à au aux en par pour sur dans que qui ce cette ces son sa ses "
              "leur leurs ne n' se s' il elle ils on y est a avec sans selon".split())


def sous_titres(chrono: dict) -> list[dict]:
    """Une ou deux lignes de 42 caractères au plus ; jamais de coupure après un mot-outil."""
    out = []
    for p in chrono["phrases"]:
        mots = p["mots"]
        i = 0
        while i < len(mots):
            j, long = i, 0
            while j < len(mots) and long + len(mots[j]["mot"]) + 1 <= 84:
                long += len(mots[j]["mot"]) + 1
                j += 1
            if j < len(mots):
                k = j
                while k - 1 > i + 2 and (norm(mots[k - 1]["mot"]) in FAIBLES or norm(mots[k]["mot"]) in ("?", ":", ";")):
                    k -= 1
                j = k
            txt = " ".join(m["mot"] for m in mots[i:j])
            out.append({"debut": mots[i]["debut"], "fin": mots[j - 1]["fin"], "texte": typo(txt)})
            i = j
    for a, b in zip(out, out[1:]):
        a["fin"] = min(max(a["fin"] + 0.3, a["debut"] + 1.0), b["debut"] - 0.04)
    return out


def srt(subs: list[dict]) -> str:
    def tc(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    def lignes(t):
        if len(t) <= 42:
            return t
        mots, best = t.split(), None
        for k in range(1, len(mots)):
            a, b = " ".join(mots[:k]), " ".join(mots[k:])
            if len(a) <= 42 and len(b) <= 42 and norm(mots[k - 1]) not in FAIBLES:
                score = abs(len(a) - len(b))
                best = min(best or (score, a, b), (score, a, b))
        return f"{best[1]}\n{best[2]}" if best else t

    return "\n".join(f"{k}\n{tc(s['debut'])} --> {tc(s['fin'])}\n{lignes(s['texte'])}\n"
                     for k, s in enumerate(subs, 1))


# ---------------------------------------------------------------------------------------------- montage
def main() -> None:
    script = json.loads((ROOT / "scripts/script.json").read_text())
    plans_cfg = json.loads((ROOT / "scripts/plans.json").read_text())
    chrono = json.loads((BUILD / "chronologie.json").read_text())
    vues = json.loads((ROOT / "assets/carte/vues.json").read_text())["vues"]
    fc = ROOT / "assets/photos/credits.json"
    photos = {Path(c["fichier"]).stem: c for c in json.loads(fc.read_text())} if fc.exists() else {}
    photos = {k: c for k, c in photos.items() if (ROOT / "assets/photos" / c["fichier"]).exists()}
    T = Temps(chrono)

    plans = []
    for p in plans_cfg["plans"]:   # photo absente (licence non trouvée) : plan de repli prévu dans plans.json
        if p["type"] == "photo" and p["photo"] not in photos:
            if "repli" not in p:
                continue
            q = {k: v for k, v in p.items() if k not in ("photo", "repli", "position", "camera")}
            q.update(p["repli"])
            if q["type"] not in ("carte", "photo"):
                q.pop("cartouche", None)
            p = q
        plans.append(p)
    for p in plans:
        p["_debut"] = ft(T(p["ancre"])) if "ancre" in p else None
    voix_fin = chrono["voix_fin"]
    t = None
    for p in plans:        # plans de fin sans ancre : après la voix, à la suite, durée fixe
        if p["_debut"] is None:
            p["_debut"] = ft(t if t is not None else voix_fin + FIN_APRES_VOIX)
            t = p["_debut"] + p.get("duree", 6)
    for a, b in zip(plans, plans[1:]):
        a["_fin"] = b["_debut"]
    plans[-1]["_fin"] = ft(plans[-1]["_debut"] + plans[-1].get("duree", 6))
    D = plans[-1]["_fin"]
    for a, b in zip(plans, plans[1:]):
        if b["_debut"] - a["_debut"] < 1.2:
            sys.exit(f"plan {a['id']} trop court ({b['_debut'] - a['_debut']:.2f} s)")

    tw, sections = [], []
    for k, p in enumerate(plans):
        pid = p["id"].lower()
        t0, t1 = p["_debut"], p["_fin"]
        fondu = 0.0 if k == 0 else p.get("fondu", FONDU)
        start = ft(max(0.0, t0 - fondu / 2))
        dur = (t1 + (plans[k + 1].get("fondu", FONDU) / 2 if k + 1 < len(plans) else 0)) - start
        typ = p["type"]
        if typ == "carte":
            corps = plan_carte(p, pid, vues, T, t0, tw)
        elif typ == "photo":
            corps = plan_photo(p, pid, photos)
        elif typ == "heure":
            corps = plan_heure(p, pid)
        elif typ == "citation":
            corps = plan_citation(p, pid)
        elif typ == "chiffres":
            corps = plan_chiffres(p, pid, T, t0, tw)
        elif typ == "constat":
            corps = plan_constat(p, pid)
        elif typ == "fin":
            corps = plan_fin(p, pid, T, t0, tw)
        elif typ == "titre":
            corps = plan_titre(p, pid)
        elif typ == "credits":
            corps = plan_credits(p, pid)
        else:
            sys.exit(f"type de plan inconnu : {typ}")
        corps += cartouche(p.get("cartouche"), pid)
        sections.append(f'<section id="{pid}" class="clip plan plan-{typ}" data-start="{start:.4f}" '
                        f'data-duration="{dur:.4f}" data-track-index="{1 + k % 2}"><div id="{pid}-in" class="inner">'
                        f'{corps}</div></section>')
        if fondu > 0:
            tw.append(f'tl.fromTo("#{pid}-in",{{opacity:0}},{{opacity:1,duration:{fondu},ease:"sine.inOut"}},{start:.4f});')
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

    # ---- bandeau du jour, horloge du samedi, sources de la phrase en cours
    hud = []
    seqs = {s["n"]: s for s in script["sequences"]}
    fin_voix_plans = max(p["_debut"] for p in plans if p["type"] != "credits")
    jours = []
    for p in chrono["phrases"]:
        j = seqs[p["seq"]]["jour"]
        if not jours or jours[-1][0] != j:
            jours.append([j, p["debut"]])
    for k, (j, t) in enumerate(jours):
        t_fin = jours[k + 1][1] if k + 1 < len(jours) else fin_voix_plans
        a = ft(max(0.0, t - 0.2)) if k else 0.0
        hud.append(f'<div id="jour{k}" class="clip jour" data-start="{a:.4f}" data-duration="{ft(t_fin) - a:.4f}" '
                   f'data-track-index="5"><span class="j-dot"></span>{esc(j)}</div>')
        tw.append(f'tl.fromTo("#jour{k}",{{opacity:0}},{{opacity:1,duration:0.6}},{a:.4f});')
    hz = plans_cfg["horloge"]
    hz_debut = ft(T(hz["debut"]))
    hz_fin = ft(T(hz["fin"]))
    hud.append(f'<div id="horloge" class="clip horloge" data-start="{hz_debut:.4f}" data-duration="{hz_fin - hz_debut:.4f}" '
               f'data-track-index="6">{horloge(hz)}</div>')
    tw.append(f'tl.fromTo("#horloge",{{opacity:0,y:-10}},{{opacity:1,y:0,duration:0.8}},{hz_debut:.4f});')
    x0, x1 = 30, 790
    pos_prec = None
    for k, m in enumerate(hz["marques"]):
        tw.append(f'tl.fromTo("#hz-m{k}",{{opacity:0.22}},{{opacity:1,duration:0.6}},{ft(T(m["revele"])):.4f});')
    for c in hz["curseur"]:
        x = h2x(c["h"], x0, x1)
        ta = ft(T(c["a"]))
        if pos_prec is None:
            tw.append(f'tl.set("#hz-cur",{{x:{x:.1f}}},{hz_debut:.4f});')
        else:
            tw.append(f'tl.fromTo("#hz-cur",{{x:{pos_prec:.1f}}},{{x:{x:.1f},duration:1.0,ease:"power2.inOut"}},{ta:.4f});')
        pos_prec = x

    src = script["sources"]
    blocs_src = []
    for p, ph in zip(chrono["phrases"], script["phrases"]):
        ids = ph.get("sources", [])
        lab = " · ".join(dict.fromkeys(f'{src[i]["media"]} ({src[i]["date"]})' for i in ids))
        if blocs_src and blocs_src[-1][0] == lab:
            continue
        blocs_src.append([lab, p["debut"]])
    for k, (lab, t) in enumerate(blocs_src):
        t_fin = blocs_src[k + 1][1] if k + 1 < len(blocs_src) else voix_fin + 0.6
        if not lab:
            continue
        a = ft(max(0.0, t - 0.1))
        hud.append(f'<div id="src{k}" class="clip sources" data-start="{a:.4f}" data-duration="{ft(t_fin) - a:.4f}" '
                   f'data-track-index="7"><span class="s-k">SOURCE{"S" if "·" in lab else ""}</span>{esc(lab)}</div>')
        tw.append(f'tl.fromTo("#src{k}",{{opacity:0}},{{opacity:1,duration:0.4}},{a:.4f});')

    css = (ROOT / "scripts/style.css").read_text()
    doc = f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>Marseille, 17 octobre</title>
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
    subs = sous_titres(chrono)
    (BUILD / "marseille-17-octobre.srt").write_text(srt(subs))
    calc = {"duree": D, "voix_fin": voix_fin, "plans": [
        {"id": p["id"], "type": p["type"], "seq": p.get("seq"), "debut": p["_debut"], "fin": p["_fin"],
         "duree": round(p["_fin"] - p["_debut"], 3), "musique": p.get("musique")} for p in plans]}
    (BUILD / "plans_calcules.json").write_text(json.dumps(calc, ensure_ascii=False, indent=1))
    courts = [f"{p['id']} {p['_fin'] - p['_debut']:.2f}s" for p in plans if p["_fin"] - p["_debut"] < 2.5]
    print(f"index.html : {len(plans)} plans, durée {D:.2f} s ({D / 60:.2f} min), {len(subs)} sous-titres"
          + (f" · plans courts : {', '.join(courts)}" if courts else ""))


if __name__ == "__main__":
    main()
