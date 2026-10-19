#!/usr/bin/env python3
"""Source lisible du plan de montage : écrit scripts/plans.json (un plan par visuel, ancré sur un mot de la voix).

Chaque plan commence sur l'ancre donnée ({phrase, mot}) ; il dure jusqu'au plan suivant. Les heures affichées
reprennent celles des sources (statut « direct » = heure d'une entrée de direct : le fait peut être antérieur).
Aucune flèche de parcours : seules les rues et les lieux cités par les sources sont mis en évidence.
"""
import json
from pathlib import Path


def A(phrase, mot=None, n=1, decalage=0.0, apres=False):
    a = {"phrase": phrase}
    if mot:
        a["mot"] = mot
    if n != 1:
        a["n"] = n
    if decalage:
        a["decalage"] = decalage
    if apres:
        a["apres"] = True
    return a


def cart(lieu, heure=None, statut=None):
    c = {"lieu": lieu}
    if heure:
        c["heure"] = heure
    if statut:
        c["statut"] = statut
    return c


ZOOM_IN = {"de": [1.0, 0, 0], "a": [1.07, 0, 0]}
ZOOM_OUT = {"de": [1.08, 0, 0], "a": [1.0, 0, 0]}
plans = []


def plan(pid, seq, ancre, typ, **kw):
    plans.append({"id": pid, "seq": seq, "ancre": ancre, "type": typ, **kw})


# 1 — Ouverture ---------------------------------------------------------------------------------------
plan("P01", 1, A("s1_date"), "photo", photo="canebiere", camera={"de": [1.0, 0, 0], "a": [1.09, -40, 0]},
     cartouche=cart("La Canebière", "11 H 28", "direct"),
     repli={"type": "carte", "vue": "canebiere", "couches": [{"ligne": "canebiere", "etat": "froid"}]})
plan("P02", 1, A("s1_poste", "poste"), "carte", vue="canebiere", camera=ZOOM_IN,
     couches=[{"ligne": "canebiere", "etat": "actif", "etiquette": "La Canebière", "pos": 0.45, "dy": 26}],
     cartouche=cart("Poste de police municipale, sur la Canebière", "11 H 28 → 11 H 47", "direct"))
plan("P03", 1, A("s1_ferreol"), "carte", vue="quadrilatere", camera=ZOOM_IN,
     couches=[{"ligne": "canebiere", "etat": "passe", "a": A("s1_ferreol")},
              {"ligne": "saint_ferreol", "etat": "actif", "a": A("s1_ferreol", "Saint-Ferréol,"),
               "etiquette": "Rue Saint-Ferréol", "pos": 0.5}],
     cartouche=cart("Rue Saint-Ferréol : magasins fermés, fracturés et pillés", "AVANT MIDI", "periode"))
plan("P04", 1, A("s1_midi"), "constat", kicker="Samedi 17 octobre", texte="Il n'est pas encore midi.", ghost="11 H",
     sous="Le rassemblement prévu à 14 h n'a même pas commencé.", sous_a=A("s1_rdv"))
plan("P05", 1, A("s1_question"), "constat", kicker="La question",
     texte="Comment une journée de mobilisation contre la vie chère a-t-elle basculé dans le pillage ?", ghost="?")
plan("P06", 1, A("s1_annonce", apres=True, decalage=0.25), "titre", kicker="Marseille · 17 octobre 2026",
     titre="Du Prado à Saint-Ferréol", sous_titre="la journée où le centre-ville a basculé",
     note="Reconstitution à partir d'articles publiés du 17 au 19 octobre 2026. Aucune image des événements : "
          "cartes OpenStreetMap et photos des lieux en temps normal.", musique="impact")

# 2 — Contexte -----------------------------------------------------------------------------------------
plan("P07", 2, A("s2_journee"), "photo", photo="panorama", camera={"de": [1.0, 0, 0], "a": [1.08, 0, -20]},
     cartouche=cart("Marseille · journée nationale contre la vie chère"),
     repli={"type": "constat", "kicker": "Samedi 17 octobre", "texte": "Journée nationale de mobilisation contre la vie chère"})
