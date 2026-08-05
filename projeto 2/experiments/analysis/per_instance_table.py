#!/usr/bin/env python3
"""Gera a tabela LaTeX de resultados POR INSTÂNCIA (apêndice do artigo).

Para cada uma das 56 instâncias, compara os 5 algoritmos com as colunas:
número de veículos, custo (distância média), gap (%), número de iterações e tempo.
Fontes: results/per_instance.csv (veículos, distância, gap) e results/raw/runs.csv
(média de iterações e de tempo por algoritmo/instância). O melhor algoritmo de cada
instância (menor gap médio) é destacado em negrito.

Saída: docs/ic_relatorio_parcial_emilly/tabela_por_instancia.tex (longtable).
"""
import csv
import os
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
PERINST = os.path.join(ROOT, "results", "per_instance.csv")
RUNS = os.path.join(ROOT, "results", "raw", "runs.csv")
OUT = os.path.join(ROOT, "docs", "ic_relatorio_parcial_emilly", "tabela_por_instancia.tex")

ALGO_ORDER = ["i1", "vnd", "grasp", "rgrasp", "tabu"]
ALGO_NAME = {"i1": "I1", "vnd": "VND", "grasp": "GRASP", "rgrasp": "GRASP-R", "tabu": "Tabu"}


def fam_key(inst):
    import re
    m = re.match(r"([A-Za-z]+)(\d)(\d+)", inst)
    if not m:
        return (inst,)
    fam, typ, num = m.group(1).upper(), int(m.group(2)), int(m.group(3))
    return (fam, typ, num)


def main():
    # per_instance: veículos, custo (dist_mean), gap_mean
    per = {}
    for r in csv.DictReader(open(PERINST)):
        per[(r["algorithm"], r["instance"])] = r

    # runs.csv: média de iterações e tempo (ms) por (algo, instância)
    it = defaultdict(list)
    tm = defaultdict(list)
    for r in csv.DictReader(open(RUNS)):
        k = (r["algorithm"], r["instance"])
        it[k].append(int(r["iters"]))
        tm[k].append(int(r["time_ms"]))

    instances = sorted({inst for (_, inst) in per}, key=fam_key)

    lines = []
    lines.append(r"% Gerado por experiments/analysis/per_instance_table.py — NÃO editar à mão.")
    lines.append(r"{\footnotesize")
    lines.append(r"\begin{longtable}{llrrrrr}")
    lines.append(r"\caption{Resultados por instância: comparação dos cinco algoritmos. "
                 r"Custo = distância média; Gap em \% ao melhor conhecido; Iter.\ e Tempo são médias "
                 r"(30 execuções para os estocásticos). O menor gap de cada instância está em negrito.}"
                 r"\label{tab:porinstancia}\\")
    lines.append(r"\toprule")
    header = (r"\textbf{Instância} & \textbf{Alg.} & \textbf{Veíc.} & \textbf{Custo} & "
              r"\textbf{Gap (\%)} & \textbf{Iter.} & \textbf{Tempo (s)} \\")
    lines.append(header)
    lines.append(r"\midrule")
    lines.append(r"\endfirsthead")
    lines.append(r"\multicolumn{7}{l}{\footnotesize\itshape continuação da Tabela~\ref{tab:porinstancia}}\\")
    lines.append(r"\toprule")
    lines.append(header)
    lines.append(r"\midrule")
    lines.append(r"\endhead")
    lines.append(r"\midrule \multicolumn{7}{r}{\footnotesize\itshape continua na próxima página}\\")
    lines.append(r"\endfoot")
    lines.append(r"\bottomrule")
    lines.append(r"\endlastfoot")

    for inst in instances:
        # melhor gap desta instância (destaca TODOS os empatados)
        gaps = {a: float(per[(a, inst)]["gap_mean"]) for a in ALGO_ORDER if (a, inst) in per}
        bestval = min(gaps.values()) if gaps else None
        lines.append(rf"\multirow{{5}}{{*}}{{{inst}}}")
        for a in ALGO_ORDER:
            r = per.get((a, inst))
            if not r:
                continue
            veh = float(r["veh_mean"])
            cost = float(r["dist_mean"])
            gap = float(r["gap_mean"])
            iters = sum(it[(a, inst)]) / len(it[(a, inst)]) if it[(a, inst)] else 0
            tsec = (sum(tm[(a, inst)]) / len(tm[(a, inst)]) / 1000.0) if tm[(a, inst)] else 0.0
            name = ALGO_NAME[a]
            gtxt = f"{gap:.2f}".replace(".", ",")
            if bestval is not None and gap <= bestval + 1e-9:
                name = rf"\textbf{{{name}}}"
                gtxt = rf"\textbf{{{gtxt}}}"
            veh_s = f"{veh:.1f}".replace(".", ",")
            cost_s = f"{cost:.1f}".replace(".", ",")
            t_s = f"{tsec:.2f}".replace(".", ",")
            lines.append(rf"  & {name} & {veh_s} & {cost_s} & {gtxt} & {iters:.0f} & {t_s} \\")
        lines.append(r"\midrule")
    # troca o último \midrule por nada (o \endlastfoot já fecha)
    if lines[-1] == r"\midrule":
        lines.pop()
    lines.append(r"\end{longtable}")
    lines.append(r"}")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"tabela escrita: {OUT}")
    print(f"  {len(instances)} instâncias × {len(ALGO_ORDER)} algoritmos = {len(instances)*len(ALGO_ORDER)} linhas")


if __name__ == "__main__":
    main()
