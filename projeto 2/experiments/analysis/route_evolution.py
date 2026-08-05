#!/usr/bin/env python3
"""Plot the route graph at each move of a search (route-evolution).

Reads a snapshot file produced by `solve --snapshots` (one line per accepted
move: idx;ms;cost;movetype;route1|route2|...) and the Solomon instance for the
coordinates. Produces individual per-move frames, a multi-panel summary, and
optionally an animated GIF.
"""
import argparse
import os
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_instance(path):
    coords = {}
    section = None
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
                coords[int(t[0])] = (float(t[1]), float(t[2]))
    return coords


def read_snapshots(path):
    snaps = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line:
            continue
        parts = line.split(";")
        if len(parts) < 5:
            continue
        idx, ms, cost, mtype, routes = parts[0], parts[1], parts[2], parts[3], parts[4]
        routes = [[int(c) for c in r.split(",") if c] for r in routes.split("|") if r]
        snaps.append({"idx": int(idx), "ms": int(ms), "cost": float(cost),
                      "mtype": mtype, "routes": routes})
    return snaps


def draw(ax, coords, routes, title):
    depot = coords[0]
    xs = [c[0] for c in coords.values()]
    ys = [c[1] for c in coords.values()]
    ax.scatter(xs, ys, s=8, c="lightgray", zorder=1)
    ax.scatter([depot[0]], [depot[1]], s=80, c="black", marker="s", zorder=3)
    cmap = plt.get_cmap("tab20")
    for i, r in enumerate(routes):
        path = [0] + r + [0]
        px = [coords[n][0] for n in path]
        py = [coords[n][1] for n in path]
        ax.plot(px, py, "-o", ms=2.5, lw=1.0, color=cmap(i % 20), zorder=2)
    ax.set_title(title, fontsize=8)
    ax.set_xticks([]); ax.set_yticks([])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True, help="path to the Solomon instance .txt")
    ap.add_argument("--snapshots", required=True, help="snapshot file from solve --snapshots")
    ap.add_argument("--out-dir", default="../../results/figures/evolution")
    ap.add_argument("--frames", action="store_true", help="also dump one PNG per move")
    ap.add_argument("--gif", action="store_true", help="also build an animated GIF")
    ap.add_argument("--stride", type=int, default=1, help="use every Nth snapshot")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    coords = parse_instance(args.instance)
    snaps = read_snapshots(args.snapshots)[:: args.stride]
    if not snaps:
        print("nenhum snapshot encontrado (algoritmo construtivo nao gera movimentos?)")
        return
    name = os.path.splitext(os.path.basename(args.instance))[0]

    # multi-panel summary: up to 8 evenly spaced frames
    k = min(8, len(snaps))
    picks = [snaps[round(i * (len(snaps) - 1) / max(1, k - 1))] for i in range(k)]
    cols = 4
    rows = (k + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(3 * cols, 3 * rows), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for ax, sn in zip(axes.flat, picks):
        ax.axis("on")
        draw(ax, coords, sn["routes"], f"mov {sn['idx']} | {sn['mtype']}\ncusto {sn['cost']:.1f}")
    fig.suptitle(f"Evolucao das rotas — {name}")
    fig.tight_layout()
    summary = os.path.join(args.out_dir, f"evolution_{name}.png")
    fig.savefig(summary, dpi=150)
    plt.close(fig)
    print(f"painel-resumo salvo em {summary}")

    frame_paths = []
    if args.frames or args.gif:
        fdir = os.path.join(args.out_dir, f"frames_{name}")
        os.makedirs(fdir, exist_ok=True)
        for sn in snaps:
            fig, ax = plt.subplots(figsize=(5, 5))
            draw(ax, coords, sn["routes"], f"{name}  mov {sn['idx']}  {sn['mtype']}  custo {sn['cost']:.1f}")
            fp = os.path.join(fdir, f"frame_{sn['idx']:05d}.png")
            fig.savefig(fp, dpi=110)
            plt.close(fig)
            frame_paths.append(fp)
        print(f"{len(frame_paths)} frames em {fdir}")

    if args.gif and frame_paths:
        try:
            from PIL import Image
            imgs = [Image.open(p) for p in frame_paths]
            gif = os.path.join(args.out_dir, f"evolution_{name}.gif")
            imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=200, loop=0)
            print(f"GIF salvo em {gif}")
        except Exception as e:
            print(f"nao foi possivel gerar GIF ({e})")


if __name__ == "__main__":
    main()
