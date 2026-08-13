"""Medicao do criterio de parada: quanto cada orcamento K entrega e quanto custa.

POR QUE ESTE SCRIPT EXISTE
--------------------------
O criterio de parada do estudo e "K iteracoes sem melhoria". O valor de K
precisa ser justificado com dado medido, nao com escolha de conveniencia. Este
script produz os dois numeros que sustentam a justificativa:

  1. COBERTURA -- que fracao da melhoria que o metodo ainda consegue obter ja
     esta capturada em K. Referencia: um orcamento K_LONG muito maior.
  2. CUSTO     -- tempo de execucao em K, medido sem concorrencia.

METODO: derivacao por truncamento, onde ela e valida
----------------------------------------------------
Rodar cada K separadamente custa a soma dos K. Em vez disso rodamos UMA vez com
K_LONG e derivamos todos os K menores do traco de convergencia. A trajetoria e
determinista dada a semente e o criterio de parada nao influencia a busca, entao
parar antes e exatamente truncar.

A premissa NAO foi assumida -- e ela nao vale para todos os metodos. A validacao
(`valida_derivacao.py`, 3 metodos x 6 instancias x 4 valores de K) aprovou o
GRASP (24/24) e a Tabu (24/24) e REPROVOU o GRASP reativo (22/24). O motivo esta
em solve.cpp: `--block-frac` define o intervalo de reponderacao como uma FRACAO
de K, de modo que mudar o orcamento muda o cronograma reativo -- em K menor o
metodo nao e o mesmo algoritmo truncado, e outro algoritmo. E o comportamento
pretendido (mantem o numero de reponderacoes constante entre orcamentos, que foi
a correcao do `block` degenerado), mas custa a derivacao.

Por isso: GRASP e Tabu derivados de uma execucao longa; reativo REEXECUTADO em
cada K. Trocar o desenho do reativo para baratear a medicao seria medir outro
algoritmo.

O holdout nao e tocado -- a medicao usa apenas as instancias de treino.
"""
import argparse
import csv
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SOLVER = os.path.join(ROOT, "solver", "build", "solve")
INS = os.path.join(ROOT, "data", "instances", "solomon")
REF = os.path.join(ROOT, "data", "reference-solutions", "dinamics")

# Parametros de qualidade calibrados; sao mantidos fixos para que a unica coisa
# que varia entre as linhas seja o orcamento.
PARAMS = {"grasp":  ["--alpha", "0.1517"],
          "rgrasp": ["--delta", "1.3992", "--block-frac", "0.1"],
          "tabu":   ["--tenure", "39"]}

K_GRID = [50, 100, 200, 400, 800, 1600, 3200]

# Metodos cuja trajetoria NAO e invariante ao criterio de parada, e que por isso
# precisam ser reexecutados em cada K em vez de derivados. Ver o cabecalho.
NAO_DERIVAVEIS = {"rgrasp"}


def best_known(name):
    with open(os.path.join(REF, f"{name}.sol")) as fh:
        for line in fh:
            if line.lower().startswith("cost"):
                return float(line.split()[-1])
    raise ValueError(f"custo de referencia ausente em {name}.sol")


def solve(algo, name, K, seed, trace=None, extra=None):
    cmd = [SOLVER, "--algo", algo, "--instance", os.path.join(INS, f"{name}.txt"),
           "--seed", str(seed), "--budget-ms", "3600000",
           "--max-no-improve", str(K), "--csv"] + PARAMS.get(algo, [])
    if trace:
        cmd += ["--trace", trace]
    if extra:
        cmd += extra
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip().split(",")
    # algo,instance,seed,distance,vehicles,time_ms,feasible,iters
    return {"distance": float(out[3]), "vehicles": int(out[4]),
            "time_ms": int(out[5]), "feasible": int(out[6]), "iters": int(out[7])}


def read_trace(path):
    with open(path) as fh:
        return [(int(r["iter"]), float(r["best"])) for r in csv.DictReader(fh)]


def derive(rows, K, is_grasp, fallback):
    """Melhor custo sob o criterio K, truncando o traco de uma execucao maior.

    `no_improve` zera na iteracao que melhora e a quebra ocorre quando ele
    atinge K; a melhoria seguinte, na iteracao i, so e alcancada se
    i - i_anterior <= K. No GRASP a primeira linha do traco e o incumbente
    inicial (a I1), registrada ANTES do laco: ela nao consome orcamento, por
    isso `prev` comeca em -1 e a linha e pulada na contagem.

    `fallback` (custo da I1) cobre o caso em que nenhuma melhoria e alcancada --
    possivel na Tabu, cujo traco nao registra a solucao inicial.
    """
    prev, best = -1, None
    for idx, (it, cost) in enumerate(rows):
        if idx == 0 and is_grasp:
            best = cost
            continue
        if it - prev > K:
            break
        best, prev = cost, it
    return fallback if best is None else best


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--instances", default=os.path.join(ROOT, "experiments/config/train.txt"))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--k-long", type=int, default=6400,
                    help="orcamento de referencia; todos os K do grid <= este sao derivados dele")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 4))
    ap.add_argument("--trace-dir", default="/tmp/stopping-traces")
    ap.add_argument("--out", default=os.path.join(ROOT, "results/stopping/convergence.csv"))
    args = ap.parse_args()

    names = [l.strip() for l in open(args.instances) if l.strip()]
    grid = [k for k in K_GRID if k <= args.k_long]
    os.makedirs(args.trace_dir, exist_ok=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    bks = {n: best_known(n) for n in names}
    print(f"{len(names)} instancias, {len(PARAMS)} metodos, K de referencia = {args.k_long}", flush=True)

    # custo da I1 por instancia: reserva para tracos sem nenhuma melhoria
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        i1 = dict(zip(names, ex.map(lambda n: solve("i1", n, -1, args.seed)["distance"], names)))
    print("I1 medida em todas as instancias", flush=True)

    def measure(job):
        """Devolve as linhas de todos os K para um par (metodo, instancia)."""
        algo, name = job
        out = []
        if algo in NAO_DERIVAVEIS:
            for K in grid:
                r = solve(algo, name, K, args.seed)
                out.append((K, r["distance"], 0, r["feasible"]))
            nota = f"reexecutado em {len(grid)} orcamentos"
        else:
            tp = os.path.join(args.trace_dir, f"{algo}_{name}_{args.seed}.csv")
            r = solve(algo, name, args.k_long, args.seed, trace=tp)
            trace = read_trace(tp)
            for K in grid:
                d = derive(trace, K, algo != "tabu", i1[name])
                out.append((K, d, int(K < args.k_long), r["feasible"]))
            nota = f"iters={r['iters']} melhorias={len(trace)}"
        return algo, name, out, nota

    jobs = [(a, n) for a in PARAMS for n in names]
    rows, done = [], 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for algo, name, out, nota in ex.map(measure, jobs):
            done += 1
            for K, dist, derived, feasible in out:
                if not feasible:
                    print(f"AVISO: {algo}/{name} K={K} devolveu solucao inviavel", flush=True)
                rows.append({"algorithm": algo, "instance": name, "seed": args.seed, "K": K,
                             "distance": round(dist, 4),
                             "gap_pct": round((dist - bks[name]) / bks[name] * 100, 6),
                             "derived": derived})
            print(f"  [{done}/{len(jobs)}] {algo:<7}{name:<7} {nota}", flush=True)

    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["algorithm", "instance", "seed", "K",
                                           "distance", "gap_pct", "derived"])
        w.writeheader()
        w.writerows(rows)
    print(f"\n{len(rows)} linhas em {args.out}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
