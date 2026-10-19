"""Cartes du centre de Marseille, construites depuis les données OpenStreetMap.

Entrée : build/osm/*.json (Overpass, `out geom`, téléchargés par make.sh carte_donnees).
Sortie : assets/carte/<vue>.png (fond de carte, densité 1,5×) et assets/carte/vues.json
(pour chaque vue : taille d'affichage, échelle, et les repères projetés en pixels d'affichage).

Les repères sont pris dans OSM par leur nom (aucun tracé dessiné à la main) ; la seule
interprétation est la « zone » des rues commerçantes : l'union des tronçons nord des rues
citées par la presse, élargie de 22 m, jamais un périmètre inventé.
© contributeurs d'OpenStreetMap, données sous licence ODbL.
"""
import glob
import json
import math
import os

from PIL import Image, ImageDraw
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import linemerge, polygonize, unary_union

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
OSM = os.path.join(RACINE, "build", "osm")
SORTIE = os.path.join(RACINE, "assets", "carte")

LAT0, LON0 = 43.285, 5.381
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110950.0
BBOX = (43.266, 5.358, 43.303, 5.404)  # sud, ouest, nord, est des données bâtiments et rues
DENSITE = 1.5   # pixels du PNG par pixel d'affichage : marge pour les zooms avant
SURECH = 2      # suréchantillonnage de l'anticrénelage

PALETTE = {
    "terre": (18, 23, 30), "bati": (37, 47, 59), "bati_bord": (45, 56, 69),
    "eau": (9, 20, 31), "parc": (22, 35, 31), "digue": (33, 43, 54),
    "route_min": (44, 54, 66), "route_maj": (61, 73, 88), "pieton": (52, 63, 76),
    "rail": (54, 60, 70),
}
LARGEUR_M = {  # largeur des voies en mètres (elles grossissent avec le zoom)
    "motorway": 18, "trunk": 18, "primary": 17, "secondary": 14, "tertiary": 12,
    "motorway_link": 9, "trunk_link": 9, "primary_link": 9, "secondary_link": 8, "tertiary_link": 8,
    "residential": 8, "unclassified": 8, "living_street": 7, "pedestrian": 8, "service": 4.5,
}
MAJEURES = {"motorway", "trunk", "primary", "secondary", "tertiary"}


def proj(lat, lon):
    return ((lon - LON0) * KX, (lat - LAT0) * KY)


def charge(*motifs):
    vus, sortie = set(), []
    for motif in motifs:
        for f in sorted(glob.glob(os.path.join(OSM, motif))):
            for e in json.load(open(f))["elements"]:
                cle = (e["type"], e["id"])
                if cle in vus:
                    continue
                vus.add(cle)
                sortie.append(e)
    return sortie


def ligne(e):
    return [proj(p["lat"], p["lon"]) for p in e.get("geometry", []) if p]


def polygones_relation(e):
    externes = [LineString([proj(p["lat"], p["lon"]) for p in m["geometry"]])
                for m in e.get("members", []) if m.get("role") == "outer" and m.get("geometry")]
    return list(polygonize(linemerge(externes))) if externes else []


def mer(cotes, cadre):
    """Polygones d'eau de mer : faces du cadre découpé par le trait de côte, côté droit (convention OSM)."""
    traits = [LineString(ligne(e)) for e in cotes if len(e.get("geometry", [])) > 1]
    fusion = linemerge(unary_union(traits))
    morceaux = cadre.intersection(fusion)
    faces = list(polygonize(unary_union([cadre.boundary, morceaux])))
    temoins = []
    for t in traits:
        c = list(t.coords)
        for a, b in zip(c[::7], c[1::7]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dy)
            if n < 1:
                continue
            m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            temoins.append(Point(m[0] + 3 * dy / n, m[1] - 3 * dx / n))  # à droite du sens de tracé
    eau = []
    for f in faces:
        dedans = sum(1 for p in temoins if f.contains(p))
        dehors = sum(1 for p in temoins if f.buffer(6).contains(p)) - dedans
        if dedans > 0 and dedans >= dehors:
            eau.append(f)
    return eau


