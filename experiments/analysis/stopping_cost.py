"""Custo de tempo por orcamento K, medido SEM concorrencia.

Complementa `stopping_budget.py`, que mede o que cada K entrega. Aqui se mede o
que cada K custa. A execucao e estritamente sequencial: com varios processos
disputando nucleos o tempo de parede infla e deixa de descrever o custo de uma
execucao isolada, que e o numero que vai para o relatorio.

Uma instancia por familia mantem o custo da propria medicao baixo e cobre os
dois horizontes (tipo 1 curto, tipo 2 longo), que e o que domina a variacao de
tempo entre instancias.
"""
import argparse
import csv
import os
import statistics
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOLVER = os.path.join(ROOT, "solver", "build", "solve")
INS = os.path.join(ROOT, "data", "instances", "solomon")

PARAMS = {"grasp":  ["--alpha", "0.1517"],
          "rgrasp": ["--delta", "1.3992", "--block-frac", "0.1"],
          "tabu":   ["--tenure", "39"]}

SAMPLE = ["C101", "C201", "R101", "R201", "RC101", "RC201"]


def solve(algo, name, K, seed):
    cmd = [SOLVER, "--algo", algo, "--instance", os.path.join(INS, f"{name}.txt"),
           "--seed", str(seed), "--budget-ms", "3600000",
           "--max-no-improve", str(K), "--csv"] + PARAMS[algo]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip().split(",")
    return int(out[5]), int(out[7])            # time_ms, iters


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ks", type=int, nargs="+", default=[200, 400, 800, 1600])
    ap.add_argument("--reps", type=int, default=3, help="repeticoes por ponto, para a mediana")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(ROOT, "results/stopping/cost.csv"))
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    rows = []
    print("medicao sequencial (1 processo por vez)\n", flush=True)
    print(f"{'algo':<8}{'K':>6}{'mediana_ms':>12}{'max_ms':>9}{'iters':>8}", flush=True)
    for algo in PARAMS:
        for K in args.ks:
            per_inst, iters = [], []
            for name in SAMPLE:
                reps = [solve(algo, name, K, args.seed) for _ in range(args.reps)]
                # a mediana das repeticoes descarta o ruido de escalonamento do SO;
                # `iters` e identico entre repeticoes (a busca e determinista)
                t = statistics.median(r[0] for r in reps)
                per_inst.append(t)
                iters.append(reps[0][1])
                rows.append({"algorithm": algo, "K": K, "instance": name,
                             "time_ms_median": int(t), "iters": reps[0][1]})
            print(f"{algo:<8}{K:>6}{int(statistics.median(per_inst)):>12}"
                  f"{int(max(per_inst)):>9}{int(statistics.median(iters)):>8}", flush=True)

    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["algorithm", "K", "instance", "time_ms_median", "iters"])
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} linhas em {args.out}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
