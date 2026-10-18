# Étape 7 — Contrôle qualité (mesuré)

> Généré par `scripts/07_controle.py` sur les fichiers **livrés** (`livrables/`).
> « Conforme » signifie mesuré et dans la règle. « À vérifier par une personne » signifie que la machine ne peut pas trancher.


## Format

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| 1080 × 1920 | 1080 × 1920, h264 High, yuv420p | **conforme** |  |
| 30 i/s constants | 30/1 (1426 images) | **conforme** |  |
| 35–50 s (cible 45 s) | 47,53 s | **conforme** |  |
| Audio et vidéo de même durée | vidéo 47,533 s, audio 47,533 s | **conforme** |  |
| Version sans son : aucune piste audio, même image | 1 flux (video), 1426 images | **conforme** |  |

## Structure

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Accroche 0–3 s : fait réel dès la 1re image, pas de « bonjour » | 1er sous-titre à 0,00 s (« Le 22 août 1911, »), carton P01 visible à 0 s, voix à 0,15 s | **conforme** |  |
| Question avant 8 s | fin de la phrase 3 à 7,55 s | **conforme** |  |
| 2 à 4 révélations | 3 révélations (fausse piste, empreinte, Florence) | **conforme** |  |
| Réponse avant 80 % de la durée | « Vincenzo » à 31,06 s = 65 % | **conforme** |  |
| Chute qui renvoie à l'accroche | phrase 18 reprend « quatre crochets » ; P14 réutilise l'image de P01 | **conforme** |  |
| Pas d'appel à s'abonner | 0 occurrence dans la voix off | **conforme** |  |