class Vue:
    def __init__(self, nom, centre, largeur_m, w=1920, h=1080):
        self.nom, self.w, self.h = nom, w, h
        self.cx, self.cy = proj(*centre)
        self.ppm = w / largeur_m  # pixels d'affichage par mètre

    def px(self, x, y, densite=1.0):
        return ((self.w / 2 + (x - self.cx) * self.ppm) * densite,
                (self.h / 2 - (y - self.cy) * self.ppm) * densite)


def ajuste(nom, points_latlon, marge_m, w=1920, h=1080):
    pts = [proj(*p) for p in points_latlon]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    larg = max(max(xs) - min(xs) + 2 * marge_m, (max(ys) - min(ys) + 2 * marge_m) * w / h)
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    lat, lon = LAT0 + cy / KY, LON0 + cx / KX
    return Vue(nom, (lat, lon), larg, w, h)


def dessine(vue, couches):
    d = DENSITE * SURECH
    img = Image.new("RGB", (int(vue.w * d), int(vue.h * d)), PALETTE["terre"])
    g = ImageDraw.Draw(img)

    def pts(coords):
        return [vue.px(x, y, d) for x, y in coords]

    def poly(p, couleur, bord=None):
        if p.is_empty:
            return
        for q in getattr(p, "geoms", [p]):
            if q.geom_type != "Polygon" or len(q.exterior.coords) < 3:
                continue
            g.polygon(pts(q.exterior.coords), fill=couleur, outline=bord)
            for trou in q.interiors:
                g.polygon(pts(trou.coords), fill=PALETTE["terre"])

    for p in couches["parcs"]:
        poly(p, PALETTE["parc"])
    for p in couches["mer"] + couches["eau"]:
        poly(p, PALETTE["eau"])
    for c in couches["digues"]:
        if len(c) > 1:
            g.line(pts(c), fill=PALETTE["digue"], width=max(1, int(3 * vue.ppm * d)))
    bord = PALETTE["bati_bord"] if vue.ppm > 0.9 else None
    for p in couches["bati"]:
        poly(p, PALETTE["bati"], bord)
    for classe, coords in couches["routes"]:
        lm = LARGEUR_M.get(classe)
        if lm is None or len(coords) < 2:
            continue
        couleur = (PALETTE["route_maj"] if classe in MAJEURES
                   else PALETTE["pieton"] if classe in ("pedestrian", "living_street") else PALETTE["route_min"])
        larg = max(1, int(round(lm * vue.ppm * d)))
        g.line(pts(coords), fill=couleur, width=larg, joint="curve")
    img = img.resize((int(vue.w * DENSITE), int(vue.h * DENSITE)), Image.LANCZOS)
    img.save(os.path.join(SORTIE, f"{vue.nom}.png"), optimize=True)


