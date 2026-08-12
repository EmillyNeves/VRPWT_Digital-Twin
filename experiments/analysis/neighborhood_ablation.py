#!/usr/bin/env python3
"""Seleção do conjunto de vizinhanças do VND — com inferência, e sem vazamento.

O relatório parcial lista OITO movimentos de busca local e afirma que deles foi
selecionado "um subconjunto mais promissor". Este script documenta a seleção.

Mapeamento dos oito movimentos para os operadores implementados (três cobrem
tanto a variante intra quanto a inter, o que se lê nos limites dos laços em
solver/src/Neighborhoods.cpp):

    Relocate intra + Relocate inter  ->  relocate      (for r2 = 0..R)
    Swap intra + Swap inter          ->  swap          (for r2 = r1..R)
    2-opt intra                      ->  twoopt        (rota unica)
    Or-opt (intra e inter)           ->  oropt         (for r2 = 0..R)
    Cross-exchange                   ->  cross         (for r2 = r1+1..R)
    2-opt inter                      ->  twooptstar    (Potvin & Rousseau 1995)

Três desenhos, todos sobre as instâncias de TREINO (a seleção não pode ser feita
no conjunto usado para reportar):

  CUMULATIVO     adiciona um operador por vez, na ordem em que foram propostos
  LEAVE-ONE-OUT  remove um operador do kit completo -> contribuição MARGINAL
  ADIÇÃO         acrescenta o 2-opt* ao kit -> o oitavo movimento se paga?

Cada comparação contra o kit de referência é testada por Wilcoxon pareado sobre
os gaps por instância, com correção de Holm para as comparações múltiplas.

Saída: results/neighborhoods/{ablation.csv, summary.csv}
"""
import csv
import os
import subprocess
import sys
from collections import defaultdict

from scipy.stats import wilcoxon

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
SOLVER = os.path.join(_ROOT, "solver", "build", "solve")
INPUT = os.path.join(_ROOT, "data", "instances", "solomon")
REFS = os.path.join(_ROOT, "data", "reference-solutions", "dinamics")
TRAIN = os.path.join(_ROOT, "experiments", "config", "train.txt")
OUTDIR = os.path.join(_ROOT, "results", "neighborhoods")

# O kit em uso, NA ORDEM DE COMPLEXIDADE MEDIDA (custo de uma varredura completa;
# ver o teste neighborhood_scan_cost_ordering e docs/verificacao/03-vizinhancas.md).
# A ordem importa: o VND reinicia na primeira vizinhanca a cada melhoria, entao a
# contribuicao marginal de um operador depende de quais outros existem E da ordem.
KIT = ["twoopt", "swap", "twooptstar", "relocate", "oropt", "cross"]
LABEL = {"relocate": "Relocate", "oropt": "Or-opt", "swap": "Swap",
         "twoopt": "2-opt intra", "cross": "Cross-exch.", "twooptstar": "2-opt*"}


def configs():
    out = []
    for i in range(1, len(KIT) + 1):                       # cumulativo
        sub = KIT[:i]
        out.append(("cumul", "+".join(LABEL[x] for x in sub), ",".join(sub)))
    for x in KIT:                                          # leave-one-out
        sub = [y for y in KIT if y != x]
        out.append(("loo", "sem " + LABEL[x], ",".join(sub)))
    out.append(("kit", "kit completo (6)", ",".join(KIT)))
    return out


def ref_cost(name):
    p = os.path.join(REFS, name + ".sol")
    for line in open(p, encoding="utf-8", errors="ignore"):
        if line.lower().startswith("cost"):
            return float(line.split()[-1])
    raise RuntimeError(f"sem custo de referencia: {name}")


def family(name):
    return name[:2] if name[1].isalpha() else name[:1] + name[1]


