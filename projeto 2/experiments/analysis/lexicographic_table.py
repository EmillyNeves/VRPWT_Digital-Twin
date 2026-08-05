#!/usr/bin/env python3
"""Tabela complementar LEXICOGRÁFICA (veículos -> distância).

Cruza os nossos melhores resultados de distância (GRASP, de per_instance.csv) com
as duas referências (Dinamics = mínima distância; SINTEF = mínimo de veículos, de
results/baseline_compare.csv) e resume por família. Mostra, de forma transparente,
que nossa solução de distância acompanha a referência de distância (Dinamics) e,
como ela, usa mais veículos que a referência lexicográfica (SINTEF) — a "contagem
alta" de veículos é a assinatura esperada da minimização de distância.

Saída: results/lexicographic_table.csv + resumo por família no stdout.
"""
import csv
import os
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
PERINST = os.path.join(ROOT, "results", "per_instance.csv")
BASE = os.path.join(ROOT, "results", "baseline_compare.csv")
OUT = os.path.join(ROOT, "results", "lexicographic_table.csv")
BEST_ALGO = "grasp"


def main():
    base = {r["instance"]: r for r in csv.DictReader(open(BASE))}
    ours = {r["instance"]: r for r in csv.DictReader(open(PERINST)) if r["algorithm"] == BEST_ALGO}

    rows = []
    for inst, b in base.items():
        o = ours.get(inst)
        if not o:
            continue
        rows.append({
            "instance": inst, "family": b["family"], "type": b["type"],
            "our_dist": float(o["dist_best"]), "our_veh": round(float(o["veh_mean"])),
            "din_dist": float(b["din_dist"]), "din_veh": int(b["din_veh"]),
            "sin_dist": float(b["sin_dist"]), "sin_veh": int(b["sin_veh"]),
        })

    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["instance", "family", "type", "our_dist", "our_veh",
                                           "din_dist", "din_veh", "sin_dist", "sin_veh"])
        w.writeheader(); w.writerows(rows)

    # resumo por família (médias)
    agg = defaultdict(lambda: defaultdict(list))
    for r in rows:
        for k in ("our_dist", "our_veh", "din_dist", "din_veh", "sin_dist", "sin_veh"):
            agg[r["family"]][k].append(r[k])
        for k in ("our_dist", "our_veh", "din_dist", "din_veh", "sin_dist", "sin_veh"):
            agg["TODAS"][k].append(r[k])

    def mean(xs):
        return sum(xs) / len(xs)

    print(f"{'família':8s} | {'nosso (GRASP)':>16s} | {'Dinamics (dist.)':>16s} | {'SINTEF (veíc.)':>16s}")
    print(f"{'':8s} | {'veíc.  dist.':>16s} | {'veíc.  dist.':>16s} | {'veíc.  dist.':>16s}")
    print("-" * 70)
    for fam in ["C", "R", "RC", "TODAS"]:
        a = agg[fam]
        print(f"{fam:8s} | {mean(a['our_veh']):5.1f} {mean(a['our_dist']):9.1f} | "
              f"{mean(a['din_veh']):5.1f} {mean(a['din_dist']):9.1f} | "
              f"{mean(a['sin_veh']):5.1f} {mean(a['sin_dist']):9.1f}")
    print(f"\nCSV: {OUT}")


if __name__ == "__main__":
    main()
