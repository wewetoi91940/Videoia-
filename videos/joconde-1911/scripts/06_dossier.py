#!/usr/bin/env python3
"""Dossier de production généré à partir des données réelles (aucun temps recopié à la main).

Entrées  : scripts/script.json, scripts/plans.json, build/chronologie.json, build/sous-titres.json
Sorties  : docs/02_script.md, docs/03_storyboard.md, docs/05_montage.md
À relancer après toute modification de la voix ou des plans : les tableaux suivent la voix réelle.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chrono  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
FPS = chrono.FPS

# Musique et bruitages, plan par plan (reflète scripts/04_audio.py).
SON = {
    "P01": "Souffle de salle vide + 3 pas lointains (réverbération longue). Bourdon ré mineur, très bas.",
    "P02": "Bourdon. Coup grave + cloche (ré) sur « disparu ».",
    "P03": "Bourdon seul : la question reste en l'air.",
    "P04": "Cloche (fa) à la coupe. Début du battement grave, 1 par seconde (l'enquête).",
    "P05": "Porte métallique de cellule à la coupe. Battement.",
    "P06": "Début du pizzicato (ré mineur). Cloche (la) + tintement de verre sur « empreinte ».",
    "P07": "Tiroir de fichier qui coulisse à la coupe. Battement, pizzicato.",
    "P08": "Fondu enchaîné (saut dans le temps). Battement, pizzicato.",
    "P09": "Cloche (ré) à la coupe. Le battement accélère (0,75 s) et le pizzicato se resserre : retournement.",
    "P10": "Cloche aiguë (ré) sur « Vincenzo ».",
    "P11": "Battement, pizzicato.",
    "P12": "Six pas sur la pierre (escalier). Fin du pizzicato et du battement.",
    "P13": "Cloche (fa dièse) : le bourdon se résout en ré majeur.",
    "P14": "Retour au bourdon d'ouverture, extinction douce sur 0,6 s pour la boucle.",
}
CAMERA_LIBELLE = "échelle / x / y en px"
TOL = 0.5 / 30            # un mot qui démarre moins d'une demi-image avant la coupe appartient au plan suivant
LONG_OK = {"P08": "fondu enchaîné : le plan s'ouvre lentement",
           "P09": "animé de l'intérieur (tracé de la route, anneau et libellé de Florence)",
           "P10": "le carton du nom apparaît à mi-plan"}


def fr(text: str) -> str:
    """Virgule décimale française hors des passages entre accents graves (code, fichiers, phonèmes)."""
    parts = text.split("`")
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r"(?<![v\w.])(\d+)\.(\d+)(?!\w|\.\d)", r"\1,\2", parts[i])
    return "`".join(parts)


def fmt(t: float) -> str:
    return f"{t:05.2f}"


def tc(t: float) -> str:
    f = round(t * FPS)
    return f"{f // (60 * FPS):02d}:{(f // FPS) % 60:02d}:{f % FPS:02d}"


def words_in(tl: dict, a: float, b: float) -> str:
    out = []
    for p in tl["phrases"]:
        for w in p["mots"]:
            if a - TOL <= w["debut"] < b - TOL:
                out.append(w["mot"])
    return " ".join(out)


def cam(c: dict) -> str:
    de, a = c["de"], c["a"]
    sens = "avance" if a[0] > de[0] else "recul" if a[0] < de[0] else "fixe"
    return f"{sens} lent : {de[0]:.2f}/{de[1]:+d}/{de[2]:+d} → {a[0]:.2f}/{a[1]:+d}/{a[2]:+d} (sine.inOut)"


def script_md(tl: dict, cfg: dict, subs: list) -> str:
    ch = json.loads((ROOT / "build/chronologie.json").read_text())
    phrases = {p["id"]: p for p in cfg["phrases"]}
    q_end = next(p["fin"] for p in tl["phrases"] if p["id"] == 3)
    rep = next(w["debut"] for w in tl["phrases"][13]["mots"] if w["mot"].startswith("Vincenzo"))
    nmots = sum(len(p["texte"].replace(" ?", "?").replace(" :", ":").split()) for p in cfg["phrases"])
    longest = max(len(p["texte"].replace(" ?", "?").replace(" :", ":").split()) for p in cfg["phrases"])
    L = [
        "# Étapes 2 — Script chronométré",
        "",
        "> Généré par `scripts/06_dossier.py` à partir de la voix réelle (`build/chronologie.json`).",
        "> Les temps sont mesurés sur le fichier audio : ce ne sont pas des estimations.",
        "",
        "## Repères",
        "",
        f"- Voix : `{cfg['voix']['moteur']}`, voix `{cfg['voix']['voix']}`, langue {cfg['voix']['langue']}, vitesse {cfg['voix']['vitesse']}.",
        f"- Durée de la vidéo : **{tl['duree']:.2f} s** (cible 45 s, plage 35–50 s). Fin de la voix : {ch['voix_fin']:.2f} s.",
        f"- **{nmots} mots** (cible 120–135), environ {ch['syllabes_estimees']} syllabes pour {ch['duree_parole']:.1f} s de parole, soit "
        f"**{ch['debit_syll_par_s']:.2f} syllabes/s** (cible environ 5).",
        f"- Phrase la plus longue : {longest} mots (maximum 15). Un fait par phrase.",
        "- Accroche : le fait réel (mur vide, date, lieu) est montré dès la première image, avec le carton « LOUVRE · 22 AOÛT 1911 » et le "
        "sous-titre « Le 22 août 1911, ». Pas de salutation.",
        f"- Question posée avant 8 s : fin de « Qui a pu la sortir du musée ? » à **{q_end:.2f} s**.",
        f"- Réponse : « Vincenzo » à **{rep:.2f} s**, soit {100 * rep / tl['duree']:.0f} % de la durée (maximum 80 %).",
        "- Chute : « Tout est parti de quatre crochets sur un mur vide. » reprend l'accroche, et le dernier plan revient au cadrage exact "
        "du premier (boucle).",
        "- Aucun appel à s'abonner.",
        "",
        "## Texte chronométré",
        "",
        "| # | Début → fin (s) | Durée | Rôle | Texte | Pause après | Consigne de lecture |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in tl["phrases"]:
        c = phrases[p["id"]]
        sec = f" *(secours {c['secours']})*" if c.get("secours") else ""
        L.append(f"| {p['id']} | {p['debut']:.2f} → {p['fin']:.2f} | {p['fin'] - p['debut']:.2f} s | {c['role']} | "
                 f"{c['texte']}{sec} | {c['pause']:.2f} s | {c['lecture']} |")
    L += ["", "## Prononciation", "", "| Mot | Consigne |", "|---|---|"]
    for k, v in cfg["prononciation"].items():
        L.append(f"| {k} | {v} |")
    L += ["",
          "La voix de synthèse n'a pas de contrôle de style : elle ne suit ces consignes que par la ponctuation, les pauses et la "
          "graphie phonétique du nom. Elles servent à un réenregistrement par une voix humaine.",
          "Phonèmes réellement produits pour le nom : `" + tl["phrases"][13]["phonemes"] + "`.",
          "",
          "## Coupes de secours (si la vidéo doit raccourcir)", ""]
    for k, v in cfg["coupes_de_secours"].items():
        L.append(f"- **{k}** (−{v['gain_s']} s) : {v['action']}")
    L += ["", "Les trois coupes combinées ramènent la vidéo à environ 44,3 s sans perdre ni la question, ni une révélation, ni la boucle.",
          "", "## Sous-titres (incrustés, une ligne)", "",
          f"{len(subs)} lignes, {max(s['chars'] for s in subs)} caractères au maximum (limite 27), "
          f"{max(s['largeur_px'] for s in subs):.0f} px de large au maximum (zone utile 880 px), "
          f"durée minimale {min(s['duree'] for s in subs):.2f} s. Fichier : `livrables/joconde-1911.srt`.", "",
          "| Début | Fin | Texte |", "|---|---|---|"]
    for s in subs:
        L.append(f"| {s['debut']:.2f} | {s['fin']:.2f} | {s['texte']} |")
    return "\n".join(L) + "\n"


def storyboard_md(tl: dict, subs: list) -> str:
    L = ["# Étape 3 — Storyboard", "",
         "> Généré par `scripts/06_dossier.py`. Temps mesurés sur la voix réelle, arrondis à l'image (30 i/s).",
         f"> Caméra : {CAMERA_LIBELLE} ; mouvements lents sur toute la durée du plan.",
         "> Textes : l'étiquette est en haut à gauche (x 60, y 200) ; légende à y 264 ; cartons centrés à y 340 ; "
         "sous-titres centrés à y 1300. Tout reste dans la zone x 60–940, y 200–1440.", "",
         "| Plan | Temps | Voix off exacte | Visuel (étiquette) | Caméra | Textes à l'écran | Transition d'entrée | Son |",
         "|---|---|---|---|---|---|---|---|"]
    for p in tl["plans"]:
        vo = words_in(tl, p["debut"], p["fin"]) or "—"
        textes = []
        if p.get("carton"):
            textes.append(f"carton « {p['carton']} »")
        if p.get("carton_2"):
            textes.append(f"carton « {p['carton_2']['texte']} » à {p['carton_2']['t']:.2f} s")
        if p.get("carton_fin"):
            textes.append(f"carton « {p['carton_fin']} » (fondu sur la dernière seconde)")
        if p.get("legende"):
            textes.append(f"légende « {p['legende']} »")
        ss = [s["texte"] for s in subs if p["debut"] - TOL <= s["debut"] < p["fin"] - TOL]
        textes.append("sous-titres : " + " / ".join(ss) if ss else "sous-titres : —")
        reveal = f" Révélation à {p['revele']['t']:.2f} s." if p.get("revele") else ""
        trans = "fondu enchaîné 0,5 s (saut dans le temps)" if p.get("transition") == "fondu" else (
            "première image" if p["id"] == "P01" else "coupe franche")
        L.append(f"| **{p['id']}** | {fmt(p['debut'])} → {fmt(p['fin'])} ({p['duree']:.2f} s) | {vo} | "
                 f"**{p['type']}** — {p['description']}{reveal} | {cam(p['camera'])} | {' ; '.join(textes)} | {trans} | {SON[p['id']]} |")
    durs = [p["duree"] for p in tl["plans"]]
    longs = [p for p in tl["plans"] if p["duree"] > 4 + 1e-3]
    L += ["", f"Durée des plans : de {min(durs):.2f} à {max(durs):.2f} s (cible 2 à 4 s). "
          + ("Au-dessus de 4 s : " + " ; ".join(f"{p['id']} ({p['duree']:.2f} s), {LONG_OK.get(p['id'], 'à justifier')}" for p in longs) + ". "
             if longs else "")
          + "Deux types de transition au total : coupe franche et un fondu."]
    return "\n".join(L) + "\n"


def montage_md(tl: dict) -> str:
    L = ["# Étape 5 — Montage", "",
         "> Généré par `scripts/06_dossier.py`. Composition : `index.html` (HyperFrames), générée par `scripts/05_composition.py`.", "",
         "## Ordre, durées et transitions", "",
         "| # | Plan | Entrée (TC) | Sortie (TC) | Images | Visuel | Transition | Ancrage sur la voix |",
         "|---|---|---|---|---|---|---|---|"]
    for i, p in enumerate(tl["plans"], 1):
        a = p["ancre"]
        anc = "début de la vidéo" if p["id"] == "P01" else (f"phrase {a['phrase']}, mot « {a['mot']} »" if "mot" in a else f"début de la phrase {a['phrase']}")
        trans = "fondu 0,5 s (le plan précédent est prolongé de 0,5 s dessous)" if p.get("transition") == "fondu" else "coupe"
        L.append(f"| {i} | {p['id']} | {tc(p['debut'])} | {tc(p['fin'])} | {round(p['duree'] * FPS)} | {p['visuel']} | {trans} | {anc} |")
    L += ["", f"Total : {round(tl['duree'] * FPS)} images, soit {tl['duree']:.3f} s. Le dernier plan (P14) finit au cadrage exact du premier "
          "(échelle 1,0, x 0, y 0) avec le même carton : la lecture en boucle de TikTok enchaîne sans saut.", "",
          "## Placements", "",
          "| Élément | Police | Taille | Position | Durée |", "|---|---|---|---|---|",
          "| Étiquette ARCHIVE / ILLUSTRATION / CARTE SCHÉMATIQUE | Oswald Bold, capitales espacées, pastille de couleur | 26 px | haut gauche, x 60, y 200, fond sombre 62 % | tout le plan |",
          "| Légende d'œuvre (ARCHIVE) | EB Garamond | 30 px | x 60, y 264, fond sombre | tout le plan |",
          "| Carton (6 mots maximum) | EB Garamond Bold, capitales | 50 px | centré, y 340, fond sombre 66 % | apparition 0,3 s après la coupe |",
          "| Sous-titres | Oswald Bold, contour sombre 9 px | 66 px | centrés sur y 1300, une ligne, ≤ 27 caractères | calés mot à mot sur la voix |",
          "| Carte : PARIS / FLORENCE | Oswald Bold | 46 px | positions projetées (Mercator) | « FLORENCE » sur le mot « Florence » |",
          "", "## Pistes audio", "",
          "| Piste | Fichier | Rôle |", "|---|---|---|",
          "| Voix | `livrables/pistes/voix.flac` | premier plan, filtre passe-haut 75 Hz, compression douce |",
          "| Musique | `livrables/pistes/musique.flac` | à 20 dB sous la voix pendant la parole (sidechain) ; remonte, jusqu'à +12 dB, dans les silences |",
          "| Bruitages | `livrables/pistes/bruitages.flac` | salle vide, porte, verre, tiroir, pas : discrets et justifiés par l'image |",
          "", "Les trois pistes ont subi le même gain et le même limiteur que le master : **voix + musique + bruitages = master**, à l'échantillon près.",
          "", "## Export", "",
          "| Paramètre | Valeur |", "|---|---|",
          "| Vidéo | H.264 High, 1080 × 1920, 30 i/s constants, yuv420p, environ 9,2 Mb/s (rendu HyperFrames, qualité « delivery ») |",
          "| Audio | AAC-LC 320 kb/s, 48 kHz, stéréo, encodé depuis le master PCM 24 bits |",
          "| Loudness | −14 LUFS intégrés, crête vraie ≤ −1,5 dBTP (mesuré : voir le contrôle qualité) |",
          "| Conteneur | MP4, `+faststart` |",
          "| Version sans son | même flux vidéo, copié sans réencodage, piste audio retirée |",
          "", "Commandes : voir `README.md` (chaîne complète, de `01_voix.py` à `make.sh`)."]
    return "\n".join(L) + "\n"


def main() -> None:
    tl = chrono.load()
    cfg = json.loads((ROOT / "scripts/script.json").read_text())
    subs = json.loads((ROOT / "build/sous-titres.json").read_text())
    DOCS.mkdir(exist_ok=True)
    (DOCS / "02_script.md").write_text(fr(script_md(tl, cfg, subs)))
    (DOCS / "03_storyboard.md").write_text(fr(storyboard_md(tl, subs)))
    (DOCS / "05_montage.md").write_text(fr(montage_md(tl)))
    print("dossier : docs/02_script.md, docs/03_storyboard.md, docs/05_montage.md")


if __name__ == "__main__":
    main()