plan("P08", 2, A("s2_programme"), "carte", vue="ensemble", camera={"de": [1.0, 0, 0], "a": [1.05, 0, 0]},
     colonne={"kicker": "Le programme annoncé", "titre": "Samedi 17 octobre",
              "lignes": ["Dès 8 h : action au rond-point du Prado",
                         "14 h : rassemblement, Vieux-Port ou Canebière selon les sources"],
              "a": [A("s2_programme", "Prado"), A("s2_programme", "rassemblement")]},
     couches=[{"point": "prado", "a": A("s2_programme", "Prado"), "etiquette": "Rond-point du Prado", "dx": -24, "dy": -80},
              {"point": "vieux_port", "a": A("s2_programme", "Vieux-Port"), "etiquette": "Vieux-Port", "dx": -24},
              {"ligne": "canebiere", "etat": "froid", "a": A("s2_programme", "Canebière")}])
plan("P09", 2, A("s2_prefet"), "citation", texte="C'est véritablement à Marseille que nous avons un point de préoccupation.",
     qui="Jacques Witkowski, préfet des Bouches-du-Rhône, la veille", source="Cité par La Provence, 18/10")
plan("P10", 2, A("s2_effectifs"), "chiffres", kicker="Les effectifs du matin", titre="Deux versions", barres=False,
     lignes=[{"affiche": "1 compagnie", "libelle": "de CRS, soit 80 policiers", "source": "Benoît Payan, maire (La Provence, 18/10)",
              "a": A("s2_effectifs", "seule")},
             {"affiche": "434 + 240", "libelle": "policiers et CRS engagés dès 7 h", "source": "Préfecture de police (bilan du 18/10)",
              "a": A("s2_prefecture")}])

# 3 — Le matin ------------------------------------------------------------------------------------------
plan("P11", 3, A("s3_methode"), "constat", kicker="Méthode", texte="Aucune chronologie officielle n'a été publiée.", ghost="?? H ??",
     sous="Les heures citées sont celles où les journalistes ont signalé les faits, en direct : un fait a pu se produire un peu avant.",
     sous_a=A("s3_methode", "heures"))
plan("P12", 3, A("s3_prado"), "carte", vue="ensemble", camera={"de": [1.0, 0, 0], "a": [1.18, 0, 0], "foyer": "prado"},
     colonne={"kicker": "Samedi · dès 8 h", "titre": "Le rond-point du Prado",
              "lignes": ["Boulevard bloqué par des poubelles et des trottinettes (ICI)",
                         "À environ 3 km au sud du Vieux-Port"],
              "a": [A("s3_prado", "poubelles"), A("s3_prado", "trois")]},
     couches=[{"point": "prado", "etiquette": "Rond-point du Prado", "dx": -24, "dy": -80},
              {"point": "vieux_port", "etat": "froid", "a": A("s3_prado", "Vieux-Port."), "etiquette": "Vieux-Port", "dx": -24}])
plan("P13", 3, A("s3_gaz"), "photo", photo="prado", camera={"de": [1.0, 0, 0], "a": [1.08, -20, 0]},
     cartouche=cart("Rond-point du Prado : une vingtaine de jeunes, puis les premiers gaz lacrymogènes", "8 H 14 → 8 H 54", "direct"),
     repli={"type": "heure", "heure": "8 H 54", "statut": "direct", "lieu": "Rond-point du Prado",
            "evenement": "Premiers jets de gaz lacrymogène ; à 8 h 14, une vingtaine de jeunes et quelques gilets jaunes au rond-point (La Provence)."})
plan("P14", 3, A("s3_castellane"), "carte", vue="prado_castellane", camera=ZOOM_IN,
     colonne={"kicker": "9 h 20 · direct de La Provence", "titre": "Vers la place Castellane",
              "lignes": ["Les gilets jaunes remontent l'avenue du Prado", "9 h 20 : signalés place Castellane"],
              "a": [A("s3_castellane", "remontent"), A("s3_castellane", "signalés")]},
     couches=[{"point": "prado", "etat": "passe"},
              {"ligne": "avenue_du_prado", "etat": "actif", "a": A("s3_castellane", "avenue")},
              {"point": "castellane", "a": A("s3_castellane", "Castellane."), "etiquette": "Place Castellane"}])
