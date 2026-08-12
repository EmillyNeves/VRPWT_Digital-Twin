#!/usr/bin/env python3
"""Análise COMPLEMENTAR: integral primal (métrica do 12º Desafio DIMACS).

A comparação PRIMÁRIA do estudo usa parada por iterações sem melhoria (reprodutível)
e gap de distância + Friedman/Nemenyi + TTT. Esta análise é COMPLEMENTAR e mede a
dimensão anytime (tempo x qualidade) pela métrica oficial da *competição* DIMACS, o
**integral primal**: para um orçamento de tempo T e o melhor-conhecido BKS,

    PI = 100 * ( [ sum_i v(i-1)*(t(i)-t(i-1)) + v(n)*(T-t(n)) ] / (T*BKS) - 1 ),

onde v(0)=1.1*BKS em t=0 e v(i) é o valor da incumbente encontrada em t(i). Menor PI
= melhor (encontra boas soluções mais cedo). RESSALVA: por usar tempo de relógio, é
DEPENDENTE DA MÁQUINA — por isso é apresentada apenas como complemento ao estudo
reprodutível. Aqui os algoritmos rodam com orçamento de tempo FIXO T (não por
iterações), com os parâmetros de qualidade calibrados (sem o critério K).

Saída: results/primal_integral.csv + results/figures/primal_integral.png
       + results/figures/anytime_convergence_<inst>.png
"""
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import os
import subprocess
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, ".."))
SOLVER = os.path.join(ROOT, "solver", "build", "solve")
INPUT = os.path.join(ROOT, "data", "instances", "solomon")
REFS = os.path.join(ROOT, "data", "reference-solutions", "dinamics")
TUNED = os.path.join(_HERE, "config", "tuned.json")

# Orçamento de tempo fixo, IGUAL para todos os métodos, com o critério por
# iterações sem melhoria DESATIVADO (ver _quality_flags). É a leitura
# complementar à parada por convergência: lá cada método para quando a própria
# curva achata (e gasta de 0% a 60% do tempo produzindo, conforme medido em
# docs/verificacao/04-criterio-de-parada.md); aqui todos recebem o mesmo T.
# Não é o 1800s da competição DIMACS -- é o teto viável neste hardware.
T_MS = 20000
INSTANCES = None      # None => conjunto de TESTE (experiments/config/test.txt)


def _quality_flags(spec):
    """Mantém apenas os parâmetros de QUALIDADE calibrados, descartando o critério
    de parada por iterações sem melhoria (--max-no-improve N): este experimento roda
    por tempo fixo T, então o algoritmo deve usar o orçamento inteiro."""
    toks = spec.split()
    out, i = [], 0
    while i < len(toks):
        if toks[i] == "--max-no-improve":
            i += 2
            continue
        out.append(toks[i]); i += 1
    return " ".join(out)


# parâmetros calibrados lidos de config/tuned.json (única fonte de verdade), sem o K;
# o VND não tem parâmetros calibráveis.
_tuned = json.load(open(TUNED))
ALGOS = {"grasp": _quality_flags(_tuned["grasp"]),
         "rgrasp": _quality_flags(_tuned["rgrasp"]),
         "tabu": _quality_flags(_tuned["tabu"]),
         "vnd": ""}
# Sementes UNIFORMES entre os estocásticos. A versão anterior usava 5/5/1/1, o
# que dava ao GRASP cinco amostras e à Tabu uma -- réplicas desiguais não podem
# entrar numa comparação. VND e Tabu são determinísticos: uma execução basta.
RUNS_STOCHASTIC = 10
SEEDS = {"grasp": RUNS_STOCHASTIC, "rgrasp": RUNS_STOCHASTIC, "tabu": 1, "vnd": 1}
COLOR = {"grasp": "#2ca02c", "rgrasp": "#1f77b4", "tabu": "#d62728", "vnd": "#9467bd"}


def bks(inst):
    for line in open(os.path.join(REFS, inst + ".sol"), errors="ignore"):
        if "ost" in line:
            return float(line.split()[-1])
    return None


