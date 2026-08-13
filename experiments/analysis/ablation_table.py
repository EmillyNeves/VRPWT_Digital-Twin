"""Gera a tabela LaTeX da ablacao de vizinhancas, para \\input{} no relatorio.

Le results/neighborhoods/{ablation.csv,summary.csv} e escreve
results/neighborhoods/ablacao.tex. Nenhum numero da tabela e escrito a mao --
regra de ouro de docs/PLANO-RELATORIO-FINAL.md. A tabela reporta, alem do
delta de gap, o placar por instancia e o p de Wilcoxon com correcao de Holm,
porque um delta medio sem significancia e leitura incompleta (o caso do
Cross-exchange: afeta 4/28 instancias e o teste nao tem poder para remove-lo).
"""
import csv
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR = os.path.join(ROOT, "results", "neighborhoods")

NOME = {"sem 2-opt intra": "sem 2-opt intra", "sem Swap": "sem Swap",
        "sem 2-opt*": "sem 2-opt\\hspace{0.5pt}*", "sem Relocate": "sem Relocate",
        "sem Or-opt": "sem Or-opt", "sem Cross-exch.": "sem Cross-exchange"}


def main():
    # gap medio do kit completo, das mesmas execucoes (design leave-one-out)
    base = [float(r["gap_pct"]) for r in csv.DictReader(open(os.path.join(DIR, "ablation.csv")))
            if r["config"] == "kit completo (6)"]
    if not base:
        sys.exit("ablation.csv sem as linhas do kit completo")
    gfull = statistics.mean(base)

    rows = list(csv.DictReader(open(os.path.join(DIR, "summary.csv"))))
    rows.sort(key=lambda r: -float(r["delta_gap_pp"]))

    def num(x, fmt):
        """Formata um numero com virgula decimal, sem tocar no resto da linha."""
        return (fmt % x).replace(".", "{,}")

    L = [r"\begin{table}[H]", r"\centering",
         r"\caption{Ablação \emph{leave-one-out} do conjunto de vizinhanças (VND, 28 instâncias "
         r"de treino): efeito de remover cada operador do kit completo, com o placar por "
         r"instância e o $p$ de Wilcoxon pareado sob correção de Holm. A remoção de qualquer "
         r"operador piora o gap médio; a última coluna mostra que o teste tem poder limitado "
         r"para os operadores que afetam poucas instâncias.}\label{tab:ablacao}",
         r"\begin{tabular}{lccccc}", r"\toprule",
         r"\textbf{Configuração} & \textbf{Gap médio (\%)} & \textbf{$\Delta$ (pp)} & "
         r"\textbf{piora/melhora/empata} & \textbf{$p$ (Holm)} & \textbf{signif.} \\",
         r"\midrule",
         f"Kit completo (6 operadores) & {num(gfull, '%.2f')} & --- & --- & --- & --- \\\\"]
    for r in rows:
        d = float(r["delta_gap_pp"])
        p = float(r["p_holm"])
        sig = "sim" if r["significant"].strip().startswith("s") else "não"
        L.append(f"\\quad {NOME.get(r['config'], r['config'])} & {num(gfull + d, '%.2f')} & "
                 f"{num(d, '%+.2f')} & {r['worse']}/{r['better']}/{r['tie']} & "
                 f"{num(p, '%.4f')} & {sig} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]

    out = os.path.join(DIR, "ablacao.tex")
    with open(out, "w") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"tabela escrita em {out}")


if __name__ == "__main__":
    sys.exit(main())
