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

### P01 et P14 — Le mur vide (00,00 → 03,13 et 44,50 → 47,53)
```
SUJET — Musée du Louvre, Salon Carré, 22 août 1911 au matin : un pan de mur tendu de tissu rouge sombre,
au centre un emplacement vide entouré de cadres dorés d'autres tableaux (toiles sombres, sans motif lisible),
quatre petits crochets de fer plantés dans le mur à l'emplacement vide, éclairage de verrière en haut à gauche.
Pas de personnage. Mention : illustration historique, reconstitution.
+ STYLE (voir bloc) + À ÉVITER (voir bloc)
```
Remarque : P14 réutilise **la même image** que P01, pour que la boucle soit exacte. Ne pas la régénérer à part.

### P02 — Les crochets (03,13 → 06,07)
```
SUJET — Gros plan sur deux crochets de fer forgé plantés dans un mur tendu de tissu rouge sombre,
leurs ombres portées nettes, une trace plus claire sur le tissu à l'emplacement du tableau disparu.
Pas de personnage, pas de cadre. Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P03 — La Joconde (06,07 → 08,17) — **NE PAS GÉNÉRER**
Œuvre réelle : utiliser **la reproduction authentique** (`assets/oeuvre/joconde-reproduction.jpg`), posée entière sur un fond sombre.
Étiquette **ARCHIVE**, légende « Léonard de Vinci, La Joconde · Musée du Louvre ». Script : `scripts/02b_oeuvre.py`.

### P04 — Soupçons (08,17 → 10,63)
```
SUJET — Rue de Paris en 1911, matin brumeux, façades haussmanniennes estompées, pavés mouillés :
un homme en manteau et chapeau melon, vu de dos, encadré par deux agents de police en pèlerine et képi,
eux aussi de dos, qui s'éloignent vers le fond. Silhouettes seulement, aucun visage.
Mention : illustration historique, scène générique (les circonstances exactes de l'arrestation ne sont pas documentées ici).
+ STYLE + À ÉVITER
```

### P05 — Prison de la Santé (10,63 → 14,27)
```
SUJET — Intérieur d'une cellule de prison vers 1911 : mur de pierres appareillées, petite fenêtre haute à barreaux,
un rai de lumière oblique et l'ombre des barreaux sur le mur, une planche-lit en bois, sol de pierre.
Pas de personnage. Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P06 — L'empreinte (14,27 → 17,30)
```
SUJET — Une plaque de verre de vitrine de musée en lumière rasante, fond bleu-vert sombre, cadre fin :
sur le verre, une empreinte de pouce apparaît en reflet clair (motif d'empreinte générique, pas une vraie empreinte).
Pas de personnage, pas de texte. Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P07 — Le fichier (17,30 → 21,00)
```
SUJET — Un grand meuble-fichier de police en bois vers 1911, des dizaines de petits tiroirs avec porte-étiquettes en laiton
VIDES, un tiroir ouvert au premier plan rempli de fiches cartonnées vierges, vues de dessus, sans aucune écriture.
Pas de personnage. Mention : illustration historique.
+ STYLE + À ÉVITER
```

### P08 — La chambre (21,00 → 25,03, entrée en fondu)
```
SUJET — Chambre mansardée parisienne la nuit, entre 1911 et 1913 : fenêtre à petits carreaux, toits de Paris et cheminées
en silhouette, pleine lune ; un lit simple et une table dans la pénombre bleue. La cachette du tableau n'est PAS montrée.
Pas de personnage. Mention : illustration historique.
+ STYLE (palette bleu nuit pour ce plan) + À ÉVITER
```

### P09 — Carte schématique (25,03 → 29,80) — **NE PAS GÉNÉRER**
La carte est **construite à partir de données réelles** avec `scripts/03_carte.py` :
- terres émergées Natural Earth 1:50m (paquet npm `world-atlas@2.0.2`, domaine public), **sans aucune frontière** ;
- projection Mercator ;
- Paris (48,857° N ; 2,352° E) et Florence (43,770° N ; 11,256° E) placées à leurs coordonnées ;
- l'arc Paris → Florence est **schématique** (ce n'est pas l'itinéraire réel) ;
- étiquette à l'écran : **CARTE SCHÉMATIQUE**.

Si on la refait dans un autre outil, ne tracer **aucune frontière**, ni actuelle ni de 1913. On évite ainsi tout anachronisme.

### P10 — L'arrestation (29,80 → 33,80)
```
SUJET — Couloir d'un hôtel modeste à Florence en décembre 1913 : papier peint ancien, parquet, une porte entrouverte
d'où sort une lumière chaude ; deux hommes en manteau et chapeau, vus de dos, se tiennent devant la porte.
Silhouettes seulement, aucun visage, aucun nom d'hôtel lisible.
Mention : illustration historique, reconstitution générique.
+ STYLE + À ÉVITER
```

### P11 — La vitrine (33,80 → 36,67) — **image composite**
```
SUJET — Atelier de vitrier dans un musée vers 1911 : une vitrine de protection en bois et verre posée contre le mur,
reflet de lumière sur le verre ; sur l'établi au premier plan, une règle, un diamant de vitrier, une plaque de verre.
L'intérieur de la vitrine est laissé VIDE et sombre : il sera rempli par la reproduction authentique.
Mention : illustration historique.
+ STYLE + À ÉVITER
```
Puis **coller la reproduction authentique** de La Joconde dans la vitrine, **après** le rendu pictural : l'œuvre n'est jamais repeinte.
C'est ce que fait `finish(..., protect=...)` dans `scripts/02_illustrations.py`.

### P12 — L'escalier (36,67 → 40,63)
```
SUJET — Escalier de service en pierre du Louvre, 1911, lumière d'une haute fenêtre : un homme en blouse blanche d'ouvrier
et casquette, VU DE DOS, descend vers la lumière ; au premier plan, sur les marches, un cadre doré VIDE abandonné.
Silhouette seulement, aucun visage, le tableau n'est pas montré.
Mention : illustration historique, reconstitution.
+ STYLE + À ÉVITER
```

### P13 — La Joconde, détail (40,63 → 44,50) — **NE PAS GÉNÉRER**
Recadrage du visage **dans la reproduction authentique**, agrandi par interpolation (aucune génération).
Étiquette **ARCHIVE**, légende « La Joconde (détail) · Musée du Louvre ».

---

## Archives réelles à chercher pour remplacer les illustrations (à faire avant publication si possible)

| Plan | Archive à chercher | Où chercher |
|---|---|---|
| P01 / P14 | Photographie du mur vide du Salon Carré (1911), avec les crochets | Gallica (BnF), Roger-Viollet, Agence Rol |
| P04 | Photographie d'Apollinaire en 1911 (sans retouche) | Gallica, Archives de Paris |
| P07 | Fiche anthropométrique de Peruggia (préfecture de police) | Musée de la préfecture de police, publications |
| P09 / P10 | Une du *Petit Parisien* ou du *Petit Journal* de décembre 1913 | Gallica (presse numérisée, domaine public) |
| P12 | Photographie de l'escalier de service et du cadre retrouvé | Gallica, Agence Rol |

Si une vraie archive remplace une illustration : passer l'étiquette en **ARCHIVE**, ajouter la légende (source et date),
et ne **jamais** la coloriser ni l'animer en faux mouvement.
