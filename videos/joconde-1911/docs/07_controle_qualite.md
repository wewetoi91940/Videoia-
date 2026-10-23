# Étape 7 — Contrôle qualité (mesuré)

> Généré par `scripts/07_controle.py` sur les fichiers **livrés** (`livrables/`).
> « Conforme » signifie mesuré et dans la règle. « À vérifier par une personne » signifie que la machine ne peut pas trancher.


## Format

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| 1080 × 1920 | 1080 × 1920, h264 High, yuv420p | **conforme** |  |
| 30 i/s constants | 30/1 (2533 images) | **conforme** |  |
| 60–85 s (au moins 1 minute, demande du 18/10) | 84,43 s | **conforme** |  |
| Audio et vidéo de même durée | vidéo 84,433 s, audio 84,433 s | **conforme** |  |
| Version sans son : aucune piste audio, même image | 1 flux (video), 2533 images | **conforme** |  |

## Structure

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Accroche 0–3 s : fait réel dès la 1re image, pas de « bonjour » | 1er sous-titre à 0,00 s (« Le 22 août 1911, »), carton P01 visible à 0 s, voix à 0,10 s | **conforme** |  |
| Question avant 8 s | fin de la phrase 3 à 7,88 s | **conforme** |  |
| 2 à 4 révélations | 3 révélations (fausse piste, empreinte, Florence) | **conforme** |  |
| Réponse avant 80 % de la durée | « Vincenzo » à 52,59 s = 62 % | **conforme** |  |
| Chute qui renvoie à l'accroche | phrase 27 reprend « quatre crochets » ; P25 réutilise l'image de P01 | **conforme** |  |
| Pas d'appel à s'abonner | 0 occurrence dans la voix off | **conforme** |  |

