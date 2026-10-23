#!/usr/bin/env python3
"""Illustrations historiques (style peint) du mini-documentaire « Le vol de la Joconde (1911) ».

Chaque scène est une reconstitution : ILLUSTRATION, jamais une archive. Règles appliquées :
- aucun visage : silhouettes de dos uniquement ;
- aucune œuvre d'art générée : la Joconde est la reproduction authentique, collée telle quelle ;
- pas de noir et blanc ni de grain d'archive : peinture en couleur sur texture de toile ;
- pas de détail non vérifié (ex. : pas de malle dans la chambre, la cachette exacte étant incertaine).

Usage : python 02_illustrations.py [nom_de_scene ...]   (sans argument : toutes les scènes)
Sortie : assets/illustrations/<scene>.png (1242×2208, soit 1,15 × le cadre 1080×1920)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from peinture import canvas_texture, paint  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/illustrations"
REPRO = ROOT / "assets/oeuvre/joconde-reproduction.jpg"
W, H = 1242, 2208


def rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def vgrad(top: str, bottom: str, w=W, h=H, curve=1.0) -> np.ndarray:
    t = (np.linspace(0, 1, h, dtype=np.float32) ** curve)[:, None, None]
    a, b = np.array(rgb(top), np.float32), np.array(rgb(bottom), np.float32)
    return np.broadcast_to(a * (1 - t) + b * t, (h, w, 3)).copy()


def light(arr: np.ndarray, cx, cy, r, color: str, amount=0.6, power=1.6) -> np.ndarray:
    yy, xx = np.mgrid[0:arr.shape[0], 0:arr.shape[1]].astype(np.float32)
    d = np.clip(1 - np.hypot(xx - cx, yy - cy) / r, 0, 1) ** power
    c = np.array(rgb(color), np.float32)
    return arr * (1 - d[..., None] * amount) + c * d[..., None] * amount


def darken_edges(arr: np.ndarray, amount=0.45) -> np.ndarray:
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.hypot((xx - w / 2) / (w * 0.62), (yy - h / 2) / (h * 0.58))
    return arr * (1 - amount * np.clip(d - 0.55, 0, 1)[..., None] ** 1.2)


def texture_noise(seed: int, scale: float, amp: float, w=W, h=H) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (max(2, int(h / scale)), max(2, int(w / scale))))
    img = Image.fromarray(((n - n.min()) / (np.ptp(n) + 1e-9) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return (np.asarray(img, np.float32) / 255 - 0.5) * amp


def to_img(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def soft_shadow(img: Image.Image, shape_fn, offset=(12, 16), blur=10, opacity=0.55) -> Image.Image:
    m = Image.new("L", img.size, 0)
    shape_fn(ImageDraw.Draw(m), offset)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(m, np.float32)[..., None] / 255 * opacity
    arr = np.asarray(img, np.float32) * (1 - a)
    return to_img(arr)


def gilt_frame(img: Image.Image, box, border=56, inner="#2a2016", seed=0) -> Image.Image:
    """Cadre doré générique, dorure vieillie (toile sombre non identifiable : aucune œuvre réelle n'est imitée)."""
    x0, y0, x1, y1 = box
    img = soft_shadow(img, lambda d, o: d.rectangle([x0 + o[0], y0 + o[1], x1 + o[0], y1 + o[1]], fill=255), (20, 28), 22, 0.7)
    d = ImageDraw.Draw(img)
    prof = [  # profil de moulure : (fraction de la bordure, teinte claire, teinte sombre)
        (0.00, "#6e5222", "#3a2a10"), (0.12, "#c9a24e", "#6a4e1e"), (0.30, "#8a6a2c", "#4a3614"),
        (0.45, "#e0c26a", "#7a5a24"), (0.62, "#9a7834", "#4e3a16"), (0.80, "#5a4218", "#2e2008"),
        (0.92, "#b8944a", "#5e4618"),
    ]
    for i in range(border):
        f = i / border
        k = max(j for j in range(len(prof)) if prof[j][0] <= f)
        hi, lo = rgb(prof[k][1]), rgb(prof[k][2])
        d.line([(x0 + i, y1 - i), (x0 + i, y0 + i), (x1 - i, y0 + i)], fill=hi, width=1)
        d.line([(x1 - i, y0 + i), (x1 - i, y1 - i), (x0 + i, y1 - i)], fill=lo, width=1)
    ix0, iy0, ix1, iy1 = x0 + border, y0 + border, x1 - border, y1 - border
    arr = np.asarray(img, np.float32).copy()
    sub = vgrad("#33271a", inner, ix1 - ix0, iy1 - iy0) + texture_noise(seed, 30, 22, ix1 - ix0, iy1 - iy0)[..., None]
    sub = light(sub, (ix1 - ix0) * 0.35, (iy1 - iy0) * 0.3, (iy1 - iy0) * 0.9, "#5a4630", 0.3)
    cy0, cx0, cy1, cx1 = max(0, iy0), max(0, ix0), min(H, iy1), min(W, ix1)
    if cy1 > cy0 and cx1 > cx0:
        arr[cy0:cy1, cx0:cx1] = sub[cy0 - iy0:cy1 - iy0, cx0 - ix0:cx1 - ix0]
    return to_img(arr)


SIL = {  # contours de silhouettes vues de dos, moitié droite (x, y) ; hauteur 1 = du sommet du chapeau au sol
    "manteau": [(0, 0.035), (0.05, 0.045), (0.066, 0.085), (0.06, 0.125), (0.048, 0.14), (0.09, 0.158), (0.15, 0.178),
                (0.172, 0.21), (0.182, 0.30), (0.19, 0.43), (0.186, 0.52), (0.166, 0.535), (0.16, 0.50), (0.17, 0.60),
                (0.178, 0.69), (0.10, 0.70), (0.078, 0.705), (0.074, 0.84), (0.07, 0.965), (0.098, 0.985), (0.096, 1.0),
                (0.018, 1.0), (0.02, 0.86), (0.016, 0.74), (0, 0.725)],
    "pelerine": [(0, 0.04), (0.05, 0.05), (0.064, 0.09), (0.058, 0.128), (0.048, 0.142), (0.10, 0.16), (0.16, 0.19),
                 (0.20, 0.26), (0.232, 0.42), (0.245, 0.56), (0.20, 0.575), (0.12, 0.58), (0.082, 0.585), (0.076, 0.80),
                 (0.07, 0.965), (0.098, 0.985), (0.096, 1.0), (0.018, 1.0), (0.02, 0.84), (0.016, 0.62), (0, 0.6)],
    "blouse": [(0, 0.04), (0.05, 0.05), (0.064, 0.09), (0.058, 0.128), (0.048, 0.142), (0.09, 0.16), (0.15, 0.18),
               (0.172, 0.215), (0.185, 0.32), (0.192, 0.46), (0.18, 0.53), (0.162, 0.535), (0.165, 0.50), (0.18, 0.60),
               (0.188, 0.64), (0.09, 0.645), (0.076, 0.65), (0.072, 0.84), (0.068, 0.965), (0.094, 0.985), (0.092, 1.0),
               (0.018, 1.0), (0.02, 0.84), (0.016, 0.68), (0, 0.665)],
    "robe": [(0, 0.05), (0.05, 0.056), (0.062, 0.09), (0.056, 0.125), (0.046, 0.14), (0.085, 0.156), (0.135, 0.176),
             (0.152, 0.21), (0.158, 0.30), (0.146, 0.36), (0.118, 0.40), (0.132, 0.45), (0.19, 0.68), (0.25, 0.97),
             (0.25, 1.0), (0, 1.0)],
}


def _smooth(points, n=8):
    """Courbe de Catmull-Rom passant par les points (contour lissé)."""
    out = []
    P = [points[0]] + points + [points[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.array, (P[i - 1], P[i], P[i + 1], P[i + 2]))
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)))
    out.append(points[-1])
    return out


