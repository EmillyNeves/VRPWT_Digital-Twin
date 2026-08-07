#!/usr/bin/env python3
"""Roteamento do Digital Twin sobre a MALHA VIÁRIA REAL de Vitória/ES.

Diferente do twin euclidiano (linha reta), aqui o solver recebe a matriz de
DISTÂNCIA real (metros, OSRM) e a matriz de TEMPO real (segundos de direção),
de modo que:
  - o custo otimizado é a distância RODOVIÁRIA total (não a linha reta);
  - as janelas de tempo e a espera usam o TEMPO REAL de direção.

Também desenha as rotas seguindo a GEOMETRIA REAL das ruas (OSRM route service).
Pré-requisito: rodar `road_network.py` uma vez para cachear a matriz e as ruas.

Uso:  .venv/bin/python digital_twin/road_twin.py [--algo grasp] [--capacity 60] [--threshold 0.0]
"""
import argparse
import json
import math
import os
import subprocess
import tempfile
import urllib.request

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from maps import load_vitoria
from road_network import load_matrix, build_cache, STREETS_CACHE
from sensors import FillSimulator

_HERE = os.path.dirname(os.path.abspath(__file__))
SOLVER = os.environ.get("VRPTW_SOLVER", os.path.join(_HERE, "..", "solver", "build", "solve"))
OUTDIR = os.path.join(_HERE, "..", "results", "digital_twin", "vitoria")
PALETTE = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#46f0f0",
           "#f032e6", "#bcf60c", "#fabebe", "#008080", "#9a6324", "#800000"]

HORIZON_S = 6 * 3600     # turno de 6 h, em segundos (escala da matriz de tempo)
SERVICE_S = 120          # 2 min de serviço por lixeira


def _demands(fills, threshold, demand_max=9):
    return [max(1, round(f * demand_max) + 1) for f in fills]


def build_instance_and_matrices(active_idx, fills, capacity, td):
    """Escreve a instância (depósito + bins ativos) e as submatrizes dist/tempo.
    Os nós da instância são [depósito(0), bin active_idx[0], ...]; os índices na
    matriz cheia são [0, active_idx[0]+1, ...]."""
    m = load_matrix()
    nodes = m["nodes"]; D = m["dist_m"]; T = m["time_s"]
    full = [0] + [i + 1 for i in active_idx]              # índices na matriz cheia
    dem = _demands([fills[i] for i in active_idx], 0.0)

    inst = os.path.join(td, "road.txt")
    with open(inst, "w") as f:
        f.write("VITORIA_ROAD\n\nVEHICLE\nNUMBER     CAPACITY\n")
        f.write(f" {max(1,len(active_idx))}  {capacity}\n\n")
        f.write("CUSTOMER\nCUST NO.  XCOORD.  YCOORD.  DEMAND  READY  DUE  SERVICE\n\n")
        # XCOORD/YCOORD são irrelevantes (a distância vem da matriz); usamos lon/lat só p/ registro
        f.write(f"0 {nodes[0]['lon']:.5f} {nodes[0]['lat']:.5f} 0 0 {HORIZON_S} 0\n")
        for j, i in enumerate(active_idx, start=1):
            f.write(f"{j} {nodes[i+1]['lon']:.5f} {nodes[i+1]['lat']:.5f} "
                    f"{dem[j-1]} 0 {HORIZON_S} {SERVICE_S}\n")

    def submatrix(M):
        return [[M[a][b] for b in full] for a in full]
    dpath = os.path.join(td, "dist.txt"); tpath = os.path.join(td, "time.txt")
    for path, M in ((dpath, submatrix(D)), (tpath, submatrix(T))):
        with open(path, "w") as f:
            f.write(f"{len(full)}\n")
            for row in M:
                f.write(" ".join(f"{x:.1f}" for x in row) + "\n")
    return inst, dpath, tpath, full


def parse_sol(path, active_idx):
    """Lê o .sol e mapeia os ids da instância (1..n) de volta para os índices dos bins."""
    routes, cost = [], None
    for line in open(path, encoding="utf-8", errors="ignore"):
        s = line.strip().lower()
        if s.startswith("route"):
            nums = [int(x) for x in line.split(":", 1)[1].split()] if ":" in line else []
            routes.append([active_idx[n - 1] for n in nums if 1 <= n <= len(active_idx)])
        elif s.startswith("cost"):
            try: cost = float(line.split()[-1])
            except ValueError: pass
    return routes, cost


