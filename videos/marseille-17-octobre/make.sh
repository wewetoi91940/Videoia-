#!/usr/bin/env bash
# Chaîne complète « marseille-17-octobre » : carte → voix → composition → audio → contrôles → rendu → livrables → contrôle qualité.
# Usage : ./make.sh [étape...]   étapes : osm carte voix composition audio check rendu livrables controle (défaut : toutes sauf osm)
# Python : PY=.venv/bin/python ./make.sh   (dépendances : requirements.txt ; ffmpeg et Node ≥ 22 requis)
# Voix   : Google Gemini. Clé GEMINI_API_KEY dans l'environnement, ou « network secret » de l'environnement cloud
#          (hôte generativelanguage.googleapis.com, en-tête x-goog-api-key) : la clé n'est alors jamais visible ici.
#          VOIX_BROUILLON=1 : voix Kokoro de calage, jamais livrée (l'étape « livrables » la refuse).
set -euo pipefail
cd "$(dirname "$0")"

PY="${PY:-python3}"
HF="npx --yes hyperframes@0.8.166"
ETAPES=("$@")
[ ${#ETAPES[@]} -eq 0 ] && ETAPES=(carte voix composition audio check rendu livrables controle)
veut() { [[ " ${ETAPES[*]} " == *" $1 "* ]]; }
titre() { printf '\n== %s\n' "$1"; }

if veut osm; then
  titre "Données OpenStreetMap (Overpass, miroir maps.mail.ru) → build/osm/"
  mkdir -p build/osm
  ov() {  # $1 = fichier, $2 = requête ; jusqu'à 4 essais (le service répond parfois 504)
    for i in 1 2 3 4; do
      code=$(curl -sS --max-time 240 -A 'videoia-marseille-doc/1.0' --data-urlencode "data=$2" \
        https://maps.mail.ru/osm/tools/overpass/api/interpreter -o "build/osm/$1.json" -w '%{http_code}')
      [ "$code" = 200 ] && return 0
      sleep $((10 * i))
    done
    echo "Échec du téléchargement $1" >&2; return 1
  }
  B='43.266,5.358,43.303,5.404'
  ov routes "[out:json][timeout:120];way[\"highway\"]($B);out geom;"
  ov cote "[out:json][timeout:120];way[\"natural\"=\"coastline\"](43.262,5.345,43.306,5.404);out geom;"
  ov digues "[out:json][timeout:120];way[\"man_made\"~\"^(pier|breakwater)\$\"]($B);out geom;"
  ov eau "[out:json][timeout:120];(way[\"natural\"=\"water\"]($B);relation[\"natural\"=\"water\"]($B);way[\"leisure\"~\"^(park|garden)\$\"]($B););out geom;"
  n=0
  for la in 43.266 43.2845; do for lo in 5.358 5.381; do
    n=$((n + 1)); la2=$("$PY" -c "print(round($la + 0.0185, 4))"); lo2=$("$PY" -c "print(round($lo + 0.023, 4))")
    ov "bati$n" "[out:json][timeout:180];way[\"building\"]($la,$lo,$la2,$lo2);out geom;"
  done; done
fi
if veut carte; then
  titre "Cartes du centre de Marseille (OpenStreetMap) + grain"
  "$PY" scripts/02_carte.py
  "$PY" scripts/03_grain.py
fi
if veut voix; then
  titre "Voix off (Google Gemini) → build/voix.wav, build/chronologie.json"
  if [ "${VOIX_BROUILLON:-0}" = 1 ]; then
    "$PY" scripts/01_voix.py --brouillon-kokoro
  else
    NODE_USE_ENV_PROXY=1 "$PY" scripts/01_voix.py
  fi
fi
if veut composition; then
  titre "Composition HyperFrames + sous-titres (index.html, SRT)"
  "$PY" scripts/05_composition.py
fi
if veut audio; then
  titre "Musique, mixage −14 LUFS → build/mix_master.wav, build/stems/"
  "$PY" scripts/04_audio.py
fi
if veut check; then
  titre "Contrôles HyperFrames (lint + check par tranches de 60 s)"
  $HF lint
  rm -f build/hf_check_*.json
  RANGES=$("$PY" -c 'import json; d = json.load(open("build/plans_calcules.json"))["duree"]
t = [i * 60 for i in range(int(d // 60) + 1)] + [d]
print(" ".join(f"{a},{int(b * 100) / 100:.2f}" for a, b in zip(t, t[1:]) if b - a > 0.5))')
  i=1
  for r in $RANGES; do
    $HF check --range "$r" --timeout 120000 --samples 10 --json 2>/dev/null \
      | "$PY" -c 'import json,sys; t=sys.stdin.read(); json.dump(json.loads(t[t.index("{"):t.rindex("}")+1]), sys.stdout)' \
      > "build/hf_check_$i.json" || true
    i=$((i + 1))
  done
  "$PY" -c 'import json,glob
e=w=0
for f in sorted(glob.glob("build/hf_check_*.json")):
    try: d=json.load(open(f))
    except Exception: print(f, "illisible"); continue
    for k in ("lint", "runtime", "layout", "motion", "contrast"):
        e+=d.get(k,{}).get("errorCount",0); w+=d.get(k,{}).get("warningCount",0)
print(f"check : {e} erreur(s), {w} avertissement(s)")'
fi
if veut rendu; then
  titre "Rendu vidéo (H.264, 1920×1080, 30 i/s)"
  mkdir -p renders
  $HF render -o renders/marseille-17-octobre-video.mp4 -q delivery --fps 30 --browser-timeout 120
fi
if veut livrables; then
  titre "Livrables : MP4 final, version sans son, pistes FLAC, sous-titres"
  VOIX_INFO=$("$PY" -c 'import json; c = json.load(open("build/chronologie.json"))
print(("BROUILLON " if c.get("brouillon", True) else "") + " / ".join(str(c.get(k)) for k in ("moteur", "voix", "modele")))')
  if [[ "$VOIX_INFO" == BROUILLON* ]]; then
    echo "Refus : la voix est un brouillon de calage ($VOIX_INFO). Les livrables ne sont pas écrasés." >&2
    exit 1
  fi
  mkdir -p livrables/pistes
  ffmpeg -v error -y -i renders/marseille-17-octobre-video.mp4 -i build/mix_master.wav \
    -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf 20 -tune stillimage -pix_fmt yuv420p -g 60 \
    -c:a aac -b:a 256k -ar 48000 -ac 2 -movflags +faststart \
    -metadata title="Marseille, 17 octobre : la journée où le centre-ville a basculé" \
    -metadata comment="Voix de synthèse ($VOIX_INFO). Cartes © contributeurs OpenStreetMap (ODbL). Photos : Wikimedia Commons (voir credits). Aucune image des événements." \
    livrables/marseille-17-octobre.mp4
  ffmpeg -v error -y -i livrables/marseille-17-octobre.mp4 -map 0:v:0 -c:v copy -an -movflags +faststart \
    livrables/marseille-17-octobre_sans-son.mp4
  for k in voix musique bruitages; do
    ffmpeg -v error -y -i "build/stems/$k.wav" -c:a flac -compression_level 8 "build/stems/$k.flac"
  done
  cp build/stems/voix.flac livrables/pistes/voix.flac
  cp build/marseille-17-octobre.srt livrables/marseille-17-octobre.srt
fi
if veut controle; then
  titre "Contrôle qualité mesuré → docs/07_controle_qualite.md"
  "$PY" scripts/07_controle.py
fi
