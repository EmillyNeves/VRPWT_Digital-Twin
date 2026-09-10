#!/usr/bin/env python3
"""Análise de sensibilidade do Digital Twin (prova de conceito).

Varia, um de cada vez, os parâmetros de MODELAGEM do cenário de coleta — limiar de
acionamento, capacidade do veículo e coeficiente de urgência da janela dinâmica —
mantendo a mesma realização de enchimento (mesma semente). Para cada valor, mede o
compromisso entre **distância total** e **transbordos**. O objetivo é justificar as
escolhas de parâmetros com evidência, em vez de fixá-las arbitrariamente — exatamente
a lacuna apontada na avaliação metodológica.

Saída: results/digital_twin/sensitivity.csv + results/digital_twin/sensitivity.png

Uso (com o venv): .venv/bin/python digital_twin/sensitivity.py [--algo grasp] [--cycles 16]
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from maps import load_vitoria
from twin import simulate, kpis, load_tuned

_HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(_HERE, "..", "results", "digital_twin")

# valores padrão (centro de cada varredura)
DEF = dict(threshold=0.70, capacity=30, urgency_coef=0.60)   # capacidade 30 = a da comparacao pareada (twin.simulate)
SWEEPS = {
    "threshold":    [0.50, 0.60, 0.70, 0.80, 0.90],
    "capacity":     [15, 20, 25, 30, 40],
    "urgency_coef": [0.0, 0.3, 0.6, 0.9],
}
LABEL = {"threshold": "limiar de coleta", "capacity": "capacidade do veículo",
         "urgency_coef": "coef. de urgência"}


def run_point(cmap, algo, cycles, budget, seed, extra, **params):
    p = dict(DEF, **params)
    hist = simulate(cmap, cycles=cycles, threshold=p["threshold"], algo=algo,
                    budget_ms=budget, capacity=p["capacity"], seed=seed, extra=extra,
                    urgency_coef=p["urgency_coef"])
    return kpis(hist)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo", default="grasp")
    ap.add_argument("--cycles", type=int, default=16)
    ap.add_argument("--budget-ms", type=int, default=300)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(OUTDIR, exist_ok=True)
    cmap = load_vitoria()
    extra = load_tuned().get(args.algo, "")
    print(f"mapa: {cmap.name} ({len(cmap.bins)} lixeiras) · algoritmo {args.algo}")

    rows = []
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, (param, values) in zip(axes, SWEEPS.items()):
        dists, overs = [], []
        for v in values:
            k = run_point(cmap, args.algo, args.cycles, args.budget_ms, args.seed, extra, **{param: v})
            dists.append(k["distancia_total"]); overs.append(k["transbordos"])
            rows.append({"parametro": param, "valor": v, "distancia_total": k["distancia_total"],
                         "coletas": k["coletas"], "transbordos": k["transbordos"]})
            print(f"  {param}={v}: dist={k['distancia_total']:.0f} transbordos={k['transbordos']}")
        ax.plot(values, dists, "o-", color="seagreen", label="distância total")
        ax.set_xlabel(LABEL[param]); ax.set_ylabel("distância total", color="seagreen")
        ax.tick_params(axis="y", labelcolor="seagreen")
        ax2 = ax.twinx()
        ax2.plot(values, overs, "s--", color="crimson", label="transbordos")
        ax2.set_ylabel("transbordos", color="crimson"); ax2.tick_params(axis="y", labelcolor="crimson")
        ax.set_title(f"Sensibilidade: {LABEL[param]}")
        ax.grid(ls=":", alpha=0.4)
    fig.suptitle(f"Digital Twin (Vitória/ES, prova de conceito) — compromisso distância × transbordos "
                 f"[{args.algo}]", y=1.02)
    fig.tight_layout()
    figpath = os.path.join(OUTDIR, "sensitivity.png")
    fig.savefig(figpath, dpi=150, bbox_inches="tight")

    with open(os.path.join(OUTDIR, "sensitivity.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["parametro", "valor", "distancia_total", "coletas", "transbordos"])
        w.writeheader(); w.writerows(rows)
    print(f"\nfigura: {figpath}\nCSV: {os.path.join(OUTDIR, 'sensitivity.csv')}")


if __name__ == "__main__":
    main()
