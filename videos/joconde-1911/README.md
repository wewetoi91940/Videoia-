# Le vol de la Joconde (1911) : mini-documentaire TikTok

Vidéo verticale (1080 × 1920, 30 i/s). Question : *Qui a pu sortir la Joconde du Louvre ?*
Tout est produit par une chaîne de scripts reproductible, sans générateur payant et sans crédit consommé.

## État actuel

| Version | Contenu | Statut |
|---|---|---|
| v1 | 47,5 s, voix Kokoro | **livrée** dans `livrables/` (voix jugée trop robotique) |
| v2 | environ 80 s, 27 phrases, 25 plans, erreurs de la v1 corrigées (`docs/01_recherche.md` § 6), **voix Google (Gemini TTS)** | chaîne prête et contrôlée sur un brouillon de calage ; **voix Google à générer** (clé requise) |

### Reprise : générer la v2 avec la voix Google

1. Créer une clé gratuite sur Google AI Studio (aistudio.google.com/apikey).
2. L'ajouter aux secrets de l'environnement cloud sous le nom **`GEMINI_API_KEY`** (menu de l'environnement → Edit → *Network secrets*, ou variable d'environnement). Ne jamais la coller dans un fichier ni dans le chat.
3. Dans une nouvelle session :
   ```bash
   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
   PY=.venv/bin/python ./make.sh voix audio composition check rendu livrables dossier
   ```
   La voix est synthétisée phrase par phrase, avec un cache : une phrase inchangée n'est pas régénérée, ce qui ménage le quota gratuit. Les temps des plans, les sous-titres, le mixage et le dossier suivent automatiquement la voix réelle.
4. Lire `docs/07_controle_qualite.md` : le point « Voix naturelle livrée » doit être conforme, et la question doit se terminer avant 8 s.

**Voix** (`scripts/script.json` → `voix`) : `Charon` (masculine, grave et posée) avec le modèle `gemini-3.8-flash-tts` et une consigne de narrateur de documentaire.
Si le modèle est refusé (accès ou quota du niveau gratuit), mettre `"modele": "gemini-2.5-flash-preview-tts"` : les phrases déjà générées restent en cache.
Autres voix Google à essayer en changeant un seul mot : `Kore` (féminine, ferme), `Orus` (masculine, ferme), `Sadaltager` (posée, savante), `Gacrux` (mûre).
Sans clé, l'étape `voix` s'arrête : il n'y a aucun repli silencieux sur la voix robotique. `VOIX_BROUILLON=1` ne sert qu'à caler un montage, et `make.sh livrables` refuse d'écraser la vidéo livrée avec un brouillon.

## Livrables (`livrables/`)

