#!/usr/bin/env python3
"""Render the Digital Twin: a per-cycle map animation + a metrics figure.

Map frames show bins colored by fill level, the active (above-threshold) bins,
the depot, and the routes the solver (re)planned that cycle. Saves PNG frames,
an animated GIF, and a metrics plot (active bins & routing distance per cycle).
"""
import argparse
import math
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

from twin import simulate, load_map, compare_algorithms, plan_routes

HORIZON, SERVICE = 5000, 5
ALGO_NAME = {"i1": "Solomon I1", "vnd": "VND", "grasp": "GRASP", "rgrasp": "GRASP reativo", "tabu": "Busca Tabu"}


def _aspect(cmap):
    if cmap.display_is_lonlat:
        lat0 = sum(b.dy for b in cmap.bins) / len(cmap.bins)
        return 1.0 / math.cos(math.radians(lat0))
    return "equal"


def draw_cycle(ax, cmap, snap, norm, cmap_colors):
    bx = [b.dx for b in cmap.bins]
    by = [b.dy for b in cmap.bins]
    fills = snap["fills"]
    ax.scatter(bx, by, c=fills, cmap=cmap_colors, norm=norm, s=42, zorder=2,
               edgecolors="none")
    # highlight active bins
    ax.scatter([cmap.bins[i].dx for i in snap["active"]],
               [cmap.bins[i].dy for i in snap["active"]],
               s=110, facecolors="none", edgecolors="red", linewidths=1.3, zorder=3)
    # mark overflowing bins (reached 100% = transbordou)
    full = snap.get("full", [])
    if full:
        ax.scatter([cmap.bins[i].dx for i in full], [cmap.bins[i].dy for i in full],
                   s=80, c="black", marker="X", zorder=5)
    ax.scatter([cmap.depot.dx], [cmap.depot.dy], marker="s", s=120, c="#1f4e79", zorder=4)
    palette = plt.get_cmap("tab20")
    for k, route in enumerate(snap["routes"]):
        path = [cmap.depot] + [cmap.bins[i] for i in route] + [cmap.depot]
        ax.plot([n.dx for n in path], [n.dy for n in path], "-",
                lw=1.2, color=palette(k % 20), zorder=1)
    ax.set_title(f"ciclo {snap['cycle']:02d} | {snap['period']} | ativas={len(snap['active'])} | "
                 f"transbordando={len(snap.get('full', []))} | veic={snap['vehicles']} | "
                 f"dist={snap['distance']:.1f}", fontsize=9)
    ax.set_xticks([]); ax.set_yticks([])
    asp = _aspect(cmap)
    if asp != "equal":
        ax.set_aspect(asp)


def render(cmap, history, out_dir, make_gif=True):
    os.makedirs(out_dir, exist_ok=True)
    fdir = os.path.join(out_dir, "frames")
    os.makedirs(fdir, exist_ok=True)
    norm = Normalize(0.0, 1.0)
    cmap_colors = "YlOrRd"

    frame_paths = []
    for snap in history:
        fig, ax = plt.subplots(figsize=(6, 6))
        draw_cycle(ax, cmap, snap, norm, cmap_colors)
        sm = ScalarMappable(norm=norm, cmap=cmap_colors)
        sm.set_array([])
        fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.04, label="nivel de enchimento")
        fig.tight_layout()
        fp = os.path.join(fdir, f"cycle_{snap['cycle']:03d}.png")
        fig.savefig(fp, dpi=110)
        plt.close(fig)
        frame_paths.append(fp)

    gif_path = None
    if make_gif and frame_paths:
        try:
            from PIL import Image
            imgs = [Image.open(p) for p in frame_paths]
            gif_path = os.path.join(out_dir, "twin.gif")
            imgs[0].save(gif_path, save_all=True, append_images=imgs[1:], duration=600, loop=0)
        except Exception as e:
            print(f"GIF falhou: {e}")

    # metrics figure
    cycles = [h["cycle"] for h in history]
    active = [len(h["active"]) for h in history]
    dist = [h["distance"] for h in history]
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.bar(cycles, active, color="tab:orange", alpha=0.6, label="lixeiras coletadas")
    ax1.set_xlabel("ciclo de monitoramento")
    ax1.set_ylabel("lixeiras coletadas", color="tab:orange")
    ax2 = ax1.twinx()
    ax2.plot(cycles, dist, "o-", color="tab:blue", label="distancia")
    ax2.set_ylabel("distancia (un. roteamento)", color="tab:blue")
    ax1.set_title(f"Digital Twin — {cmap.name} (transbordos acumulados: {history[-1]['overflow']})")
    fig.tight_layout()
    metrics_path = os.path.join(out_dir, "metrics.png")
    fig.savefig(metrics_path, dpi=130)
    plt.close(fig)

    return gif_path, metrics_path, len(frame_paths)