plan("P14b", 3, A("s3_castellane", "9"), "photo", photo="castellane", camera={"de": [1.0, 0, 0], "a": [1.07, 0, -10]},
     cartouche=cart("Place Castellane", "9 H 20", "direct"))
plan("P15", 3, A("s3_reformes"), "carte", vue="matin", camera={"de": [1.0, 0, 0], "a": [1.06, 0, 0]},
     colonne={"kicker": "Matinée · entrées du direct de La Provence", "titre": "Des groupes dans la ville",
              "lignes": ["9 h 34 : devant la préfecture", "10 h 19 : gare Saint-Charles", "10 h 43 : Réformés, « un bon millier »"],
              "a": [A("s3_reformes", "préfecture,"), A("s3_reformes", "Saint-Charles,"), A("s3_reformes", "Réformés,")]},
     couches=[{"point": "castellane", "etat": "passe"},
              {"point": "prefecture", "a": A("s3_reformes", "préfecture,"), "etiquette": "Préfecture", "dx": -24},
              {"point": "saint_charles", "a": A("s3_reformes", "Saint-Charles,"), "etiquette": "Gare Saint-Charles", "dx": -24, "dy": -50},
              {"point": "reformes", "a": A("s3_reformes", "Réformés,"), "etiquette": "Les Réformés"},
              {"ligne": "canebiere", "etat": "froid", "a": A("s3_reformes", "Canebière")}])

# 4 — Avant midi ----------------------------------------------------------------------------------------
plan("P16", 4, A("s4_poste"), "carte", vue="canebiere", camera={"de": [1.0, 0, 0], "a": [1.08, 0, 0]},
     couches=[{"ligne": "canebiere", "etat": "actif", "etiquette": "La Canebière", "pos": 0.45, "dy": 26},
              {"point": "reformes", "etat": "passe"}],
     cartouche=cart("Poste de police municipale · « 42, La Canebière » selon le maire", "11 H 28", "direct"))
plan("P17", 4, A("s4_molotov"), "constat", kicker="À vérifier", texte="Des cocktails Molotov ?", ghost="?",
     sous="Ils circulent sur les réseaux sociaux. L'AFP, la préfecture et La Provence ne parlent que de fumigènes.",
     sous_a=A("s4_molotov", "mais"))
plan("P18", 4, A("s4_crs"), "photo", photo="canebiere", position="50% 60%", camera={"de": [1.12, 30, 0], "a": [1.04, 0, 0]},
     cartouche=cart("Des CRS postés juste au-dessus du poste (Marsactu)", "FIN DE MATINÉE", "periode"),
     repli={"type": "constat", "kicker": "Marsactu · fin de matinée", "texte": "Des CRS postés juste au-dessus n'interviennent pas."})
plan("P19", 4, A("s4_magasins"), "heure", heure="11 H 46", statut="direct",
     evenement="Pillage de la boutique SFR de la Canebière ; à 11 h 54, celui de JD Sports (La Provence).", lieu="La Canebière")
plan("P20", 4, A("s4_prefet"), "citation", texte="Nous ne faisons pas face à une manifestation, mais véritablement à des pillages.",
     qui="Le préfet, à propos de la situation depuis midi", source="La Provence, direct, 17/10")

# 5 — L'hôtel de ville ----------------------------------------------------------------------------------
plan("P21", 5, A("s5_mairie"), "carte", vue="vieux_port", camera=ZOOM_IN,
     couches=[{"point": "hotel_de_ville", "a": A("s5_mairie", "l'hôtel"), "etiquette": "Hôtel de ville"},
              {"ligne": "quai_du_port", "etat": "passe", "a": A("s5_mairie", "quai"), "etiquette": "Quai du Port", "pos": 0.3, "dy": 24}],
     cartouche=cart("Hôtel de ville, quai du Port", "MI-JOURNÉE", "periode"))