def silhouette(img: Image.Image, cx, ground, height, kind="manteau", hat="bowler", color="#1c1816",
               rim=("#f3d9a0", 0.0, -1.0), rim_amount=0.55, haze=None) -> Image.Image:
    """Silhouette vue de dos (aucun visage), contours lissés, lumière de contour venant de la source."""
    ss = 4
    half = SIL[kind]
    right = _smooth([(x, y) for x, y in half])
    left = [(-x, y) for x, y in reversed(right)]
    pts = right + left
    m = Image.new("L", (W * ss // 4, H * ss // 4), 0)  # même taille que l'image (ss/4 = 1)
    big = Image.new("L", (W * ss, H * ss), 0)
    bd = ImageDraw.Draw(big)
    scale = height * ss
    bd.polygon([(cx * ss + x * scale, (ground - height) * ss + y * scale) for x, y in pts], fill=255)
    hx, hy = cx * ss, (ground - height) * ss
    if hat == "bowler":
        bd.ellipse([hx - 0.105 * scale, hy + 0.03 * scale, hx + 0.105 * scale, hy + 0.058 * scale], fill=255)
        bd.chord([hx - 0.068 * scale, hy - 0.012 * scale, hx + 0.068 * scale, hy + 0.10 * scale], 180, 360, fill=255)
    elif hat == "kepi":
        bd.polygon([(hx - 0.062 * scale, hy + 0.05 * scale), (hx + 0.062 * scale, hy + 0.05 * scale),
                    (hx + 0.056 * scale, hy - 0.025 * scale), (hx - 0.056 * scale, hy - 0.025 * scale)], fill=255)
    elif hat == "capeline":
        bd.ellipse([hx - 0.15 * scale, hy + 0.028 * scale, hx + 0.15 * scale, hy + 0.062 * scale], fill=255)
        bd.chord([hx - 0.062 * scale, hy - 0.02 * scale, hx + 0.062 * scale, hy + 0.09 * scale], 180, 360, fill=255)
    elif hat == "canotier":
        bd.rectangle([hx - 0.112 * scale, hy + 0.034 * scale, hx + 0.112 * scale, hy + 0.05 * scale], fill=255)
        bd.rectangle([hx - 0.06 * scale, hy - 0.004 * scale, hx + 0.06 * scale, hy + 0.04 * scale], fill=255)
    elif hat == "cap":
        bd.chord([hx - 0.07 * scale, hy + 0.0 * scale, hx + 0.07 * scale, hy + 0.09 * scale], 180, 360, fill=255)
        bd.ellipse([hx - 0.07 * scale, hy + 0.035 * scale, hx + 0.075 * scale, hy + 0.055 * scale], fill=255)
    m = big.resize((W, H), Image.LANCZOS)
    a = np.asarray(m, np.float32)[..., None] / 255
    arr = np.asarray(img, np.float32)
    body = np.broadcast_to(np.array(rgb(color), np.float32), arr.shape).copy()
    if kind == "blouse":
        yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
        smock = ((yy > ground - height * 0.86) & (yy < ground - height * 0.355))[..., None]
        body = np.where(smock, np.array(rgb("#d6cfc0"), np.float32), body)
    if haze is not None:
        hc, ha = haze
        body = body * (1 - ha) + np.array(rgb(hc), np.float32) * ha
    rc, dx, dy = rim
    shift = np.roll(np.roll(a, int(-dx * 5), axis=1), int(-dy * 5), axis=0)  # voisin côté lumière
    edge = np.clip(a - shift, 0, 1)
    edge = np.asarray(Image.fromarray((edge[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5)), np.float32)[..., None] / 255
    body = body + np.array(rgb(rc), np.float32) * edge * rim_amount * 1.6
    arr = arr * (1 - a) + body * a
    return to_img(arr)


def finish(base: Image.Image, seed: int, protect: tuple | None = None, post=None, brushes=None) -> Image.Image:
    painted = paint(base, seed, **({"brushes": brushes} if brushes else {}))
    painted = canvas_texture(painted, seed)
    if protect:
        box, art = protect
        painted.paste(art, box[:2])
    if post:
        painted = post(painted)
    return painted


# ------------------------------------------------------------------ scènes

def _mur(seed=11, hooks_on=True) -> Image.Image:
    """Mur du Salon Carré (non peint) : base commune du mur vide, de Béroud, de la foule et du retour."""
    arr = vgrad("#6e3326", "#2a1310", curve=0.9)
    arr += texture_noise(seed, 9, 10)[..., None]
    xx = np.arange(W, dtype=np.float32)
    arr += (np.sin(xx / 6.0) * 3.0)[None, :, None]  # trame verticale du tissu mural
    arr = light(arr, W / 2, -500, 2100, "#f1d9b0", 0.42, 1.3)  # lumière zénithale (verrière)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 140], fill=rgb("#8a6a44"))
    d.rectangle([0, 140, W, 158], fill=rgb("#3a2216"))
    d.rectangle([0, 158, W, 166], fill=rgb("#b08a58"))
    for box in [(-260, 560, 300, 1430), (950, 600, 1510, 1510), (40, 210, 320, 470), (960, 200, 1250, 450),
                (60, 1600, 400, 1930), (880, 1640, 1300, 1990)]:
        img = gilt_frame(img, box, border=52 if box[2] - box[0] > 400 else 34, seed=seed + abs(box[0]) + box[1])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 2040, W, H], fill=rgb("#24160e"))
    d.rectangle([0, 2030, W, 2042], fill=rgb("#6a4a2c"))
    arr = light(np.asarray(img, np.float32), 621, 1030, 700, "#d89a7a", 0.22, 1.2)
    img = to_img(darken_edges(arr, 0.55))
    if not hooks_on:
        return img
    hooks = [(505, 770), (737, 770), (505, 1290), (737, 1290)]

    def hook_shapes(dr, o):
        for x, y in hooks:
            dr.rounded_rectangle([x - 9 + o[0], y - 18 + o[1], x + 9 + o[0], y + 22 + o[1]], 6, fill=255)
            dr.polygon([(x - 6 + o[0], y + 16 + o[1]), (x + 6 + o[0], y + 16 + o[1]), (x + 14 + o[0], y + 36 + o[1]), (x + 2 + o[0], y + 34 + o[1])], fill=255)

    img = soft_shadow(img, hook_shapes, (10, 14), 5, 0.65)
    d = ImageDraw.Draw(img)
    for x, y in hooks:
        d.rounded_rectangle([x - 9, y - 18, x + 9, y + 22], 6, fill=rgb("#2a2622"))
        d.polygon([(x - 6, y + 16), (x + 6, y + 16), (x + 14, y + 36), (x + 2, y + 34)], fill=rgb("#2a2622"))
        d.line([(x - 5, y - 14), (x - 5, y + 16)], fill=rgb("#8a8274"), width=3)
    return img


def scene_mur_vide(seed=11) -> Image.Image:
    return finish(_mur(seed), seed)


def scene_crochets(seed=12) -> Image.Image:
    arr = vgrad("#7a3a2a", "#3a1a14")
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    arr += (np.sin(xx / 4.0) * 4 + np.sin(yy / 5.0) * 3)[..., None]
    arr += texture_noise(seed, 6, 14)[..., None]
    arr = light(arr, 120, 300, 1700, "#f3d6a8", 0.5, 1.4)
    img = to_img(darken_edges(arr, 0.5))
    hooks = [(410, 980), (850, 1010)]

    def shapes(dr, o, s=1.0):
        for x, y in hooks:
            dr.rounded_rectangle([x - 26 + o[0], y - 70 + o[1], x + 26 + o[0], y + 60 + o[1]], 18, fill=255)
            dr.polygon([(x - 20 + o[0], y + 44 + o[1]), (x + 18 + o[0], y + 44 + o[1]), (x + 52 + o[0], y + 120 + o[1]), (x + 14 + o[0], y + 116 + o[1])], fill=255)

    img = soft_shadow(img, shapes, (60, 80), 22, 0.7)
    d = ImageDraw.Draw(img)
    for x, y in hooks:
        d.rounded_rectangle([x - 26, y - 70, x + 26, y + 60], 18, fill=rgb("#26221e"))
        d.polygon([(x - 20, y + 44), (x + 18, y + 44), (x + 52, y + 120), (x + 14, y + 116)], fill=rgb("#26221e"))
        d.line([(x - 15, y - 58), (x - 15, y + 46)], fill=rgb("#a49a88"), width=7)
        d.ellipse([x - 12, y - 14, x + 12, y + 10], fill=rgb("#14110e"))
    return finish(img, seed)


def scene_soupcons(seed=13) -> Image.Image:
    arr = vgrad("#c8c2b4", "#5a544a", curve=0.8)
    vx, vy = W / 2, 980
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    for side in (-1, 1):
        xe = 0 if side < 0 else W
        xi = vx + side * 210
        d.polygon([(xe, -40), (xi, 640), (xi, 1240), (xe, 1950)], fill=rgb("#6e655a" if side < 0 else "#625a50"))
        for k in range(7):
            t0 = k / 7
            for j in range(3):
                fx0 = 0.12 + j * 0.28
                fx1 = fx0 + 0.14

                def P(t, f):
                    x = xe + (xi - xe) * t
                    ytop = -40 + (640 + 40) * t
                    ybot = 1950 + (1240 - 1950) * t
                    return (x, ytop + (ybot - ytop) * f)
                a, b = t0 + 0.03, t0 + 0.09
                d.polygon([P(a, fx0), P(b, fx0), P(b, fx1), P(a, fx1)], fill=rgb("#2a2a30"))
    d.polygon([(0, 1950), (vx - 210, 1240), (vx + 210, 1240), (W, 1950), (W, H), (0, H)], fill=rgb("#4a463e"))
    arr = np.asarray(img, np.float32).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    street = (yy > 1240).astype(np.float32)
    arr += (np.sin(xx / 13) * np.sin(yy / 9) * 10 * street)[..., None]
    arr = light(arr, 1020, 980, 520, "#f4d79a", 0.55, 1.6)
    fog = np.clip(1 - np.hypot(xx - vx, (yy - vy) * 1.3) / 900, 0, 1)[..., None] ** 1.3
    arr = arr * (1 - fog * 0.7) + np.array(rgb("#d8d2c4"), np.float32) * fog * 0.7
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.rectangle([1006, 620, 1016, 1500], fill=rgb("#1a1814"))
    d.polygon([(990, 600), (1032, 600), (1040, 660), (982, 660)], fill=rgb("#f6dfa6"))
    img = silhouette(img, 452, 1725, 610, "pelerine", "kepi", "#1a1f2c", rim=("#e8e0cc", 0, -1), haze=("#9a968c", 0.18))
    img = silhouette(img, 790, 1725, 610, "pelerine", "kepi", "#1a1f2c", rim=("#e8e0cc", 0, -1), haze=("#9a968c", 0.18))
    img = silhouette(img, 621, 1705, 660, "manteau", "bowler", "#241e1a", rim=("#f2e2c0", 0, -1), haze=("#9a968c", 0.12))
    return finish(img, seed)


def scene_prison(seed=14) -> Image.Image:
    arr = vgrad("#7f7566", "#3b352e")
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rows = (yy // 120).astype(int)
    offset = (rows % 2) * 110
    mortar = ((yy % 120) < 7) | (((xx + offset) % 220) < 7)
    arr[mortar] *= 0.62
    arr += texture_noise(seed, 7, 22)[..., None]
    arr[yy > 1720] = arr[yy > 1720] * 0.55
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    wx0, wy0, wx1, wy1 = 690, 250, 1000, 600
    d.rectangle([wx0 - 20, wy0 - 20, wx1 + 20, wy1 + 20], fill=rgb("#4a4238"))
    d.rectangle([wx0, wy0, wx1, wy1], fill=rgb("#e9e1c6"))
    arr = np.asarray(img, np.float32).copy()
    beam = Image.new("L", (W, H), 0)
    ImageDraw.Draw(beam).polygon([(wx0, wy0), (wx1, wy0), (640, 2208), (-160, 2208)], fill=255)
    bars = Image.new("L", (W, H), 0)
    bd = ImageDraw.Draw(bars)
    for i in range(1, 5):
        x = wx0 + (wx1 - wx0) * i / 5
        bd.polygon([(x - 7, wy0), (x + 7, wy0), (x - 0.42 * (x - 300) + 30, 2208), (x - 0.42 * (x - 300) - 6, 2208)], fill=255)
    b = np.asarray(beam.filter(ImageFilter.GaussianBlur(28)), np.float32)[..., None] / 255
    s = np.asarray(bars.filter(ImageFilter.GaussianBlur(8)), np.float32)[..., None] / 255
    arr = arr * (1 + 0.55 * b * (1 - s)) + np.array(rgb("#f0d9a0"), np.float32) * 0.18 * b * (1 - s)
    arr = darken_edges(arr, 0.55)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    for i in range(1, 5):
        x = wx0 + (wx1 - wx0) * i / 5
        d.rectangle([x - 8, wy0, x + 8, wy1], fill=rgb("#26221e"))
    d.rectangle([wx0, (wy0 + wy1) / 2 - 7, wx1, (wy0 + wy1) / 2 + 7], fill=rgb("#26221e"))
    d.rectangle([90, 1560, 560, 1600], fill=rgb("#2a2420"))
    d.rectangle([110, 1600, 130, 1840], fill=rgb("#1e1a16"))
    d.rectangle([520, 1600, 540, 1840], fill=rgb("#1e1a16"))
    return finish(img, seed)


def scene_empreinte(seed=15) -> Image.Image:
    arr = vgrad("#13262c", "#081013")
    arr = light(arr, 160, 760, 1400, "#4a8a96", 0.45, 1.5)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.polygon([(150, 360), (1120, 410), (1100, 1780), (130, 1730)], outline=rgb("#9fd2da"), width=6)
    arr = np.asarray(img, np.float32).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sheen = np.clip(1 - np.abs((xx - yy * 0.45) - 120) / 260, 0, 1)
    arr += (sheen * 26)[..., None]
    img = to_img(arr)
    layer = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(layer)
    cx, cy = 640, 990
    rng = np.random.default_rng(seed)
    for k in range(30):
        r = 18 + k * 14
        pts = []
        for i in range(200):
            t = 2 * math.pi * i / 200
            rr = r * (1 + 0.07 * math.sin(2 * t + k * 0.35) + 0.03 * math.sin(5 * t + k))
            x = cx + rr * math.cos(t) * 0.82
            y = cy + rr * math.sin(t) * 1.12 - (k * 2.2 if math.sin(t) < 0 else 0)
            pts.append((x, y))
        for i in range(len(pts)):
            if rng.random() < 0.06:
                continue
            ld.line([pts[i], pts[(i + 1) % len(pts)]], fill=255, width=6)
    fade = np.clip(1.15 - np.hypot((xx - cx) / 420, (yy - cy) / 560), 0, 1)
    m = np.asarray(layer.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255 * fade
    arr = np.asarray(img, np.float32) * (1 - 0.65 * m[..., None]) + np.array(rgb("#dff3f5"), np.float32) * 0.65 * m[..., None]
    return finish(to_img(arr), seed, brushes=(40, 22, 11, 5, 3))


def scene_fichier(seed=16) -> Image.Image:
    arr = vgrad("#3a2414", "#1a0e08")
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    cols, rows = 6, 9
    x0, y0, x1, y1 = 60, 240, 1180, 1560
    cw, rh = (x1 - x0) / cols, (y1 - y0) / rows
    for r in range(rows):
        for c in range(cols):
            bx0, by0 = x0 + c * cw + 6, y0 + r * rh + 6
            bx1, by1 = bx0 + cw - 12, by0 + rh - 12
            d.rectangle([bx0 - 6, by0 - 6, bx1 + 6, by1 + 6], fill=rgb("#22140a"))
            tone = 0.85 + 0.15 * ((r * 7 + c * 3) % 5) / 4
            d.rectangle([bx0, by0, bx1, by1], fill=tuple(int(v * tone) for v in rgb("#7a4c28")))
            mx = (bx0 + bx1) / 2
            d.rectangle([mx - 40, by0 + 22, mx + 40, by0 + 52], fill=rgb("#d9c9a2"), outline=rgb("#a8884a"), width=4)
            d.ellipse([mx - 22, by0 + 74, mx + 22, by0 + 104], fill=rgb("#b8913e"))
    dx0, dx1 = 400, 842
    d.polygon([(dx0 - 50, 1700), (dx1 + 50, 1700), (dx1, 1250), (dx0, 1250)], fill=rgb("#5a3a1e"))
    for i in range(14):
        y = 1290 + i * 26
        inset = 40 - i * 2.2
        d.polygon([(dx0 + inset - 20, y + 40), (dx1 - inset + 20, y + 40), (dx1 - inset, y), (dx0 + inset, y)], fill=rgb("#efe4c8") if i % 2 else rgb("#e2d5b4"))
        d.line([(dx0 + inset - 20, y + 40), (dx1 - inset + 20, y + 40)], fill=rgb("#b8a882"), width=2)
    d.rectangle([dx0 - 50, 1700, dx1 + 50, 1900], fill=rgb("#6a4424"))
    d.ellipse([621 - 40, 1770, 621 + 40, 1820], fill=rgb("#c49a46"))
    arr = light(np.asarray(img, np.float32), 200, 120, 1900, "#ffd890", 0.4, 1.5)
    return finish(to_img(darken_edges(arr, 0.6)), seed)


def scene_chambre(seed=17) -> Image.Image:
    arr = vgrad("#232236", "#0e0d16")
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.polygon([(560, 0), (W, 0), (W, 1100), (980, 700)], fill=rgb("#17162a"))
    wx0, wy0, wx1, wy1 = 170, 380, 560, 960
    d.rectangle([wx0 - 30, wy0 - 30, wx1 + 30, wy1 + 30], fill=rgb("#2c2a3a"))
    sky = vgrad("#24324e", "#6a7488", wx1 - wx0, wy1 - wy0)
    sky = light(sky, 270, 150, 160, "#f2ecd2", 0.95, 2.2)
    win = to_img(sky)
    wd = ImageDraw.Draw(win)
    roofs = [(0, 420), (60, 360), (120, 380), (150, 300), (190, 300), (200, 340), (260, 330), (300, 280), (330, 280), (340, 330), (390, 340), (390, 580), (0, 580)]
    wd.polygon(roofs, fill=rgb("#141626"))
    for x in (95, 170, 315):
        wd.rectangle([x, 250, x + 16, 330], fill=rgb("#141626"))
    img.paste(win, (wx0, wy0))
    d = ImageDraw.Draw(img)
    d.rectangle([wx0, (wy0 + wy1) / 2 - 8, wx1, (wy0 + wy1) / 2 + 8], fill=rgb("#2c2a3a"))
    d.rectangle([(wx0 + wx1) / 2 - 8, wy0, (wx0 + wx1) / 2 + 8, wy1], fill=rgb("#2c2a3a"))
    arr = np.asarray(img, np.float32).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    floor = yy > 1650
    arr[floor] = arr[floor] * 0.9 + np.array(rgb("#2a2030"), np.float32) * 0.1
    arr += (((yy > 1650) & ((xx + (yy - 1650) * 0.6) % 150 < 5)) * -14.0)[..., None]
    beam = Image.new("L", (W, H), 0)
    ImageDraw.Draw(beam).polygon([(wx0, wy0), (wx1, wy0), (1050, 2208), (380, 2208)], fill=255)
    bm = np.asarray(beam.filter(ImageFilter.GaussianBlur(40)), np.float32)[..., None] / 255
    arr = arr * (1 + 0.5 * bm) + np.array(rgb("#9aa6c8"), np.float32) * 0.16 * bm
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.rectangle([700, 1500, W + 40, 1640], fill=rgb("#3a3450"))
    d.rectangle([690, 1400, 712, 1900], fill=rgb("#1a1824"))
    d.polygon([(700, 1500), (W + 40, 1480), (W + 40, 1560), (700, 1560)], fill=rgb("#5a5470"))
    d.rectangle([250, 1520, 520, 1545], fill=rgb("#2e2620"))
    d.rectangle([270, 1545, 290, 1880], fill=rgb("#221c18"))
    d.rectangle([480, 1545, 500, 1880], fill=rgb("#221c18"))
    d.ellipse([340, 1440, 410, 1525], fill=rgb("#4a4458"))
    d.rectangle([362, 1400, 388, 1450], fill=rgb("#6a6480"))
    return finish(img, seed)


def scene_arrestation(seed=18) -> Image.Image:
    vx, vy = 621, 930
    arr = vgrad("#5a4026", "#2a1c10")
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 0), (W, 0), (vx + 150, vy - 230), (vx - 150, vy - 230)], fill=rgb("#2a1e12"))
    d.polygon([(0, H), (W, H), (vx + 150, vy + 260), (vx - 150, vy + 260)], fill=rgb("#4a3a2a"))
    d.polygon([(0, 0), (vx - 150, vy - 230), (vx - 150, vy + 260), (0, H)], fill=rgb("#7a5a38"))
    d.polygon([(W, 0), (vx + 150, vy - 230), (vx + 150, vy + 260), (W, H)], fill=rgb("#6a4c2e"))
    d.rectangle([vx - 150, vy - 230, vx + 150, vy + 260], fill=rgb("#3a2a1a"))
    for i in range(12):
        t = (i / 12) ** 1.7
        y = vy + 260 + (H - vy - 260) * t
        xl = vx - 150 + (0 - (vx - 150)) * t
        xr = vx + 150 + (W - (vx + 150)) * t
        d.line([(xl, y), (xr, y)], fill=rgb("#3a2c1e"), width=3)
    for i in range(-6, 7):
        d.line([(vx + i * 25, vy + 260), (vx + i * 220, H)], fill=rgb("#3a2c1e"), width=3)

    def door_pt(t, f):
        x = W + (vx + 150 - W) * t
        ytop = 0 + (vy - 230) * t
        ybot = H + (vy + 260 - H) * t
        return (x, ytop + (ybot - ytop) * f)
    d.polygon([door_pt(0.42, 0.18), door_pt(0.62, 0.22), door_pt(0.62, 1.0), door_pt(0.42, 1.0)], fill=rgb("#ffd79a"))
    d.polygon([door_pt(0.42, 0.18), door_pt(0.47, 0.19), door_pt(0.47, 1.0), door_pt(0.42, 1.0)], fill=rgb("#4a3420"))
    arr = np.asarray(img, np.float32).copy()
    arr = light(arr, 900, 1500, 700, "#ffc97a", 0.45, 1.5)
    arr = light(arr, vx, 160, 500, "#ffe2a8", 0.35, 1.8)
    img = to_img(darken_edges(arr, 0.5))
    img = silhouette(img, 555, 1650, 600, "manteau", "bowler", "#1a1714", rim=("#ffc97a", 1, -0.3), rim_amount=0.7)
    img = silhouette(img, 742, 1615, 570, "manteau", "bowler", "#1d1a22", rim=("#ffc97a", 1, -0.3), rim_amount=0.8)
    return finish(img, seed)


