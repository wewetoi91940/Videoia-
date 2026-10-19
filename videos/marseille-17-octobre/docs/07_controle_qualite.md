# Contrôle qualité mesuré

*Généré par `scripts/07_controle.py` : 12/12 points conformes.*

| Point | État | Mesure |
|---|---|---|
| Voix Google livrée | ✅ conforme | moteur gemini, voix Charon, modèle gemini-3.1-flash-tts-preview |
| Durée 6 à 9 min 30 | ✅ conforme | 509.3 s (8 min 29.3 s), voix seule 491.3 s |
| Loudness −14 LUFS ±0,5 | ✅ conforme | -14.17 LUFS |
| Crête vraie ≤ −1,5 dBTP | ✅ conforme | -1.6 dBTP |
| Musique ≥ 15 dB sous la voix | ✅ conforme | écart intégré 31.44 dB ; fenêtres de 400 ms : médiane 29.8 dB, 5e centile 25.3 dB, min 12.2 dB |
| Plans lisibles (≥ 2 s) | ✅ conforme | 58 plans ; plus court : P14b (2.87 s) |
| Chaque phrase chiffrée ou citée a une source | ✅ conforme | toutes sourcées |
| Heures affichées présentes dans la narration ou les sources | ✅ conforme | 29 heures affichées ; affichées sans être dites (sourcées dans le direct de La Provence ou la préfecture) : 9 h 34, 10 h 19, 11 h 47, 15 h 00, 15 h 53, 17 h 15 |
| Aucune source issue d'un site qui refuse Claude-User | ✅ conforme | 40 sources, 14 domaines |
| Photos sous licence libre, créditées | ✅ conforme | 11 photos créditées |
| hyperframes check sans erreur | ✅ conforme | 0 erreur(s), 819 avertissement(s) (tranches de 60 s) |
| Vidéo livrée 1920×1080, 30 i/s, avec son | ✅ conforme | 1920×1080, 30/1 i/s, 1 piste(s) audio, 509.30 s, 540.8 Mo |
