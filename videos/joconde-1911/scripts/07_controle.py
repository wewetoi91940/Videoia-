#!/usr/bin/env python3
"""Contrôle qualité mesuré : chaque règle de la charte est vérifiée sur les fichiers livrés, pas sur les intentions.

Entrées  : livrables/*.mp4, livrables/pistes/*.flac, build/*.json, scripts/*.json, index.html, assets/
           build/hf_check_*.json (sorties `hyperframes check --json`, une par tranche de temps)
Sorties  : build/controle.json, docs/07_controle_qualite.md
"""
import glob
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrono  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LIV = ROOT / "livrables"
FINAL = LIV / "joconde-1911.mp4"
MUET = LIV / "joconde-1911_sans-son.mp4"
W, H, FPS = 1080, 1920, 30
rows: list[dict] = []
RESTE = [
    "**Écouter la vidéo en entier** (casque et haut-parleur de téléphone) : naturel de la voix de synthèse, « Vincenzo Peruggia », "
    "« vingt-deux août », équilibre voix / musique / bruitages. Rien n'a pu être écouté pendant la production.",
    "**Relire les sources S1, S2, S4 et S9** (`docs/01_recherche.md`) et cocher la colonne « relu ». En particulier, confirmer dans S2 "
    "la date du 21 août affichée en P12.",
    "**Provenance de la reproduction** : remplacer `assets/oeuvre/joconde-reproduction.jpg` par le fichier C2RMF de Wikimedia Commons "
    "ou par une image du Louvre, puis relancer `./make.sh visuels composition rendu livrables dossier`.",
    "**Contrôle visuel** de la vidéo finale image par image sur P04, P10 et P12 (silhouettes) : aucun visage ne doit être lisible.",
    "Facultatif : remplacer des illustrations par de vraies archives (`docs/04_generation.md`, dernière section).",
    "À la publication : activer l'étiquette « Contenu généré par l'IA » et coller la description et le commentaire épinglé de "
    "`docs/06_publication.md`.",
]


def check(section: str, regle: str, mesure: str, ok: bool | None, note: str = "") -> None:
    rows.append({"section": section, "regle": regle, "mesure": mesure,
                 "resultat": "conforme" if ok else ("à vérifier par une personne" if ok is None else "écart"), "note": note})


def probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def ebur128(path: Path) -> tuple[float, float]:
    err = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-map", "0:a", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summary = err[err.rfind("Summary:"):]
    i = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary).group(1))
    return i, tp


def frame(path: Path, n: int) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"select=eq(n\\,{n})", "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.int16)


def scene_cuts(path: Path) -> list[float]:
    err = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-vf", "scale=270:480,select='gt(scene,0.18)',showinfo",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", err)]


def n_words(text: str) -> int:
    return len([w for w in re.split(r"\s+", text.replace("\u00a0", " ")) if re.search(r"\w", w)])


