#!/usr/bin/env python3
"""Time-to-target (TTT) plot (Aiex, Resende & Ribeiro).

For many independent runs of one stochastic algorithm on one instance, computes
the time to first reach a target cost (from each run's convergence trace) and
plots the empirical cumulative probability P(time <= t). Runs that never reach
the target are reported as not-reached.

Generate the runs with, e.g.:
  python runner.py --instance-list <one> --algos grasp --runs 200 --budget-ms 30000 --target <cost>
(--target makes runs stop as soon as the target is hit, so TTT runs are cheap.)
"""
import argparse
import glob
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))   # raiz do repositorio
_RES  = os.path.join(_ROOT, "results")



def time_to_target(trace_path, target):
    df = pd.read_csv(trace_path)
    hit = df[df["best"] <= target + 1e-6]
    return float(hit["elapsed_ms"].iloc[0]) if not hit.empty else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace-dir", default=os.path.join(_RES, "raw", "traces"))
    ap.add_argument("--algo", required=True)
    ap.add_argument("--instance", required=True)
    ap.add_argument("--target-cost", type=float, required=True)
    ap.add_argument("--fig-dir", default=os.path.join(_RES, "figures"))
    args = ap.parse_args()
    os.makedirs(args.fig_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(args.trace_dir, f"{args.algo}_{args.instance}_s*.csv")))
    if not files:
        print(f"sem tracos para {args.algo} em {args.instance}")
        return

    times, reached = [], 0
    for f in files:
        t = time_to_target(f, args.target_cost)
        if t is not None:
            times.append(t); reached += 1
    n = len(files)
    print(f"runs={n} atingiram_alvo={reached} ({100.0 * reached / n:.1f}%)")
    if not times:
        print("nenhum run atingiu o alvo; aumente o orcamento ou relaxe o alvo")
        return

    times.sort()
    # standard TTT plotting position: p_i = (i - 0.5)/N
    probs = [(i + 0.5) / n for i in range(len(times))]
    plt.figure(figsize=(7, 4.5))
    plt.step(times, probs, where="post")
    plt.xlabel("tempo para atingir o alvo (ms)")
    plt.ylabel("probabilidade acumulada")
    plt.title(f"TTT — {args.algo} em {args.instance} (alvo={args.target_cost:.1f})")
    plt.ylim(0, 1)
    plt.grid(ls=":", alpha=0.5)
    plt.tight_layout()
    path = os.path.join(args.fig_dir, f"ttt_{args.algo}_{args.instance}.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"TTT salvo em {path}")


if __name__ == "__main__":
    main()