def scene_vitrine(seed=19) -> Image.Image:
    arr = vgrad("#3a2a1c", "#140c08")
    arr += texture_noise(seed, 18, 16)[..., None]
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    gx0, gy0, gx1, gy1 = 300, 330, 942, 1260
    d.polygon([(gx1, gy0), (gx1 + 70, gy0 + 50), (gx1 + 70, gy1 + 40), (gx1, gy1)], fill=rgb("#4a3420"))
    d.polygon([(gx0, gy0), (gx1, gy0), (gx1 + 70, gy0 + 50), (gx0 + 70, gy0 + 50)], fill=rgb("#5a4028"))
    d.rectangle([gx0 - 26, gy0 - 26, gx1 + 26, gy1 + 26], fill=rgb("#6a4a28"))
    d.rectangle([gx0, gy0, gx1, gy1], fill=rgb("#2a2018"))
    art_box = (gx0 + 26, gy0 + 26, gx1 - 26, gy1 - 26)
    art = Image.open(REPRO).convert("RGB")
    aw, ah = art_box[2] - art_box[0], art_box[3] - art_box[1]
    sc = max(aw / art.width, ah / art.height)
    art = art.resize((int(art.width * sc + 0.5), int(art.height * sc + 0.5)), Image.LANCZOS)
    left, top = (art.width - aw) // 2, (art.height - ah) // 2
    art = art.crop((left, top, left + aw, top + ah))
    img.paste(art.filter(ImageFilter.GaussianBlur(3)), art_box[:2])
    d = ImageDraw.Draw(img)
    d.polygon([(0, 1520), (W, 1520), (W, H), (0, H)], fill=rgb("#5a3a20"))
    d.rectangle([0, 1500, W, 1530], fill=rgb("#7a5430"))
    d.polygon([(160, 1700), (980, 1640), (990, 1672), (170, 1734)], fill=rgb("#b8b4ac"))
    for i in range(0, 32):
        x = 170 + i * 25.5
        d.line([(x, 1700 - i * 1.9), (x, 1714 - i * 1.9)], fill=rgb("#4a4640"), width=3)
    d.polygon([(640, 1830), (900, 1790), (930, 1840), (690, 1900)], fill=rgb("#9fbcc0"))
    d.rounded_rectangle([250, 1880, 520, 1920], 12, fill=rgb("#2a2420"))
    d.ellipse([500, 1884, 540, 1916], fill=rgb("#c8c8c8"))
    arr = light(np.asarray(img, np.float32), 300, 0, 1900, "#ffd59a", 0.32, 1.4)
    base = to_img(darken_edges(arr, 0.5))

    def reflections(im: Image.Image) -> Image.Image:
        a = np.asarray(im, np.float32).copy()
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        inside = (xx > gx0) & (xx < gx1) & (yy > gy0) & (yy < gy1)
        s1 = np.clip(1 - np.abs((xx + yy * 0.55) - 1560) / 46, 0, 1)
        s2 = np.clip(1 - np.abs((xx + yy * 0.55) - 1700) / 18, 0, 1)
        s3 = np.clip(1 - np.abs((xx + yy * 0.55) - 640) / 30, 0, 1)
        refl = (s1 * 0.16 + s2 * 0.12 + s3 * 0.10) * inside
        a = a * (1 - refl[..., None]) + 255 * refl[..., None]
        return to_img(a)

    return finish(base, seed, protect=(art_box, art), post=reflections)


