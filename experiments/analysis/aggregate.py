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

    # ESFORCO UTIL: `time_ms` e o tempo total ate o criterio de parada disparar;
    # `time_to_best_ms` e o instante em que a melhor solucao foi encontrada. A
    # razao entre os dois diz quanto da execucao foi produtivo e quanto foi gasto
    # esperando o criterio. E o dado que sustenta (ou derruba) a alegacao de
    # comparacao em pe de igualdade, ja que uma "iteracao" custa coisas
    # diferentes em cada metodo.
    has_ttb = "time_to_best_ms" in df.columns
    if has_ttb:
        df["useful_pct"] = 100.0 * df["time_to_best_ms"].fillna(0) / df["time_ms"].clip(lower=1)

    aggs = dict(dist_mean=("distance", "mean"), dist_best=("distance", "min"),
                dist_std=("distance", "std"), veh_mean=("vehicles", "mean"),
                gap_mean=("gap_pct", "mean"), gap_best=("gap_pct", "min"),
                time_mean_ms=("time_ms", "mean"))
    if "iters" in df.columns:
        aggs["iters_mean"] = ("iters", "mean")
    if "improvements" in df.columns:
        aggs["improvements_mean"] = ("improvements", "mean")
    if has_ttb:
        aggs["time_to_best_mean_ms"] = ("time_to_best_ms", "mean")
        aggs["useful_pct_mean"] = ("useful_pct", "mean")

    per = (df.groupby(["algorithm", "instance", "family", "type"], as_index=False).agg(**aggs))
    per["dist_std"] = per["dist_std"].fillna(0.0)
    per.to_csv(os.path.join(args.out_dir, "per_instance.csv"), index=False)

    # per-family mean gap%
    fam = (per.groupby(["algorithm", "family"], as_index=False)
              .agg(gap_mean=("gap_mean", "mean")))
    fam_pivot = fam.pivot(index="algorithm", columns="family", values="gap_mean")
    fam_pivot = fam_pivot.reindex(order_algos(fam_pivot.index))
    fam_pivot.to_csv(os.path.join(args.out_dir, "gap_by_family.csv"))

    # overall
    o_aggs = dict(gap_mean=("gap_mean", "mean"), gap_best=("gap_best", "mean"),
                  veh_mean=("veh_mean", "mean"), time_mean_ms=("time_mean_ms", "mean"))
    for c in ("iters_mean", "improvements_mean", "time_to_best_mean_ms", "useful_pct_mean"):
        if c in per.columns:
            o_aggs[c] = (c, "mean")
    overall = per.groupby("algorithm").agg(**o_aggs).reindex(order_algos(per["algorithm"].unique()))
    overall.to_csv(os.path.join(args.out_dir, "overall.csv"))

    # GENERALIZACAO: o sentido da divisao 28/28 e mostrar que os parametros
    # calibrados no TREINO valem no TESTE. Sem os dois lado a lado nao ha
    # evidencia contra sobreajuste.
    cfg = os.path.join(_ROOT, "experiments", "config")
    splits = {}
    for name in ("train", "test"):
        p = os.path.join(cfg, name + ".txt")
        if os.path.isfile(p):
            splits[name] = {l.strip() for l in open(p) if l.strip()}
    gen = None
    if len(splits) == 2:
        rows = []
        for name, keep in splits.items():
            sub = per[per["instance"].isin(keep)]
            g = sub.groupby("algorithm")["gap_mean"].mean().rename(name)
            rows.append(g)
        gen = pd.concat(rows, axis=1).reindex(order_algos(per["algorithm"].unique()))
        gen["delta_pp"] = gen["test"] - gen["train"]
        gen.to_csv(os.path.join(args.out_dir, "generalization.csv"))

    # CONTAGEM DE EXECUCOES -- o rascunho do relatorio traz dois numeros
    # diferentes e ambos errados. Este e o numero, derivado do proprio CSV.
    counts = df.groupby("algorithm").size().reindex(order_algos(df["algorithm"].unique()))
    counts.to_csv(os.path.join(args.out_dir, "run_counts.csv"), header=["runs"])

    pd.set_option("display.float_format", lambda v: f"{v:.2f}")
    print("=== Gap% medio ao best-known, por familia ===")
    print(fam_pivot.to_string())
    print("\n=== Resumo geral ===")
    print(overall.to_string())
    if gen is not None:
        print("\n=== Generalizacao: gap% medio treino x teste ===")
        print(gen.to_string())
    print(f"\n=== Execucoes: {len(df)} no total ===")
    print(counts.to_string())
    print(f"\nTabelas em {args.out_dir}/ (per_instance, gap_by_family, overall, "
          f"generalization, run_counts)")


if __name__ == "__main__":
    main()
