#!/usr/bin/env python3
"""Ablação do kit de vizinhanças (justificativa empírica da escolha).

Roda o VND (determinístico) com diferentes subconjuntos de vizinhanças nas 56
instâncias Solomon-100 e mede o gap de distância ao melhor-conhecido (Dinamics).
Dois desenhos:
  (1) CUMULATIVO: adiciona operadores na ordem do VND
      {Rel} ⊂ {Rel,Or} ⊂ {Rel,Or,Swap} ⊂ {Rel,Or,Swap,2opt} ⊂ {todos}
      → mostra a contribuição MARGINAL de cada operador.
  (2) LEAVE-ONE-OUT: kit completo menos um operador de cada vez
      → mostra a NECESSIDADE de cada operador.

Justifica, com números, por que o kit de 5 vizinhanças é adotado. Usa o VND
porque é determinístico (1 execução por instância) e barato, isolando o efeito
das vizinhanças do ruído estocástico do GRASP/Tabu.

Saída: results/ablation.csv + results/ablation_summary.csv + resumo no stdout.
"""
import csv
import os
import re
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, ".."))
SOLVER = os.path.join(ROOT, "solver", "build", "solve")
INPUT = os.path.join(ROOT, "input")
REFS = os.path.join(ROOT, "solution (Dinamics)")

ALL = ["relocate", "oropt", "swap", "twoopt", "cross"]
LABEL = {"relocate": "Relocate", "oropt": "Or-opt", "swap": "Swap",
         "twoopt": "2-opt", "cross": "Cross-exch."}

CONFIGS = []
# (1) cumulativo (ordem do VND)
for k in range(1, len(ALL) + 1):
    sub = ALL[:k]
    CONFIGS.append(("cumul:" + "+".join(LABEL[x] for x in sub), ",".join(sub)))
# (2) leave-one-out a partir do kit completo
for x in ALL:
    sub = [y for y in ALL if y != x]
    CONFIGS.append(("sem:" + LABEL[x], ",".join(sub)))


def ref_cost(name):
    p = os.path.join(REFS, name + ".sol")
    if os.path.isfile(p):
        for line in open(p, errors="ignore"):
            if "ost" in line:
                m = re.search(r"[-+]?\d+\.?\d*", line)
                if m:
                    return float(m.group())
    return None


def family_type(name):
    m = re.match(r"([A-Za-z]+)(\d)", name)
    return (m.group(1).upper(), int(m.group(2))) if m else ("?", 0)


def run(name, neigh):
    inst = os.path.join(INPUT, name + ".txt")
    out = subprocess.run([SOLVER, "--algo", "vnd", "--instance", inst,
                          "--neighborhoods", neigh, "--csv"],
                         capture_output=True, text=True)
    f = out.stdout.strip().splitlines()[-1].split(",")
    return float(f[3]), int(f[4]), int(f[5])   # dist, veh, time_ms


def main():
    names = sorted(os.path.splitext(f)[0] for f in os.listdir(INPUT) if f.endswith(".txt"))
    rows = []
    for name in names:
        fam, typ = family_type(name)
        ref = ref_cost(name)
        for label, neigh in CONFIGS:
            dist, veh, ms = run(name, neigh)
            gap = (dist - ref) / ref * 100.0 if ref else None
            rows.append({"config": label, "neighborhoods": neigh, "instance": name,
                         "family": fam, "type": typ, "dist": dist, "veh": veh,
                         "time_ms": ms, "gap_pct": gap})

    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    with open(os.path.join(ROOT, "results", "ablation.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["config", "neighborhoods", "instance", "family",
                                           "type", "dist", "veh", "time_ms", "gap_pct"])
        w.writeheader()
        w.writerows(rows)

    # resumo: gap médio e tempo médio por configuração
    summ = {}
    for r in rows:
        c = r["config"]
        summ.setdefault(c, {"gaps": [], "ms": [], "neigh": r["neighborhoods"]})
        if r["gap_pct"] is not None:
            summ[c]["gaps"].append(r["gap_pct"])
        summ[c]["ms"].append(r["time_ms"])

    order = [c for c, _ in CONFIGS]
    with open(os.path.join(ROOT, "results", "ablation_summary.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["config", "neighborhoods", "gap_mean_pct", "time_mean_ms", "n"])
        for c in order:
            g = summ[c]["gaps"]; m = summ[c]["ms"]
            w.writerow([c, summ[c]["neigh"], f"{sum(g)/len(g):.3f}" if g else "",
                        f"{sum(m)/len(m):.1f}", len(g)])

    print(f"{'configuração':40s} {'gap_médio%':>11s} {'tempo_médio_ms':>15s}")
    for c in order:
        g = summ[c]["gaps"]; m = summ[c]["ms"]
        print(f"{c:40s} {sum(g)/len(g):>11.3f} {sum(m)/len(m):>15.1f}")
    print("\nCSVs: results/ablation.csv, results/ablation_summary.csv")


if __name__ == "__main__":
    main()
