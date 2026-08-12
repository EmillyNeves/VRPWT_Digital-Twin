#!/usr/bin/env python3
"""A calibração valeu a pena? — parâmetros clássicos × calibrados pelo irace.

O relatório dedica um capítulo ao irace e não apresenta nenhuma evidência de que
calibrar melhorou alguma coisa. Esta é a comparação que responde isso, e é a
primeira pergunta que uma banca faz sobre um capítulo de calibração.

DESENHO. Os dois regimes rodam com o MESMO critério de parada (o K fixado pela
análise de joelho), as MESMAS instâncias e o MESMO número de sementes. A única
diferença são os hiperparâmetros de qualidade. Sem isso a comparação
confundiria orçamento com qualidade.

  clássico   grasp  --alpha 0.3          RCL de tamanho moderado (Feo & Resende)
             rgrasp --delta 1.0          expoente do artigo original
                    --block-frac 0.1     ~10 reponderações por execução
             tabu   --tenure 15          ~0,15n para n = 100
  calibrado  o que estiver em config/tuned.json

A avaliação é no conjunto de TESTE — as instâncias que o irace nunca viu.

Saída: results/calibration_gain.csv + config/default.json (gerado daqui, para
que o K nunca divirja do calibrado).
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
_EXP = os.path.join(_ROOT, "experiments")
CFG = os.path.join(_EXP, "config")

CLASSIC = {"grasp":  "--alpha 0.3",
           "rgrasp": "--delta 1.0 --block-frac 0.1",
           "tabu":   "--tenure 15"}


def write_default_json():
    """Gera config/default.json com o MESMO K do calibrado."""
    fixed = json.load(open(os.path.join(CFG, "fixed_K.json")))
    out = {a: f"{p} --max-no-improve {fixed[a]}" for a, p in CLASSIC.items() if a in fixed}
    path = os.path.join(CFG, "default.json")
    json.dump(out, open(path, "w"), indent=2)
    return path, out


def gaps_from(csv_path, keep):
    """gap médio por (algoritmo, instância), restrito a `keep`."""
    acc = defaultdict(list)
    with open(csv_path) as fh:
        for r in csv.DictReader(fh):
            if r["instance"] in keep and r["gap_pct"]:
                acc[(r["algorithm"], r["instance"])].append(float(r["gap_pct"]))
    return {k: sum(v) / len(v) for k, v in acc.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=30, help="sementes para os estocásticos")
    ap.add_argument("--jobs", type=int, default=14)
    ap.add_argument("--tuned-csv", default=os.path.join(_ROOT, "results", "raw", "runs.csv"),
                    help="CSV do estudo calibrado (já executado)")
    ap.add_argument("--skip-run", action="store_true",
                    help="não reexecuta o regime clássico; usa o CSV existente")
    args = ap.parse_args()

    path, defaults = write_default_json()
    print("config/default.json (regime clássico, mesmo K do calibrado):")
    print(json.dumps(defaults, indent=2))

    if not os.path.isfile(args.tuned_csv):
        sys.exit(f"CSV do estudo calibrado ausente: {args.tuned_csv}\n"
                 f"rode antes: bash experiments/pipelines/2_run_study.sh")

    raw = os.path.join(_ROOT, "results", "raw")
    default_csv = os.path.join(raw, "runs_default.csv")

    if not args.skip_run:
        print(f"\nexecutando o regime CLÁSSICO no conjunto de teste ({args.runs} sementes)...")
        subprocess.run(
            [sys.executable, os.path.join(_EXP, "runner.py"),
             "--solver", os.path.join(_ROOT, "solver", "build", "solve"),
             "--instances-dir", os.path.join(_ROOT, "data", "instances", "solomon"),
             "--refs-dir", os.path.join(_ROOT, "data", "reference-solutions", "dinamics"),
             "--algos", "grasp,rgrasp,tabu", "--runs", str(args.runs),
             "--instance-list", os.path.join(CFG, "test.txt"),
             "--params-file", path, "--jobs", str(args.jobs),
             "--out", default_csv,
             "--sol-dir", os.path.join(raw, "sol_default"),
             "--trace-dir", os.path.join(raw, "traces_default")],
            check=True, cwd=_EXP)

    keep = {l.strip() for l in open(os.path.join(CFG, "test.txt")) if l.strip()}
    tuned = gaps_from(args.tuned_csv, keep)
    default = gaps_from(default_csv, keep)

    rows = []
    for algo in ("grasp", "rgrasp", "tabu"):
        insts = sorted(i for (a, i) in tuned if a == algo) or []
        pairs = [(default.get((algo, i)), tuned.get((algo, i))) for i in insts]
        pairs = [(d, t) for d, t in pairs if d is not None and t is not None]
        if not pairs:
            continue
        d_mean = sum(d for d, _ in pairs) / len(pairs)
        t_mean = sum(t for _, t in pairs) / len(pairs)
        better = sum(1 for d, t in pairs if t < d - 1e-9)
        worse = sum(1 for d, t in pairs if t > d + 1e-9)
        rows.append({"algorithm": algo, "n_instances": len(pairs),
                     "gap_default": round(d_mean, 4), "gap_tuned": round(t_mean, 4),
                     "gain_pp": round(d_mean - t_mean, 4),
                     "tuned_better": better, "tuned_worse": worse,
                     "tie": len(pairs) - better - worse})

    out = os.path.join(_ROOT, "results", "calibration_gain.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"\n{'algoritmo':10} {'clássico':>10} {'calibrado':>10} {'ganho':>9}"
          f" {'melhor':>7} {'pior':>6} {'empate':>7}")
    for r in rows:
        print(f"{r['algorithm']:10} {r['gap_default']:9.3f}% {r['gap_tuned']:9.3f}%"
              f" {r['gain_pp']:+8.3f}pp {r['tuned_better']:7} {r['tuned_worse']:6} {r['tie']:7}")
    print(f"\nartefato -> {out}")


if __name__ == "__main__":
    main()
