# Marseille, 17 octobre : du Prado à Saint-Ferréol, la journée où le centre-ville a basculé

Documentaire narré, 16:9 (1920 × 1080, 30 i/s), environ 8 à 9 minutes. État des connaissances : lundi 19 octobre 2026.
Toute la vidéo est produite par une chaîne de scripts reproductible, sans image d'actualité sous droits.

## Ce que montre la vidéo

- **Cartes** du centre de Marseille construites depuis OpenStreetMap (`scripts/02_carte.py`) : rues et lieux pris par leur nom,
  **aucun parcours inventé** (pas de flèches), la « zone » des pillages est l'union des tronçons des rues citées par la presse.
- **Cartons d'heure** avec un statut explicite : heure publiée, heure d'une entrée de direct (le fait peut être antérieur),
  période approximative, heure prévue, heure donnée par une seule source.
- **Horloge du samedi** (6 h → 3 h) en haut à droite : seules des heures publiées y figurent.
- **Sources à l'écran** pour chaque phrase (bas à droite), citations attribuées, chiffres contradictoires côte à côte.
- **Photos libres des lieux** (Wikimedia Commons), toujours étiquetées « le lieu en temps normal ».

## Recherche

| Fichier | Contenu |
|---|---|
| `docs/00_dossier_initial.md` | Premier dossier (extraits de moteur de recherche) : historique, en partie corrigé |
| `docs/01_verification_sources.md` | **Vérification fait par fait** sur plus de 60 articles lus en entier : sources, verdicts, contradictions, heures publiées |
| `scripts/script.json` | Texte de la voix off (70 phrases, 12 séquences), avec les sources de chaque phrase |
| `scripts/plans_source.py` → `scripts/plans.json` | Plan de montage : 57 plans ancrés sur des mots de la voix |
| `docs/06_publication.md` | Titre, description, chapitres, sources, mentions IA |
| `docs/07_controle_qualite.md` | Contrôle qualité **mesuré** |

Règles suivies : aucune heure inventée ; heure d'événement et heure de publication distinguées ; estimations officielles
attribuées ; aucune personne privée identifiable ; robots.txt respecté (France 3, franceinfo, France 24, BFMTV, Le Monde,
TF1 Info et Ouest-France refusent l'agent « Claude-User » : aucun de leurs articles n'est utilisé comme source).

## Fabriquer la vidéo

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PY=.venv/bin/python ./make.sh osm          # une fois : données OpenStreetMap (build/osm/, non versionné)
PY=.venv/bin/python ./make.sh              # carte voix composition audio check rendu livrables controle
```

### Voix Google (Gemini TTS)

La voix livrée est `Charon` (modèle `gemini-3.1-flash-tts-preview`), synthétisée **par séquences** : 8 requêtes en tout
(le niveau gratuit en autorise environ 10 par jour et par modèle). Chaque bloc est ensuite redécoupé en phrases sur ses silences
réels ; le montage, les sous-titres et la musique suivent la voix réelle.

La clé n'est **jamais** écrite dans un fichier ni collée dans une conversation. Deux façons de la fournir :

1. **Network secret** de l'environnement cloud (recommandé) : *Edit cloud environment* → *Network secrets* → *Add secret*,
   hôte `generativelanguage.googleapis.com`, en-tête `x-goog-api-key` sans préfixe. La clé reste hors de la session.
   Lancer alors `GEMINI_API_KEY=proxy-injected PY=.venv/bin/python ./make.sh voix composition audio check rendu livrables controle`
   (la valeur `proxy-injected` sert seulement à passer le contrôle de présence : le proxy remplace l'en-tête).
2. Variable d'environnement `GEMINI_API_KEY` de l'environnement.

`VOIX_BROUILLON=1 ./make.sh voix …` produit une voix Kokoro de **calage** (montage, durées) ; `make.sh livrables` refuse de la livrer.

## Livrables (`livrables/`)

| Fichier | Contenu |
|---|---|
| `marseille-17-octobre.mp4` | Vidéo finale, H.264 + AAC, −14 LUFS, crête vraie ≤ −1,5 dBTP |
| `marseille-17-octobre_sans-son.mp4` | Même image, sans son |
| `marseille-17-octobre.srt` | Sous-titres (2 lignes de 42 caractères au plus) |
| `pistes/voix.flac` | Voix seule, au niveau du mix |

## Outils bloqués et solutions retenues

| Blocage | Solution | Conséquence |
|---|---|---|
| WebFetch en panne dans l'environnement (DNS) | Lecture des pages par `curl` après vérification du robots.txt pour « Claude-User » | Sites qui refusent : extraits de recherche seulement, jamais utilisés comme source unique |
| Overpass principal (overpass-api.de) injoignable | Miroir `maps.mail.ru` | Données OSM du 19/10/2026 |
| Wikimedia Commons : `/w/api.php` interdit par robots.txt | Pages `/wiki/File:` et `upload.wikimedia.org` seulement | Recherche de photos plus lente |
| Clé Gemini non transmise à la session | Chaîne prête ; voix de calage Kokoro pour le montage | La voix Google se génère dès que la clé est disponible |
| Images d'actualité (AFP, BFMTV, France 3…) sous droits | Cartes, cartons, photos libres des lieux | Aucune image des événements |