def route_road(active_idx, fills, algo="grasp", capacity=60, extra=""):
    if not active_idx:
        return [], 0.0
    with tempfile.TemporaryDirectory() as td:
        inst, dpath, tpath, _ = build_instance_and_matrices(active_idx, fills, capacity, td)
        sol = os.path.join(td, "road.sol")
        cmd = [SOLVER, "--algo", algo, "--instance", inst, "--dist-matrix", dpath,
               "--time-matrix", tpath, "--out", sol, "--budget-ms", "2000"] + (extra.split() if extra else [])
        subprocess.run(cmd, capture_output=True, text=True)
        return parse_sol(sol, active_idx)


def osrm_leg_geometry(waypoints_lonlat, timeout=30):
    """Geometria real de direção (lista de [lon,lat]) ligando os waypoints, via OSRM."""
    coords = ";".join(f"{lo},{la}" for lo, la in waypoints_lonlat)
    url = (f"https://router.project-osrm.org/route/v1/driving/{coords}"
           f"?overview=full&geometries=geojson")
    try:
        r = json.load(urllib.request.urlopen(url, timeout=timeout))
        if r.get("code") == "Ok":
            return r["routes"][0]["geometry"]["coordinates"]
    except Exception:
        pass
    return waypoints_lonlat   # fallback: linhas retas


def visualize(cmap, routes, fig_path):
    fig, ax = plt.subplots(figsize=(11, 11))
    # ruas reais (cinza)
    if os.path.isfile(STREETS_CACHE):
        streets = json.load(open(STREETS_CACHE))
        for ft in streets["features"]:
            xs = [c[0] for c in ft["geometry"]["coordinates"]]
            ys = [c[1] for c in ft["geometry"]["coordinates"]]
            ax.plot(xs, ys, color="#d9d9d9", lw=0.5, zorder=1)
    depot = cmap.depot
    # rotas seguindo as ruas reais (OSRM)
    for k, r in enumerate(routes):
        if not r:
            continue
        wpts = [(depot.dx, depot.dy)] + [(cmap.bins[i].dx, cmap.bins[i].dy) for i in r] + [(depot.dx, depot.dy)]
        geom = osrm_leg_geometry(wpts)
        xs = [c[0] for c in geom]; ys = [c[1] for c in geom]
        ax.plot(xs, ys, color=PALETTE[k % len(PALETTE)], lw=2.4, zorder=3,
                label=f"Caminhão {k+1} ({len(r)} lixeiras)")
    # lixeiras + depósito
    served = [i for r in routes for i in r]
    ax.scatter([cmap.bins[i].dx for i in served], [cmap.bins[i].dy for i in served],
               c="black", s=18, zorder=4)
    ax.scatter([depot.dx], [depot.dy], marker="*", c="#1f4e79", s=380, zorder=5,
               edgecolors="white", label="depósito (AMARIV)")
    ax.set_title("Digital Twin — rotas sobre a malha viária REAL de Vitória/ES\n"
                 "(distância e tempo de direção reais via OSRM/OpenStreetMap)", fontsize=12)
    ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.set_aspect(1.0 / math.cos(math.radians(depot.dy)))
    fig.tight_layout(); fig.savefig(fig_path, dpi=140, bbox_inches="tight"); plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo", default="grasp")
    ap.add_argument("--capacity", type=int, default=60)
    ap.add_argument("--threshold", type=float, default=0.0,
                    help="0 = roteia todos os 38 PEVs; >0 = só os acima do enchimento")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    build_cache()                          # garante o cache (matriz + ruas)
    cmap = load_vitoria()
    sim = FillSimulator(len(cmap.bins), seed=args.seed)
    for c in range(3):
        sim.step(c)                        # algumas rodadas para encher
    fills = list(sim.fill)
    active = [i for i in range(len(cmap.bins)) if fills[i] >= args.threshold]

    routes, cost = route_road(active, fills, algo=args.algo, capacity=args.capacity)
    # KPIs reais
    m = load_matrix(); D = m["dist_m"]; T = m["time_s"]
    tot_d = tot_t = 0.0
    for r in routes:
        seq = [0] + [i + 1 for i in r] + [0]
        for a, b in zip(seq, seq[1:]):
            tot_d += D[a][b]; tot_t += T[a][b]
    tot_t += SERVICE_S * sum(len(r) for r in routes)
    os.makedirs(OUTDIR, exist_ok=True)
    figp = os.path.join(OUTDIR, "vitoria_road_routes.png")
    visualize(cmap, routes, figp)
    print(f"PEVs roteados: {sum(len(r) for r in routes)} | caminhões: {len([r for r in routes if r])}")
    print(f"distância rodoviária total: {tot_d/1000:.1f} km")
    print(f"tempo de operação estimado: {tot_t/3600:.2f} h (direção {sum(T[s][e] for r in routes for s,e in zip([0]+[i+1 for i in r],[i+1 for i in r]+[0]))/3600:.2f} h + serviço)")
    print(f"figura: {figp}")


if __name__ == "__main__":
    main()
