# Étape 4 — Instructions de génération, plan par plan

Chaque bloc ci-dessous se suffit à lui-même : on peut le copier tel quel dans n'importe quel générateur d'images.
Le **bloc de style** et la **liste « à éviter »** sont donc répétés dans chaque plan.

> **Ce qui a réellement été utilisé pour cette version.** Aucun générateur payant ni aucun crédit.
> Les illustrations ont été **peintes par code**, de façon reproductible, avec `scripts/02_illustrations.py` :
> scènes construites en formes simples, puis rendu en touches de pinceau et texture de toile (`scripts/peinture.py`).
> Les blocs ci-dessous décrivent les mêmes plans. Ils servent si l'on veut, plus tard, les régénérer avec un modèle d'image.
> Dans ce cas, un modèle payant consomme des crédits : **demander l'accord avant de lancer la génération.**
>
> Format de sortie de chaque image : 1242 × 2208 px (9:16, 15 % de marge pour les mouvements de caméra lents), PNG.
> Toutes ces images reçoivent à l'écran l'étiquette **ILLUSTRATION** en haut à gauche.

---

## Bloc de style (répété dans chaque plan)

```
STYLE — illustration historique, peinture à l'huile moderne, touches de pinceau visibles, texture de toile,
couleurs sourdes et chaudes (bruns, ocres, rouge sombre, or éteint), lumière unique et dirigée, clair-obscur doux,
composition verticale 9:16 avec le sujet au centre, haut et bas laissés calmes (zones de texte),
ambiance documentaire sobre, Paris 1911-1913. Image en couleur.
```

## À éviter (répété dans chaque plan)

```
À ÉVITER — visage reconnaissable d'une personne réelle (montrer silhouette, dos, mains ou ombre seulement) ;
faux noir et blanc, faux grain de film, fausses rayures, faux sépia « archive » ; faux document d'époque
(journal, fiche de police, lettre, tampon, signature, écriture lisible) ; texte, lettres ou chiffres dans l'image ;
reproduction ou réinterprétation de La Joconde ou de toute autre œuvre réelle ; logos, uniformes modernes,
objets anachroniques (néons, plastique, ampoules LED, voitures modernes) ; frontières sur une carte ; gore, violence ;
style photo-réaliste ou 3D lisse.
```

---

### P01 et P25 — Le mur vide (ouverture et boucle)
```
SUJET — Musée du Louvre, Salon Carré, 22 août 1911 au matin : un pan de mur tendu de tissu rouge sombre,
au centre un emplacement vide entouré de cadres dorés d'autres tableaux (toiles sombres, sans motif lisible),
quatre petits crochets de fer plantés dans le mur à l'emplacement vide, éclairage de verrière en haut à gauche.
Pas de personnage. Mention : illustration historique, reconstitution.
+ STYLE + À ÉVITER
```
P25 réutilise **la même image** que P01 : la boucle est exacte. Ne pas la régénérer séparément.

### P02 — Les crochets
```
SUJET — Gros plan sur deux crochets de fer forgé plantés dans un mur tendu de tissu rouge sombre,
leurs ombres portées nettes, une trace plus claire sur le tissu à l'emplacement du tableau disparu.
Pas de personnage, pas de cadre. Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P03 et P22 — La Joconde — **NE PAS GÉNÉRER**
Utiliser la **reproduction authentique** (`assets/oeuvre/joconde-reproduction.jpg`), posée entière sur fond sombre.
Le bandeau du haut est laissé libre pour l'étiquette **ARCHIVE**, la légende « Léonard de Vinci, La Joconde · Musée du Louvre » et le carton (`scripts/02b_oeuvre.py`).

### P04 — Le peintre copiste
```
SUJET — Le même mur du Salon Carré, emplacement vide et quatre crochets ; au premier plan à gauche, un peintre
en manteau et chapeau melon, VU DE DOS, en silhouette ; à droite, son chevalet dont on ne voit que le DOS de la toile
(lin brut et châssis en bois, aucune image peinte visible). Aucun visage.
Mention : illustration historique, reconstitution.
+ STYLE + À ÉVITER
```

### P05 — Chez le photographe ?
```
SUJET — Atelier photographique vers 1911 : une chambre photographique en bois à soufflet sur un trépied,
objectif en laiton, voile noir de mise au point, lumière latérale d'une fenêtre, parquet. Pas de personnage, pas de texte.
Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P06 et P20 — L'escalier : le cadre vide
```
SUJET — Escalier de service en pierre du Louvre, 1911, lumière d'une haute fenêtre : sur les marches au premier plan,
un cadre doré VIDE et une plaque de verre (la vitre de protection) abandonnés. Pas de personnage.
Mention : illustration historique, reconstitution.
+ STYLE + À ÉVITER
```

