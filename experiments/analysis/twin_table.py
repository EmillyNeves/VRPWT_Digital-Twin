"""Gera a tabela dinamico x estatico do gemeo digital (tab:twin), executando a
comparacao com semente fixa e escrevendo CSV + LaTeX. Nenhum numero copiado a mao.

A simulacao usa a camada LoRaWAN com os padroes do modulo (pdr=0.98, duty=1);
o cenario estatico nao usa sensores por definicao (coleta programada).
"""
import csv
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "digital_twin"))
os.environ.setdefault("VRPTW_SOLVER", os.path.join(ROOT, "solver", "build", "solve"))

from twin import compare_scenarios, load_map          # noqa: E402

OUT = os.path.join(ROOT, "results", "digital_twin")


def main():
    cmap = load_map("vitoria", None)
    comp, _, _ = compare_scenarios(cmap, cycles=16, frequency=3, seed=0)
    os.makedirs(OUT, exist_ok=True)

    with open(os.path.join(OUT, "compare.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["regime", "distancia", "coletas", "transbordos", "ciclos_com_rota"])
        for nome, k in comp.items():
            w.writerow([nome, k["distancia_total"], k["coletas"], k["transbordos"], k["ciclos_com_rota"]])

    d, e = comp["dinamico"], comp["estatico"]
    L = [r"\begin{table}[H]", r"\centering",
         r"\caption{Gêmeo digital (Vitória/ES, 16 ciclos, mesma realização de enchimento e "
         r"canal LoRaWAN com $\mathit{pdr}=0{,}98$): coleta dinâmica guiada pelos sensores "
         r"contra coleta estática de frequência fixa (a cada 3 ciclos). O regime estático "
         r"não usa sensores --- coleta todas as lixeiras no dia programado.}\label{tab:twin}",
         r"\begin{tabular}{lcccc}", r"\toprule",
         r"\textbf{Regime} & \textbf{Distância} & \textbf{Coletas} & \textbf{Transbordos} & "
         r"\textbf{Ciclos com rota} \\", r"\midrule",
         f"Dinâmico (sob demanda) & {d['distancia_total']:.1f} & {d['coletas']} & "
         f"\\textbf{{{d['transbordos']}}} & {d['ciclos_com_rota']} \\\\".replace(".", "{,}"),
         f"Estático (a cada 3 ciclos) & {e['distancia_total']:.1f} & {e['coletas']} & "
         f"{e['transbordos']} & {e['ciclos_com_rota']} \\\\".replace(".", "{,}"),
         r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    with open(os.path.join(OUT, "compare.tex"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("-> results/digital_twin/compare.{csv,tex}")
    print(comp)


if __name__ == "__main__":
    sys.exit(main())