## Voix off

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| 120–135 mots | 133 mots | **conforme** |  |
| Phrases ≤ 15 mots | maximum 12 mots | **conforme** |  |
| Environ 5 syllabes/s | 4,92 syll./s (201 syllabes estimées, 40,8 s de parole) | **conforme** |  |
| Propos attribués | phrase 17 : « Pour beaucoup d'historiens, … » | **conforme** |  |
| Chiffres arrondis restés vrais | « près d'une semaine » (6 jours, F5) ; « plus de deux ans » (28 mois, F10) | **conforme** |  |
| Texte chronométré, coupes de secours | 18 phrases chronométrées ; coupes A, B, C | **conforme** |  |
| Écoute humaine : naturel, noms, liaisons | non faite (aucune écoute possible dans l'environnement de production) | **à vérifier par une personne** | Phonèmes vérifiés à l'écrit : « vingt-deux août » [vɛ̃tdøz‿ut], « Peruggia » [peʁudʒa]. |

## Exactitude

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| ≥ 1 source par fait, 2 pour dates et chiffres | 20 faits sourcés ; dates et chiffres à 2 sources ou plus | **conforme** |  |
| Incertitudes reformulées ou supprimées | 17 points d'incertitude, chacun avec sa décision | **conforme** |  |
| Sources lues seulement en extrait signalées | toutes les sources : lues en extrait (réseau limité) | **à vérifier par une personne** | Relire S1, S2, S4 et S9 avant publication. |

## Visuels

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Étiquette en haut à gauche sur chaque plan | 14 étiquettes pour 14 plans : ARCHIVE × 2, CARTE SCHÉMATIQUE × 1, ILLUSTRATION × 11 | **conforme** |  |
| Illustrations peintes, jamais de faux noir et blanc | saturation moyenne de 0,15 (soupcons) à 0,59 ; aucune image grise | **conforme** |  |
| Pas de faux document d'époque | fichier de police P07 : fiches vierges ; aucun texte dans les images | **conforme** |  |
| Pas de visage généré d'une personne réelle | personnes : silhouettes de dos uniquement (P04, P10, P12) | **à vérifier par une personne** | Vérifié sur le MP4 final (une image au milieu de chaque plan) ; à revoir image par image avant publication. |
| Œuvre réelle : reproduction authentique, « détail » si recadrée | P03 entière, P11 collée après peinture, P13 légende « (détail) » | **conforme** |  |
| Changement visuel toutes les 2–4 s | plans de 2,10 à 4,77 s ; au-dessus de 4 s : P09 4,77 s | **à vérifier par une personne** | P08 : fondu ; P09 : tracé de route, anneau et libellé animés à l'intérieur du plan. |
| Mouvements lents | zoom ≤ 2,9 %/s, translation ≤ 7,6 px/s | **conforme** |  |

## Textes

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Sous-titres : 1 ligne, ≤ 27 caractères | 39 lignes, max 27 caractères, `white-space: nowrap` | **conforme** |  |
| Sous-titres dans x 60–940 | largeur max 802 px, centrés sur x 500 → de 99 à 901 px | **conforme** |  |
| Taille 64–72 px, vers y = 1300 | 66 px, centrés sur y 1300 | **conforme** |  |
| Groupes de sens, lisibles | aucune fin de ligne sur un mot-outil ; durée min 0,65 s | **conforme** |  |
| Cartons ≤ 6 mots, en haut | 10 cartons, max 4 mots, y 340 | **conforme** |  |
| Zone x 60–940 / y 200–1440, pas de chevauchement (hyperframes check) | 3 tranches : 0 problème de mise en page, 0 erreur d'exécution ou de mouvement | **conforme** |  |
| Contraste lisible (WCAG AA) | 37/37 textes conformes | **conforme** |  |

## Son

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Export −14 LUFS | -14,0 LUFS intégrés (fichier MP4 final, ffmpeg ebur128) | **conforme** |  |
| Crête ≤ −1,5 dBFS (crête vraie) | -1,6 dBTP | **conforme** |  |
| Musique ≥ 15 dB sous la voix pendant la parole (viser 20) | écart moyen 20,6 dB ; fenêtres de 400 ms : médiane 18,9 dB, min 15,5 dB, 0 % sous 15 dB | **conforme** |  |
| La musique remonte dans les silences | -34,2 LUFS pendant la parole → -26,4 LUFS dans les silences (+7,8 dB) | **conforme** |  |
| Pistes séparées = master | écart max entre la somme voix + musique + bruitages et le master : -132 dBFS | **conforme** |  |
| Voix au premier plan, bruitages discrets | pendant la parole, bruitages sous la voix de 21,6 dB (médiane) et 13,6 dB au minimum (112 fenêtres de 400 ms) | **conforme** |  |
| Musique libre de droits | composée et synthétisée par code (scripts/04_audio.py) : aucun échantillon tiers | **conforme** |  |

## Montage

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Lint HyperFrames sans erreur | 0 erreur, 18 avertissements (duplicate_media_discovery_risk, nested_structure_needs_subcomposition, timeline_track_too_dense) | **conforme** | Avertissements d'organisation pour Studio ; l'image du mur est réutilisée exprès en P01 et P14 (boucle). |
| Coupe franche par défaut, fondu seulement pour un saut dans le temps | 12 coupes, 1 fondu (P08 : 1911 → 1913) | **conforme** |  |
| Aucun gadget | animations : caméra lente, apparitions en fondu ; courbes utilisées : power1.in, power1.inOut, power2.out, sine.inOut | **conforme** |  |
| Le dernier plan s'enchaîne avec le premier (boucle) | première et dernière image hors sous-titres : écart moyen 1,41/255, 0,12 % de pixels > 8 | **conforme** |  |
| Image calée sur la voix réelle | 12 coupes mesurées dans la vidéo ; écart max +17 ms (P06) | **conforme** |  |

## Livrables

| Règle | Mesure | Résultat | Note |
|---|---|---|---|
| Fichiers livrés | 8/8 présents | **conforme** |  |

## Synchronisation : coupes mesurées dans la vidéo et voix

| Plan | Écart coupe − mot d'ancrage |
|---|---|
| P02 | -7 ms |
| P03 | +14 ms |
| P04 | +13 ms |
| P05 | -12 ms |
| P06 | +17 ms |
| P07 | -16 ms |
| P09 | +4 ms |
| P10 | +0 ms |
| P11 | -1 ms |
| P12 | +11 ms |
| P13 | +5 ms |
| P14 | +1 ms |

Une image dure 33 ms : un écart sous ±34 ms tombe dans l'image où commence le mot.

## Reste à faire avant de publier

1. **Écouter la vidéo en entier** (casque et haut-parleur de téléphone) : naturel de la voix de synthèse, « Vincenzo Peruggia », « vingt-deux août », équilibre voix / musique / bruitages. Rien n'a pu être écouté pendant la production.
2. **Relire les sources S1, S2, S4 et S9** (`docs/01_recherche.md`) et cocher la colonne « relu ». En particulier, confirmer dans S2 la date du 21 août affichée en P12.
3. **Provenance de la reproduction** : remplacer `assets/oeuvre/joconde-reproduction.jpg` par le fichier C2RMF de Wikimedia Commons ou par une image du Louvre, puis relancer `./make.sh visuels composition rendu livrables dossier`.
4. **Contrôle visuel** de la vidéo finale image par image sur P04, P10 et P12 (silhouettes) : aucun visage ne doit être lisible.
5. Facultatif : remplacer des illustrations par de vraies archives (`docs/04_generation.md`, dernière section).
6. À la publication : activer l'étiquette « Contenu généré par l'IA » et coller la description et le commentaire épinglé de `docs/06_publication.md`.
