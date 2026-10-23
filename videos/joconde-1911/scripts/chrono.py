"""Calcul des temps absolus des plans à partir de la voix réelle (build/chronologie.json)."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FPS = 30


def frame_time(t: float) -> float:
    """Temps de l'image la plus proche, tronqué au dix-millième (jamais au-dessus de n/FPS :
    un arrondi vers le haut ferait démarrer le plan une image trop tard)."""
    return (round(t * FPS) * 10000 // FPS) / 10000


def _norm(w: str) -> str:
    return re.sub(r"[^\wÀ-ÿ'’]", "", w).lower()


def load() -> dict:
    chrono = json.loads((ROOT / "build/chronologie.json").read_text())
    plans = json.loads((ROOT / "scripts/plans.json").read_text())
    phrases = {p["id"]: p for p in chrono["phrases"]}

    def at(ancre: dict) -> float:
        p = phrases[ancre["phrase"]]
        if "mot" not in ancre:
            return p["debut"]
        target = _norm(ancre["mot"])
        for w in p["mots"]:
            if _norm(w["mot"]) == target:
                return w["debut"]
        raise KeyError(f"mot {ancre['mot']!r} absent de la phrase {ancre['phrase']}")

    duree = round(chrono["voix_fin"] + plans["fin_apres_voix_s"], 3)
    duree = frame_time(duree)
    out = []
    for i, pl in enumerate(plans["plans"]):
        start = 0.0 if i == 0 else at(pl["ancre"])
        out.append({**pl, "debut": frame_time(start)})
    for i, pl in enumerate(out):
        pl["fin"] = out[i + 1]["debut"] if i + 1 < len(out) else duree
        pl["duree"] = round(pl["fin"] - pl["debut"], 4)
        for key in ("revele", "carton_2", "cloche", "coup"):
            if key in pl:
                pl[key] = dict(pl[key])
                pl[key]["t"] = round(at(pl[key]), 3) if "phrase" in pl[key] else pl["debut"]
    return {"duree": duree, "plans": out, "phrases": chrono["phrases"], "voix_fin": chrono["voix_fin"],
            "musique": plans.get("musique", {}), "voix": {k: chrono.get(k) for k in ("moteur", "modele", "voix", "brouillon")}}


if __name__ == "__main__":
    tl = load()
    print(f"durée totale {tl['duree']} s")
    for p in tl["plans"]:
        print(f"{p['id']}  {p['debut']:6.2f} → {p['fin']:6.2f}  ({p['duree']:4.2f} s)  {p['type']:<17} {p['visuel']}")
