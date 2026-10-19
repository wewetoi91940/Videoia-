#!/usr/bin/env python3
"""Floutage des visages sur les photos des lieux (aucune personne privée identifiable).

Détecteur YuNet (OpenCV), appliqué sur l'image agrandie ×2 et découpée en tuiles pour trouver les petits visages
de passants. Chaque visage est flouté sur une zone élargie de 60 %. Les originaux restent dans
build/photos_originales/ (non versionné) ; la liste des modifications est ajoutée à assets/photos/credits.json.
Modèle : https://github.com/opencv/opencv_zoo (face_detection_yunet_2023mar.onnx), téléchargé dans build/modeles/.
"""
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "assets/photos"
ORIG = ROOT / "build/photos_originales"
MODELE = ROOT / "build/modeles/yunet.onnx"
SANS_PERSONNE = {"castellane.jpg", "prefecture.jpg", "panorama.jpg"}   # vérifiées à l'œil : personne dans le champ
# Bande où se trouvent les passants (fraction de la hauteur) : au-dessus, le détecteur prend des sculptures pour des visages.
BANDE = {"hotel-de-ville.jpg": 0.85, "prado.jpg": 0.70}


def visages(img: np.ndarray) -> list[tuple[int, int, int, int]]:
    grand = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    H, W = grand.shape[:2]
    T, R = 1600, 200
    det = cv2.FaceDetectorYN.create(str(MODELE), "", (T, T), 0.55, 0.3, 5000)
    boites = []
    for y0 in range(0, H, T - R):
        for x0 in range(0, W, T - R):
            tuile = grand[y0:y0 + T, x0:x0 + T]
            h, w = tuile.shape[:2]
            if h < 40 or w < 40:
                continue
            det.setInputSize((w, h))
            _, f = det.detect(tuile)
            for x, y, bw, bh in ([] if f is None else f[:, :4]):
                boites.append(((x0 + x) / 2, (y0 + y) / 2, bw / 2, bh / 2))
    return [tuple(int(v) for v in b) for b in boites]


def flouter(img: np.ndarray, boites) -> np.ndarray:
    out = img.copy()
    for x, y, w, h in boites:
        cx, cy, r = x + w / 2, y + h / 2, max(w, h) * 0.8
        a, b = max(0, int(cx - r)), max(0, int(cy - r))
        c, d = min(img.shape[1], int(cx + r)), min(img.shape[0], int(cy + r))
        if c - a < 4 or d - b < 4:
            continue
        k = max(9, int(r) | 1)
        out[b:d, a:c] = cv2.GaussianBlur(out[b:d, a:c], (k, k), r / 2)
    return out


def main():
    ORIG.mkdir(parents=True, exist_ok=True)
    credits = json.loads((PHOTOS / "credits.json").read_text())
    for c in credits:
        f = c["fichier"]
        if f in SANS_PERSONNE:
            continue
        src = ORIG / f
        if not src.exists():
            shutil.copy2(PHOTOS / f, src)
        img = cv2.imread(str(src))
        boites = [bx for bx in visages(img) if bx[1] + bx[3] / 2 >= BANDE.get(f, 0) * img.shape[0]]
        cv2.imwrite(str(PHOTOS / f), flouter(img, boites), [cv2.IMWRITE_JPEG_QUALITY, 90])
        if boites or f == "saint-ferreol.jpg":
            plaques = " et plaques d'immatriculation" if f == "saint-ferreol.jpg" else ""
            c["modifications"] = f"image modifiée : visages{plaques} floutés ({len(boites)} détection(s) automatique(s))"
        print(f"{f:20} {len(boites):3d} visage(s)")
    (PHOTOS / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
