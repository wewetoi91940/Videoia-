"""Habillage fixe en images (au lieu de dégradés CSS, coûteux à la capture) : grain, fond des cartons, vignette, voile.

Graines fixes ; un léger tramage évite les bandes de compression dans les dégradés.
"""
from pathlib import Path

import numpy as np
from PIL import Image

A = Path(__file__).resolve().parent.parent / "assets"
W, H = 1920, 1080
rng = np.random.default_rng(17)

# grain de film (répété)
g = np.clip(128 + rng.normal(0, 46, (512, 512)), 0, 255).astype(np.uint8)
Image.fromarray(g, "L").save(A / "grain.png", optimize=True)

y, x = np.mgrid[0:H, 0:W].astype(np.float32)
trame = rng.uniform(-0.5, 0.5, (H, W)).astype(np.float32)

# fond des cartons : #11161c, halo ambré en bas à gauche, grille fine tous les 120 px
bg = np.array([17, 22, 28], np.float32)
acc = np.array([233, 162, 59], np.float32)
d = np.sqrt(((x - 0.12 * W) / (0.70 * W)) ** 2 + ((y - 0.88 * H) / (0.60 * H)) ** 2)
halo = np.clip(1 - d / 0.7, 0, 1) ** 1.6 * 0.14
img = bg + (acc - bg) * halo[..., None]
grille = ((x % 120) < 1) | ((y % 120) < 1)
img = np.where(grille[..., None], img + (np.array([236, 230, 218], np.float32) - img) * 0.045, img)
Image.fromarray(np.clip(img + trame[..., None], 0, 255).astype(np.uint8), "RGB").save(A / "fond.png", optimize=True)


def rgba(alpha, couleur=(12, 16, 21)):
    a = np.clip(alpha * 255 + trame, 0, 255).astype(np.uint8)
    rgb = np.broadcast_to(np.array(couleur, np.uint8), (H, W, 3))
    return Image.fromarray(np.dstack([rgb, a]), "RGBA")


# vignette des cartes : bords assombris
d = np.sqrt(((x - W / 2) / (0.75 * W)) ** 2 + ((y - 0.45 * H) / (0.70 * H)) ** 2)
rgba(np.clip((d - 0.55) / 0.45, 0, 1) * 0.78).save(A / "vignette.png", optimize=True)

# voile des photos : bas et haut assombris pour la lisibilité des cartouches
bas = np.sqrt(((x - W / 2) / (1.2 * W)) ** 2 + ((y - 1.10 * H) / (0.80 * H)) ** 2)
haut = np.sqrt(((x - W / 2) / (1.2 * W)) ** 2 + ((y + 0.20 * H) / (0.60 * H)) ** 2)
a_bas = np.interp(bas, [0, 0.45, 0.70], [0.92, 0.35, 0])
a_haut = np.interp(haut, [0, 0.60], [0.70, 0])
rgba(np.maximum(a_bas, a_haut)).save(A / "voile.png", optimize=True)
