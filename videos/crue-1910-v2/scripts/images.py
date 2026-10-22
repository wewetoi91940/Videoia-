#!/usr/bin/env python3
"""Étalonnage par émotion, précalculé dans les fichiers (assets/photos → build/img).

Pourquoi précalculé : l'étalonnage du moteur (`data-color-grading`) passe par un shader ; un essai de 2 s a mis
3 min 23 s à se rendre, contre 3 min 33 s pour les 44 s de la V1. Ici, chaque archive reçoit une teinte fixe selon
l'émotion du plan (froid = angoisse, nuit = sous terre, doux = empathie, chaud = entraide, papier = document,
naturel = aujourd'hui). Rien n'est ajouté à l'image : on ne change que la couleur et la luminosité.

Sorties : build/img/<nom>.jpg (la carte photo) et build/img/<nom>-fond.jpg (fond 9:16 flou et assombri, 540 × 960,
affiché en plein écran derrière la carte pour l'effet de profondeur).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "assets/photos", ROOT / "build/img"

# teinte : (ombres, hautes lumières, part de la teinte, gamma, contraste)
TEINTES = {
    "froid": ((8, 20, 30), (214, 233, 238), 0.85, 1.0, 1.10),
    "nuit": ((3, 10, 16), (168, 204, 212), 0.90, 1.15, 1.12),
    "doux": ((24, 19, 16), (238, 228, 214), 0.80, 1.0, 1.04),
    "chaud": ((40, 18, 6), (255, 236, 200), 0.30, 0.97, 1.05),
    "papier": ((34, 24, 14), (246, 234, 208), 0.75, 1.0, 1.08),
    "naturel": ((0, 0, 0), (255, 255, 255), 0.0, 1.0, 1.04),
}
IMAGES = {
    "saint-lazare": "froid", "saints-peres": "froid", "panorama": "froid", "passy": "froid", "rue-leblanc": "froid",
    "saint-michel": "nuit", "daumesnil": "froid", "gymnase": "doux", "petit-journal": "chaud", "plan-1910": "papier",
    "repere-celestins": "naturel",
}


def teinter(im: Image.Image, teinte: str) -> Image.Image:
    sombre, clair, part, gamma, contraste = TEINTES[teinte]
    rgb = np.asarray(im.convert("RGB"), dtype=np.float64) / 255
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    lum = np.clip((lum - 0.5) * contraste + 0.5, 0, 1) ** gamma
    duo = np.array(sombre) / 255 + lum[..., None] * (np.array(clair) - np.array(sombre)) / 255
    base = np.clip((rgb - 0.5) * contraste + 0.5, 0, 1) ** gamma
    out = base * (1 - part) + duo * part
    if teinte == "chaud":   # illustration en couleurs : on garde ses couleurs, réchauffées
        out = np.clip(out * np.array([1.05, 1.0, 0.88]), 0, 1)
    return Image.fromarray((out * 255).round().astype(np.uint8))


def fond(im: Image.Image) -> Image.Image:
    """Recadrage 9:16 au centre, flou fort, assombri, vignette : un décor, jamais lu."""
    w, h = im.size
    cw = min(w, h * 9 / 16)
    ch = cw * 16 / 9
    x0, y0 = (w - cw) / 2, max(0, (h - ch) / 2)
    f = im.crop((round(x0), round(y0), round(x0 + cw), round(y0 + min(ch, h)))).resize((540, 960), Image.LANCZOS)
    f = f.filter(ImageFilter.GaussianBlur(26))
    a = np.asarray(f, dtype=np.float64) * 0.42
    yy, xx = np.mgrid[0:960, 0:540]
    vig = 1 - 0.45 * (((xx - 270) / 270) ** 2 + ((yy - 480) / 480) ** 2) / 2
    return Image.fromarray(np.clip(a * vig[..., None], 0, 255).astype(np.uint8))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for nom, teinte in IMAGES.items():
        im = teinter(Image.open(SRC / f"{nom}.jpg"), teinte)
        im.save(OUT / f"{nom}.jpg", quality=90)
        fond(im).save(OUT / f"{nom}-fond.jpg", quality=85)
    print(f"{len(IMAGES)} images étalonnées → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
