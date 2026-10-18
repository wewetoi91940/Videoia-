# Étape 5 — Montage

> Généré par `scripts/06_dossier.py`. Composition : `index.html` (HyperFrames), générée par `scripts/05_composition.py`.

## Ordre, durées et transitions

| # | Plan | Entrée (TC) | Sortie (TC) | Images | Visuel | Transition | Ancrage sur la voix |
|---|---|---|---|---|---|---|---|
| 1 | P01 | 00:00:00 | 00:02:22 | 82 | mur_vide | coupe | début de la vidéo |
| 2 | P02 | 00:02:22 | 00:06:07 | 105 | crochets | coupe | phrase 1, mot « il » |
| 3 | P03 | 00:06:07 | 00:08:13 | 66 | joconde | coupe | début de la phrase 3 |
| 4 | P04 | 00:08:13 | 00:11:15 | 92 | beroud | coupe | début de la phrase 4 |
| 5 | P05 | 00:11:15 | 00:13:16 | 61 | photographe | coupe | début de la phrase 5 |
| 6 | P06 | 00:13:16 | 00:16:27 | 101 | escalier_vide | coupe | début de la phrase 6 |
| 7 | P07 | 00:16:27 | 00:20:27 | 120 | foule | coupe | début de la phrase 7 |
| 8 | P08 | 00:20:27 | 00:24:11 | 104 | juge | coupe | début de la phrase 8 |
| 9 | P09 | 00:24:11 | 00:27:26 | 105 | prison | coupe | début de la phrase 9 |
| 10 | P10 | 00:27:26 | 00:32:18 | 142 | empreinte | coupe | début de la phrase 11 |
| 11 | P11 | 00:32:18 | 00:35:05 | 77 | fichier | coupe | début de la phrase 12 |
| 12 | P12 | 00:35:05 | 00:37:06 | 61 | loupe | coupe | début de la phrase 13 |
| 13 | P13 | 00:37:06 | 00:41:16 | 130 | chambre | fondu 0,5 s (le plan précédent est prolongé de 0,5 s dessous) | début de la phrase 14 |
| 14 | P14 | 00:41:16 | 00:46:13 | 147 | carte | coupe | début de la phrase 16 |
| 15 | P15 | 00:46:13 | 00:50:22 | 129 | antiquaire | coupe | début de la phrase 17 |
| 16 | P16 | 00:50:22 | 00:54:11 | 109 | arrestation | coupe | début de la phrase 18 |
| 17 | P17 | 00:54:11 | 00:57:20 | 99 | vitrier | coupe | phrase 19, mot « vitrier » |
| 18 | P18 | 00:57:20 | 01:00:28 | 98 | vitrine | coupe | phrase 20, mot « vitrine » |
| 19 | P19 | 01:00:28 | 01:03:25 | 87 | escalier | coupe | phrase 21, mot « en » |
| 20 | P20 | 01:03:25 | 01:06:08 | 73 | escalier_vide | coupe | début de la phrase 22 |
| 21 | P21 | 01:06:08 | 01:09:17 | 99 | proces | coupe | début de la phrase 23 |
| 22 | P22 | 01:09:17 | 01:12:08 | 81 | joconde | coupe | début de la phrase 24 |
| 23 | P23 | 01:12:08 | 01:17:02 | 144 | retour | coupe | début de la phrase 25 |
| 24 | P24 | 01:17:02 | 01:21:01 | 119 | joconde_detail | coupe | début de la phrase 26 |
| 25 | P25 | 01:21:01 | 01:24:13 | 102 | mur_vide | coupe | début de la phrase 27 |

Total : 2533 images, soit 84,433 s. Le dernier plan (P14) finit au cadrage exact du premier (échelle 1,0, x 0, y 0) avec le même carton : la lecture en boucle de TikTok enchaîne sans saut.

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