def _draw_routes(ax, cmap, fills, active, routes, title):
    ax.scatter([b.dx for b in cmap.bins], [b.dy for b in cmap.bins], c=fills, cmap="YlOrRd",
               vmin=0, vmax=1, s=28, zorder=2)
    ax.scatter([cmap.bins[i].dx for i in active], [cmap.bins[i].dy for i in active],
               s=85, facecolors="none", edgecolors="red", linewidths=0.9, zorder=3)
    ax.scatter([cmap.depot.dx], [cmap.depot.dy], marker="s", s=90, c="black", zorder=4)
    pal = plt.get_cmap("tab20")
    for k, r in enumerate(routes):
        path = [cmap.depot] + [cmap.bins[i] for i in r] + [cmap.depot]
        ax.plot([n.dx for n in path], [n.dy for n in path], "-", lw=1.0, color=pal(k % 20), zorder=1)
    ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    if cmap.display_is_lonlat:
        ax.set_aspect(_aspect(cmap))


def render_before_after(cmap, active, fills, rb, db, ra, da, out_dir, algo_before, algo_after):
    os.makedirs(out_dir, exist_ok=True)
    ganho = (db - da) / db * 100.0 if db > 0 else 0.0
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 6.2))
    _draw_routes(a1, cmap, fills, active, rb,
                 f"Antes — {ALGO_NAME.get(algo_before, algo_before)}\nΣ dist = {db:.0f} | {len(rb)} rotas")
    _draw_routes(a2, cmap, fills, active, ra,
                 f"Depois — {ALGO_NAME.get(algo_after, algo_after)}\nΣ dist = {da:.0f} | "
                 f"ganho = {db - da:.0f} ({ganho:.1f}%)")
    fig.suptitle(f"Otimização da rota num ciclo de pico — {cmap.name} ({len(active)} lixeiras)", fontsize=12)
    fig.tight_layout()
    path = os.path.join(out_dir, "before_after.png")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path, ganho


def render_algo_comparison(comp, cmap_name, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    algos = list(comp.keys())
    totals = [comp[a]["kpis"]["distancia_total"] for a in algos]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax1.bar(algos, totals, color="tab:green")
    ax1.set_ylabel("distancia total (un. roteamento)")
    ax1.set_title("Distancia total por algoritmo")
    for a in algos:
        ax2.plot(comp[a]["per_cycle"], marker="o", ms=3, label=a)
    ax2.set_xlabel("ciclo"); ax2.set_ylabel("distancia do ciclo")
    ax2.set_title("Distancia por ciclo"); ax2.legend()
    fig.suptitle(f"Algoritmos aplicados no Digital Twin — {cmap_name}")
    fig.tight_layout()
    path = os.path.join(out_dir, "algo_comparison.png")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["solomon", "wcvrptw", "vitoria"], default="vitoria")
    ap.add_argument("--arg", default=None)
    ap.add_argument("--cycles", type=int, default=24)
    ap.add_argument("--threshold", type=float, default=0.6)
    ap.add_argument("--algo", default="grasp")
    ap.add_argument("--budget-ms", type=int, default=800)
    ap.add_argument("--capacity", type=int, default=30)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--compare-algos", action="store_true",
                    help="apply all algorithms in the Twin and plot the comparison")
    ap.add_argument("--algos", default="i1,vnd,grasp,rgrasp,tabu")
    ap.add_argument("--before-after", action="store_true",
                    help="before/after route optimization (I1 vs --algo-after) on a peak cycle")
    ap.add_argument("--algo-after", default="grasp")
    args = ap.parse_args()

    cmap = load_map(args.source, args.arg)
    out_dir = args.out_dir or os.path.join("../results/digital_twin", args.source)

    if args.before_after:
        hist = simulate(cmap, cycles=args.cycles, threshold=args.threshold, algo="i1",
                        budget_ms=args.budget_ms, capacity=args.capacity)
        snap = max(hist, key=lambda h: len(h["active"]))      # busiest (peak) cycle
        active, fills = snap["active"], snap["fills"]
        rb, db = plan_routes(cmap, active, fills, "i1", args.budget_ms, args.capacity,
                             HORIZON, SERVICE, True, args.threshold)
        ra, da = plan_routes(cmap, active, fills, args.algo_after, args.budget_ms, args.capacity,
                             HORIZON, SERVICE, True, args.threshold)
        path, ganho = render_before_after(cmap, active, fills, rb, db, ra, da, out_dir,
                                          "i1", args.algo_after)
        print(f"antes (i1): {db:.0f} | depois ({args.algo_after}): {da:.0f} | ganho {ganho:.1f}%")
        print(f"figura: {path}")
        return

    if args.compare_algos:
        algos = [a.strip() for a in args.algos.split(",") if a.strip()]
        comp = compare_algorithms(cmap, cycles=args.cycles, algos=algos, threshold=args.threshold,
                                  budget_ms=args.budget_ms, capacity=args.capacity)
        path = render_algo_comparison(comp, cmap.name, out_dir)
        for a, r in comp.items():
            print(f"  {a:8s} dist={r['kpis']['distancia_total']:.1f} "
                  f"coletas={r['kpis']['coletas']} transbordos={r['kpis']['transbordos']}")
        print(f"comparacao de algoritmos: {path}")
        return

    history = simulate(cmap, cycles=args.cycles, threshold=args.threshold, algo=args.algo,
                       budget_ms=args.budget_ms, capacity=args.capacity)
    gif, metrics, nframes = render(cmap, history, out_dir)
    print(f"{cmap.name}: {nframes} frames")
    print(f"GIF: {gif}")
    print(f"metricas: {metrics}")


if __name__ == "__main__":
    main()
