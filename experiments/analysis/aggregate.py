#!/usr/bin/env python3
"""Aggregate the master CSV into per-instance and per-family tables.

Primary metric = total distance (gap% to best-known). Secondary = vehicles
(Solomon lexicographic view). For stochastic algorithms it reports mean/best/std
over the runs; deterministic ones have a single run.
"""
import argparse
import os
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))   # raiz do repositorio
_RES  = os.path.join(_ROOT, "results")


ALGO_ORDER = ["i1", "vnd", "grasp", "rgrasp", "tabu"]


def order_algos(idx):
    return [a for a in ALGO_ORDER if a in idx] + [a for a in idx if a not in ALGO_ORDER]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-csv", default=os.path.join(_RES, "raw", "runs.csv"))
    ap.add_argument("--out-dir", default=_RES)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    df = pd.read_csv(args.runs_csv)

    # per (algorithm, instance): aggregate over runs
    per = (df.groupby(["algorithm", "instance", "family", "type"], as_index=False)
             .agg(dist_mean=("distance", "mean"), dist_best=("distance", "min"),
                  dist_std=("distance", "std"), veh_mean=("vehicles", "mean"),
                  gap_mean=("gap_pct", "mean"), gap_best=("gap_pct", "min")))
    per["dist_std"] = per["dist_std"].fillna(0.0)
    per.to_csv(os.path.join(args.out_dir, "per_instance.csv"), index=False)

    # per-family mean gap%
    fam = (per.groupby(["algorithm", "family"], as_index=False)
              .agg(gap_mean=("gap_mean", "mean")))
    fam_pivot = fam.pivot(index="algorithm", columns="family", values="gap_mean")
    fam_pivot = fam_pivot.reindex(order_algos(fam_pivot.index))
    fam_pivot.to_csv(os.path.join(args.out_dir, "gap_by_family.csv"))

    # overall
    overall = (per.groupby("algorithm")
                  .agg(gap_mean=("gap_mean", "mean"), gap_best=("gap_best", "mean"),
                       veh_mean=("veh_mean", "mean")))
    overall = overall.reindex(order_algos(overall.index))
    overall.to_csv(os.path.join(args.out_dir, "overall.csv"))

    pd.set_option("display.float_format", lambda v: f"{v:.2f}")
    print("=== Gap% medio ao best-known, por familia ===")
    print(fam_pivot.to_string())
    print("\n=== Resumo geral (gap% medio/melhor, veiculos medios) ===")
    print(overall.to_string())
    print(f"\nTabelas salvas em {args.out_dir}/ (per_instance.csv, gap_by_family.csv, overall.csv)")


if __name__ == "__main__":
    main()