def run_trace(algo, inst, seed):
    """Roda solve com orçamento de tempo T e retorna a lista [(t_ms, best), ...]."""
    with tempfile.TemporaryDirectory() as td:
        tr = os.path.join(td, "t.csv")
        cmd = [SOLVER, "--algo", algo, "--instance", os.path.join(INPUT, inst + ".txt"),
               "--seed", str(seed), "--budget-ms", str(T_MS), "--print-cost",
               "--trace", tr] + ALGOS[algo].split()
        subprocess.run(cmd, capture_output=True, text=True)
        pts = []
        if os.path.isfile(tr):
            for r in csv.DictReader(open(tr)):
                pts.append((float(r["elapsed_ms"]), float(r["best"])))
        return pts


def primal_integral(trace, T, ref):
    """Integral primal (fórmula DIMACS). trace = [(t,best)] das incumbentes."""
    pts = [(0.0, 1.1 * ref)] + [(min(t, T), v) for t, v in trace]
    area = 0.0
    for i in range(1, len(pts)):
        t0, v0 = pts[i - 1]
        t1, _ = pts[i]
        area += v0 * (t1 - t0)          # valor v0 vigente em [t0, t1]
    tn, vn = pts[-1]
    area += vn * (T - tn)               # cauda: última incumbente até T
    return 100.0 * (area / (T * ref) - 1.0)


