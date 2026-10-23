#!/usr/bin/env python3
"""Textes de publication → docs/06_publication.md : titre, description, chapitres calés sur la voix réelle, sources, mentions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def tc(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def main():
    script = json.loads((ROOT / "scripts/script.json").read_text())
    chrono = json.loads((ROOT / "build/chronologie.json").read_text())
    debuts = {}
    for p in chrono["phrases"]:
        debuts.setdefault(p["seq"], p["debut"])
    chapitres = [f"{tc(0 if s['n'] == 1 else debuts[s['n']])} {s['titre']}" for s in script["sequences"]]
    sources = []
    for ph in script["phrases"]:
        for s in ph.get("sources", []):
            if s not in sources and s != "OSM":
                sources.append(s)
    lignes_src = [f"- {script['sources'][s]['media']} ({script['sources'][s]['date']}) — {script['sources'][s]['titre']} : "
                  f"{script['sources'][s]['url']}" for s in sources]
    voix = f"{chrono.get('moteur')} / {chrono.get('voix')} / {chrono.get('modele')}"
    md = f"""# Publication

## Titre
**{script['titre']}**

Variantes courtes : « Marseille, 17 octobre : ce que l'on sait, heure par heure » · « 17 octobre à Marseille : chronologie d'une journée de pillages »

## Description (YouTube)
Samedi 17 octobre 2026, une journée nationale de mobilisation contre la vie chère dégénère dans le centre de Marseille :
poste de police municipale attaqué en fin de matinée, hôtel de ville forcé à la mi-journée, pillages jusque dans la nuit.
Ce documentaire reconstitue la journée à partir des articles et des directs publiés du 17 au 19 octobre, distingue
les heures publiées des périodes approximatives, et attribue chaque chiffre à sa source.

Aucune image des événements : cartes OpenStreetMap et photos des lieux en temps normal.
Les heures « direct » sont les heures de mise en ligne d'une entrée de direct : le fait peut être antérieur.

**Chapitres**
{chr(10).join(chapitres)}

**Sources**
{chr(10).join(lignes_src)}

**Fabrication** : voix de synthèse ({voix}) · cartes © contributeurs d'OpenStreetMap (ODbL) ·
photos Wikimedia Commons (voir `assets/photos/credits.json`) · musique composée par programme.

## Mentions obligatoires à l'écran et en description
- « Voix de synthèse » (contenu généré par IA) : à déclarer sur YouTube (« contenu modifié ou synthétique ») et sur TikTok (étiquette IA).
- © contributeurs d'OpenStreetMap (déjà à l'écran sur chaque carte).
- Auteur et licence de chaque photo (déjà à l'écran, et dans la description si la plateforme l'exige).

## Avant de publier
- Relire `docs/01_verification_sources.md` § D (contradictions) : les chiffres de pilleurs et de commerces restent contestés.
- Si un bilan officiel actualisé est publié après le 19 octobre, mettre à jour la séquence 11 et le carton de fin.
- Ne pas ajouter d'images d'actualité sans licence (AFP, BFMTV, France 3, CNews…).
"""
    (ROOT / "docs/06_publication.md").write_text(md)
    print(f"docs/06_publication.md : {len(chapitres)} chapitres, {len(lignes_src)} sources")


if __name__ == "__main__":
    main()
