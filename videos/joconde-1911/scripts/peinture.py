"""Moteur de rendu « style peint » : repeint une composition de base en coups de pinceau orientés.

Principe (rendu pictural par couches, d'après Hertzmann 1998) : on part d'un fond flou, puis chaque
couche de pinceau, du plus gros au plus fin, ne repeint que là où la toile s'écarte encore de la
référence. Les touches suivent les isophotes (perpendiculaires au gradient de luminance), ce qui
donne des coups de brosse qui épousent les formes. Tout est déterministe (graine fixe).
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def _blur(img: Image.Image, r: float) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(max(0.1, r)))


def _flow_field(h: int, w: int, rng: np.random.Generator) -> np.ndarray:
    """Champ d'angles lisse pour les zones sans gradient (touches régulières, légèrement diagonales)."""
    small = rng.normal(0, 1, (max(2, h // 160), max(2, w // 160)))
    img = Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-9) * 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC)
    return (np.asarray(img, np.float32) / 255.0 - 0.5) * 0.55 + math.radians(-62)


def paint(ref: Image.Image, seed: int, brushes=(44, 24, 12, 6, 3), tol=(0, 16, 14, 13, 20),
          lengths=(9, 10, 9, 7, 4), jitter=0.035) -> Image.Image:
    rng = np.random.default_rng(seed)
    ref = ref.convert("RGB")
    w, h = ref.size
    angle_default = _flow_field(h, w, rng)
    canvas = _blur(ref, brushes[0] * 0.9)
    for bi, b in enumerate(brushes):
        blur_img = _blur(ref, b * 0.45)
        bnp = np.asarray(blur_img, np.float32)
        lum = (bnp @ np.array([0.299, 0.587, 0.114], np.float32))
        lum_s = np.asarray(_blur(Image.fromarray(np.clip(lum, 0, 255).astype(np.uint8)), b * 0.5), np.float32)
        gy, gx = np.gradient(lum_s)
        mag = np.hypot(gx, gy)
        cnp = np.asarray(canvas, np.float32)
        diff = np.linalg.norm(cnp - bnp, axis=2)
        step = max(2, int(b * 0.7))
        hh, ww = (h // step) * step, (w // step) * step
        blocks = diff[:hh, :ww].reshape(hh // step, step, ww // step, step).transpose(0, 2, 1, 3).reshape(hh // step, ww // step, -1)
        means = blocks.mean(axis=2)
        argm = blocks.argmax(axis=2)
        by, bx = np.nonzero(means >= (tol[bi] if bi else -1))
        oy, ox = np.divmod(argm[by, bx], step)
        ys, xs = by * step + oy, bx * step + ox
        order = rng.permutation(len(ys))
        draw = ImageDraw.Draw(canvas)
        width = max(1, int(round(b * 0.9)))
        rad = width / 2
        col_tol = 26 + b * 0.6
        noise = rng.normal(0, 1, (len(ys), 4)).astype(np.float32)
        for n, i in enumerate(order):
            x0, y0 = float(xs[i]), float(ys[i])
            base = bnp[int(y0), int(x0)]
            col = np.clip(base * (1 + noise[n, 0] * jitter) + noise[n, 1:4] * 3.0, 0, 255)
            pts = [(x0, y0)]
            x, y, pdx, pdy = x0, y0, 0.0, 0.0
            for k in range(lengths[bi]):
                iy, ix = int(y), int(x)
                if mag[iy, ix] > 0.9:
                    dx, dy = -gy[iy, ix] / mag[iy, ix], gx[iy, ix] / mag[iy, ix]
                else:
                    a = angle_default[iy, ix]
                    dx, dy = math.cos(a), math.sin(a)
                if dx * pdx + dy * pdy < 0:
                    dx, dy = -dx, -dy
                if k:
                    dx, dy = 0.55 * dx + 0.45 * pdx, 0.55 * dy + 0.45 * pdy
                    nrm = math.hypot(dx, dy) or 1.0
                    dx, dy = dx / nrm, dy / nrm
                x, y = x + dx * b * 0.75, y + dy * b * 0.75
                if not (0 <= x < w - 1 and 0 <= y < h - 1):
                    break
                if k >= 1 and np.abs(bnp[int(y), int(x)] - base).sum() > col_tol:
                    break
                pts.append((x, y))
                pdx, pdy = dx, dy
            fill = tuple(int(c) for c in col)
            if len(pts) > 1:
                draw.line(pts, fill=fill, width=width, joint="curve")
            for px, py in (pts[0], pts[-1]):
                draw.ellipse([px - rad, py - rad, px + rad, py + rad], fill=fill)
    return canvas


def canvas_texture(img: Image.Image, seed: int, strength: float = 0.07) -> Image.Image:
    """Texture de toile peinte (trame + relief), pas de grain photographique."""
    rng = np.random.default_rng(seed + 991)
    w, h = img.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = 0.5 + 0.25 * np.sin(xx * 2 * math.pi / 3.1) + 0.25 * np.sin(yy * 2 * math.pi / 3.3)
    fiber = rng.normal(0, 1, (h, w)).astype(np.float32)
    fiber = np.asarray(_blur(Image.fromarray(((fiber + 3) / 6 * 255).clip(0, 255).astype(np.uint8)), 0.8), np.float32) / 255
    relief = np.asarray(img.convert("L").filter(ImageFilter.EMBOSS), np.float32) / 255 - 0.5
    t = (weave * 0.6 + fiber * 0.4)
    arr = np.asarray(img, np.float32)
    arr *= (1 - strength + strength * t)[..., None]
    arr += relief[..., None] * 6
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