def scene_escalier(seed=20, man=True) -> Image.Image:
    arr = vgrad("#5e5446", "#1e1a16")
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    vx = 700
    for i in range(16):
        t0 = i / 16
        t1 = (i + 1) / 16
        y0 = 2208 - 1500 * (t0 ** 0.8)
        y1 = 2208 - 1500 * (t1 ** 0.8)
        hw0 = 760 * (1 - t0 * 0.72)
        hw1 = 760 * (1 - t1 * 0.72)
        cx0 = 560 + (vx - 560) * t0
        cx1 = 560 + (vx - 560) * t1
        tone = 0.6 + 0.4 * (1 - t0)
        d.polygon([(cx0 - hw0, y0), (cx0 + hw0, y0), (cx1 + hw1, y1), (cx1 - hw1, y1)], fill=tuple(int(v * tone) for v in rgb("#8a7c66")))
        d.line([(cx1 - hw1, y1), (cx1 + hw1, y1)], fill=rgb("#2c261e"), width=max(2, int(10 * (1 - t0))))
    d.polygon([(0, 0), (330, 0), (470, 700), (0, 1200)], fill=rgb("#4a4236"))
    d.polygon([(W, 0), (940, 0), (930, 700), (W, 1500)], fill=rgb("#3e372e"))
    d.rectangle([600, 120, 820, 520], fill=rgb("#efe6cc"))
    d.rectangle([706, 120, 714, 520], fill=rgb("#4a4236"))
    arr = np.asarray(img, np.float32).copy()
    arr = light(arr, 710, 380, 900, "#f6e6c0", 0.45, 1.5)
    arr += texture_noise(seed, 8, 14)[..., None]
    img = to_img(darken_edges(arr, 0.45))
    if man:
        img = silhouette(img, 690, 1010, 470, "blouse", "cap", "#1e1a16", rim=("#f6e6c0", 0, -1), rim_amount=0.4)
    else:  # la vitre de la boîte de protection, posée contre la marche, à côté du cadre
        d = ImageDraw.Draw(img)
        d.polygon([(600, 1640), (1010, 1600), (1050, 2120), (640, 2170)], fill=rgb("#9fb4b0"))
        d.line([(640, 1660), (690, 2150)], fill=rgb("#e8f0ea"), width=6)
    d = ImageDraw.Draw(img)
    fx0, fy0, fx1, fy1 = 90, 1500, 520, 2140
    for i in range(44):
        t = i / 44
        hi = tuple(int(c) for c in np.array(rgb("#e2c46e")) * (1 - t) + np.array(rgb("#8c6a2c")) * t)
        d.rectangle([fx0 + i, fy0 + i, fx1 - i, fy1 - i], outline=hi, width=1)
    return finish(img, seed)


