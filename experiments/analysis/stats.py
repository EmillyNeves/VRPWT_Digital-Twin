#!/usr/bin/env python3
"""Non-parametric comparison across algorithms (Demsar 2006).

Builds an instance x algorithm matrix of the per-instance mean metric (gap% by
default), runs the Friedman test, the Nemenyi post-hoc, and draws a
critical-difference diagram. Restrict to the test instances with --instance-list.
"""
import argparse
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import friedmanchisquare
import scikit_posthocs as sp

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))   # raiz do repositorio
_RES  = os.path.join(_ROOT, "results")


ALGO_ORDER = ["i1", "vnd", "grasp", "rgrasp", "tabu"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-csv", default=os.path.join(_RES, "raw", "runs.csv"))
    ap.add_argument("--out-dir", default=_RES)
    ap.add_argument("--fig-dir", default=os.path.join(_RES, "figures"))
    ap.add_argument("--metric", default="gap_pct", choices=["gap_pct", "distance"])
    ap.add_argument("--instance-list", default=None, help="restrict to these instances (e.g. test set)")
    args = ap.parse_args()
    os.makedirs(args.fig_dir, exist_ok=True)

    df = pd.read_csv(args.runs_csv)
    if args.instance_list and os.path.isfile(args.instance_list):
        keep = {l.strip() for l in open(args.instance_list) if l.strip()}
        df = df[df["instance"].isin(keep)]

    agg = df.groupby(["algorithm", "instance"])[args.metric].mean().reset_index()
    mat = agg.pivot(index="instance", columns="algorithm", values=args.metric).dropna(axis=0)
    algos = [a for a in ALGO_ORDER if a in mat.columns] + [a for a in mat.columns if a not in ALGO_ORDER]
    mat = mat[algos]

    if mat.shape[0] < 2 or mat.shape[1] < 3:
        print(f"dados insuficientes para Friedman (instancias={mat.shape[0]}, algoritmos={mat.shape[1]})")
        return

    stat, p = friedmanchisquare(*[mat[a].values for a in mat.columns])
    ranks = mat.rank(axis=1, method="average")        # lower metric => better => rank 1
    avg_ranks = ranks.mean(axis=0)

    nem = sp.posthoc_nemenyi_friedman(mat.values)
    nem.index = mat.columns
    nem.columns = mat.columns
    nem.to_csv(os.path.join(args.out_dir, "nemenyi_pvalues.csv"))

    print(f"Friedman: chi2={stat:.4f}  p={p:.6g}  (instancias={mat.shape[0]}, algoritmos={mat.shape[1]})")
    print("\nRanks medios (menor = melhor):")
    print(avg_ranks.sort_values().to_string())
    print("\nNemenyi p-values:")
    print(nem.round(4).to_string())

    plt.rcParams.update({"font.size": 12})
    plt.figure(figsize=(9, 2.6))
    sp.critical_difference_diagram(avg_ranks, nem)
    metric_label = "gap (\\%)" if args.metric == "gap_pct" else "distância"
    plt.title("Diagrama de diferença crítica — " + metric_label.replace("\\%", "%")
              + "\n(teste de Friedman + pós-teste de Nemenyi, " + r"$\alpha=0{,}05$)")
    plt.tight_layout()
    cd_path = os.path.join(args.fig_dir, "cd_diagram.png")
    plt.savefig(cd_path, dpi=150)
    print(f"\nDiagrama CD salvo em {cd_path}")


if __name__ == "__main__":
    main()