def main():
    os.makedirs(SORTIE, exist_ok=True)
    s, o, n, e = BBOX
    cadre = Polygon([proj(s, o), proj(s, e), proj(n, e), proj(n, o)])
    routes = charge("routes.json")
    cotes = [x for x in charge("cote.json") if x.get("tags", {}).get("natural") == "coastline"]
    eau_parcs = charge("eau.json")
    couches = {"routes": [], "bati": [], "parcs": [], "eau": [], "digues": [], "mer": mer(cotes, cadre)}
    for x in routes:
        couches["routes"].append((x["tags"]["highway"], ligne(x)))
    for x in charge("bati*.json"):
        c = ligne(x)
        if len(c) >= 3:
            couches["bati"].append(Polygon(c))
    for x in eau_parcs:
        t = x.get("tags", {})
        geoms = polygones_relation(x) if x["type"] == "relation" else (
            [Polygon(ligne(x))] if len(x.get("geometry", [])) >= 3 else [])
        cle = "eau" if t.get("natural") == "water" else "parcs"
        couches[cle] += [q for q in geoms if q.is_valid]
    for x in charge("digues.json"):
        couches["digues"].append(ligne(x))

    # --- Repères, tous pris dans OSM par leur nom -------------------------------------------
    def rue(nom, lat_min=None):
        segs = []
        for x in routes:
            if x.get("tags", {}).get("name") != nom:
                continue
            c = [(p["lat"], p["lon"]) for p in x["geometry"]]
            if lat_min is not None:
                c = [q for q in c if q[0] >= lat_min]
            if len(c) > 1:
                segs.append(LineString([proj(*q) for q in c]))
        m = linemerge(unary_union(segs))
        return list(getattr(m, "geoms", [m]))

    def centre_nom(nom, source=routes):
        geoms = [LineString(ligne(x)) if len(x.get("geometry", [])) > 1 else Point(ligne(x)[0])
                 for x in source if x.get("tags", {}).get("name") == nom]
        return unary_union(geoms).centroid

    batiments = charge("bati*.json")
    hdv = [Polygon(ligne(x)) for x in batiments
           if x.get("tags", {}).get("name") == "Hôtel de ville" and len(x.get("geometry", [])) >= 3]
    lignes = {
        "canebiere": rue("La Canebière"),
        "saint_ferreol": rue("Rue Saint-Ferréol", 43.2903),
        "paradis": rue("Rue Paradis", 43.2903),
        "grignan": rue("Rue Grignan"),
        "montgrand": rue("Rue Montgrand"),
        "quai_du_port": rue("Quai du Port"),
        "avenue_du_prado": rue("Avenue du Prado", 43.2712),   # tronçon rond-point → Castellane (« remontent l'avenue du Prado », La Provence)
    }
    zone = unary_union([l.buffer(22, cap_style=2) for k in ("saint_ferreol", "paradis", "grignan", "montgrand")
                        for l in lignes[k]])
    points = {
        "prado": centre_nom("Rond-Point du Prado"),
        "castellane": centre_nom("Place Castellane"),
        "hotel_de_ville": unary_union(hdv).centroid,
        "prefecture": centre_nom("Place Félix Baret"),
        "reformes": Point(proj(43.29880, 5.38551)),
        "vieux_port": Point(proj(43.29495, 5.37010)),
        "quai_des_belges": centre_nom("Quai des Belges"),
        "saint_charles": Point(proj(43.30176, 5.38053)),   # bâtiment OSM « Escalier de la gare Saint-Charles »
        "dugommier": Point(proj(43.29761, 5.38111)),       # extrémité sud du boulevard Dugommier, sur la Canebière
    }
    latlon = {k: (LAT0 + p.y / KY, LON0 + p.x / KX) for k, p in points.items()}

    vues = [
        ajuste("ensemble", [latlon["prado"], latlon["hotel_de_ville"], latlon["reformes"]], 260, 1080, 1080),
        ajuste("prado_castellane", [latlon["prado"], latlon["castellane"]], 330, 1080, 1080),
        ajuste("matin", [latlon["castellane"], latlon["saint_charles"], latlon["prefecture"], latlon["reformes"]], 120,
               1080, 1080),
        ajuste("hypercentre", [latlon["hotel_de_ville"], latlon["reformes"], latlon["prefecture"]], 170),
        ajuste("canebiere", [latlon["quai_des_belges"], latlon["reformes"]], 160),
        ajuste("quadrilatere", [(LAT0 + y / KY, LON0 + x / KX) for x, y in zone.exterior.coords]
               if zone.geom_type == "Polygon" else
               [(LAT0 + y / KY, LON0 + x / KX) for g in zone.geoms for x, y in g.exterior.coords], 120),
        ajuste("vieux_port", [latlon["hotel_de_ville"], latlon["quai_des_belges"], (43.2935, 5.3650)], 140),
    ]
    sortie = {"attribution": "© contributeurs d'OpenStreetMap (ODbL)",
              "osm_base": json.load(open(os.path.join(OSM, "routes.json")))["osm3s"]["timestamp_osm_base"],
              "vues": {}}
    for v in vues:
        dessine(v, couches)

        def enpx(geom):
            return [[round(c, 1) for c in v.px(x, y)] for x, y in geom.coords]

        sortie["vues"][v.nom] = {
            "image": f"assets/carte/{v.nom}.png", "w": v.w, "h": v.h, "densite": DENSITE,
            "px_par_m": round(v.ppm, 4),
            "lignes": {k: [enpx(l) for l in ls] for k, ls in lignes.items()},
            "zone_rues": [enpx(g.exterior) for g in getattr(zone, "geoms", [zone])],
            "points": {k: [round(c, 1) for c in v.px(p.x, p.y)] for k, p in points.items()},
        }
        print(f"{v.nom:18} {v.w}×{v.h}  {1 / v.ppm:5.2f} m/px  largeur {v.w / v.ppm:6.0f} m")
    json.dump(sortie, open(os.path.join(SORTIE, "vues.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