### P07 — La foule devant le mur vide
```
SUJET — Le même mur du Salon Carré, emplacement vide et quatre crochets ; au premier plan, une foule de visiteurs
de 1911 VUS DE DOS, en silhouettes (chapeaux melon, canotiers, capelines), qui regardent l'emplacement vide.
Aucun visage. Mention : illustration historique, reconstitution.
+ STYLE + À ÉVITER
```

### P08 — Le bureau du juge d'instruction
```
SUJET — Bureau d'un juge d'instruction à Paris en 1911 : boiseries vert sombre, grand bureau en bois, lampe à
abat-jour vert, quelques feuilles VIERGES, fauteuil vide ; au premier plan, un homme en manteau et chapeau melon,
VU DE DOS, en silhouette. Aucun visage, aucun texte.
Mention : illustration historique, scène générique (le lieu exact de l'audition n'est pas représenté).
+ STYLE + À ÉVITER
```

### P09 — Prison de la Santé
```
SUJET — Intérieur d'une cellule de prison vers 1911 : mur de pierres appareillées, petite fenêtre haute à barreaux,
un rai de lumière oblique et l'ombre des barreaux sur le mur, une planche-lit en bois, sol de pierre.
Pas de personnage. Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P10 — L'empreinte
```
SUJET — Une plaque de verre de vitrine de musée en lumière rasante, fond bleu-vert sombre, cadre fin :
sur le verre, une empreinte de pouce apparaît en reflet clair (motif générique, pas une vraie empreinte).
Pas de personnage, pas de texte. Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P11 — Le fichier de police
```
SUJET — Un grand meuble-fichier de police en bois vers 1911, des dizaines de petits tiroirs avec porte-étiquettes
en laiton VIDES, un tiroir ouvert au premier plan rempli de fiches cartonnées VIERGES, sans aucune écriture.
Pas de personnage. Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P12 — La loupe
```
SUJET — Vue plongeante sur un bureau en bois : la plaque de verre portant l'empreinte (motif générique),
une loupe à monture de laiton posée dessus qui agrandit les sillons. Lumière de lampe chaude. Pas de texte.
Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P13 — La chambre (entrée en fondu)
```
SUJET — Chambre mansardée parisienne la nuit, entre 1911 et 1913 : fenêtre à petits carreaux, toits de Paris et
cheminées en silhouette, pleine lune ; un lit simple et une table dans la pénombre bleue. La cachette du tableau
n'est PAS montrée. Pas de personnage. Mention : illustration historique.
+ STYLE (palette bleu nuit pour ce plan) + À ÉVITER
```

### P14 — Carte schématique — **NE PAS GÉNÉRER**
La carte est **construite à partir de données réelles** avec `scripts/03_carte.py` :
- terres émergées Natural Earth 1:50m (paquet npm `world-atlas@2.0.2`, domaine public), **sans aucune frontière** ;
- projection Mercator ;
- Paris (48,857° N ; 2,352° E) et Florence (43,770° N ; 11,256° E) placées à leurs coordonnées ;
- l'arc Paris → Florence est **schématique** (ce n'est pas l'itinéraire réel) ;
- étiquette à l'écran : **CARTE SCHÉMATIQUE**.

### P15 — Chez l'antiquaire, à Florence — **image composite**
```
SUJET — Boutique d'antiquaire à Florence en décembre 1913 : étagères de vases anciens, suspension, grande table ;
au centre, un panneau posé sur un support, laissé VIDE et sombre (il sera rempli par la reproduction authentique) ;
au premier plan, deux hommes en manteau et chapeau melon, VUS DE DOS. Aucun visage, aucun texte.
Mention : illustration historique, reconstitution.
+ STYLE + À ÉVITER
```
Puis coller la **reproduction authentique** dans l'emplacement, **après** le rendu pictural (`finish(..., protect=...)`).