plan("P22", 5, A("s5_porte"), "photo", photo="hotel-de-ville", camera={"de": [1.0, 0, 0], "a": [1.08, 0, -10]},
     cartouche=cart("Hôtel de ville : la double porte en bois forcée (AFP)", "MI-JOURNÉE", "periode"),
     repli={"type": "constat", "kicker": "AFP · mi-journée", "texte": "La double porte en bois est forcée avec des barrières de sécurité."})
plan("P23", 5, A("s5_porte", "criant"), "citation", texte="C'est la Révolution, on prend la Bastille.",
     qui="Cris rapportés par un journaliste de l'AFP", source="AFP, 17/10")
plan("P24", 5, A("s5_heure"), "heure", heure="13 H 20", statut="direct",
     evenement="La porte de l'hôtel de ville est ouverte, gardée par des CRS. L'heure de l'intrusion n'a pas été publiée.",
     lieu="Hôtel de ville · quai du Port")
plan("P25", 5, A("s5_repli"), "constat", kicker="Le maire", texte="« Un mouvement de repli des CRS »", ghost="CRS",
     sous="C'est, selon Benoît Payan, ce qui a laissé la porte libre.")

# 6 — 14 h ----------------------------------------------------------------------------------------------
plan("P26", 6, A("s6_14h"), "heure", heure="14 H", statut="prevue",
     evenement="Rassemblement annoncé, sur le Vieux-Port ou sur la Canebière selon les sources.", lieu="Centre-ville", musique="impact")
plan("P27", 6, A("s6_face"), "photo", photo="vieux-port", camera={"de": [1.0, 0, 0], "a": [1.07, 20, 0]},
     cartouche=cart("Vieux-Port : face-à-face pendant près d'une heure (Marsactu)", "APRÈS-MIDI", "periode"),
     repli={"type": "carte", "vue": "vieux_port", "couches": [{"point": "vieux_port", "etiquette": "Vieux-Port"}]})
plan("P28", 6, A("s6_reformes"), "carte", vue="canebiere", camera=ZOOM_OUT,
     couches=[{"point": "reformes", "a": A("s6_reformes", "Réformés,"), "etiquette": "Les Réformés", "dx": -24},
              {"ligne": "canebiere", "etat": "froid", "a": A("s6_cortege", "remontent"), "etiquette": "Cortège sur la Canebière", "pos": 0.45, "dy": 26}],
     cartouche=cart("La manifestation a lieu aux Réformés (La Provence)", "≈ 15 H", "periode"))
plan("P29", 6, A("s6_cortege"), "heure", heure="14 H 51", statut="direct",
     evenement="Plusieurs milliers de manifestants remontent pacifiquement la Canebière (La Provence).", lieu="La Canebière")
plan("P30", 6, A("s6_auditrice"), "citation", texte="À cause de tout ce chaos, on n'a pas pu lancer notre manifestation.",
     qui="Une auditrice gilet jaune", source="Europe 1, 18/10")

# 7 — Transports ----------------------------------------------------------------------------------------
plan("P31", 7, A("s7_1525"), "heure", heure="15 H 25", statut="unique",
     evenement="Transports en commun arrêtés sur décision du préfet (La Clé Publique).", lieu="Réseau de la RTM", musique="coupure")
plan("P32", 7, A("s7_lp"), "photo", photo="metro", camera={"de": [1.0, 0, 0], "a": [1.06, 0, 0]},
     cartouche=cart("Métro et tram « totalement à l'arrêt » (La Provence)", "16 H 03", "direct"),
     repli={"type": "constat", "kicker": "16 h 03 · La Provence", "texte": "Métro et tram totalement à l'arrêt, à la demande du préfet."})

# 8 — Pillages de l'après-midi --------------------------------------------------------------------------
plan("P33", 8, A("s8_secteur"), "carte", vue="quadrilatere", camera={"de": [1.0, 0, 0], "a": [1.06, 0, 0]},
     couches=[{"ligne": "canebiere", "etat": "passe", "a": A("s8_secteur", "Canebière")},
              {"zone": "zone_rues", "a": A("s8_secteur", "secteur")},
              {"ligne": "saint_ferreol", "a": A("s8_secteur", "Saint-Ferréol,"), "etiquette": "Saint-Ferréol", "pos": 0.35},
              {"ligne": "paradis", "a": A("s8_secteur", "Paradis,"), "etiquette": "Paradis", "pos": 0.6},
              {"ligne": "grignan", "a": A("s8_secteur", "Grignan,"), "etiquette": "Grignan", "pos": 0.3, "dy": -50},
              {"ligne": "montgrand", "a": A("s8_secteur", "Montgrand."), "etiquette": "Montgrand", "pos": 0.25, "dy": 22}],
     cartouche=cart("Rues citées par la presse", "APRÈS-MIDI", "periode"))