def run(name, neigh):
    out = subprocess.run(
        [SOLVER, "--algo", "vnd", "--instance", os.path.join(INPUT, name + ".txt"),
         "--neighborhoods", neigh, "--csv"],
        capture_output=True, text=True)
    f = out.stdout.strip().split(",")
    if len(f) < 7:
        raise RuntimeError(f"solver falhou em {name} [{neigh}]: {out.stderr}")
    return float(f[3]), int(f[4]), int(f[6])          # distancia, veiculos, viavel


def holm(pairs):
    """pairs = [(rotulo, p)] -> {rotulo: p_ajustado} (Holm step-down)."""
    ordered = sorted(pairs, key=lambda t: t[1])
    m, adj, running = len(ordered), {}, 0.0
    for i, (lbl, p) in enumerate(ordered):
        running = max(running, (m - i) * p)
        adj[lbl] = min(1.0, running)
    return adj


def main():
    if not os.access(SOLVER, os.X_OK):
        sys.exit("solver nao compilado: make -C solver")
    os.makedirs(OUTDIR, exist_ok=True)
    names = [l.strip() for l in open(TRAIN) if l.strip()]
    print(f"ablacao em {len(names)} instancias de TREINO x {len(configs())} configuracoes")

    rows, gaps = [], defaultdict(dict)
    for kind, label, neigh in configs():
        for name in names:
            dist, veh, feas = run(name, neigh)
            gap = (dist - ref_cost(name)) / ref_cost(name) * 100.0
            rows.append([kind, label, neigh, name, family(name), dist, veh, feas, round(gap, 4)])
            gaps[label][name] = gap
        m = sum(gaps[label].values()) / len(names)
        print(f"  {label:34} gap medio {m:6.3f}%")

    with open(os.path.join(OUTDIR, "ablation.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["design", "config", "neighborhoods", "instance", "family",
                    "distance", "vehicles", "feasible", "gap_pct"])
        w.writerows(rows)

    # ---- inferencia: cada variante contra o kit completo ---------------------
    base = gaps["kit completo (6)"]
    tests = []
    for kind, label, _ in configs():
        if label == "kit completo (6)":
            continue
        if kind != "loo":
            continue
        d = [gaps[label][n] - base[n] for n in names]
        if all(abs(x) < 1e-12 for x in d):
            tests.append((label, 1.0, 0.0, 0, 0, len(names)))
            continue
        p = wilcoxon(d, alternative="two-sided", zero_method="zsplit").pvalue
        worse = sum(1 for x in d if x > 1e-9)
        better = sum(1 for x in d if x < -1e-9)
        tests.append((label, p, sum(d) / len(d), worse, better, len(names) - worse - better))

    adj = holm([(t[0], t[1]) for t in tests])
    print(f"\n{'variante':34} {'delta gap':>10} {'piora':>6} {'melhora':>8} {'empata':>7}"
          f" {'p':>9} {'p Holm':>9} {'signif.':>8}")
    summary = []
    for label, p, dmean, worse, better, tie in tests:
        pa = adj[label]
        sig = "sim" if pa < 0.05 else "nao"
        print(f"{label:34} {dmean:+9.3f}pp {worse:6} {better:8} {tie:7} {p:9.4f} {pa:9.4f} {sig:>8}")
        summary.append({"config": label, "delta_gap_pp": round(dmean, 4),
                        "worse": worse, "better": better, "tie": tie,
                        "p_wilcoxon": round(p, 6), "p_holm": round(pa, 6),
                        "significant": sig})

    # ---- por familia: onde cada operador importa ----------------------------
    print("\ncontribuicao marginal por familia (delta do gap ao remover o operador)")
    fams = sorted({family(n) for n in names})
    print(f"{'operador removido':34}" + "".join(f"{f:>10}" for f in fams))
    for kind, label, _ in configs():
        if kind != "loo":
            continue
        line = f"{label:34}"
        for f in fams:
            sel = [n for n in names if family(n) == f]
            line += f"{sum(gaps[label][n] - base[n] for n in sel) / len(sel):+9.2f} "
        print(line)

    with open(os.path.join(OUTDIR, "summary.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    print(f"\nartefatos -> {OUTDIR}/")


if __name__ == "__main__":
    main()
