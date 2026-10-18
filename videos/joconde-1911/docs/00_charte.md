# Charte du projet : mini-documentaires d'histoire pour TikTok

Cette charte vaut pour chaque épisode. La colonne « Contrôle » indique comment chaque règle est vérifiée par `scripts/07_controle.py` ou, à défaut, par une personne.

## 1. Format

| Règle | Contrôle |
|---|---|
| 1080 × 1920, 30 i/s | ffprobe sur le MP4 livré |
| **60 à 85 s** (au moins 1 minute, demande du 18/10 ; 35–50 s dans la v1) | ffprobe |
| Une histoire, une question | lecture du script |

## 2. Structure

| Règle | Contrôle |
|---|---|
| Accroche 0–3 s : un fait réel montré dès la première image, sans « bonjour » | 1er sous-titre à 0 s, carton visible à 0 s |
| Question posée avant 8 s | fin de la phrase « question » < 8 s |
| 2 à 4 révélations | rôles du script |
| Réponse avant 80 % de la durée | début du mot-réponse / durée |
| Chute qui renvoie à l'accroche (boucle) | même image en ouverture et en fermeture, écart de pixels mesuré |
| Pas d'appel à s'abonner | recherche de mots dans le script |

## 3. Voix off

| Règle | Contrôle |
|---|---|
| Français oral, phrases ≤ 15 mots, un fait par phrase | décompte automatique |
| Environ 5 syllabes/s, environ 3 mots par seconde de parole | décompte et chronologie réelle |
| Voix naturelle : voix Google (Gemini TTS), consigne de narrateur de documentaire ; Kokoro seulement en brouillon de calage, jamais livré | champ `brouillon` de `build/chronologie.json` |
| Propos attribués (« pour beaucoup d'historiens »…) | lecture |
| Chiffres arrondis seulement s'ils restent vrais | renvoi au tableau des faits |
| Texte chronométré, coupes de secours prévues | `scripts/script.json` |
| Écoute de la voix, des noms et des liaisons | **personne** |

## 4. Exactitude

| Règle | Contrôle |
|---|---|
| Au moins une source par fait ; deux pour chaque date et chaque chiffre | tableau des faits (`docs/01_recherche.md`) |
| Point incertain : reformulé ou supprimé | tableau des incertitudes |
| Sources lues seulement en extrait : signalées | colonne « Lecture » |
| Confusions possibles : repérées | § 4 de la recherche, réponses prêtes (`docs/06_publication.md`) |

## 5. Visuels

| Règle | Contrôle |
|---|---|
| Étiquette en haut à gauche : **ARCHIVE**, **ILLUSTRATION** ou **CARTE SCHÉMATIQUE** | une étiquette par plan |
| Illustration : style peint ; jamais de faux noir et blanc ni de faux grain d'archive | saturation mesurée de chaque image |
| Carte : construite depuis de vraies données, sans frontière anachronique | `scripts/03_carte.py` : terres seules |
| Jamais de faux document d'époque | lecture des instructions de génération, contrôle visuel |
| Jamais de visage généré d'une personne réelle : silhouette, dos, mains ou ombre | **personne** (contrôle visuel) |
| Œuvre réelle jamais générée : reproduction authentique, « détail » si recadrée | légendes |
| Changement visuel toutes les 2 à 4 s, mouvements lents | durée des plans, vitesse de caméra |

## 6. Textes à l'écran

| Règle | Contrôle |
|---|---|
| Tout dans la zone x 60–940, y 200–1440 | `hyperframes check` (mise en page) + calcul des largeurs |
| Sous-titres : une ligne, ≤ 27 caractères, groupes de sens, 64–72 px, vers y = 1300 ; apostrophe typographique (’) | `scripts/05_composition.py` (découpe optimale, mots-outils jamais en fin de ligne, nom propre jamais coupé) |
| Aucun texte posé sur une œuvre réelle (hors sous-titres) | instantanés de contrôle |
| Cartons : ≤ 6 mots, en haut, une ligne | décompte |
| Contraste lisible | `hyperframes check` (WCAG AA) |

## 7. Son

| Règle | Contrôle |
|---|---|
| Voix au premier plan | bruitages ≥ 12 dB sous la voix pendant la parole |
| Musique ≥ 15 dB sous la voix pendant la parole (viser 20 dB), qui remonte dans les silences | mesures BS.1770 par fenêtres de 400 ms |
| Musique libre de droits ; bruitages discrets et justifiés par l'image | musique et bruitages synthétisés par code |
| Export −14 LUFS, crête ≤ −1,5 dBFS (crête vraie) | ffmpeg ebur128 sur le MP4 livré |

## 8. Montage

| Règle | Contrôle |
|---|---|
| Coupe franche par défaut ; fondu seulement pour un saut dans le temps ; 2 types de transition au maximum | `scripts/plans.json` |
| Aucun gadget (pas de secousse, de rebond, de glitch, de zoom brutal) | courbes d'animation utilisées |
| Le dernier plan s'enchaîne avec le premier | écart de pixels entre la première et la dernière image |
| Image calée sur la voix réelle | coupes détectées dans la vidéo comparées aux mots d'ancrage |

## 9. Production

- **Crédits** : prévenir avant toute dépense (générateur d'images payant, voix payante, banque d'images).
- **Fichiers** : ne rien supprimer sans avoir vérifié son contenu.
- **Outil bloqué** : trouver une autre solution sans s'arrêter, puis noter ce qui a changé et pourquoi.
- **Transparence** : mention « voix de synthèse / illustrations générées » dans la description, et étiquette TikTok « Contenu généré par l'IA ».
- **Livrables** : vidéo finale ; version sans son ; pistes séparées (voix, musique, bruitages) dont la somme donne le master ; sous-titres SRT ; cartes ; dossier (étapes 1 à 7) ; scripts.
