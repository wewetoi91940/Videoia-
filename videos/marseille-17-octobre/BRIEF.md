---
workflow: general-video
flow: automation
storyboard: no
message: "Le 17 octobre, le centre de Marseille a été pillé dès la fin de matinée, bien avant le rassemblement prévu à 14 h : voici ce que les sources permettent d'établir, heure par heure, et ce qui reste incertain."
destination: youtube
aspect: 1920x1080
language: fr
audience: grand public francophone
length: 8-9 min
angle: enquête documentaire chronologique, non sensationnelle
---

## Intent

Documentaire narré sur la journée du samedi 17 octobre 2026 à Marseille : comment une journée de
mobilisation contre la vie chère a dégénéré dans le centre-ville, heure par heure, puis les bilans
contradictoires du dimanche et du lundi. Ton : journaliste d'investigation, immersif mais jamais
sensationnel. Demande de l'utilisateur : « Fais en sorte que la vidéo soit finie et parfaite. »

## Assets

- /tmp/…/scratchpad/marseille-17-octobre-dossier.md — dossier d'enquête et scénario (12 séquences), copié dans `docs/01_recherche.md`.

## Customizations

- Voix off Google (Gemini TTS), comme pour la Joconde : jamais de voix robotique livrée.
- Cartes du centre de Marseille construites depuis OpenStreetMap (© contributeurs OSM, ODbL), sans parcours inventé.
- Cartons d'heures qui distinguent heure publiée, période et heure de publication d'une dépêche.
- Chaque chiffre et chaque citation affichés avec leur source.

## Notes

- Règle absolue : n'inventer aucune heure ; attribuer toute estimation officielle ; aucune personne privée identifiable.
- Aucune image d'actualité sous droits (AFP, BFMTV, France 3, CNews…) : photos libres des lieux (Wikimedia Commons),
  toujours étiquetées « le lieu, en temps normal », jamais présentées comme des images de la journée.
- Sites dont le robots.txt refuse Claude-User : jamais téléchargés (extraits de moteur de recherche seulement).