def _paste_art(box) -> Image.Image:
    """Reproduction authentique recadrée (cover) à la taille de la boîte : jamais repeinte, collée après la peinture."""
    art = Image.open(REPRO).convert("RGB")
    aw, ah = box[2] - box[0], box[3] - box[1]
    sc = max(aw / art.width, ah / art.height)
    art = art.resize((int(art.width * sc + 0.5), int(art.height * sc + 0.5)), Image.LANCZOS)
    left, top = (art.width - aw) // 2, (art.height - ah) // 2
    return art.crop((left, top, left + aw, top + ah))


def scene_beroud(seed=21) -> Image.Image:
    """22 août 1911 : un peintre copiste, de dos, devant l'emplacement vide (on voit le dos de sa toile)."""
    img = _mur(seed)
    d = ImageDraw.Draw(img)
    ex = 930
    for x_bot in (ex - 190, ex + 190):
        d.polygon([(ex - 10, 1000), (ex + 10, 1000), (x_bot + 16, 2208), (x_bot - 16, 2208)], fill=rgb("#3e2812"))
    d.rectangle([ex - 9, 980, ex + 9, 2208], fill=rgb("#33200e"))
    d.rectangle([ex - 190, 1500, ex + 190, 1530], fill=rgb("#4a3018"))
    cx0, cy0, cx1, cy1 = ex - 170, 1060, ex + 170, 1500     # dos de la toile : lin brut et châssis, aucune image
    d.rectangle([cx0, cy0, cx1, cy1], fill=rgb("#b9a78a"))
    for x in (cx0, cx1 - 26, (cx0 + cx1) // 2 - 12):
        d.rectangle([x, cy0, x + 26, cy1], fill=rgb("#7a5a34"))
    d.rectangle([cx0, cy0, cx1, cy0 + 26], fill=rgb("#7a5a34"))
    d.rectangle([cx0, cy1 - 26, cx1, cy1], fill=rgb("#7a5a34"))
    d.rectangle([cx0, (cy0 + cy1) // 2 - 12, cx1, (cy0 + cy1) // 2 + 12], fill=rgb("#7a5a34"))
    img = to_img(light(np.asarray(img, np.float32), 300, 1700, 900, "#1a0c08", 0.35, 1.2))
    img = silhouette(img, 300, 2260, 960, "manteau", "bowler", "#1c1612", rim=("#f1d9b0", 0.3, -1), rim_amount=0.6)
    return finish(img, seed)


def scene_photographe(seed=22) -> Image.Image:
    """Les gardiens croient d'abord le tableau parti au service photographique : chambre photographique sur pied."""
    arr = vgrad("#5c5a50", "#24221e")
    arr += texture_noise(seed, 10, 12)[..., None]
    arr = light(arr, 80, 500, 1500, "#f4e6c4", 0.45, 1.4)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1760, W, H], fill=rgb("#3a2c20"))
    for i in range(10):
        d.line([(0, 1760 + i * 46), (W, 1760 + i * 46)], fill=rgb("#2a2016"), width=3)
    for x_bot in (380, 640, 900):
        d.polygon([(632, 1260), (648, 1260), (x_bot + 14, 2050), (x_bot - 14, 2050)], fill=rgb("#4a3420"))
    d.rectangle([520, 1180, 760, 1270], fill=rgb("#3a2818"))
    d.rectangle([330, 820, 560, 1190], fill=rgb("#5a3c20"))                    # chambre arrière (verre dépoli)
    d.rectangle([350, 840, 540, 1170], fill=rgb("#8a8a7c"))
    folds = 9                                                                    # soufflet
    for i in range(folds):
        t0, t1 = i / folds, (i + 1) / folds
        def edge(t):
            return 560 + 300 * t, 840 + 70 * t, 1170 - 70 * t
        x0, a0, b0 = edge(t0)
        x1, a1, b1 = edge(t1)
        d.polygon([(x0, a0), (x1, a1), (x1, b1), (x0, b0)], fill=rgb("#1e1a16" if i % 2 else "#2c2620"))
    d.rectangle([860, 880, 900, 1130], fill=rgb("#5a3c20"))                    # planchette avant
    d.ellipse([890, 940, 1010, 1070], fill=rgb("#b08a40"))                       # objectif en laiton
    d.ellipse([918, 968, 982, 1042], fill=rgb("#121212"))
    d.polygon([(300, 760), (590, 780), (600, 900), (560, 1320), (470, 1380), (300, 1300)], fill=rgb("#141210"))  # voile noir
    arr = darken_edges(np.asarray(img, np.float32), 0.5)
    return finish(to_img(arr), seed)


def scene_escalier_vide(seed=23) -> Image.Image:
    return scene_escalier(seed, man=False)


def scene_foule(seed=24) -> Image.Image:
    """À la réouverture, la foule vient voir l'emplacement vide (silhouettes de dos)."""
    img = _mur(seed)
    people = [(120, "robe", "capeline", "#2a1e1c"), (330, "manteau", "bowler", "#1a1614"),
              (560, "manteau", "canotier", "#221c18"), (790, "robe", "capeline", "#2c2220"),
              (1000, "manteau", "bowler", "#18120e"), (1190, "manteau", "cap", "#201a16")]
    for i, (x, kind, hat, col) in enumerate(people):
        h = 1180 + (i % 3) * 50
        img = silhouette(img, x, 2560 + (i % 2) * 40, h, kind, hat, col, rim=("#f1d9b0", 0, -1), rim_amount=0.55)
    return finish(img, seed)


def scene_juge(seed=25) -> Image.Image:
    """7 septembre 1911 : bureau d'un juge d'instruction ; un homme en chapeau melon, de dos."""
    arr = vgrad("#34402f", "#141a12")
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    arr += (((xx % 310) < 8) * -18.0)[..., None]
    arr += texture_noise(seed, 12, 12)[..., None]
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1100, W, 1130], fill=rgb("#2a2014"))
    d.rounded_rectangle([470, 640, 790, 1180], 40, fill=rgb("#1e140c"))          # dossier de fauteuil, vide
    d.polygon([(60, 1150), (1180, 1150), (1242, 1460), (0, 1460)], fill=rgb("#5a3a20"))   # bureau
    d.rectangle([0, 1460, W, 1520], fill=rgb("#3a2414"))
    d.rectangle([0, 1520, W, H], fill=rgb("#2a1a10"))
    for x0, y0, x1, y1 in [(260, 1230, 470, 1300), (300, 1300, 520, 1370), (560, 1250, 700, 1330)]:
        d.polygon([(x0, y0), (x1, y0 - 10), (x1 + 20, y1), (x0 + 16, y1 + 8)], fill=rgb("#ddd2b8"))   # feuilles vierges
    d.rectangle([905, 1060, 921, 1250], fill=rgb("#8a6a2c"))                       # lampe à abat-jour vert
    d.ellipse([850, 1240, 980, 1270], fill=rgb("#8a6a2c"))
    d.chord([790, 980, 1040, 1120], 180, 360, fill=rgb("#1f5a3a"))
    arr = light(np.asarray(img, np.float32), 915, 1260, 560, "#ffe2a0", 0.6, 1.6)
    img = to_img(darken_edges(arr, 0.55))
    img = silhouette(img, 400, 2420, 1300, "manteau", "bowler", "#15110e", rim=("#ffd890", 1, -0.6), rim_amount=0.7)
    return finish(img, seed)