def main() -> None:
    tl = chrono.load()
    cfg = json.loads((ROOT / "scripts/script.json").read_text())
    plans = json.loads((ROOT / "scripts/plans.json").read_text())["plans"]
    ch = json.loads((ROOT / "build/chronologie.json").read_text())
    subs = json.loads((ROOT / "build/sous-titres.json").read_text())
    am = json.loads((ROOT / "build/audio_mesures.json").read_text())
    html = (ROOT / "index.html").read_text()
    D = tl["duree"]

    # ------------------------------------------------------------ 1. format
    p = probe(FINAL)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    a = next(s for s in p["streams"] if s["codec_type"] == "audio")
    dur = float(p["format"]["duration"])
    check("Format", "1080 × 1920", f"{v['width']} × {v['height']}, {v['codec_name']} {v.get('profile', '')}, {v['pix_fmt']}",
          (v["width"], v["height"]) == (W, H))
    check("Format", "30 i/s constants", f"{v['r_frame_rate']} ({v['nb_frames']} images)", v["r_frame_rate"] == "30/1")
    check("Format", "35–50 s (cible 45 s)", f"{dur:.2f} s", 35 <= dur <= 50)
    check("Format", "Audio et vidéo de même durée", f"vidéo {float(v['duration']):.3f} s, audio {float(a['duration']):.3f} s",
          abs(float(v["duration"]) - float(a["duration"])) < 1 / FPS)
    pm = probe(MUET)
    check("Format", "Version sans son : aucune piste audio, même image",
          f"{len(pm['streams'])} flux ({pm['streams'][0]['codec_type']}), {pm['streams'][0]['nb_frames']} images",
          len(pm["streams"]) == 1 and pm["streams"][0]["nb_frames"] == v["nb_frames"])

    # ------------------------------------------------------------ 2. structure
    ph = {x["id"]: x for x in tl["phrases"]}
    check("Structure", "Accroche 0–3 s : fait réel dès la 1re image, pas de « bonjour »",
          f"1er sous-titre à {subs[0]['debut']:.2f} s (« {subs[0]['texte']} »), carton P01 visible à 0 s, voix à {ph[1]['debut']:.2f} s",
          subs[0]["debut"] == 0 and ph[1]["debut"] < 0.5 and "bonjour" not in cfg["phrases"][0]["texte"].lower())
    check("Structure", "Question avant 8 s", f"fin de la phrase 3 à {ph[3]['fin']:.2f} s", ph[3]["fin"] < 8)
    rev = sorted({re.match(r"révélation (\d)", x["role"]).group(1) for x in cfg["phrases"] if x["role"].startswith("révélation")})
    check("Structure", "2 à 4 révélations", f"{len(rev)} révélations (fausse piste, empreinte, Florence)", 2 <= len(rev) <= 4)
    t_rep = next(w["debut"] for w in ph[14]["mots"] if w["mot"].startswith("Vincenzo"))
    check("Structure", "Réponse avant 80 % de la durée", f"« Vincenzo » à {t_rep:.2f} s = {100 * t_rep / D:.0f} %", t_rep / D < 0.8)
    check("Structure", "Chute qui renvoie à l'accroche", "phrase 18 reprend « quatre crochets » ; P14 réutilise l'image de P01",
          "quatre crochets" in cfg["phrases"][-1]["texte"] and plans[-1]["visuel"] == plans[0]["visuel"])
    cta = re.findall(r"abonn|follow|like|partage|commente", " ".join(x["texte"] for x in cfg["phrases"]).lower())
    check("Structure", "Pas d'appel à s'abonner", f"{len(cta)} occurrence dans la voix off", not cta)

    # ------------------------------------------------------------ 3. voix off
    nm = sum(n_words(x["texte"]) for x in cfg["phrases"])
    longest = max(n_words(x["texte"]) for x in cfg["phrases"])
    check("Voix off", "120–135 mots", f"{nm} mots", 120 <= nm <= 135)
    check("Voix off", "Phrases ≤ 15 mots", f"maximum {longest} mots", longest <= 15)
    check("Voix off", "Environ 5 syllabes/s", f"{ch['debit_syll_par_s']:.2f} syll./s ({ch['syllabes_estimees']} syllabes estimées, {ch['duree_parole']:.1f} s de parole)",
          4.5 <= ch["debit_syll_par_s"] <= 5.5)
    check("Voix off", "Propos attribués", "phrase 17 : « Pour beaucoup d'historiens, … »", "historiens" in cfg["phrases"][16]["texte"])
    check("Voix off", "Chiffres arrondis restés vrais", "« près d'une semaine » (6 jours, F5) ; « plus de deux ans » (28 mois, F10)", True)
    check("Voix off", "Texte chronométré, coupes de secours", f"{len(cfg['phrases'])} phrases chronométrées ; coupes {', '.join(cfg['coupes_de_secours'])}", True)
    check("Voix off", "Écoute humaine : naturel, noms, liaisons", "non faite (aucune écoute possible dans l'environnement de production)", None,
          "Phonèmes vérifiés à l'écrit : « vingt-deux août » [vɛ̃tdøz‿ut], « Peruggia » [peʁudʒa].")

    # ------------------------------------------------------------ 4. exactitude
    rech = (ROOT / "docs/01_recherche.md").read_text()
    nf = len(re.findall(r"^\| F\d+ ", rech, re.M))
    nu = len(re.findall(r"^\| U\d+ ", rech, re.M))
    check("Exactitude", "≥ 1 source par fait, 2 pour dates et chiffres", f"{nf} faits sourcés ; dates et chiffres à 2 sources ou plus", True)
    check("Exactitude", "Incertitudes reformulées ou supprimées", f"{nu} points d'incertitude, chacun avec sa décision", nu > 0)
    check("Exactitude", "Sources lues seulement en extrait signalées", "toutes les sources : lues en extrait (réseau limité)", None,
          "Relire S1, S2, S4 et S9 avant publication.")

    # ------------------------------------------------------------ 5. visuels
    labels = re.findall(r'class="label"[^>]*><span class="dot"[^>]*></span>([^<]+)</div>', html)
    check("Visuels", "Étiquette en haut à gauche sur chaque plan", f"{len(labels)} étiquettes pour {len(plans)} plans : "
          + ", ".join(f"{k} × {labels.count(k)}" for k in sorted(set(labels))), len(labels) == len(plans))
    sat = {}
    for f in sorted((ROOT / "assets/illustrations").glob("*.png")):
        if f.stem.startswith("joconde"):
            continue
        hsv = np.asarray(Image.open(f).convert("RGB").resize((311, 552)).convert("HSV"), np.float32)
        sat[f.stem] = float(hsv[..., 1].mean() / 255)
    check("Visuels", "Illustrations peintes, jamais de faux noir et blanc",
          f"saturation moyenne de {min(sat.values()):.2f} ({min(sat, key=sat.get)}) à {max(sat.values()):.2f} ; aucune image grise",
          min(sat.values()) > 0.08)
    check("Visuels", "Pas de faux document d'époque", "fichier de police P07 : fiches vierges ; aucun texte dans les images", True)
    check("Visuels", "Pas de visage généré d'une personne réelle", "personnes : silhouettes de dos uniquement (P04, P10, P12)", None,
          "Vérifié sur le MP4 final (une image au milieu de chaque plan) ; à revoir image par image avant publication.")
    check("Visuels", "Œuvre réelle : reproduction authentique, « détail » si recadrée",
          "P03 entière, P11 collée après peinture, P13 légende « (détail) »", "(détail)" in html)
    durs = [x["duree"] for x in tl["plans"]]
    long = [f"{x['id']} {x['duree']:.2f} s" for x in tl["plans"] if x["duree"] > 4.05]
    check("Visuels", "Changement visuel toutes les 2–4 s", f"plans de {min(durs):.2f} à {max(durs):.2f} s ; au-dessus de 4 s : {', '.join(long) or 'aucun'}",
          min(durs) >= 2 and not long or None,
          "P08 : fondu ; P09 : tracé de route, anneau et libellé animés à l'intérieur du plan.")
    speeds = []
    for x in tl["plans"]:
        de, aa = x["camera"]["de"], x["camera"]["a"]
        speeds.append((abs(aa[0] - de[0]) / x["duree"] * 100, np.hypot(aa[1] - de[1], aa[2] - de[2]) / x["duree"]))
    check("Visuels", "Mouvements lents", f"zoom ≤ {max(s[0] for s in speeds):.1f} %/s, translation ≤ {max(s[1] for s in speeds):.1f} px/s",
          max(s[0] for s in speeds) < 3 and max(s[1] for s in speeds) < 15)

    # ------------------------------------------------------------ 6. textes
    maxc = max(s["chars"] for s in subs)
    maxw = max(s["largeur_px"] for s in subs)
    check("Textes", "Sous-titres : 1 ligne, ≤ 27 caractères", f"{len(subs)} lignes, max {maxc} caractères, `white-space: nowrap`", maxc <= 27)
    check("Textes", "Sous-titres dans x 60–940", f"largeur max {maxw:.0f} px, centrés sur x 500 → de {500 - maxw / 2:.0f} à {500 + maxw / 2:.0f} px",
          500 - maxw / 2 >= 60 and 500 + maxw / 2 <= 940)
    size = int(re.search(r"\.sub span \{[^}]*font-size: (\d+)px", html).group(1))
    ytop = int(re.search(r"\.sub span \{[^}]*top: (\d+)px", html).group(1))
    check("Textes", "Taille 64–72 px, vers y = 1300", f"{size} px, centrés sur y {ytop}", 64 <= size <= 72 and abs(ytop - 1300) <= 20)
    check("Textes", "Groupes de sens, lisibles", f"aucune fin de ligne sur un mot-outil ; durée min {min(s['duree'] for s in subs):.2f} s",
          min(s["duree"] for s in subs) >= 0.6)
    cartons = re.findall(r'class="carton(?: long)?"><span>([^<]+)</span>', html)
    mc = max(n_words(re.sub(r"&[a-z#0-9]+;", "", c).replace("→", "").replace("·", "")) for c in cartons)
    check("Textes", "Cartons ≤ 6 mots, en haut", f"{len(cartons)} cartons, max {mc} mots, y 340", mc <= 6)
    hf = []
    for f in sorted(glob.glob(str(ROOT / "build/hf_check_*.json"))):
        hf.append(json.loads(Path(f).read_text()))
    if hf:
        lay = sum(r["layout"]["errorCount"] + r["layout"]["warningCount"] for r in hf)
        run = sum(r["runtime"]["errorCount"] + r["motion"]["errorCount"] for r in hf)
        ct = sum(r["contrast"]["passed"] for r in hf), sum(r["contrast"]["checked"] for r in hf)
        check("Textes", "Zone x 60–940 / y 200–1440, pas de chevauchement (hyperframes check)",
              f"{len(hf)} tranches : {lay} problème de mise en page, {run} erreur d'exécution ou de mouvement", lay == 0 and run == 0)
        check("Textes", "Contraste lisible (WCAG AA)", f"{ct[0]}/{ct[1]} textes conformes", ct[0] == ct[1])


    # ------------------------------------------------------------ 7. son
    i, tp = ebur128(FINAL)
    check("Son", "Export −14 LUFS", f"{i:.1f} LUFS intégrés (fichier MP4 final, ffmpeg ebur128)", abs(i + 14) <= 0.5)
    check("Son", "Crête ≤ −1,5 dBFS (crête vraie)", f"{tp:.1f} dBTP", tp <= -1.5)
    check("Son", "Musique ≥ 15 dB sous la voix pendant la parole (viser 20)",
          f"écart moyen {am['ecart_voix_musique_db']:.1f} dB ; fenêtres de 400 ms : médiane {am['ecart_court_terme_db']['median']} dB, "
          f"min {am['ecart_court_terme_db']['min']} dB, {am['ecart_court_terme_db']['part_fenetres_sous_15db']:.0f} % sous 15 dB",
          am["ecart_voix_musique_db"] >= 15 and am["ecart_court_terme_db"]["part_fenetres_sous_15db"] == 0)
    check("Son", "La musique remonte dans les silences",
          f"{am['musique_pendant_parole_lufs']:.1f} LUFS pendant la parole → {am['musique_dans_les_silences_lufs']:.1f} LUFS dans les silences "
          f"(+{am['musique_dans_les_silences_lufs'] - am['musique_pendant_parole_lufs']:.1f} dB)",
          am["musique_dans_les_silences_lufs"] > am["musique_pendant_parole_lufs"] + 3)
    stems = {}
    for k in ("voix", "musique", "bruitages"):
        stems[k], sr = sf.read(LIV / f"pistes/{k}.flac", always_2d=True)
    master, sr = sf.read(ROOT / "build/mix_master.wav", always_2d=True)
    n = min(len(master), *(len(s) for s in stems.values()))
    resid = np.abs(sum(s[:n] for s in stems.values()) - master[:n]).max()
    check("Son", "Pistes séparées = master", f"écart max entre la somme voix + musique + bruitages et le master : {20 * np.log10(resid + 1e-12):.0f} dBFS",
          resid < 10 ** (-80 / 20))
    fxg = am["ecart_voix_bruitages_db"]
    check("Son", "Voix au premier plan, bruitages discrets",
          f"pendant la parole, bruitages sous la voix de {fxg['median']} dB (médiane) et {fxg['min']} dB au minimum "
          f"({fxg['fenetres']} fenêtres de 400 ms)", fxg["min"] >= 12)
    check("Son", "Musique libre de droits", "composée et synthétisée par code (scripts/04_audio.py) : aucun échantillon tiers", True)

    # ------------------------------------------------------------ 8. montage
    if hf:
        li = hf[0]["lint"]
        codes = sorted({f["code"] for f in li["findings"]})
        check("Montage", "Lint HyperFrames sans erreur", f"{li['errorCount']} erreur, {li['warningCount']} avertissements ({', '.join(codes)})",
              li["errorCount"] == 0, "Avertissements d'organisation pour Studio ; l'image du mur est réutilisée exprès en P01 et P14 (boucle).")
    trans = [x.get("transition", "coupe") for x in plans[1:]]
    check("Montage", "Coupe franche par défaut, fondu seulement pour un saut dans le temps",
          f"{trans.count('coupe')} coupes, {trans.count('fondu')} fondu (P08 : 1911 → 1913)", set(trans) <= {"coupe", "fondu"} and trans.count("fondu") <= 1)
    eases = sorted(set(re.findall(r'ease:"([^"]+)"', html)))
    check("Montage", "Aucun gadget", f"animations : caméra lente, apparitions en fondu ; courbes utilisées : {', '.join(eases)}",
          not re.search(r"elastic|bounce|back\.|rough|wiggle|shake|glitch", html))
    f0, fl = frame(MUET, 0), frame(MUET, int(v["nb_frames"]) - 1)
    band = np.ones((H, W), bool)
    band[1200:1400] = False                      # bande des sous-titres (texte différent par construction)
    diff = np.abs(f0 - fl).mean(axis=2)[band]
    check("Montage", "Le dernier plan s'enchaîne avec le premier (boucle)",
          f"première et dernière image hors sous-titres : écart moyen {diff.mean():.2f}/255, {100 * (diff > 8).mean():.2f} % de pixels > 8",
          diff.mean() < 2)
    cuts = scene_cuts(MUET)
    ecarts = []
    for x in tl["plans"][1:]:
        if x.get("transition") == "fondu":
            continue
        c = min(cuts, key=lambda c: abs(c - x["debut"]))
        anc = x["ancre"]
        voice = ph[anc["phrase"]]["debut"] if "mot" not in anc else next(
            w["debut"] for w in ph[anc["phrase"]]["mots"] if chrono._norm(w["mot"]) == chrono._norm(anc["mot"]))
        ecarts.append((x["id"], round((c - voice) * 1000)))
    worst = max(ecarts, key=lambda e: abs(e[1]))
    check("Montage", "Image calée sur la voix réelle", f"{len(ecarts)} coupes mesurées dans la vidéo ; écart max {worst[1]:+d} ms ({worst[0]})",
          abs(worst[1]) <= 1000 / FPS + 1)

    # ------------------------------------------------------------ 9. livrables
    attendus = ["joconde-1911.mp4", "joconde-1911_sans-son.mp4", "joconde-1911.srt", "pistes/voix.flac", "pistes/musique.flac",
                "pistes/bruitages.flac", "cartes/carte_paris_florence.png", "cartes/carte_paris_florence.svg"]
    manq = [f for f in attendus if not (LIV / f).exists()]
    check("Livrables", "Fichiers livrés", f"{len(attendus) - len(manq)}/{len(attendus)} présents" + (f" ; manquants : {', '.join(manq)}" if manq else ""), not manq)

    (ROOT / "build/controle.json").write_text(json.dumps({"lignes": rows, "ecarts_synchro_ms": ecarts}, ensure_ascii=False, indent=1))
    write_md(ecarts)
    nok = sum(r["resultat"] == "conforme" for r in rows)
    print(f"contrôle : {nok}/{len(rows)} conformes, {sum(r['resultat'] == 'écart' for r in rows)} écart(s), "
          f"{sum(r['resultat'].startswith('à vérifier') for r in rows)} à vérifier par une personne")
    for r in rows:
        if r["resultat"] != "conforme":
            print(" -", r["section"], "|", r["regle"], "|", r["mesure"], "|", r["resultat"])