def main():
    global T_MS, INSTANCES, SEEDS
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-ms", type=int, default=T_MS)
    ap.add_argument("--runs", type=int, default=RUNS_STOCHASTIC)
    ap.add_argument("--instances-file",
                    default=os.path.join(_HERE, "config", "test.txt"))
    ap.add_argument("--instances", default=None, help="lista separada por vírgula")
    ap.add_argument("--jobs", type=int, default=14)
    a = ap.parse_args()
    T_MS = a.budget_ms
    SEEDS = {"grasp": a.runs, "rgrasp": a.runs, "tabu": 1, "vnd": 1}
    if a.instances:
        INSTANCES = [x.strip() for x in a.instances.split(",") if x.strip()]
    else:
        INSTANCES = [l.strip() for l in open(a.instances_file) if l.strip()]
    print(f"tempo igual T={T_MS/1000:.0f}s, {len(INSTANCES)} instancias, "
          f"{a.runs} sementes nos estocasticos, K desativado")

    # As execuções são independentes entre si; sequencialmente, 28 instâncias x
    # 10 sementes x T = 20s levariam horas. O solver é single-thread, então um
    # pool de processos externos escala quase linearmente.
    tasks = [(inst, algo, s)
             for inst in INSTANCES for algo in ALGOS
             for s in range(1, SEEDS[algo] + 1)]
    print(f"  {len(tasks)} execucoes em {a.jobs} processos...")
    traces = {}
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(run_trace, algo, inst, s): (inst, algo, s)
                for inst, algo, s in tasks}
        for n, fut in enumerate(as_completed(futs), 1):
            traces[futs[fut]] = fut.result()
            if n % 25 == 0 or n == len(tasks):
                print(f"    {n}/{len(tasks)}", flush=True)

    rows, final_rows = [], []
    pi_by = {a_: [] for a_ in ALGOS}
    for inst in INSTANCES:
        ref = bks(inst)
        traces_for_plot = {}
        for algo in ALGOS:
            pis, traces_all = [], []
            for s in range(1, SEEDS[algo] + 1):
                tr = traces[(inst, algo, s)]
                traces_all.append(tr)
                pi = primal_integral(tr, T_MS, ref)
                pis.append(pi)
                if s == 1:
                    traces_for_plot[algo] = tr
            mean_pi = sum(pis) / len(pis)
            pi_by[algo].append(mean_pi)
            rows.append({"instance": inst, "algorithm": algo, "bks": ref,
                         "T_ms": T_MS, "primal_integral_mean": round(mean_pi, 4),
                         "runs": SEEDS[algo]})
            # qualidade FINAL sob tempo igual: a incumbente ao fim de T
            finals = [tr[-1][1] for tr in traces_all if tr]
            if finals:
                gaps = [100.0 * (f - ref) / ref for f in finals]
                final_rows.append({"instance": inst, "algorithm": algo, "bks": ref,
                                   "T_ms": T_MS, "runs": len(finals),
                                   "gap_mean": round(sum(gaps) / len(gaps), 4),
                                   "gap_best": round(min(gaps), 4)})
            print(f"  {inst} {algo:7s}: PI={mean_pi:.3f}")

        # figura de convergência anytime: só para as representativas, senão
        # seriam 28 arquivos que ninguém olha
        if inst not in ("R101", "RC101", "R201", "C101"):
            continue
        plt.figure(figsize=(7, 4.2))
        for algo, tr in traces_for_plot.items():
            if not tr:
                continue
            xs = [0] + [t / 1000.0 for t, _ in tr] + [T_MS / 1000.0]
            ys = [1.1 * ref] + [v for _, v in tr] + [tr[-1][1]]
            plt.step(xs, ys, where="post", label=algo, color=COLOR[algo], lw=1.8)
        plt.axhline(ref, ls=":", color="gray", label=f"melhor conhecido ({ref:.0f})")
        plt.xlabel("tempo (s)"); plt.ylabel("distância da incumbente")
        plt.title(f"Convergência anytime — {inst}")
        plt.legend(fontsize=8); plt.grid(ls=":", alpha=0.4); plt.tight_layout()
        plt.savefig(os.path.join(ROOT, "results", "figures", f"anytime_convergence_{inst}.png"), dpi=150)
        plt.close()

    # CSV
    with open(os.path.join(ROOT, "results", "primal_integral.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["instance", "algorithm", "bks", "T_ms",
                                           "primal_integral_mean", "runs"])
        w.writeheader(); w.writerows(rows)

    # tabela de qualidade final sob TEMPO IGUAL -- a leitura que o critério por
    # iterações sem melhoria não fornece
    eq = os.path.join(ROOT, "results", "equal_time.csv")
    with open(eq, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["instance", "algorithm", "bks", "T_ms",
                                           "runs", "gap_mean", "gap_best"])
        w.writeheader(); w.writerows(final_rows)
    agg = {}
    for r in final_rows:
        agg.setdefault(r["algorithm"], []).append(r["gap_mean"])
    print(f"\n=== Qualidade final sob TEMPO IGUAL (T={T_MS/1000:.0f}s) ===")
    for a_ in ALGOS:
        if a_ in agg:
            print(f"  {a_:7s} gap medio {sum(agg[a_])/len(agg[a_]):7.3f}%  "
                  f"({len(agg[a_])} instancias)")
    print(f"  -> {eq}")

    # figura resumo: PI médio por algoritmo (média sobre instâncias)
    algos = list(ALGOS)
    means = [sum(pi_by[a]) / len(pi_by[a]) for a in algos]
    plt.figure(figsize=(6, 4))
    plt.bar(algos, means, color=[COLOR[a] for a in algos])
    for i, m in enumerate(means):
        plt.text(i, m, f"{m:.2f}", ha="center", va="bottom", fontsize=9)
    plt.ylabel("integral primal médio (menor = melhor)")
    plt.title(f"Integral primal (DIMACS), T={T_MS//1000}s — média sobre {len(INSTANCES)} instâncias")
    plt.grid(axis="y", ls=":", alpha=0.4); plt.tight_layout()
    plt.savefig(os.path.join(ROOT, "results", "figures", "primal_integral.png"), dpi=150)
    plt.close()

    print(f"\n=== integral primal médio (menor = melhor) ===")
    for a, m in zip(algos, means):
        print(f"  {a:7s}: {m:.3f}")
    print(f"\nCSV: results/primal_integral.csv | figuras: results/figures/primal_integral.png + anytime_convergence_*.png")


if __name__ == "__main__":
    main()
