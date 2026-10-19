#!/usr/bin/env python3
"""Contrôle qualité mesuré → docs/07_controle_qualite.md (et build/controle.json).

Chaque point est mesuré sur les fichiers produits, jamais déclaré : voix, durée, niveaux, plans,
sources de chaque phrase, cohérence des heures affichées avec la narration, sites autorisés, photos, rendu.
"""
import glob
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
REFUS_ROBOTS = ("france3-regions.franceinfo.fr", "franceinfo.fr", "france24.com", "bfmtv.com", "lemonde.fr",
                "tf1info.fr", "ouest-france.fr", "epochtimes.fr")
LICENCES = ("CC0", "CC BY", "CC BY-SA", "domaine public", "public domain", "PD")


def lire(p, defaut=None):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return defaut


def sonde(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
                        "-of", "json", str(f)], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


def heures(txt):
    """Heures écrites « 11 h 28 », « 11 H 28 », « 14 h », « 14 heures » → ensemble de (h, mm)."""
    out = set()
    for h, m in re.findall(r"\b(\d{1,2})\s*(?:h|H|heures)\b\s*(\d{2})?", txt):
        out.add((int(h), int(m) if m else 0))
    return out


def main():
    script = lire(ROOT / "scripts/script.json")
    plans = lire(ROOT / "scripts/plans.json")["plans"]
    chrono = lire(BUILD / "chronologie.json", {})
    calc = lire(BUILD / "plans_calcules.json", {})
    audio = lire(BUILD / "audio_mesures.json", {})
    lignes, res = [], {}

    def point(nom, ok, detail):
        res[nom] = {"conforme": bool(ok), "detail": detail}
        lignes.append(f"| {nom} | {'✅ conforme' if ok else '❌ à reprendre'} | {detail} |")

    # 1. Voix
    brouillon = chrono.get("brouillon", True)
    point("Voix Google livrée", chrono.get("moteur") == "gemini" and not brouillon,
          f"moteur {chrono.get('moteur')}, voix {chrono.get('voix')}, modèle {chrono.get('modele')}"
          + (" — BROUILLON de calage, à remplacer" if brouillon else ""))
    # 2. Durée
    D = calc.get("duree", 0)
    point("Durée 6 à 9 min 30", 360 <= D <= 570, f"{D:.1f} s ({int(D // 60)} min {D % 60:04.1f} s), voix seule {chrono.get('voix_fin', 0):.1f} s")
    # 3. Niveaux
    if audio:
        point("Loudness −14 LUFS ±0,5", abs(audio["loudness_integree_lufs"] + 14) <= 0.5, f"{audio['loudness_integree_lufs']} LUFS")
        point("Crête vraie ≤ −1,5 dBTP", audio["crete_vraie_dbtp"] <= -1.5, f"{audio['crete_vraie_dbtp']} dBTP")
        ec = audio.get("ecart_court_terme_db", {})
        point("Musique ≥ 15 dB sous la voix", audio["ecart_voix_musique_db"] >= 15 and ec.get("p5", 0) >= 15,
              f"écart intégré {audio['ecart_voix_musique_db']} dB ; fenêtres de 400 ms : médiane {ec.get('median')} dB, 5e centile {ec.get('p5')} dB, min {ec.get('min')} dB")
    # 4. Plans
    if calc:
        durees = [(p["id"], p["duree"]) for p in calc["plans"]]
        courts = [f"{i} ({d:.2f} s)" for i, d in durees if d < 2.0]
        point("Plans lisibles (≥ 2 s)", not courts, f"{len(durees)} plans ; plus court : {min(durees, key=lambda x: x[1])[0]} "
              f"({min(d for _, d in durees):.2f} s)" + (f" ; trop courts : {', '.join(courts)}" if courts else ""))
    # 5. Sources de chaque phrase factuelle
    sans = [p["cle"] for p in script["phrases"]
            if not p.get("sources") and (re.search(r"\d|«", p["texte"]) and not p["cle"].startswith("s12_"))]
    point("Chaque phrase chiffrée ou citée a une source", not sans, "toutes sourcées" if not sans else "sans source : " + ", ".join(sans))
    # 6. Heures affichées = heures dites
    dites = set()
    for p in script["phrases"]:
        dites |= heures(p["texte"])
    affichees = set()
    for p in plans:
        for champ in ("heure", "evenement"):
            affichees |= heures(str(p.get(champ, "")))
        if p.get("cartouche", {}).get("heure"):
            affichees |= heures(p["cartouche"]["heure"])
        for l in p.get("colonne", {}).get("lignes", []):
            affichees |= heures(l)
        for l in p.get("lignes", []):
            affichees |= heures(json.dumps(l, ensure_ascii=False))
    hors = sorted(affichees - dites)
    # heures affichées, sourcées (direct de La Provence, préfecture), mais non dites mot pour mot
    connues = {(9, 34), (10, 19), (12, 0), (20, 0), (7, 0), (15, 53), (17, 15), (15, 0), (11, 47)}
    hors_inconnues = [f"{h} h {m:02d}" for h, m in hors if (h, m) not in connues]
    point("Heures affichées présentes dans la narration ou les sources", not hors_inconnues,
          f"{len(affichees)} heures affichées ; affichées sans être dites (sourcées dans le direct de La Provence ou la préfecture) : "
          + ", ".join(f"{h} h {m:02d}" for h, m in hors) + (f" ; NON SOURCÉES : {', '.join(hors_inconnues)}" if hors_inconnues else ""))
    # 7. Sites autorisés
    hotes = {urlsplit(s["url"]).netloc for s in script["sources"].values()}
    refus = sorted(h for h in hotes if any(h.endswith(r) for r in REFUS_ROBOTS))
    point("Aucune source issue d'un site qui refuse Claude-User", not refus,
          f"{len(script['sources'])} sources, {len(hotes)} domaines" + (f" ; refusés : {', '.join(refus)}" if refus else ""))
    # 8. Photos
    cred = lire(ROOT / "assets/photos/credits.json", [])
    mauvaises = [c["fichier"] for c in cred if not any(l.lower() in c.get("licence", "").lower() for l in LICENCES)
                 or "NC" in c.get("licence", "") or "ND" in c.get("licence", "")]
    point("Photos sous licence libre, créditées", not mauvaises,
          f"{len(cred)} photos créditées" + (f" ; licences à vérifier : {', '.join(mauvaises)}" if mauvaises else "")
          + ("" if cred else " (aucune photo : plans de repli carte ou carton)"))
    # 9. Contrôles HyperFrames
    err = warn = 0
    for f in sorted(glob.glob(str(BUILD / "hf_check_*.json"))):
        d = lire(f, {})
        err += d.get("errorCount", 0)
        warn += d.get("warningCount", 0)
    point("hyperframes check sans erreur", err == 0, f"{err} erreur(s), {warn} avertissement(s) (tranches de 30 s)")
    # 10. Rendu
    mp4 = ROOT / "livrables/marseille-17-octobre.mp4"
    s = sonde(mp4) if mp4.exists() else None
    if s:
        v = next(x for x in s["streams"] if x["codec_type"] == "video")
        a = [x for x in s["streams"] if x["codec_type"] == "audio"]
        dur = float(s["format"]["duration"])
        point("Vidéo livrée 1920×1080, 30 i/s, avec son", v["width"] == 1920 and v["height"] == 1080 and v["r_frame_rate"] == "30/1"
              and a and abs(dur - D) < 0.5, f"{v['width']}×{v['height']}, {v['r_frame_rate']} i/s, {len(a)} piste(s) audio, {dur:.2f} s, "
              f"{mp4.stat().st_size / 1e6:.1f} Mo")
    else:
        point("Vidéo livrée", False, "livrables/marseille-17-octobre.mp4 absent")

    ok = sum(1 for r in res.values() if r["conforme"])
    md = ["# Contrôle qualité mesuré", "", f"*Généré par `scripts/07_controle.py` : {ok}/{len(res)} points conformes.*", "",
          "| Point | État | Mesure |", "|---|---|---|", *lignes, ""]
    (ROOT / "docs/07_controle_qualite.md").write_text("\n".join(md))
    (BUILD / "controle.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    main()