| Fichier | Contenu |
|---|---|
| `joconde-1911.mp4` | Vidéo finale (v1 pour l'instant) : image, voix, musique, bruitages, sous-titres incrustés. −14 LUFS, crête vraie −1,6 dBTP |
| `joconde-1911_sans-son.mp4` | Même image (flux copié à l'identique), sans piste audio |
| `joconde-1911.srt` | Sous-titres (une ligne chacune, ≤ 27 caractères) |
| `pistes/voix.flac`, `pistes/musique.flac`, `pistes/bruitages.flac` | Pistes séparées, 48 kHz, 24 bits. Leur somme donne exactement le master |
| `cartes/` | Carte Paris → Florence : PNG (fond peint), SVG (vectoriel, avec les villes), JSON (sources et coordonnées) |

## Dossier de production (`docs/`)

| Fichier | Étape |
|---|---|
| `00_charte.md` | Charte du projet, avec le mode de contrôle de chaque règle |
| `01_recherche.md` | 1. Sources, tableau des faits, tableau des incertitudes, confusions possibles |
| `02_script.md` | 2. Script chronométré sur la voix réelle, rôles, consignes de lecture, prononciation, coupes de secours |
| `03_storyboard.md` | 3. Storyboard plan par plan : temps, voix off exacte, visuel, caméra, textes, transition, son |
| `04_generation.md` | 4. Instructions de génération autonomes par plan (bloc de style, liste « à éviter », carte construite depuis des données) |
| `05_montage.md` | 5. Montage : ordre, durées, transitions, placements, pistes, export |
| `06_publication.md` | 6. Titres, description, hashtags, question, sources à épingler, mentions IA, réponses prêtes |
| `07_controle_qualite.md` | 7. Contrôle qualité **mesuré** sur les fichiers livrés |

Les fichiers 02, 03, 05 et 07 sont **générés** à partir des données réelles. Il ne faut pas les éditer à la main : il faut relancer `./make.sh dossier`.

## Chaîne de production

```
scripts/script.json ──▶ 01_voix.py (+ voix_gemini.mjs : Google Gemini TTS) ──▶ build/voix.wav + build/chronologie.json
scripts/plans.json  ──▶ chrono.py : plans calés sur les mots de la voix, arrondis à l'image
                         02_illustrations.py + peinture.py ──▶ assets/illustrations/*.png (peintes par code)
                         02b_oeuvre.py ──▶ plans de l'œuvre (reproduction authentique, recadrage « détail »)
                         03_carte.py ──▶ assets/cartes/ (Natural Earth, Mercator, sans frontières)
                         04_audio.py ──▶ musique + bruitages synthétisés, ducking, −14 LUFS ──▶ build/mix_master.wav, build/stems/
                         05_composition.py ──▶ index.html (HyperFrames) + sous-titres + SRT
                         hyperframes lint / check / render ──▶ renders/
                         make.sh livrables ──▶ livrables/
                         06_dossier.py, 07_controle.py ──▶ docs/02, 03, 05, 07
```

### Installation

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
npx --yes hyperframes@0.8.166 tts "test" -v ff_siwis   # télécharge le modèle Kokoro dans ~/.cache/hyperframes/tts (une fois)
PY=.venv/bin/python ./make.sh                           # tout ; ou par étapes : ./make.sh audio composition rendu livrables dossier
```

Prérequis : Node ≥ 22, ffmpeg. Le rendu dure environ 4 min sur CPU.

### Réutiliser pour un autre épisode

1. Copier le dossier. Réécrire `scripts/script.json` (phrases, rôles, consignes de lecture, coupes de secours) et `scripts/plans.json` (un plan par visuel, ancré sur un mot de la voix).
2. Écrire les scènes dans `scripts/02_illustrations.py`. Les outils `silhouette`, `gilt_frame`, `light` et `finish` sont réutilisables.
3. Adapter `CITIES` et `TARGET` dans `scripts/03_carte.py`.
4. Lancer `./make.sh`, puis lire `docs/07_controle_qualite.md` : chaque écart y est mesuré.

## Outils bloqués et solutions de remplacement

| Blocage | Solution retenue | Conséquence |
|---|---|---|
| Réseau limité à GitHub, npm et PyPI : pages web impossibles à ouvrir | Recherche par extraits du moteur de recherche | Toutes les sources sont marquées « lues en extrait » ; à relire avant publication |
| Wikimedia Commons inaccessible | Reproduction de la Joconde prise dans un gist GitHub public (`git clone`) | Provenance de la photographie à confirmer, ou fichier à remplacer (même cadrage) |
| Générateur d'images Canva disponible, mais payant en crédits | **Non utilisé**, faute d'accord sur les crédits. Illustrations peintes par code | Rendu plus simple qu'un modèle d'image, mais reproductible et sans visage |
| Pas de bibliothèque musicale ni de banque de bruitages accessible | Musique et bruitages composés et synthétisés en Python | Aucun droit tiers |
| Paquet Kokoro absent du système | Environnement Python dédié (`kokoro-onnx` depuis PyPI) | Voix locale de la v1, jugée trop robotique |
| Voix Google demandée (v2), mais aucune clé Google valide dans l'environnement | Chaîne branchée sur Gemini TTS via le module `media-use` de HyperFrames ; la clé reste à ajouter comme secret | La v2 attend la voix ; tout le reste (script, visuels, montage, son, contrôles) est prêt |
| Flow (Google) n'a pas d'API de voix | Gemini TTS : même famille de voix génératives Google | — |
| Kokoro ne donne pas l'horodatage des mots | Synthèse phrase par phrase, puis mots répartis au prorata des phonèmes et recalés sur les silences réels | Sous-titres calés sur la voix (vérifié en image) |
| CDN jsDelivr bloqué | Données cartographiques récupérées par `npm pack world-atlas@2.0.2` | — |
| `hyperframes check` limité à 120 s par appel | Contrôle par tranches de 16 s (`--range`) | Couverture complète conservée |

## Corrections de la version 2 (demande du 18/10)

Voix Google au lieu de Kokoro ; vidéo d'au moins 1 minute ; erreurs E1 à E7 corrigées (détail dans `docs/01_recherche.md` § 6) :
Apollinaire incarcéré par un juge (et non « soupçonné par la police »), scène de rue non documentée supprimée, apostrophes typographiques,
œuvre jamais recouverte par un carton, noms propres jamais coupés dans les sous-titres, 10 nouvelles scènes (découverte, foule, juge, loupe,
antiquaire, vitrier, procès, retour…), musique et bruitages pilotés par des repères (`plans.json` → `musique`, `bruitage`, `cloche`).

## Corrections faites pendant le contrôle qualité de la v1

- **Sous-titres** : découpe optimale par programmation dynamique. Aucune fin de ligne sur un mot-outil, et chaque ligne dure au moins 0,64 s.
- **Cartons** : ajout d'un fond sombre, car « PRISON DE LA SANTÉ » et « LUNDI 21 AOÛT 1911 » passaient sur des fenêtres claires. Les cartons longs restent sur une ligne.
- **Raccords P03 et P04** : ils arrivaient une image trop tard (arrondi de `data-start` vers le haut). Les débuts de plans sont maintenant tronqués à l'image ; écart mesuré ≤ 17 ms.
- **Bruitages** : la porte de cellule (P05) couvrait « Il passe près d'une semaine » (−0,9 dB d'écart). Les bruitages passent désormais sous la voix pendant la parole : écart minimal de 13,6 dB.