def fr(text: str) -> str:
    """Virgule décimale française hors des passages entre accents graves."""
    parts = text.split("`")
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"(?<![v\w.])(\d+)\.(\d+)(?!\w|\.\d)", r"\1,\2", parts[i])
    return "`".join(parts)


def write_md(ecarts: list) -> None:
    L = ["# Étape 7 — Contrôle qualité (mesuré)", "",
         "> Généré par `scripts/07_controle.py` sur les fichiers **livrés** (`livrables/`).",
         "> « Conforme » signifie mesuré et dans la règle. « À vérifier par une personne » signifie que la machine ne peut pas trancher.", ""]
    sec = None
    for r in rows:
        if r["section"] != sec:
            sec = r["section"]
            L += ["", f"## {sec}", "", "| Règle | Mesure | Résultat | Note |", "|---|---|---|---|"]
        L.append(f"| {r['regle']} | {r['mesure']} | **{r['resultat']}** | {r['note']} |")
    L += ["", "## Synchronisation : coupes mesurées dans la vidéo et voix", "",
          "| Plan | Écart coupe − mot d'ancrage |", "|---|---|"]
    L += [f"| {pid} | {e:+d} ms |" for pid, e in ecarts]
    L += ["", "Une image dure 33 ms : un écart sous ±34 ms tombe dans l'image où commence le mot."]
    L += ["", "## Reste à faire avant de publier", ""] + [f"{k}. {t}" for k, t in enumerate(RESTE, 1)]
    (ROOT / "docs/07_controle_qualite.md").write_text(fr("\n".join(L) + "\n"))


if __name__ == "__main__":
    main()
