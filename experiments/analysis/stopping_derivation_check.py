"""Guarda do metodo de medicao usado em `stopping_budget.py`.

Aquele script obtem o resultado sob um orcamento K truncando o traco de uma
execucao mais longa, em vez de reexecutar. Isso so e legitimo se a trajetoria do
metodo for invariante ao criterio de parada. Este script CONFERE essa premissa,
comparando derivado contra executado.

Resultado conhecido (ago/2026):

    GRASP   24/24  derivavel
    Tabu    24/24  derivavel
    Reativo 22/24  NAO derivavel

O reativo falha porque `--block-frac` (solve.cpp) define o intervalo de
reponderacao como fracao de K: mudar o orcamento muda o cronograma reativo, e a
execucao curta nao e a longa truncada. Por isso `stopping_budget.py` o reexecuta
em cada K. A falha e ESPERADA e o script a trata como tal -- o que ele bloqueia
e uma falha NOVA, em metodo que hoje se supoe derivavel.
"""
import argparse
import csv
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOLVER = os.path.join(ROOT, "solver", "build", "solve")
INS = os.path.join(ROOT, "data", "instances", "solomon")

PARAMS = {"grasp":  ["--alpha", "0.1517"],
          "rgrasp": ["--delta", "1.3992", "--block-frac", "0.1"],
          "tabu":   ["--tenure", "39"]}

# Metodos que NAO se espera derivar; divergencia neles nao reprova a medicao.
ESPERADO_NAO_DERIVAVEL = {"rgrasp"}

SAMPLE = ["C101", "C201", "R101", "R201", "RC101", "RC201"]


def solve(algo, name, K, seed, trace=None):
    cmd = [SOLVER, "--algo", algo, "--instance", os.path.join(INS, f"{name}.txt"),
           "--seed", str(seed), "--budget-ms", "3600000",
           "--max-no-improve", str(K), "--csv"] + PARAMS[algo]
    if trace:
        cmd += ["--trace", trace]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip().split(",")
    return float(out[3])


def read_trace(path):
    with open(path) as fh:
        return [(int(r["iter"]), float(r["best"])) for r in csv.DictReader(fh)]


def derive(rows, K, is_grasp):
    """Ver a docstring homonima em stopping_budget.py -- as duas tem que casar."""
    prev, best = -1, None
    for idx, (it, cost) in enumerate(rows):
        if idx == 0 and is_grasp:
            best = cost
            continue
        if it - prev > K:
            break
        best, prev = cost, it
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ks", type=int, nargs="+", default=[50, 100, 200, 400])
    ap.add_argument("--k-long", type=int, default=800)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    placar = {a: [0, 0] for a in PARAMS}          # [conferem, divergem]
    print(f"{'algo':<8}{'inst':<8}{'K':>6}{'derivado':>11}{'executado':>11}   veredito", flush=True)
    for algo in PARAMS:
        for name in SAMPLE:
            tp = f"/tmp/deriv_{algo}_{name}.csv"
            solve(algo, name, args.k_long, args.seed, trace=tp)
            rows = read_trace(tp)
            for K in args.ks:
                d = derive(rows, K, algo != "tabu")
                if d is None:                     # nenhuma melhoria: a I1 nao esta no traco da Tabu
                    continue
                e = solve(algo, name, K, args.seed)
                bate = abs(d - e) < 0.05          # o CSV imprime a distancia com 1 casa
                placar[algo][0 if bate else 1] += 1
                if not bate:
                    print(f"{algo:<8}{name:<8}{K:>6}{d:>11.1f}{e:>11.1f}   DIVERGE", flush=True)

    print("\nplacar por metodo:", flush=True)
    novas = 0
    for algo, (ok, bad) in placar.items():
        esperado = algo in ESPERADO_NAO_DERIVAVEL
        if bad == 0:
            estado = "derivavel"
        elif esperado:
            estado = "NAO derivavel (esperado; reexecutado por K)"
        else:
            estado = "NAO derivavel -- REGRESSAO"
            novas += 1
        print(f"  {algo:<8}{ok:>4}/{ok + bad:<4} {estado}", flush=True)

    if novas:
        print(f"\n{novas} metodo(s) deixaram de ser derivaveis. "
              f"Acrescente-os a NAO_DERIVAVEIS em stopping_budget.py e reexecute a medicao.",
              flush=True)
    return 1 if novas else 0


if __name__ == "__main__":
    sys.exit(main())