plan("P34", 8, A("s8_bourse"), "heure", heure="15 H 02", statut="direct",
     evenement="Des dizaines de personnes forcent une grille du Centre Bourse ; à 15 h 53, boutiques de luxe pillées rue Paradis et rue Grignan.",
     lieu="Centre Bourse · rues Paradis et Grignan")
plan("P35", 8, A("s8_feu"), "photo", photo="saint-ferreol", camera={"de": [1.0, 0, 0], "a": [1.08, 0, 10]},
     cartouche=cart("Rue Saint-Ferréol : un magasin incendié, le feu gagne l'immeuble", "15 H 39", "direct"),
     repli={"type": "heure", "heure": "15 H 39", "statut": "direct", "evenement": "Un magasin incendié rue Saint-Ferréol ; le feu gagne l'immeuble.", "lieu": "Rue Saint-Ferréol"})
plan("P36", 8, A("s8_acoups"), "citation", texte="Quelques CRS, retranchés dans des rues et divisés en petits groupes, interviennent par à-coups.",
     qui="Une journaliste de Marsactu, sur place", source="Marsactu, 17/10")
plan("P37", 8, A("s8_temoin"), "constat", kicker="Témoignage", texte="Une habitante dit avoir vu les CRS « laisser faire ».", ghost="« … »",
     sous="Recueilli par ICI Provence : un témoignage, pas un constat.", sous_a=A("s8_temoin", "témoignage,"))
plan("P38", 8, A("s8_centaure"), "chiffres", kicker="Renforts", titre="Ce que détaille la préfecture", barres=False,
     lignes=[{"affiche": "2", "libelle": "blindés Centaure, avec 12 gendarmes, à partir de 13 h 30", "source": "Préfecture de police (18/10)",
              "a": A("s8_centaure", "Centaure")},
             {"affiche": "152", "libelle": "gendarmes supplémentaires, à partir de 20 h seulement", "source": "Préfecture de police (18/10)",
              "a": A("s8_centaure", "préfecture.")}])

# 9 — Le soir, la nuit ----------------------------------------------------------------------------------
plan("P39", 9, A("s9_point"), "chiffres", kicker="Vers 17 h · le préfet", titre="Premier point", barres=False,
     lignes=[{"affiche": "7 000 – 8 000", "libelle": "pilleurs", "source": "Le préfet (La Provence, direct)", "a": A("s9_point", "pilleurs,")},
             {"affiche": "30 ou 40", "libelle": "magasins touchés", "source": "Le préfet (La Provence, direct)", "a": A("s9_point", "magasins")},
             {"affiche": "29", "libelle": "blessés parmi les forces de l'ordre (17 h 15)", "source": "Le préfet (La Provence, direct)",
              "a": A("s9_point", "blessés")}])
plan("P40", 9, A("s9_18h"), "heure", heure="18 H", statut="publiee",
     evenement="« Le centre-ville de Marseille est plongé dans un chaos » (Marsactu).", lieu="Centre-ville")
plan("P41", 9, A("s9_gazent"), "citation", texte="Ils gazent souvent, font exploser des grenades de désencerclement de temps en temps, chargent rarement.",
     qui="Une journaliste de Marsactu, vers 18 h", source="Marsactu, 17/10")
