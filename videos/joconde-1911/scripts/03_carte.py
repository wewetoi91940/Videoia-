#!/usr/bin/env python3
"""Carte schématique Paris → Florence à partir de données géographiques réelles.

Données : Natural Earth 1:50m (domaine public), terres émergées seulement (paquet npm world-atlas,
fichier land-50m.json). Aucune frontière n'est tracée : pas de frontière anachronique possible.
Projection : Mercator, échelle calée pour que Paris et Florence tombent aux positions voulues.
Le trait Paris → Florence est un arc schématique : l'itinéraire réel du voleur n'est pas documenté.

Sorties : assets/cartes/carte_paris_florence.png (fond, 1242×2208),
          assets/cartes/carte_paris_florence.svg (version vectorielle),
          assets/cartes/carte.json (positions des villes, en pixels du cadre 1080×1920).
"""
import json
import math
import subprocess
import tarfile
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets/cartes"
W, H = 1242, 2208           # fond peint aux dimensions des illustrations (1,15 × 1080×1920)
FRAME_SCALE = 1080 / W
CITIES = {                   # coordonnées WGS84 (degrés décimaux)
    "Paris": (48.8566, 2.3522),
    "Florence": (43.7696, 11.2558),
}
TARGET = {"Paris": (265, 640), "Florence": (930, 1235)}  # positions voulues dans l'image 1242×2208


def load_land() -> dict:
    cache = ROOT / "build/land-50m.json"
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["npm", "pack", "world-atlas@2.0.2", "--silent"], cwd=tmp, check=True)
            with tarfile.open(Path(tmp) / "world-atlas-2.0.2.tgz") as tar:
                cache.write_bytes(tar.extractfile("package/land-50m.json").read())
    return json.loads(cache.read_text())


def decode_arcs(topo: dict) -> list[list[tuple[float, float]]]:
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)
    return arcs


def rings(topo: dict) -> list[list[tuple[float, float]]]:
    arcs = decode_arcs(topo)

    def arc(i):
        return arcs[i] if i >= 0 else arcs[~i][::-1]

    out = []
    for geom in topo["objects"]["land"]["geometries"]:
        polys = geom["arcs"] if geom["type"] == "MultiPolygon" else [geom["arcs"]]
        for poly in polys:
            for ring in poly:
                pts = []
                for i in ring:
                    seg = arc(i)
                    pts.extend(seg if not pts else seg[1:])
                out.append(pts)
    return out


def merc(lat: float, lon: float) -> tuple[float, float]:
    return math.radians(lon), math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (px, py), (fx, fy) = merc(*CITIES["Paris"]), merc(*CITIES["Florence"])
    (tpx, tpy), (tfx, tfy) = TARGET["Paris"], TARGET["Florence"]
    k = (tfy - tpy) / (py - fy)                 # pixels par radian (même échelle en x et en y)
    ox, oy = tpx - px * k, tpy + py * k

    def project(lat, lon):
        x, y = merc(lat, lon)
        return x * k + ox, oy - y * k

    check_x = project(*CITIES["Florence"])[0]
    arr = np.zeros((H, W, 3), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sea_top, sea_bot = np.array([16, 26, 32], np.float32), np.array([8, 14, 18], np.float32)
    arr[:] = sea_top * (1 - yy[..., None] / H) + sea_bot * (yy[..., None] / H)
    land = Image.new("L", (W, H), 0)
    coast = Image.new("L", (W, H), 0)
    ld, cd = ImageDraw.Draw(land), ImageDraw.Draw(coast)
    svg_paths = []
    for ring in rings(load_land()):
        if not any(-25 < lon < 40 and 25 < lat < 65 for lon, lat in ring):
            continue
        pts = [project(lat, lon) for lon, lat in ring]
        ld.polygon(pts, fill=255)
        cd.line(pts + [pts[0]], fill=255, width=3)
        svg_paths.append("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z")
    lm = np.asarray(land, np.float32)[..., None] / 255
    rng = np.random.default_rng(7)
    grain = np.asarray(Image.fromarray((rng.random((H // 6, W // 6)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None] / 255
    land_col = np.array([58, 51, 38], np.float32) * (0.92 + 0.16 * grain)
    arr = arr * (1 - lm) + land_col * lm
    cm = np.asarray(coast.filter(ImageFilter.GaussianBlur(0.8)), np.float32)[..., None] / 255
    arr = arr * (1 - cm * 0.85) + np.array([170, 148, 104], np.float32) * cm * 0.85
    glow = np.asarray(coast.filter(ImageFilter.GaussianBlur(14)), np.float32)[..., None] / 255
    arr += glow * (1 - lm) * np.array([40, 50, 46], np.float32) * 0.6
    vign = np.clip(np.hypot((xx - W / 2) / (W * 0.7), (yy - H * 0.45) / (H * 0.6)) - 0.5, 0, 1)[..., None]
    arr *= 1 - 0.5 * vign
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(OUT / "carte_paris_florence.png", optimize=True)

    cities_px = {n: project(*c) for n, c in CITIES.items()}
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           '<rect width="100%" height="100%" fill="#0c1418"/>',
           f'<path d="{" ".join(svg_paths)}" fill="#3a3326" stroke="#aa9468" stroke-width="3" fill-rule="evenodd"/>']
    for n, (x, y) in cities_px.items():
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="#f2ead8"/>')
        svg.append(f'<text x="{x + (24 if n == "Paris" else -24):.1f}" y="{y - 22:.1f}" font-family="Oswald" font-size="44" '
                   f'fill="#f2ead8" text-anchor="{"start" if n == "Paris" else "end"}">{n.upper()}</text>')
    svg.append("</svg>")
    (OUT / "carte_paris_florence.svg").write_text("\n".join(svg))
    meta = {
        "source": "Natural Earth 1:50m (domaine public) via npm world-atlas@2.0.2, land-50m.json",
        "projection": "Mercator",
        "villes_lat_lon": CITIES,
        "villes_px_cadre_1080x1920": {n: [round(x * FRAME_SCALE, 1), round(y * FRAME_SCALE, 1)] for n, (x, y) in cities_px.items()},
        "villes_px_image_1242x2208": {n: [round(x, 1), round(y, 1)] for n, (x, y) in cities_px.items()},
        "florence_x_cible_de_mise_en_page": TARGET["Florence"][0],
        "florence_x_projete_utilise": round(check_x, 1),   # position géographique vraie (échelle isotrope, calée sur l'axe nord-sud)
    }
    (OUT / "carte.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(json.dumps(meta, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
