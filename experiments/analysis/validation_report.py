#!/usr/bin/env python3
"""Prova de que as rotas produzidas respeitam janelas de tempo e capacidade.

O CSV mestre traz apenas um bit (`feasible` = 0/1) por execução. Isso responde
"é viável?" mas não "com quanta folga?" -- e folga zero é o que separa uma
solução válida de uma inválida por erro de arredondamento. Aqui a validação é
refeita por um recálculo INDEPENDENTE (o binário `validate`, que recaminha cada
rota do zero sem confiar em nenhum cache do solver) e reportada com as margens.

Duas saídas:

  results/validation_summary.csv   uma linha por arquivo .sol -- a prova global
                                   ("N de M soluções viáveis")
  results/validation_routes.csv    uma linha por ROTA da melhor solução de cada
                                   (algoritmo, instância) -- a prova detalhada,
                                   com folga de capacidade, folga da janela mais
                                   apertada e folga do horizonte no retorno

Uso:
  python3 experiments/analysis/validation_report.py [--sol-dir results/raw/sol]
"""
import argparse
import csv
import os
import re
import subprocess
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
VALIDATE = os.path.join(_ROOT, "solver", "build", "validate")
INPUT = os.path.join(_ROOT, "data", "instances", "solomon")

ROUTE_COLS = ["instance", "route", "customers", "load", "capacity", "load_slack",
              "distance", "return_time", "horizon", "horizon_slack",
              "min_tw_slack", "tightest_customer", "feasible"]

# results/raw/sol/<algo>_<INSTANCIA>_s<semente>.sol
NAME_RE = re.compile(r"^(?P<algo>[a-z0-9]+)_(?P<inst>[A-Z]+\d+)_s(?P<seed>\d+)$")


def sol_cost(path):
    for line in open(path, encoding="utf-8", errors="ignore"):
        if line.lower().startswith("cost"):
            try:
                return float(line.split()[-1])
            except ValueError:
                pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sol-dir", default=os.path.join(_ROOT, "results", "raw", "sol"))
    ap.add_argument("--out-dir", default=os.path.join(_ROOT, "results"))
    args = ap.parse_args()

    if not os.access(VALIDATE, os.X_OK):
        sys.exit(f"binario ausente: {VALIDATE}\nrode: make -C solver")
    if not os.path.isdir(args.sol_dir):
        sys.exit(f"diretorio de solucoes ausente: {args.sol_dir}\n"
                 f"rode o estudo antes: bash experiments/pipelines/2_run_study.sh")

    files = sorted(f for f in os.listdir(args.sol_dir) if f.endswith(".sol"))
    if not files:
        sys.exit(f"nenhum .sol em {args.sol_dir}")

    # ---- prova global: toda solucao produzida e viavel? --------------------
    summary, best = [], {}
    for fn in files:
        stem = os.path.splitext(fn)[0]
        m = NAME_RE.match(stem)
        if not m:
            continue
        algo, inst, seed = m["algo"], m["inst"], int(m["seed"])
        path = os.path.join(args.sol_dir, fn)
        rc = subprocess.run([VALIDATE, os.path.join(INPUT, inst + ".txt"), path],
                            capture_output=True, text=True).returncode
        feasible = 1 if rc == 0 else 0
        cost = sol_cost(path)
        summary.append({"algorithm": algo, "instance": inst, "seed": seed,
                        "cost": cost, "feasible": feasible})
        key = (algo, inst)
        if cost is not None and (key not in best or cost < best[key][0]):
            best[key] = (cost, path, inst)

    with open(os.path.join(args.out_dir, "validation_summary.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["algorithm", "instance", "seed", "cost", "feasible"])
        w.writeheader()
        w.writerows(summary)

    n_ok = sum(r["feasible"] for r in summary)
    print(f"validacao global: {n_ok}/{len(summary)} solucoes viaveis")
    if n_ok != len(summary):
        bad = [r for r in summary if not r["feasible"]]
        print("  INVIAVEIS:", ", ".join(f"{r['algorithm']}/{r['instance']}/s{r['seed']}" for r in bad[:10]))

    per_algo = defaultdict(lambda: [0, 0])
    for r in summary:
        per_algo[r["algorithm"]][0] += r["feasible"]
        per_algo[r["algorithm"]][1] += 1
    for a in sorted(per_algo):
        ok, tot = per_algo[a]
        print(f"  {a:8} {ok}/{tot}")

    # ---- prova detalhada: folgas por rota da melhor solucao ----------------
    rows = []
    for (algo, inst), (_, path, _) in sorted(best.items()):
        out = subprocess.run([VALIDATE, os.path.join(INPUT, inst + ".txt"), path, "--csv"],
                             capture_output=True, text=True)
        for line in out.stdout.strip().splitlines():
            f = line.split(",")
            if len(f) == len(ROUTE_COLS):
                rows.append([algo] + f)

    with open(os.path.join(args.out_dir, "validation_routes.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["algorithm"] + ROUTE_COLS)
        w.writerows(rows)

    if rows:
        cap = [float(r[6]) for r in rows]        # load_slack
        tw = [float(r[11]) for r in rows]        # min_tw_slack
        hz = [float(r[10]) for r in rows]        # horizon_slack
        print(f"\ndetalhe por rota: {len(rows)} rotas da melhor solucao de cada (algoritmo, instancia)")
        print(f"  folga de capacidade   min={min(cap):8.2f}  (0 = veiculo cheio, ainda valido)")
        print(f"  folga da janela       min={min(tw):8.2f}  (negativo = VIOLACAO)")
        print(f"  folga do horizonte    min={min(hz):8.2f}  (negativo = VIOLACAO)")
        viol = sum(1 for r in rows if r[13] == "0")
        print(f"  rotas invalidas       {viol}")

    print(f"\nartefatos -> {args.out_dir}/validation_summary.csv, validation_routes.csv")


if __name__ == "__main__":
    main()