plan("P42", 9, A("s9_nuit"), "carte", vue="quadrilatere", camera=ZOOM_OUT,
     couches=[{"zone": "zone_rues", "a": A("s9_nuit")},
              {"ligne": "paradis", "a": A("s9_nuit", "Paradis"), "etiquette": "Rue Paradis · 19 h 09", "pos": 0.6},
              {"ligne": "saint_ferreol", "a": A("s9_nuit", "Saint-Ferréol."), "etiquette": "Rue Saint-Ferréol · vers 20 h", "pos": 0.35}],
     cartouche=cart("Pillages encore signalés à la tombée de la nuit", "19 H 09 · VERS 20 H", "direct"))
plan("P43", 9, A("s9_107"), "photo", photo="prefecture", camera={"de": [1.0, 0, 0], "a": [1.07, 0, 0]},
     cartouche=cart("La préfecture annonce 107 policiers blessés", "VERS 22 H", "periode"),
     repli={"type": "heure", "prefixe": "Vers", "heure": "22 H", "statut": "periode",
            "evenement": "La préfecture annonce 107 policiers blessés.", "lieu": "Préfecture de police"})
plan("P44", 9, A("s9_2h"), "heure", prefixe="Vers", heure="2 H", statut="periode",
     evenement="Des commerces sont encore attaqués dans le centre-ville (Destimed).", lieu="Nuit du 17 au 18 octobre")

# 10 — Dimanche ----------------------------------------------------------------------------------------
plan("P45", 10, A("s10_matin"), "photo", photo="vieux-port-2", camera={"de": [1.1, 0, 0], "a": [1.0, 0, 0]},
     cartouche=cart("Marseille", "DIMANCHE 18 OCTOBRE", "jour"),
     repli={"type": "constat", "kicker": "Dimanche 18 octobre", "texte": "Marseille découvre son centre-ville."})
plan("P46", 10, A("s10_constats"), "carte", vue="quadrilatere", camera=ZOOM_IN,
     couches=[{"ligne": "canebiere", "etat": "passe", "a": A("s10_constats", "Canebière")},
              {"zone": "zone_rues", "a": A("s10_constats", "Canebière")},
              {"ligne": "montgrand", "etat": "passe", "a": A("s10_constats", "Montgrand,"), "etiquette": "Rue Montgrand", "pos": 0.25, "dy": 22}],
     cartouche=cart("De la Canebière à la rue Montgrand", "DIMANCHE", "jour"))
plan("P47", 10, A("s10_affiche"), "citation", texte="Entièrement vidée. Fermée pour trois mois.",
     qui="Affichette d'une boutique de téléphonie, rue Paradis", source="Le Parisien, 18/10")
plan("P48", 10, A("s10_bilans"), "chiffres", kicker="Dimanche · les bilans", titre="Les bilans divergent", barres=False,
     lignes=[{"affiche": "+ 600", "libelle": "commerces vandalisés", "source": "Chambre de commerce (ICI Provence)", "a": A("s10_cci")},
             {"affiche": "+ 30 000", "libelle": "pilleurs, dont 8 000 « émeutiers », « au plus fort des événements »",
              "source": "Préfecture de police", "a": A("s10_pref")},
             {"affiche": "99", "libelle": "gardes à vue", "source": "Préfecture de police", "a": A("s10_gav")},
             {"affiche": "118", "libelle": "blessés parmi les forces de l'ordre, dont 3 hospitalisés", "source": "Préfecture de police",
              "a": A("s10_gav", "118")}])

# 11 — Lundi --------------------------------------------------------------------------------------------
plan("P49", 11, A("s11_inter"), "constat", kicker="Lundi 19 octobre · France Inter",
     texte="Pour Benoît Payan, la doctrine de maintien de l'ordre est « inefficace ».", ghost="19.10")
plan("P50", 11, A("s11_1500"), "chiffres", kicker="Combien de pilleurs ?", titre="Quatre chiffres, aucun décompte indépendant",
     lignes=[{"affiche": "7 000 – 8 000", "valeur": 7500, "libelle": "le préfet, samedi vers 17 h", "source": "La Provence, direct"},
             {"affiche": "+ 30 000", "valeur": 30000, "libelle": "la préfecture de police, dimanche", "source": "Made in Marseille, Gomet'"},
             {"affiche": "1 500", "valeur": 1500, "libelle": "« des policiers et des gradés », selon le maire", "source": "ICI Provence, 19/10",
              "a": A("s11_1500", "parlent")},
             {"affiche": "≈ 10 000", "valeur": 10000, "libelle": "des policiers cités par Europe 1", "source": "Europe 1, 19/10",
              "a": A("s11_10000")}],
     note="Aucune méthode de comptage n'a été publiée.", note_a=A("s11_quatre"))
