#!/usr/bin/env python3
"""Plans « œuvre » à partir de la reproduction authentique (aucune génération, aucune retouche de l'œuvre).

- joconde.png        : reproduction entière posée sur fond sombre (cadre 1242×2208).
- joconde_detail.png : recadrage du visage (DÉTAIL), agrandi en Lanczos (interpolation, pas de génération).
Seules opérations sur l'œuvre : redimensionnement et recadrage.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets/oeuvre/joconde-reproduction.jpg"
OUT = ROOT / "assets/illustrations"
W, H = 1242, 2208


def background() -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.hypot((xx - W / 2) / W, (yy - H * 0.44) / H)
    base = np.array([24, 20, 16], np.float32) * (1 - np.clip(d * 1.4, 0, 1))[..., None] + np.array([8, 7, 6], np.float32)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def main() -> None:
    art = Image.open(SRC).convert("RGB")
    bg = background()
    tw = 1000
    full = art.resize((tw, round(art.height * tw / art.width)), Image.LANCZOS)
    x, y = (W - full.width) // 2, 300
    shadow = Image.new("L", (W, H), 0)
    shadow.paste(255, (x + 16, y + 24, x + full.width + 16, y + full.height + 24))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))
    arr = np.asarray(bg, np.float32) * (1 - 0.7 * np.asarray(shadow, np.float32)[..., None] / 255)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    img.paste(full, (x, y))
    img.save(OUT / "joconde.png", optimize=True)

    cw = 640
    ch = round(cw * H / W)
    cx, cy = 482, 470          # centre approximatif du visage dans la reproduction (960×1452)
    box = (cx - cw // 2, max(0, cy - ch // 2), cx + cw // 2, max(0, cy - ch // 2) + ch)
    detail = art.crop(box).resize((W, H), Image.LANCZOS)
    detail.save(OUT / "joconde_detail.png", optimize=True)
    print("œuvre : plan entier", full.size, "à", (x, y), "· détail", box, "→", detail.size)


if __name__ == "__main__":
    main()
