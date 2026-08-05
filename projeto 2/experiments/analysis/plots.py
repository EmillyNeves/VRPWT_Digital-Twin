#!/usr/bin/env python3
"""Convergence curves and gap boxplots."""
import argparse
import glob
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ALGO_ORDER = ["i1", "vnd", "grasp", "rgrasp", "tabu"]


def convergence(instance, trace_dir, fig_dir, budget_ms):
    plt.figure(figsize=(7, 4.5))
    plotted = 0
    for algo in ALGO_ORDER:
        files = sorted(glob.glob(os.path.join(trace_dir, f"{algo}_{instance}_s*.csv")))
        if not files:
            continue
        df = pd.read_csv(files[0])
        if df.empty:
            continue
        plt.step(df["elapsed_ms"], df["best"], where="post", label=algo)
        plotted += 1
    if plotted == 0:
        print(f"sem tracos para {instance}")
        return
    if budget_ms:
        plt.axvline(budget_ms, ls="--", c="gray", lw=1, label="orcamento")
    plt.xlabel("tempo (ms)")
    plt.ylabel("melhor distancia")
    plt.title(f"Convergencia — {instance}")
    plt.legend()
    plt.tight_layout()
    path = os.path.join(fig_dir, f"convergence_{instance}.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"convergencia salva em {path}")


def boxplot(runs_csv, fig_dir):
    df = pd.read_csv(runs_csv)
    if "gap_pct" not in df or df["gap_pct"].dropna().empty:
        print("sem gap_pct para boxplot")
        return
    algos = [a for a in ALGO_ORDER if a in set(df["algorithm"])]
    data = [df[df["algorithm"] == a]["gap_pct"].dropna().values for a in algos]
    plt.figure(figsize=(7, 4.5))
    plt.boxplot(data, tick_labels=algos, showmeans=True)
    plt.ylabel("gap% ao best-known")
    plt.title("Distribuicao do gap% por algoritmo")
    plt.grid(axis="y", ls=":", alpha=0.5)
    plt.tight_layout()
    path = os.path.join(fig_dir, "boxplot_gap.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"boxplot salvo em {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-csv", default="../../results/raw/runs.csv")
    ap.add_argument("--trace-dir", default="../../results/raw/traces")
    ap.add_argument("--fig-dir", default="../../results/figures")
    ap.add_argument("--instance", default=None, help="instance for the convergence plot")
    ap.add_argument("--budget-ms", type=int, default=0)
    args = ap.parse_args()
    os.makedirs(args.fig_dir, exist_ok=True)

    boxplot(args.runs_csv, args.fig_dir)
    if args.instance:
        convergence(args.instance, args.trace_dir, args.fig_dir, args.budget_ms)


if __name__ == "__main__":
    main()