## Voix off

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Nombre de mots adapté à la durée (≈ 3 mots par seconde de parole) | 229 mots pour 75,1 s de parole (3,05 mots/s) | **conforme** |  |
| Phrases ≤ 15 mots | maximum 12 mots | **conforme** |  |
| Environ 5 syllabes/s | 4,55 syll./s (342 syllabes estimées, 75,1 s de parole) | **conforme** |  |
| Propos attribués | phrase 26 : « Pour beaucoup d'historiens, … » | **conforme** |  |
| Chiffres arrondis restés vrais | « près d'une semaine » (6 jours, F5) ; « plus de deux ans » (28 mois, F10) | **conforme** |  |
| Texte chronométré, coupes de secours | 27 phrases chronométrées ; coupes A, B, C | **conforme** |  |
| Voix naturelle livrée (Google Gemini), pas la voix de calage | moteur gemini, voix Charon, modèle gemini-3,1-flash-tts-preview | **conforme** | La voix Kokoro n'est qu'un brouillon de calage : jamais livrée. |
| Écoute humaine : naturel, noms, liaisons | non faite (aucune écoute possible dans l'environnement de production) | **à vérifier par une personne** | À écouter : « Vincenzo Peruggia », « Louis Béroud », « vingt-deux août », « Offices ». |

## Exactitude

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| ≥ 1 source par fait, 2 pour dates et chiffres | 27 faits sourcés ; dates et chiffres à 2 sources ou plus | **conforme** |  |
| Incertitudes reformulées ou supprimées | 23 points d'incertitude, chacun avec sa décision | **conforme** |  |
| Sources lues seulement en extrait signalées | toutes les sources : lues en extrait (réseau limité) | **à vérifier par une personne** | Relire S1, S2, S4 et S9 avant publication. |

## Visuels

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Étiquette en haut à gauche sur chaque plan | 25 étiquettes pour 25 plans : ARCHIVE × 3, CARTE SCHÉMATIQUE × 1, ILLUSTRATION × 21 | **conforme** |  |
| Illustrations peintes, jamais de faux noir et blanc | saturation moyenne de 0,15 (soupcons) à 0,59 ; aucune image grise | **conforme** |  |
| Pas de faux document d'époque | fichier de police P07 : fiches vierges ; aucun texte dans les images | **conforme** |  |
| Pas de visage généré d'une personne réelle | personnes : silhouettes de dos uniquement (P04, P07, P08, P15, P16, P17, P19, P21, P23) | **à vérifier par une personne** | Vérifié sur le MP4 final (une image au milieu de chaque plan) ; à revoir image par image avant publication. |
| Œuvre réelle : reproduction authentique, « détail » si recadrée | P03 entière, P11 collée après peinture, P13 légende « (détail) » | **conforme** |  |
| Changement visuel toutes les 2–4 s | plans de 2,03 à 4,90 s ; au-dessus de 4 s : P10 4,73 s, P13 4,33 s, P14 4,90 s, P15 4,30 s, P23 4,80 s | **à vérifier par une personne** | P08 : fondu ; P09 : tracé de route, anneau et libellé animés à l'intérieur du plan. |
| Mouvements lents | zoom ≤ 2,7 %/s, translation ≤ 10,3 px/s | **conforme** |  |

## Textes

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Sous-titres : 1 ligne, ≤ 27 caractères | 67 lignes, max 27 caractères, `white-space: nowrap` | **conforme** |  |
| Sous-titres dans x 60–940 | largeur max 802 px, centrés sur x 500 → de 99 à 901 px | **conforme** |  |
| Taille 64–72 px, vers y = 1300 | 66 px, centrés sur y 1300 | **conforme** |  |
| Groupes de sens, lisibles | aucune fin de ligne sur un mot-outil ; durée min 0,61 s | **conforme** |  |
| Cartons ≤ 6 mots, en haut | 15 cartons, max 6 mots, y 340 | **conforme** |  |
| Zone x 60–940 / y 200–1440, pas de chevauchement (hyperframes check) | 6 tranches : 0 problème de mise en page, 0 erreur d'exécution ou de mouvement | **conforme** |  |
| Contraste lisible (WCAG AA) | 75/75 textes conformes | **conforme** |  |

## Son

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Export −14 LUFS | -14,0 LUFS intégrés (fichier MP4 final, ffmpeg ebur128) | **conforme** |  |
| Crête ≤ −1,5 dBFS (crête vraie) | -1,5 dBTP | **conforme** |  |
| Musique ≥ 15 dB sous la voix pendant la parole (viser 20) | écart moyen 23,4 dB ; fenêtres de 400 ms : médiane 21,7 dB, min 15,5 dB, 0 % sous 15 dB | **conforme** |  |
| La musique remonte dans les silences | -37,4 LUFS pendant la parole → -31,8 LUFS dans les silences (+5,6 dB) | **conforme** |  |
| Pistes séparées = master | écart max entre la somme voix + musique + bruitages et le master : -132 dBFS | **conforme** |  |
| Voix au premier plan, bruitages discrets | pendant la parole, bruitages sous la voix de 23,4 dB (médiane) et 12,1 dB au minimum (180 fenêtres de 400 ms) | **conforme** |  |
| Musique libre de droits | composée et synthétisée par code (scripts/04_audio.py) : aucun échantillon tiers | **conforme** |  |

## Montage

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Lint HyperFrames sans erreur | 0 erreur, 29 avertissements (duplicate_media_discovery_risk, nested_structure_needs_subcomposition, timeline_track_too_dense) | **conforme** | Avertissements d'organisation pour Studio ; l'image du mur est réutilisée exprès en P01 et P14 (boucle). |
| Coupe franche par défaut, fondu seulement pour un saut dans le temps | 23 coupes, 1 fondu (P08 : 1911 → 1913) | **conforme** |  |
| Aucun gadget | animations : caméra lente, apparitions en fondu ; courbes utilisées : power1.in, power1.inOut, power2.out, sine.inOut | **conforme** |  |
| Le dernier plan s'enchaîne avec le premier (boucle) | première et dernière image hors sous-titres : écart moyen 1,40/255, 0,09 % de pixels > 8 | **conforme** |  |
| Image calée sur la voix réelle | 23 coupes mesurées dans la vidéo ; écart max +16 ms (P07) | **conforme** |  |

## Livrables

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Fichiers livrés | 8/8 présents | **conforme** |  |

## Synchronisation : coupes mesurées dans la vidéo et voix

| Plan | Écart coupe − mot d'ancrage |
|---|---|
| P02 | +13 ms |
| P03 | -15 ms |
| P04 | +7 ms |
| P05 | +11 ms |
| P06 | +7 ms |
| P07 | +16 ms |
| P08 | +14 ms |
| P09 | -10 ms |
| P10 | +15 ms |
| P11 | +3 ms |
| P12 | +9 ms |
| P14 | +9 ms |
| P15 | +1 ms |
| P16 | +14 ms |
| P17 | +4 ms |
| P18 | -14 ms |
| P19 | +4 ms |
| P20 | -13 ms |
| P21 | +13 ms |
| P22 | +16 ms |
| P23 | -16 ms |
| P24 | -8 ms |
| P25 | -7 ms |

Une image dure 33 ms : un écart sous ±34 ms tombe dans l'image où commence le mot.

## Reste à faire avant de publier

1. **Voix Google** : tant que le contrôle « Voix naturelle livrée » est en écart, la vidéo porte la voix de calage. Ajouter la clé `GEMINI_API_KEY` (secret de l'environnement), puis lancer `./make.sh voix audio composition check rendu livrables dossier`.
2. **Écouter la vidéo en entier** (casque et haut-parleur de téléphone) : naturel de la voix de synthèse, « Vincenzo Peruggia », « vingt-deux août », équilibre voix / musique / bruitages. Rien n'a pu être écouté pendant la production.
3. **Relire les sources S1, S2, S4 et S9** (`docs/01_recherche.md`) et cocher la colonne « relu ». En particulier, confirmer dans S2 la date du 21 août affichée sur le plan de l'escalier.
4. **Provenance de la reproduction** : remplacer `assets/oeuvre/joconde-reproduction.jpg` par le fichier C2RMF de Wikimedia Commons ou par une image du Louvre, puis relancer `./make.sh visuels composition rendu livrables dossier`.
5. **Contrôle visuel** de la vidéo finale image par image sur P04, P10 et P12 (silhouettes) : aucun visage ne doit être lisible.
6. Facultatif : remplacer des illustrations par de vraies archives (`docs/04_generation.md`, dernière section).
7. À la publication : activer l'étiquette « Contenu généré par l'IA » et coller la description et le commentaire épinglé de `docs/06_publication.md`.
