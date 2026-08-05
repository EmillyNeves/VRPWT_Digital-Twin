#!/usr/bin/env python3
"""Map loaders for the Digital Twin.

Three sources of bin locations, all normalized to a common structure:
  - Solomon benchmark instances (planar coordinates),
  - WCVRPTW (Kim et al. 2006) waste-collection instances (feet),
  - real selective-collection points of Vitoria/ES (lon/lat from the city GIS).

Each node carries routing coordinates `rx, ry` (normalized to a ~0..100 box so
the C++ solver behaves consistently across sources) and display coordinates
`dx, dy` (lon/lat for Vitoria, raw planar otherwise).
"""
from dataclasses import dataclass, field
import json
import math
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


@dataclass
class Node:
    id: int
    rx: float
    ry: float
    dx: float
    dy: float
    label: str = ""


@dataclass
class CityMap:
    name: str
    depot: Node
    bins: list = field(default_factory=list)
    display_is_lonlat: bool = False

    def nodes(self):
        return [self.depot] + self.bins


def _normalize(coords):
    """Scale a list of (x,y) into a ~0..100 box, preserving aspect ratio."""
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    minx, miny = min(xs), min(ys)
    span = max(max(xs) - minx, max(ys) - miny) or 1.0
    return [((x - minx) / span * 100.0, (y - miny) / span * 100.0) for x, y in coords]


def _solomon_rows(path):
    rows, section = [], None
    for raw in open(path, encoding="utf-8", errors="ignore"):
        s = raw.replace("\r", "").strip()
        if not s:
            continue
        if "CUSTOMER" in s:
            section = "cust"; continue
        if section == "cust" and ("CUST" in s or "XCOORD" in s):
            continue
        if section == "cust":
            t = s.split()
            if len(t) >= 3:
                rows.append((int(t[0]), float(t[1]), float(t[2])))
    return rows


def load_solomon(name, input_dir=os.path.join(_HERE, "..", "input")):
    rows = _solomon_rows(os.path.join(input_dir, name + ".txt"))
    coords = [(x, y) for _, x, y in rows]
    norm = _normalize(coords)
    nodes = [Node(i, nx, ny, x, y, "deposito" if i == 0 else f"lixeira {rid}")
             for i, ((nx, ny), (rid, x, y)) in enumerate(zip(norm, rows))]
    return CityMap(f"Solomon {name}", nodes[0], nodes[1:], display_is_lonlat=False)


def load_wcvrptw(path):
    """Kim et al. format: 5 config lines, a header line, then
    Stop_ID X Y Early Late Service Load Type  (type 0=depot, 1=stop, 2=landfill)."""
    raw_rows = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        s = line.replace("\r", "").strip()
        if not s or "//" in s or s.lower().startswith("stop"):   # skip config/comment/header lines
            continue
        t = s.split()
        if len(t) < 8:
            continue
        try:
            raw_rows.append((int(t[0]), float(t[1]), float(t[2]), int(float(t[7]))))
        except ValueError:
            continue
    # Approach: keep only the collection points (type 1) and the central depot
    # (type 0); IGNORE intermediate depots / landfills (type 2), since our solver
    # is a pure VRPTW without mid-route unloading.
    raw_rows = [r for r in raw_rows if r[3] in (0, 1)]
    coords = [(x, y) for _, x, y, _ in raw_rows]
    norm = _normalize(coords)
    depot, bins = None, []
    for (nx, ny), (sid, x, y, typ) in zip(norm, raw_rows):
        if typ == 0 and depot is None:
            depot = Node(sid, nx, ny, x, y, "deposito central")
        elif typ == 1:
            bins.append(Node(sid, nx, ny, x, y, f"ponto de coleta {sid}"))
    if depot is None:                      # no explicit central depot: use the centroid
        depot = Node(0, sum(b.rx for b in bins) / len(bins), sum(b.ry for b in bins) / len(bins),
                     sum(b.dx for b in bins) / len(bins), sum(b.dy for b in bins) / len(bins),
                     "deposito central")
    return CityMap(f"WCVRPTW {os.path.basename(path)}", depot, bins, display_is_lonlat=False)


def load_vitoria(geojson_path=os.path.join(_HERE, "data", "vitoria_coleta_seletiva.geojson"),
                 depot_lonlat=(-40.3054441, -20.2935859),
                 depot_label="AMARIV - galpao de triagem (coleta seletiva)"):
    """Real selective-collection points (PEVs) of Vitoria/ES. Projects lon/lat to
    local meters for routing; keeps lon/lat for display. The depot defaults to the
    real AMARIV recycling-association facility (Rua Arlindo Sodre; lon/lat from
    OpenStreetMap), which receives Vitoria's selective collection. Pass
    depot_lonlat=None to fall back to the centroid of the points."""
    d = json.load(open(geojson_path, encoding="utf-8"))
    feats = d.get("features", [])
    lonlat, labels = [], []
    for ft in feats:
        lon, lat = ft["geometry"]["coordinates"][:2]
        p = ft.get("properties", {})
        lonlat.append((lon, lat))
        labels.append(p.get("nome") or p.get("logradouro") or "PEV")
    lat0 = sum(la for _, la in lonlat) / len(lonlat)
    lon0 = sum(lo for lo, _ in lonlat) / len(lonlat)

    def to_m(lon, lat):
        return ((lon - lon0) * math.cos(math.radians(lat0)) * 111320.0,
                (lat - lat0) * 110540.0)

    if depot_lonlat is None:
        depot_lonlat = (lon0, lat0)
        depot_label = "centroide dos pontos (suposicao)"
    planar = [to_m(lo, la) for lo, la in lonlat] + [to_m(*depot_lonlat)]
    norm = _normalize(planar)
    bins = [Node(i + 1, norm[i][0], norm[i][1], lonlat[i][0], lonlat[i][1], labels[i])
            for i in range(len(lonlat))]
    depot = Node(0, norm[-1][0], norm[-1][1], depot_lonlat[0], depot_lonlat[1], depot_label)
    return CityMap("Vitoria/ES - coleta seletiva", depot, bins, display_is_lonlat=True)


if __name__ == "__main__":
    for m in (load_solomon("R101"), load_wcvrptw("../wcvrptw-instances-main/instances/102_stop.txt"),
              load_vitoria()):
        print(f"{m.name}: {len(m.bins)} lixeiras + deposito; "
              f"display={'lon/lat' if m.display_is_lonlat else 'planar'}; "
              f"ex bin rx,ry=({m.bins[0].rx:.1f},{m.bins[0].ry:.1f})")