plan("P51", 11, A("s11_centime"), "constat", kicker="Le maire", texte="Indemniser les commerçants « au centime près ».", ghost="€")
plan("P52", 11, A("s11_controle"), "citation", texte="Oui, il y a eu une perte de contrôle.",
     qui="Laurent Nuñez, ministre de l'Intérieur", source="France Inter, 19/10 (cité par ICI)")
plan("P53", 11, A("s11_demission"), "constat", kicker="Paris · Élysée", texte="Démission de Laurent Nuñez refusée", ghost="19.10",
     sous="« La nécessité d'un commandement continu des forces de l'ordre »", sous_a=A("s11_demission", "nécessité"))
plan("P54", 11, A("s11_interdit"), "constat", kicker="Marseille · lundi 19 octobre", texte="Rassemblements interdits de 12 h à 20 h", ghost="12 → 20",
     sous="La visite du ministre de l'Intérieur est reportée.", sous_a=A("s11_interdit", "visite"))

# 12 — Ce que l'on sait --------------------------------------------------------------------------------
plan("P55", 12, A("s12_sait"), "fin", colonnes=[
    {"titre": "Ce que l'on sait", "a": A("s12_sait"),
     "lignes": ["Dès 8 h : blocage au Prado", "Avant midi : premiers pillages signalés", "Mi-journée : l'hôtel de ville forcé",
                "Vers 2 h : des commerces encore attaqués"],
     "a_lignes": [A("s12_sait", "Prado"), A("s12_sait", "pillages"), A("s12_sait", "l'hôtel"), A("s12_sait", "nuit.")]},
    {"titre": "Ce qui reste incertain", "a": A("s12_incertain"),
     "lignes": ["Le nombre réel de pilleurs", "Le nombre de commerces touchés", "Les effectifs réellement engagés", "L'heure précise de plusieurs faits"],
     "a_lignes": [A("s12_incertain", "pilleurs,"), A("s12_incertain", "commerces"), A("s12_incertain", "effectifs"), A("s12_incertain", "l'heure")]},
    {"titre": "La question ouverte", "a": A("s12_question"),
     "lignes": ["Pourquoi le centre a-t-il pu être pillé de la fin de matinée jusque dans la nuit ?",
                "« Des réponses claires » attendues (Emmanuel Macron) ; non publiées au 19 octobre"],
     "a_lignes": [A("s12_question", "pourquoi"), A("s12_macron")]}])

# Sources de fin (sans voix) ----------------------------------------------------------------------------
script = json.loads((Path(__file__).resolve().parent / "script.json").read_text())
utilisees = []
for ph in script["phrases"]:
    for s in ph.get("sources", []):
        if s not in utilisees and s != "OSM":
            utilisees.append(s)
lignes = [f'{script["sources"][s]["media"]} ({script["sources"][s]["date"]}) — {script["sources"][s]["titre"]}' for s in utilisees]
moitie = (len(lignes) + 1) // 2
plans.append({"id": "P56", "seq": 12, "type": "credits", "duree": 9.0, "kicker": "Sources (lues entre le 17 et le 19 octobre 2026)",
              "blocs": [{"titre": "Articles et directs", "lignes": lignes[:moitie]}, {"titre": "", "lignes": lignes[moitie:]}]})
plans.append({"id": "P57", "seq": 12, "type": "credits", "duree": 8.0, "kicker": "Fabrication", "blocs": [
    {"titre": "Images", "lignes": ["Aucune image des événements du 17 octobre.",
                                   "Cartes : © contributeurs d'OpenStreetMap (ODbL), données du 19/10/2026.",
                                   "Photos des lieux en temps normal : Wikimedia Commons (auteurs et licences en description)."]},
    {"titre": "Son", "lignes": ["Voix de synthèse : Google Gemini (TTS).", "Musique composée par programme, libre de droits."]},
    {"titre": "Méthode", "lignes": ["Heures « direct » : heure de mise en ligne d'une entrée de direct ; le fait peut être antérieur.",
                                    "Chiffres attribués à leur source ; aucun n'est présenté comme établi.",
                                    "Personne privée ni personne interpellée identifiable."]}]})

