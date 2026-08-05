#!/usr/bin/env python3
"""Grafo VIÁRIO REAL de Vitória/ES para o Digital Twin.

Diferente do grafo euclidiano (linha reta entre pontos), este módulo obtém:
  (1) a MATRIZ DE DISTÂNCIA e a MATRIZ DE TEMPO REAIS de direção entre o depósito
      (AMARIV) e os 38 PEVs, pela malha viária do OpenStreetMap, via serviço OSRM
      (router.project-osrm.org, table service);
  (2) a GEOMETRIA das ruas (Overpass API) na região, para desenhar as ruas reais.

Tudo é cacheado em digital_twin/data/ para não depender da rede em cada execução:
  - vitoria_road_matrix.json : {nodes, dist_m [NxN], time_s [NxN]}
  - vitoria_streets.geojson  : ruas (LineStrings) para visualização.

A distância de direção é ~1,2-1,6x a linha reta (fator de circuito real da cidade),
e o tempo é a duração real de direção — base para janelas/espera realistas no twin.
"""
import json
import math
import os
import urllib.parse
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(_HERE, "data")
MATRIX_CACHE = os.path.join(DATA, "vitoria_road_matrix.json")
STREETS_CACHE = os.path.join(DATA, "vitoria_streets.geojson")

OSRM = "https://router.project-osrm.org"
OVERPASS = "https://overpass-api.de/api/interpreter"
# vias trafegáveis por veículo (exclui calçada/ciclovia/trilha)
DRIVABLE = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified",
            "residential", "living_street", "motorway_link", "trunk_link",
            "primary_link", "secondary_link", "tertiary_link", "road"}


def _vitoria_points():
    """Depósito (AMARIV) na posição 0, seguido dos 38 PEVs (lon, lat, rótulo)."""
    from maps import load_vitoria
    cm = load_vitoria()
    pts = [(cm.depot.dx, cm.depot.dy, cm.depot.label)]
    pts += [(b.dx, b.dy, b.label) for b in cm.bins]
    return pts


def fetch_osrm_matrix(points, timeout=90):
    """Matriz NxN de distância (m) e tempo (s) de direção, via OSRM table."""
    coords = ";".join(f"{lo},{la}" for lo, la, _ in points)
    url = f"{OSRM}/table/v1/driving/{coords}?annotations=distance,duration"
    r = json.load(urllib.request.urlopen(url, timeout=timeout))
    if r.get("code") != "Ok":
        raise RuntimeError(f"OSRM falhou: {r.get('code')} {r.get('message','')}")
    return r["distances"], r["durations"]


def fetch_overpass_streets(points, margin=0.004, timeout=120):
    """Geometria das ruas trafegáveis na bbox dos pontos (Overpass)."""
    lats = [la for _, la, _ in points]
    lons = [lo for lo, _, _ in points]
    bbox = (min(lats) - margin, min(lons) - margin, max(lats) + margin, max(lons) + margin)
    q = (f"[out:json][timeout:{timeout}];"
         f"way[highway~\"^({'|'.join(DRIVABLE)})$\"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});"
         f"out geom;")
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(OVERPASS, data=data,
                                 headers={"User-Agent": "vrptw-digital-twin/1.0 (IC UFES)",
                                          "Accept": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout + 30))
    feats = []
    for el in r.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [[g["lon"], g["lat"]] for g in el["geometry"]]
        feats.append({"type": "Feature",
                      "properties": {"highway": el.get("tags", {}).get("highway", ""),
                                     "name": el.get("tags", {}).get("name", "")},
                      "geometry": {"type": "LineString", "coordinates": coords}})
    return {"type": "FeatureCollection", "features": feats}


def build_cache(force=False):
    os.makedirs(DATA, exist_ok=True)
    pts = _vitoria_points()
    if force or not os.path.isfile(MATRIX_CACHE):
        print(f"buscando matriz OSRM de {len(pts)} nós...")
        dist, time = fetch_osrm_matrix(pts)
        json.dump({"nodes": [{"lon": lo, "lat": la, "label": lb} for lo, la, lb in pts],
                   "dist_m": dist, "time_s": time}, open(MATRIX_CACHE, "w"))
        print(f"  matriz salva: {MATRIX_CACHE}")
    if force or not os.path.isfile(STREETS_CACHE):
        print("buscando ruas (Overpass)...")
        streets = fetch_overpass_streets(pts)
        json.dump(streets, open(STREETS_CACHE, "w"))
        print(f"  {len(streets['features'])} ruas salvas: {STREETS_CACHE}")
    return MATRIX_CACHE, STREETS_CACHE


def load_matrix():
    return json.load(open(MATRIX_CACHE))


def circuity_report():
    """Compara distância rodoviária x linha reta (fator de circuito médio)."""
    m = load_matrix()
    nodes = m["nodes"]; dist = m["dist_m"]
    def hav(a, b):
        R = 6371000.0
        la1, lo1, la2, lo2 = map(math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
        h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
        return 2 * R * math.asin(math.sqrt(h))
    facs = []
    n = len(nodes)
    for i in range(n):
        for j in range(n):
            if i != j and dist[i][j] and dist[i][j] > 0:
                e = hav(nodes[i], nodes[j])
                if e > 50:
                    facs.append(dist[i][j] / e)
    return sum(facs) / len(facs), min(facs), max(facs)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="refazer o download mesmo com cache")
    args = ap.parse_args()
    build_cache(force=args.force)
    avg, lo, hi = circuity_report()
    m = load_matrix()
    print(f"\nnós: {len(m['nodes'])} (depósito + {len(m['nodes'])-1} PEVs)")
    print(f"fator de circuito (rodovia/reta): médio={avg:.2f} min={lo:.2f} max={hi:.2f}")
    print(f"ex.: depósito->PEV1 = {m['dist_m'][0][1]:.0f} m, {m['time_s'][0][1]:.0f} s")
