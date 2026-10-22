# crue-1910-v2 — TikTok « La crue de 1910 », version émotion

Version 2 du test `videos/crue-1910-tiktok/` : même sujet, mêmes sources, mais une courbe émotionnelle et la
grammaire des formats courts de 2025–2026. Dirigée avec la skill `tiktok-retention-director`.
Vidéo livrée : `livrables/crue-1910-v2.mp4` (versionnée, comme celle de la V1) et les sous-titres
`livrables/crue-1910-v2.srt`.

| Fichier | Rôle |
| --- | --- |
| `BRIEF.md` | intention, style visé, contraintes (gratuit, aucun son d'époque simulé) |
| `SOURCES.md` | registre des faits (13 lignes) et des images (licences, crédits) |
| `DIRECTION.md` | ce qui change par rapport à la V1, 5 accroches, carte des émotions, rétention, plans, contrôle qualité |
| `STORYBOARD.md` | 11 plans avec `beat_role`, `emotion`, et les clés de réalisation |
| `SCRIPT.md` | texte lu (nombres en toutes lettres) et vitesse de la voix ligne par ligne |
| `scripts/images.py` | étalonnage par émotion précalculé + fonds flous → `build/img/` |
| `scripts/build.py` | voix, transcription, sous-titres mot à mot, musique et mixage, `index.html` |
| `compositions/organic-light-leak-overlay.html` | bloc du registre HyperFrames, passé en 1080 × 1920 |

## Refaire la vidéo

```bash
cd videos/crue-1910-v2
export HYPERFRAMES_PYTHON=../marseille-17-octobre/.venv/bin/python     # Python avec kokoro-onnx, soundfile, scipy, pyloudnorm
# voix (gratuite, locale) : une ligne de SCRIPT.md par fichier, à sa vitesse
#   npx hyperframes@0.8.166 tts "<ligne>" -v ff_siwis -l fr-fr -s <vitesse> -o build/voix/l<N>.wav
$HYPERFRAMES_PYTHON scripts/images.py
$HYPERFRAMES_PYTHON scripts/build.py
node ../../.agents/skills/tiktok-retention-director/scripts/retention_lint.mjs --storyboard STORYBOARD.md
npx --yes hyperframes@0.8.166 lint
npx --yes hyperframes@0.8.166 check --timeout 30000
npx --yes hyperframes@0.8.166 render -q delivery -o renders/crue-1910-v2-brut.mp4
node ../../.agents/skills/tiktok-retention-director/scripts/tiktok_qc.mjs --video livrables/crue-1910-v2.mp4 --target 52 --sheet renders/qc-sheet.jpg
```

`build/` (voix, mix, images étalonnées, transcription) et `renders/` sont régénérés et non versionnés.