def scene_loupe(seed=26) -> Image.Image:
    """La vitre et son empreinte sous la loupe : l'indice existe, personne ne fait le rapprochement."""
    arr = vgrad("#4a2e18", "#1e1208")
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    arr += (np.sin(yy / 11 + np.sin(xx / 140) * 2) * 6)[..., None]
    arr = light(arr, 200, 300, 1500, "#ffd890", 0.4, 1.4)
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    plate = [(170, 560), (1010, 470), (1080, 1560), (240, 1650)]
    d.polygon(plate, fill=rgb("#3c5652"))
    d.line(plate + [plate[0]], fill=rgb("#b8d6d2"), width=5)
    layer = Image.new("L", (W, H), 0)
    ld = ImageDraw.Draw(layer)
    cx, cy = 600, 1060
    for k in range(22):
        r = 14 + k * 11
        pts = [(cx + r * math.cos(t) * 0.82 * (1 + 0.06 * math.sin(2 * t + k * 0.3)),
                cy + r * math.sin(t) * 1.1) for t in np.linspace(0, 2 * math.pi, 160)]
        ld.line(pts, fill=255, width=4)
    m = np.asarray(layer.filter(ImageFilter.GaussianBlur(1)), np.float32)[..., None] / 255
    arr = np.asarray(img, np.float32)
    lens = (np.hypot(xx - 640, yy - 1000) < 250)[..., None]
    k_in = np.where(lens, 0.75, 0.28)
    arr = arr * (1 - m * k_in) + np.array(rgb("#e6f4f2"), np.float32) * m * k_in
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.ellipse([640 - 262, 1000 - 262, 640 + 262, 1000 + 262], outline=rgb("#b48a3c"), width=26)
    d.polygon([(800, 1190), (840, 1160), (1120, 1560), (1070, 1600)], fill=rgb("#2a1a0e"))
    d.polygon([(1010, 1480), (1060, 1450), (1120, 1560), (1070, 1600)], fill=rgb("#b48a3c"))
    arr = np.asarray(img, np.float32)
    sheen = np.clip(1 - np.abs((xx - yy * 0.5) - 120) / 140, 0, 1) * (np.hypot(xx - 640, yy - 1000) < 240)
    arr = arr + (sheen * 40)[..., None]
    return finish(to_img(darken_edges(arr, 0.55)), seed, brushes=(40, 22, 11, 5, 3))