# Horloge du samedi (6 h → 3 h) : seules des heures publiées ; les périodes sont des bandes ---------------------
horloge = {
    "debut": A("s3_prado"), "fin": A("s10_matin", decalage=-0.4),
    "marques": [
        {"de": "8:00", "type": "publiee", "revele": A("s3_prado")},
        {"de": "8:14", "type": "direct", "revele": A("s3_gaz")},
        {"de": "8:54", "type": "direct", "revele": A("s3_gaz", "54,")},
        {"de": "9:20", "type": "direct", "revele": A("s3_castellane", "signalés")},
        {"de": "9:34", "type": "direct", "revele": A("s3_reformes", "préfecture,")},
        {"de": "10:19", "type": "direct", "revele": A("s3_reformes", "Saint-Charles,")},
        {"de": "10:43", "type": "direct", "revele": A("s3_reformes", "millier")},
        {"de": "11:28", "type": "direct", "revele": A("s4_poste", "attaqué")},
        {"de": "11:46", "type": "direct", "revele": A("s4_magasins", "46,")},
        {"de": "11:54", "type": "direct", "revele": A("s4_magasins", "54,")},
        {"de": "12:00", "a": "13:20", "type": "periode", "revele": A("s5_mairie", "mi-journée,")},
        {"de": "13:20", "type": "direct", "revele": A("s5_heure", "20,")},
        {"de": "14:00", "type": "prevue", "revele": A("s6_14h")},
        {"de": "14:51", "type": "direct", "revele": A("s6_cortege")},
        {"de": "15:02", "type": "direct", "revele": A("s8_bourse")},
        {"de": "15:25", "type": "publiee", "revele": A("s7_1525")},
        {"de": "15:39", "type": "direct", "revele": A("s8_feu")},
        {"de": "16:03", "type": "direct", "revele": A("s7_lp")},
        {"de": "16:45", "a": "17:15", "type": "periode", "revele": A("s9_point")},
        {"de": "18:00", "type": "publiee", "revele": A("s9_18h")},
        {"de": "19:09", "type": "direct", "revele": A("s9_nuit")},
        {"de": "19:45", "a": "20:15", "type": "periode", "revele": A("s9_nuit", "vers")},
        {"de": "21:45", "a": "22:15", "type": "periode", "revele": A("s9_107")},
        {"de": "25:45", "a": "26:15", "type": "periode", "revele": A("s9_2h", "2")},
    ],
    "curseur": [
        {"h": "8:00", "a": A("s3_prado")}, {"h": "8:54", "a": A("s3_gaz", "54,")}, {"h": "9:20", "a": A("s3_castellane", "signalés")},
        {"h": "10:43", "a": A("s3_reformes", "millier")}, {"h": "11:28", "a": A("s4_poste", "attaqué")},
        {"h": "11:54", "a": A("s4_magasins", "54,")}, {"h": "13:20", "a": A("s5_heure", "20,")}, {"h": "14:00", "a": A("s6_14h")},
        {"h": "14:51", "a": A("s6_cortege")}, {"h": "15:25", "a": A("s7_1525")}, {"h": "16:03", "a": A("s7_lp")},
        {"h": "15:02", "a": A("s8_bourse")}, {"h": "15:39", "a": A("s8_feu")}, {"h": "17:00", "a": A("s9_point")},
        {"h": "18:00", "a": A("s9_18h")}, {"h": "19:09", "a": A("s9_nuit")}, {"h": "22:00", "a": A("s9_107")},
        {"h": "26:00", "a": A("s9_2h", "2")},
    ],
}
sortie = Path(__file__).resolve().parent / "plans.json"
sortie.write_text(json.dumps({"plans": plans, "horloge": horloge}, ensure_ascii=False, indent=1))
print(f"plans.json : {len(plans)} plans")
