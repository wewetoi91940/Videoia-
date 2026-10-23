# La Seine arrête les horloges — crue de 1910 (TikTok, 45 s)

Test de la skill `tiktok-retention-director` (`.agents/skills/tiktok-retention-director/`) : une vidéo TikTok
historique de 44 s, 1080 × 1920, en français, faite d'archives du domaine public et d'une voix de synthèse locale.

| Fichier | Rôle (étape de la skill) |
| --- | --- |
| `BRIEF.md` | brief : TikTok, 1080×1920, 45 s, public, ton (étape 0) |
| `SOURCES.md` | registre des faits (trois sources lues, statut de chaque fait) et des images (auteur, licence) (étapes 1 et 9) |
| `DIRECTION.md` | analyse du sujet, 5 accroches et le choix, carte de rétention, tableau des plans, journal de contrôle (étapes 1–8) |
| `STORYBOARD.md` | 8 plans au format HyperFrames + colonnes de direction (durée, image, caméra, animation, texte, son, transition, changements) |
| `SCRIPT.md` | texte lu par la voix (nombres en toutes lettres) |
| `scripts/build.py` | montage : voix placée, mots datés (Whisper local), mixage, sous-titres, `index.html` |
| `livrables/crue-1910-tiktok.mp4` | vidéo à publier (≈ 21 Mo) |

Refaire la vidéo (sans crédit payant) :

```bash
export HYPERFRAMES_PYTHON=../marseille-17-octobre/.venv/bin/python     # Python avec kokoro-onnx
# voix : une ligne de SCRIPT.md par fichier build/voix/lN.wav
npx hyperframes tts "<ligne>" --voice ff_siwis --lang fr-fr --speed 0.92 -o build/voix/l1.wav
../marseille-17-octobre/.venv/bin/python scripts/build.py              # index.html + mixage
node ../../.claude/skills/tiktok-retention-director/scripts/retention_lint.mjs --storyboard STORYBOARD.md
npx hyperframes check --at-transitions
npx hyperframes render -o renders/crue-1910-tiktok-brut.mp4 -q delivery --fps 30
node ../../.claude/skills/tiktok-retention-director/scripts/tiktok_qc.mjs --video livrables/crue-1910-tiktok.mp4 --target 45 --sheet build/qc/qc-sheet.jpg
```

Le mixage et le découpage des sous-titres réutilisent `videos/marseille-17-octobre/scripts/04_audio.py` et
`05_composition.py`.