def scene_antiquaire(seed=27) -> Image.Image:
    """Florence, décembre 1913 : le tableau examiné chez l'antiquaire (reproduction authentique, collée après peinture)."""
    arr = vgrad("#4e3620", "#1a1008")
    arr += texture_noise(seed, 14, 14)[..., None]
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    for y in (420, 760, 1100):                                                    # étagères et objets anciens
        d.rectangle([0, y, 300, y + 22], fill=rgb("#2e1c0e"))
        d.rectangle([942, y, W, y + 22], fill=rgb("#2e1c0e"))
        for x, w_, h_ in [(40, 80, 150), (150, 60, 110), (980, 90, 170), (1110, 70, 120)]:
            d.ellipse([x, y - h_, x + w_, y], fill=rgb("#6a4a2a"))
            d.rectangle([x + w_ * 0.3, y - h_ - 30, x + w_ * 0.7, y - h_ + 10], fill=rgb("#5a3e22"))
    box = (431, 600, 811, 1152)                                                   # 380 × 552 : proportions du panneau
    d.rectangle([box[0] - 30, box[1] - 30, box[2] + 30, box[3] + 30], fill=rgb("#2a1c10"))
    d.polygon([(box[0] + 40, box[3] + 30), (box[2] - 40, box[3] + 30), (box[2] + 60, 1420), (box[0] - 60, 1420)], fill=rgb("#3a2614"))
    d.polygon([(100, 1250), (1142, 1250), (1242, 1700), (0, 1700)], fill=rgb("#5a3a1e"))   # table
    d.rectangle([0, 1700, W, H], fill=rgb("#24160c"))
    d.line([(621, 0), (621, 330)], fill=rgb("#1a120a"), width=6)                 # suspension
    d.chord([500, 300, 742, 470], 180, 360, fill=rgb("#8a6a30"))
    arr = light(np.asarray(img, np.float32), 621, 700, 760, "#ffd08a", 0.5, 1.4)
    base = to_img(darken_edges(arr, 0.55))
    base = silhouette(base, 250, 2560, 1260, "manteau", "bowler", "#18120e", rim=("#ffd08a", 0.4, -1), rim_amount=0.7)
    base = silhouette(base, 1000, 2600, 1300, "manteau", "bowler", "#1c1612", rim=("#ffd08a", -0.4, -1), rim_amount=0.7)
    return finish(base, seed, protect=(box, _paste_art(box)))


