# Étape 5 — Montage

> Généré par `scripts/06_dossier.py`. Composition : `index.html` (HyperFrames), générée par `scripts/05_composition.py`.

## Ordre, durées et transitions

| # | Plan | Entrée (TC) | Sortie (TC) | Images | Visuel | Transition | Ancrage sur la voix |
|---|---|---|---|---|---|---|---|
| 1 | P01 | 00:00:00 | 00:03:04 | 94 | mur_vide | coupe | début de la vidéo |
| 2 | P02 | 00:03:04 | 00:06:02 | 88 | crochets | coupe | phrase 1, mot « il » |
| 3 | P03 | 00:06:02 | 00:08:05 | 63 | joconde | coupe | début de la phrase 3 |
| 4 | P04 | 00:08:05 | 00:10:19 | 74 | soupcons | coupe | début de la phrase 4 |
| 5 | P05 | 00:10:19 | 00:14:08 | 109 | prison | coupe | début de la phrase 5 |
| 6 | P06 | 00:14:08 | 00:17:09 | 91 | empreinte | coupe | début de la phrase 7 |
| 7 | P07 | 00:17:09 | 00:21:00 | 111 | fichier | coupe | début de la phrase 8 |
| 8 | P08 | 00:21:00 | 00:25:01 | 121 | chambre | fondu 0,5 s (le plan précédent est prolongé de 0,5 s dessous) | début de la phrase 10 |
| 9 | P09 | 00:25:01 | 00:29:24 | 143 | carte | coupe | début de la phrase 12 |
| 10 | P10 | 00:29:24 | 00:33:24 | 120 | arrestation | coupe | début de la phrase 13 |
| 11 | P11 | 00:33:24 | 00:36:20 | 86 | vitrine | coupe | début de la phrase 15 |
| 12 | P12 | 00:36:20 | 00:40:19 | 119 | escalier | coupe | début de la phrase 16 |
| 13 | P13 | 00:40:19 | 00:44:15 | 116 | joconde_detail | coupe | début de la phrase 17 |
| 14 | P14 | 00:44:15 | 00:47:16 | 91 | mur_vide | coupe | début de la phrase 18 |

Total : 1426 images, soit 47,533 s. Le dernier plan (P14) finit au cadrage exact du premier (échelle 1,0, x 0, y 0) avec le même carton : la lecture en boucle de TikTok enchaîne sans saut.

## Placements

| Élément | Police | Taille | Position | Durée |
|---|---|---|---|---|
| Étiquette ARCHIVE / ILLUSTRATION / CARTE SCHÉMATIQUE | Oswald Bold, capitales espacées, pastille de couleur | 26 px | haut gauche, x 60, y 200, fond sombre 62 % | tout le plan |
| Légende d'œuvre (ARCHIVE) | EB Garamond | 30 px | x 60, y 264, fond sombre | tout le plan |
| Carton (6 mots maximum) | EB Garamond Bold, capitales | 50 px | centré, y 340, fond sombre 66 % | apparition 0,3 s après la coupe |
| Sous-titres | Oswald Bold, contour sombre 9 px | 66 px | centrés sur y 1300, une ligne, ≤ 27 caractères | calés mot à mot sur la voix |
| Carte : PARIS / FLORENCE | Oswald Bold | 46 px | positions projetées (Mercator) | « FLORENCE » sur le mot « Florence » |

## Pistes audio

| Piste | Fichier | Rôle |
|---|---|---|
| Voix | `livrables/pistes/voix.flac` | premier plan, filtre passe-haut 75 Hz, compression douce |
| Musique | `livrables/pistes/musique.flac` | à 20 dB sous la voix pendant la parole (sidechain) ; remonte, jusqu'à +12 dB, dans les silences |
| Bruitages | `livrables/pistes/bruitages.flac` | salle vide, porte, verre, tiroir, pas : discrets et justifiés par l'image |

Les trois pistes ont subi le même gain et le même limiteur que le master : **voix + musique + bruitages = master**, à l'échantillon près.

## Export

| Paramètre | Valeur |
|---|---|
| Vidéo | H.264 High, 1080 × 1920, 30 i/s constants, yuv420p, environ 9,2 Mb/s (rendu HyperFrames, qualité « delivery ») |
| Audio | AAC-LC 320 kb/s, 48 kHz, stéréo, encodé depuis le master PCM 24 bits |
| Loudness | −14 LUFS intégrés, crête vraie ≤ −1,5 dBTP (mesuré : voir le contrôle qualité) |
| Conteneur | MP4, `+faststart` |
| Version sans son | même flux vidéo, copié sans réencodage, piste audio retirée |

Commandes : voir `README.md` (chaîne complète, de `01_voix.py` à `make.sh`).