### P16 — L'arrestation
```
SUJET — Couloir d'un hôtel modeste à Florence en décembre 1913 : papier peint ancien, parquet, une porte entrouverte
d'où sort une lumière chaude ; deux hommes en manteau et chapeau, VUS DE DOS, devant la porte.
Aucun visage, aucun nom d'hôtel lisible. Mention : illustration historique, reconstitution générique.
+ STYLE + À ÉVITER
```

### P17 — Le vitrier
```
SUJET — Une salle du Louvre avant le vol : mur rouge et cadres dorés, une vitrine de protection en bois et verre,
vide, fixée au mur ; une plaque de verre posée contre le mur ; au premier plan, un ouvrier en blouse blanche et
casquette, VU DE DOS. Aucun visage. Mention : illustration historique, reconstitution.
+ STYLE + À ÉVITER
```

### P18 — La vitrine — **image composite**
```
SUJET — Atelier de vitrier dans un musée vers 1911 : une vitrine de protection en bois et verre posée contre le mur,
reflet de lumière sur le verre ; sur l'établi au premier plan, une règle, un diamant de vitrier, une plaque de verre.
L'intérieur de la vitrine est laissé VIDE et sombre. Mention : illustration historique.
+ STYLE + À ÉVITER
```
Puis coller la **reproduction authentique** dans la vitrine, après la peinture : l'œuvre n'est jamais repeinte.

### P19 — L'escalier, le lundi 21 août
```
SUJET — Escalier de service en pierre du Louvre, 1911, lumière d'une haute fenêtre : un homme en blouse blanche
d'ouvrier et casquette, VU DE DOS, dans l'escalier ; au premier plan, sur les marches, un cadre doré VIDE abandonné.
Le tableau n'est pas montré. Aucun visage. Mention : illustration historique, reconstitution.
+ STYLE + À ÉVITER
```

### P21 — Le procès
```
SUJET — Salle d'audience à Florence en juin 1914 : boiseries, grande baie cintrée lumineuse, estrade de la cour
avec trois hauts dossiers VIDES ; devant la balustrade, l'accusé debout, VU DE DOS, sans chapeau ; au premier plan,
quelques têtes du public de dos. Aucun visage, aucun texte, aucun emblème.
Mention : illustration historique, reconstitution générique.
+ STYLE + À ÉVITER
```

### P23 — Le retour au Louvre — **image composite**
```
SUJET — Le mur du Salon Carré le 4 janvier 1914 : au centre, un cadre doré de nouveau accroché, son intérieur laissé
VIDE (il sera rempli par la reproduction authentique) ; au premier plan, la foule de 1914 VUE DE DOS (chapeaux melon,
canotiers, capelines). Aucun visage. Mention : illustration historique, reconstitution.
+ STYLE + À ÉVITER
```
Puis coller la **reproduction authentique** dans le cadre, après la peinture.

### P24 — La Joconde, détail — **NE PAS GÉNÉRER**
Recadrage du visage **dans la reproduction authentique**, agrandi par interpolation (aucune génération).
Étiquette **ARCHIVE**, légende « La Joconde (détail) · Musée du Louvre ».

---

## Archives réelles à chercher pour remplacer les illustrations (à faire avant publication si possible)

| Plan | Archive à chercher | Où chercher |
|---|---|---|
| P01 / P07 / P25 | Photographie du mur vide du Salon Carré (1911), avec les crochets ; photographies de la foule à la réouverture | Gallica (BnF), Roger-Viollet, Agence Rol |
| P08 | Photographie d'Apollinaire en 1911 (sans retouche) | Gallica, Archives de Paris |
| P11 | Fiche anthropométrique de Peruggia (préfecture de police) | Musée de la préfecture de police, publications |
| P15 / P16 | Une du *Petit Parisien* ou du *Petit Journal* de décembre 1913 | Gallica (presse numérisée, domaine public) |
| P06 / P19 / P20 | Photographie de l'escalier de service et du cadre retrouvé | Gallica, Agence Rol |
| P21 | Photographie de Peruggia au procès de Florence (1914) | Gallica, archives de presse italiennes |
| P23 | Photographie du retour de la Joconde au Louvre (janvier 1914) | Gallica, Agence Rol |

Si une vraie archive remplace une illustration : passer l'étiquette en **ARCHIVE**, ajouter la légende (source et date),
et ne **jamais** la coloriser ni l'animer en faux mouvement.