def scene_vitrier(seed=28) -> Image.Image:
    """Avant le vol : un vitrier en blouse, de dos, devant une vitrine de protection qu'il vient de poser."""
    img = _mur(seed, hooks_on=False)
    d = ImageDraw.Draw(img)
    gx0, gy0, gx1, gy1 = 380, 560, 862, 1260
    d.rectangle([gx0 - 24, gy0 - 24, gx1 + 24, gy1 + 24], fill=rgb("#5a3c20"))
    d.rectangle([gx0, gy0, gx1, gy1], fill=rgb("#3a1a14"))
    d.polygon([(880, 1300), (1150, 1250), (1180, 1980), (900, 2030)], fill=rgb("#8fa8a6"))   # vitre posée contre le mur
    arr = np.asarray(img, np.float32).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    inside = (xx > gx0) & (xx < gx1) & (yy > gy0) & (yy < gy1)
    s1 = np.clip(1 - np.abs((xx + yy * 0.55) - 1300) / 50, 0, 1) * inside
    arr = arr * (1 - 0.2 * s1[..., None]) + 255 * 0.2 * s1[..., None]
    img = to_img(arr)
    img = silhouette(img, 470, 2330, 1180, "blouse", "cap", "#1e1a16", rim=("#f1d9b0", 0.2, -1), rim_amount=0.5)
    return finish(img, seed)


def scene_proces(seed=29) -> Image.Image:
    """Florence, juin 1914 : salle d'audience ; l'accusé, de dos, devant la cour (sièges vides, aucun visage)."""
    arr = vgrad("#5a4028", "#22160c")
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    arr += (((xx % 207) < 6) * -16.0 * (yy < 1150))[..., None]
    img = to_img(arr)
    d = ImageDraw.Draw(img)
    d.chord([321, 120, 921, 720], 180, 360, fill=rgb("#e8dcbc"))               # lunette éclairée
    d.rectangle([321, 420, 921, 440], fill=rgb("#4a3420"))
    for x in (380, 621, 862):
        d.rounded_rectangle([x - 90, 700, x + 90, 1050], 30, fill=rgb("#2a1a0e"))   # hauts dossiers vides
    d.rectangle([40, 980, 1202, 1240], fill=rgb("#4a2e16"))                       # estrade de la cour
    d.rectangle([40, 960, 1202, 990], fill=rgb("#6a4626"))
    for x in range(80, 1202, 120):
        d.rectangle([x, 1020, x + 80, 1210], outline=rgb("#3a220e"), width=6)
    d.rectangle([0, 1240, W, H], fill=rgb("#2e1e10"))
    d.rectangle([0, 1520, W, 1550], fill=rgb("#5a3a1c"))                          # balustrade
    for x in range(20, W, 70):
        d.rectangle([x, 1550, x + 22, 1760], fill=rgb("#4a2e16"))
    arr = light(np.asarray(img, np.float32), 621, 420, 900, "#ffe8b8", 0.45, 1.5)
    img = to_img(darken_edges(arr, 0.5))
    img = silhouette(img, 621, 1700, 760, "manteau", None, "#16110c", rim=("#ffe2a8", 0, -1), rim_amount=0.65)
    for x, h_, hat in [(130, 1100, "bowler"), (1110, 1150, "bowler"), (330, 1000, "cap")]:
        img = silhouette(img, x, 2700, h_, "manteau", hat, "#120e0a", rim=("#ffe2a8", 0, -1), rim_amount=0.35)
    return finish(img, seed)


def scene_retour(seed=30) -> Image.Image:
    """4 janvier 1914 : la Joconde (reproduction authentique) de retour sur le mur, la foule de dos."""
    img = _mur(seed, hooks_on=False)
    frame = (361, 650, 881, 1351)
    img = gilt_frame(img, frame, border=60, seed=seed)
    box = (frame[0] + 60, frame[1] + 60, frame[2] - 60, frame[3] - 60)
    for i, (x, kind, hat, col) in enumerate([(160, "robe", "capeline", "#2a1e1c"), (420, "manteau", "bowler", "#1a1614"),
                                             (830, "manteau", "canotier", "#221c18"), (1090, "robe", "capeline", "#2c2220")]):
        img = silhouette(img, x, 2660 + (i % 2) * 40, 1180, kind, hat, col, rim=("#f1d9b0", 0, -1), rim_amount=0.55)
    return finish(img, seed, protect=(box, _paste_art(box)))


SCENES = {
    "mur_vide": scene_mur_vide,
    "crochets": scene_crochets,
    "soupcons": scene_soupcons,
    "prison": scene_prison,
    "empreinte": scene_empreinte,
    "fichier": scene_fichier,
    "chambre": scene_chambre,
    "arrestation": scene_arrestation,
    "vitrine": scene_vitrine,
    "escalier": scene_escalier,
    "beroud": scene_beroud,
    "photographe": scene_photographe,
    "escalier_vide": scene_escalier_vide,
    "foule": scene_foule,
    "juge": scene_juge,
    "loupe": scene_loupe,
    "antiquaire": scene_antiquaire,
    "vitrier": scene_vitrier,
    "proces": scene_proces,
    "retour": scene_retour,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    names = sys.argv[1:] or list(SCENES)
    for name in names:
        img = SCENES[name]()
        img.save(OUT / f"{name}.png", optimize=True)
        print("illustration", name, img.size)


if __name__ == "__main__":
    main()
