---
workflow: general-video
flow: automation
storyboard: no
message: "Imagine Paris en janvier 1910 : les horloges s'arrêtent, l'eau envahit tout, la ville s'entraide — et le niveau de la Seine est encore gravé sur les murs."
destination: tiktok
aspect: 1080x1920
language: fr
audience: jeunes adultes curieux d'histoire, sur TikTok
length: 55s
angle: story
---

## Intent

V2 de `videos/crue-1910-tiktok/` à la demande : « plus d'émotion », « plus nouveau », « dans la mode de 2026 ».
Même sujet, mêmes règles de fiabilité, mais une vraie courbe émotionnelle : malaise → angoisse → empathie → chaleur
→ vertige → gravité, avec une narration « POV » au tutoiement (« Imagine : … »).

Style visé (formats courts 2025–2026) : sous-titres mot à mot avec le mot prononcé en couleur, titres cinétiques,
archive en « carte » sur un fond flou (profondeur), couleur qui change avec l'émotion, design sonore marqué (tic-tac,
coupure, battement, montée, impact), fin qui reboucle sur le début (le tic-tac reprend).

## Assets

- Archives de 1910 du domaine public (Agence Rol / BnF, cartes postales ELD, AHK, ND Phot., A. Taride, Héliotypie
  E. Le Deley, une du *Petit Journal*) et une photo récente sous CC BY-SA 3.0 d'un repère de crue — `SOURCES.md`.

## Customizations

- Voix de synthèse locale gratuite (Kokoro, `ff_siwis`), vitesse réglée phrase par phrase : aucun crédit payant.
- Musique et bruitages composés par programme (aucun son d'époque simulé, aucune foule, aucune sirène).
- Étalonnage précalculé (`scripts/images.py`) : couleur seulement, aucun élément ajouté aux archives.

## Notes

- Les deux cadrans d'horloge sont des illustrations, signalées comme telles ; l'heure affichée n'est pas une donnée.
- Le détourage automatique (`remove-background`) a été essayé sur trois archives pour un effet « pop-out » : sujet vide
  ou coupé sur les trois (modèle fait pour des personnes en photo moderne). Abandonné ; profondeur obtenue par la
  carte photo sur fond flou et un léger décalage de vitesse entre les deux.
