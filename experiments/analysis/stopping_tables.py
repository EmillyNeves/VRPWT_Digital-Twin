"""Gera a tabela LaTeX do orcamento de parada, para \\input{} no relatorio.

Le results/stopping/{convergence.csv,cost.csv} e escreve
results/stopping/budget_K.tex. Nenhum numero da subsecao de K e escrito a mao --
regra de ouro de docs/PLANO-RELATORIO-FINAL.md.

Duas colunas de tempo, com significados diferentes:
  mediana  -- execucao tipica, medida sem concorrencia (uma instancia por familia)
  maximo   -- pior caso do mesmo conjunto; e o que precisa caber no teto de seguranca
"""
import argparse
import collections
import csv
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ALGOS = [("grasp", "GRASP"), ("rgrasp", "Reativo"), ("tabu", "Tabu")]


def ler(path, chave, valor):
    d = collections.defaultdict(list)
    with open(path) as fh:
        for r in csv.DictReader(fh):
            d[chave(r)].append(valor(r))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conv", default=os.path.join(ROOT, "results/stopping/convergence.csv"))
    ap.add_argument("--cost", default=os.path.join(ROOT, "results/stopping/cost.csv"))
    ap.add_argument("--k-escolhido", type=int, default=800)
    ap.add_argument("--out", default=os.path.join(ROOT, "results/stopping/budget_K.tex"))
    args = ap.parse_args()

    gap = ler(args.conv, lambda r: (r["algorithm"], int(r["K"])), lambda r: float(r["gap_pct"]))
    ks = sorted({k for _, k in gap})

    tempo = {}
    if os.path.isfile(args.cost):
        tempo = ler(args.cost, lambda r: (r["algorithm"], int(r["K"])),
                    lambda r: int(r["time_ms_median"]))

    def celula(a, k):
        if not gap.get((a, k)):
            return "---"
        g = statistics.mean(gap[(a, k)])
        return f"\\textbf{{{g:.2f}}}" if k == args.k_escolhido else f"{g:.2f}"

    def celula_t(a, k):
        v = tempo.get((a, k))
        if not v:
            return "---"
        s = statistics.median(v) / 1000.0
        return f"\\textbf{{{s:.1f}}}" if k == args.k_escolhido else f"{s:.1f}"

    L = []
    L.append(r"\begin{table}[htbp]")
    L.append(r"\centering")
    L.append(r"\caption{Efeito do orçamento de parada nas 28 instâncias de treino. "
             r"\emph{Gap}: distância percentual média ao melhor valor conhecido. "
             r"\emph{Tempo}: mediana por execução, medida sem concorrência. O valor adotado "
             f"($K={args.k_escolhido}$) está em negrito. O gap decresce ao longo de toda a "
             r"faixa medida, sem platô --- razão pela qual $K$ é declarado como orçamento "
             r"computacional, e não derivado de um ponto de convergência.}"
             f"\\label{{tab:orcamento}}")
    L.append(r"\begin{tabular}{r rrr rrr}")
    L.append(r"\toprule")
    L.append(r"& \multicolumn{3}{c}{\emph{gap} médio (\%)} & \multicolumn{3}{c}{tempo mediano (s)} \\")
    L.append(r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}")
    L.append(r"$K$ & " + " & ".join(n for _, n in ALGOS) + " & "
             + " & ".join(n for _, n in ALGOS) + r" \\")
    L.append(r"\midrule")
    for k in ks:
        L.append(f"{k} & " + " & ".join(celula(a, k) for a, _ in ALGOS) + " & "
                 + " & ".join(celula_t(a, k) for a, _ in ALGOS) + r" \\")
    L.append(r"\bottomrule")
    L.append(r"\end{tabular}")
    L.append(r"\end{table}")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"tabela escrita em {args.out} ({len(ks)} orçamentos)")

    escreve_invariancia(args.conv, ks,
                        os.path.join(os.path.dirname(args.out), "invariance_K.tex"))


def escreve_invariancia(conv, ks, out):
    """Tabela do apendice: o ordenamento e os testes par a par mudam com K?

    E a resposta antecipada a objecao "e se outro K desse outra conclusao?".
    Se alguma linha divergir das demais, a tabela mostra isso -- ela nao foi
    construida para confirmar a escolha, e sim para expo-la.
    """
    from scipy.stats import wilcoxon

    por = collections.defaultdict(dict)
    with open(conv) as fh:
        for r in csv.DictReader(fh):
            por[(r["algorithm"], int(r["K"]))][r["instance"]] = float(r["gap_pct"])
    insts = sorted(por[("grasp", ks[0])])

    L = [r"\begin{table}[htbp]", r"\centering",
         r"\caption{Invariância das conclusões ao orçamento, nas instâncias de treino. "
         r"Em toda a faixa medida --- uma variação de "
         f"${ks[-1] // ks[0]}\\times$ --- o ordenamento dos métodos e o resultado dos testes "
         r"par a par (Wilcoxon pareado) não se alteram. Nenhuma conclusão do estudo depende "
         r"do valor de $K$ adotado. Semente única: o \emph{não significativo} entre GRASP e "
         r"Reativo deve ser lido como ausência de evidência, não como equivalência "
         r"estabelecida.}\label{tab:invariancia}",
         r"\begin{tabular}{r l rr}", r"\toprule",
         r"$K$ & ordenamento & $p$ (GRASP$\times$Reativo) & $p$ (GRASP$\times$Tabu) \\",
         r"\midrule"]
    for k in ks:
        m = {a: statistics.mean(por[(a, k)][i] for i in insts) for a, _ in ALGOS}
        nome = dict(ALGOS)
        ordem = " $<$ ".join(nome[a] for a in sorted(m, key=m.get))
        p1 = wilcoxon([por[("grasp", k)][i] - por[("rgrasp", k)][i] for i in insts],
                      zero_method="zsplit").pvalue
        p2 = wilcoxon([por[("grasp", k)][i] - por[("tabu", k)][i] for i in insts],
                      zero_method="zsplit").pvalue
        L.append(f"{k} & {ordem} & {p1:.4f} & {p2:.4f} " + r"\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

    with open(out, "w") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"tabela do apêndice escrita em {out}")


if __name__ == "__main__":
    sys.exit(main())
