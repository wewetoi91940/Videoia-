#!/usr/bin/env bash
# Chaîne complète « joconde-1911 » : voix → visuels → carte → audio → composition → contrôles → rendu → livrables → dossier.
# Usage : ./make.sh [étape...]   étapes : voix visuels carte audio composition check rendu livrables dossier (défaut : toutes)
# Python : PY=/chemin/vers/venv/bin/python ./make.sh   (dépendances : requirements.txt ; ffmpeg et Node ≥ 22 requis)
set -euo pipefail
cd "$(dirname "$0")"

PY="${PY:-python3}"
HF="npx --yes hyperframes@0.8.166"
ETAPES=("$@")
[ ${#ETAPES[@]} -eq 0 ] && ETAPES=(voix visuels carte audio composition check rendu livrables dossier)
veut() { [[ " ${ETAPES[*]} " == *" $1 "* ]]; }
titre() { printf '\n== %s\n' "$1"; }

if veut voix; then
  titre "Voix off (Kokoro, ff_siwis) → build/voix.wav, build/chronologie.json"
  "$PY" scripts/01_voix.py
fi
if veut visuels; then
  titre "Illustrations peintes par code + plans de l'œuvre (reproduction authentique)"
  "$PY" scripts/02_illustrations.py
  "$PY" scripts/02b_oeuvre.py
fi
if veut carte; then
  titre "Carte schématique (Natural Earth, sans frontières)"
  "$PY" scripts/03_carte.py
fi
if veut audio; then
  titre "Musique, bruitages, mixage −14 LUFS → build/mix_master.wav, build/stems/"
  "$PY" scripts/04_audio.py
fi
if veut composition; then
  titre "Composition HyperFrames + sous-titres (index.html, SRT)"
  "$PY" scripts/05_composition.py > /dev/null
fi
if veut check; then
  titre "Contrôles HyperFrames (lint + check par tranches de 16 s, limite de 120 s par appel)"
  $HF lint
  rm -f build/hf_check_*.json
  D=$("$PY" -c 'import sys; sys.path.insert(0, "scripts"); import chrono; print(chrono.load()["duree"])')
  i=1
  for r in "0,16" "16,32" "32,$D"; do
    # Un échec n'arrête pas la chaîne : il est consigné dans le JSON et ressort dans docs/07_controle_qualite.md.
    $HF check --range "$r" --timeout 60000 --samples 6 --json 2>/dev/null \
      | "$PY" -c 'import json,sys; t=sys.stdin.read(); json.dump(json.loads(t[t.index("{"):t.rindex("}")+1]), sys.stdout)' \
      > "build/hf_check_$i.json" || true
    i=$((i + 1))
  done
fi
if veut rendu; then
  titre "Rendu vidéo (H.264, 1080×1920, 30 i/s)"
  $HF render -o renders/joconde-1911-video.mp4 -q delivery --fps 30 --browser-timeout 120
fi
if veut livrables; then
  titre "Livrables : MP4 final, version sans son, pistes FLAC, cartes"
  mkdir -p livrables/pistes livrables/cartes
  ffmpeg -v error -y -i renders/joconde-1911-video.mp4 -i build/mix_master.wav \
    -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 320k -ar 48000 -ac 2 -movflags +faststart \
    -metadata title="Le vol de la Joconde (1911)" \
    -metadata comment="Voix de synthèse (Kokoro, ff_siwis) ; illustrations générées par code ; reproduction authentique de l'œuvre." \
    livrables/joconde-1911.mp4
  ffmpeg -v error -y -i renders/joconde-1911-video.mp4 -map 0:v:0 -c:v copy -an -movflags +faststart \
    -metadata title="Le vol de la Joconde (1911) — sans son" livrables/joconde-1911_sans-son.mp4
  for k in voix musique bruitages; do
    ffmpeg -v error -y -i "build/stems/$k.wav" -c:a flac -compression_level 8 "livrables/pistes/$k.flac"
  done
  cp assets/cartes/carte_paris_florence.png assets/cartes/carte_paris_florence.svg assets/cartes/carte.json livrables/cartes/
fi
if veut dossier; then
  titre "Dossier de production (tableaux générés) et contrôle qualité mesuré"
  "$PY" scripts/06_dossier.py
  "$PY" scripts/07_controle.py
fi
