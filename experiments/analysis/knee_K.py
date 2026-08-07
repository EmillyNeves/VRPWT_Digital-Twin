#!/usr/bin/env python3
"""Análise de convergência (JOELHO) para FIXAR o critério de parada K.

K (iterações sem melhoria) é um ORÇAMENTO, monótono em qualidade: mais K nunca
piora o gap. Calibrá-lo pelo gap (irace) o leva ao teto do intervalo. A forma
metodologicamente correta é DESACOPLAR: FIXAR K pelo joelho da curva gap×K
(onde mais paciência rende retorno desprezível) e calibrar apenas os parâmetros
de qualidade a esse K fixo.

Para cada algoritmo, varremos K nas instâncias de TREINO (com os parâmetros de
qualidade correntes) e escolhemos o MENOR K cujo gap médio está a <= EPS_PP pontos
percentuais do gap no maior K testado (o joelho).

Saída: experiments/config/fixed_K.json + results/figures/knee_K.png
"""
import csv
import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
SOLVER = os.path.join(ROOT, "solver", "build", "solve")
INPUT = os.path.join(ROOT, "data", "instances", "solomon")
REFS = os.path.join(ROOT, "data", "reference-solutions", "dinamics")
TRAIN = os.path.join(ROOT, "experiments", "config", "train.txt")
OUT_JSON = os.path.join(ROOT, "experiments", "config", "fixed_K.json")
FIG = os.path.join(ROOT, "results", "figures", "knee_K.png")

EPS_PP = 0.10   # joelho: gap a <= 0,10 ponto percentual do melhor

# parâmetros de QUALIDADE correntes (sem K); varremos K separadamente
QUALITY = {"grasp": "--alpha 0.1596",
           "rgrasp": "--delta 1.7822 --block 183",
           "tabu": "--tenure 35"}
KGRID = {"grasp": [20, 40, 60, 90, 130, 180, 250],
         "rgrasp": [20, 40, 60, 90, 130, 180, 250],
         "tabu": [100, 200, 400, 600, 900, 1400]}
SEEDS = {"grasp": 3, "rgrasp": 3, "tabu": 1}
COLOR = {"grasp": "#2ca02c", "rgrasp": "#1f77b4", "tabu": "#d62728"}


def ref_cost(name):
    for line in open(os.path.join(REFS, name + ".sol"), errors="ignore"):
        if "ost" in line:
            m = re.search(r"[-+]?\d+\.?\d*", line)
            if m:
                return float(m.group())
    return None


def run(algo, name, K, seed):
    out = subprocess.run(
        [SOLVER, "--algo", algo, "--instance", os.path.join(INPUT, name + ".txt"),
         "--seed", str(seed), "--budget-ms", "600000", "--max-no-improve", str(K),
         "--print-cost"] + QUALITY[algo].split(),
        capture_output=True, text=True)
    try:
        cost = float(out.stdout.strip().splitlines()[-1])
        ref = ref_cost(name)
        return (cost - ref) / ref * 100.0
    except Exception:
        return None


def main():
    names = [l.strip() for l in open(TRAIN) if l.strip()]
    tasks = []
    for algo in QUALITY:
        for K in KGRID[algo]:
            for name in names:
                for s in range(1, SEEDS[algo] + 1):
                    tasks.append((algo, name, K, s))
    print(f"{len(tasks)} execuções (treino={len(names)} instâncias)...")

    gaps = {}  # (algo,K) -> list of gaps
    with ThreadPoolExecutor(max_workers=14) as ex:
        futs = {ex.submit(run, *t): t for t in tasks}
        done = 0
        for fu in futs:
            pass
        for fu in list(futs):
            g = fu.result(); t = futs[fu]
            done += 1
            if g is not None:
                gaps.setdefault((t[0], t[2]), []).append(g)
            if done % 200 == 0:
                print(f"  {done}/{len(tasks)}")

    fixed = {}
    fig, ax = plt.subplots(figsize=(8, 5))
    summary = []
    for algo in QUALITY:
        Ks = KGRID[algo]
        means = [sum(gaps[(algo, K)]) / len(gaps[(algo, K)]) for K in Ks]
        best = min(means)
        # joelho: menor K cujo gap <= best + EPS_PP
        knee = next((K for K, m in zip(Ks, means) if m <= best + EPS_PP), Ks[-1])
        fixed[algo] = knee
        for K, m in zip(Ks, means):
            summary.append({"algo": algo, "K": K, "gap_mean_pct": round(m, 4)})
        ax.plot(Ks, means, "o-", color=COLOR[algo], label=f"{algo} (joelho K={knee})")
        ax.axvline(knee, color=COLOR[algo], ls=":", alpha=0.6)
        print(f"  {algo:7s}: joelho K={knee}  gaps={[round(m,3) for m in means]}")

    ax.set_xlabel("K (iterações sem melhoria)"); ax.set_ylabel("gap médio no treino (%)")
    ax.set_title("Seleção de K pelo joelho da curva gap×K (instâncias de treino)")
    ax.legend(); ax.grid(ls=":", alpha=0.4); fig.tight_layout()
    os.makedirs(os.path.dirname(FIG), exist_ok=True)
    fig.savefig(FIG, dpi=150, bbox_inches="tight")

    json.dump(fixed, open(OUT_JSON, "w"), indent=2)
    with open(os.path.join(ROOT, "results", "knee_K.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["algo", "K", "gap_mean_pct"]); w.writeheader(); w.writerows(summary)
    print(f"\nK fixo por joelho: {fixed}\nJSON: {OUT_JSON}\nfigura: {FIG}")


if __name__ == "__main__":
    main()
