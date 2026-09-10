"""Gera as tabelas LaTeX da secao de Resultados a partir dos CSVs agregados.

Substitui as tabelas antes escritas a mao (tab:overall, tab:familia, tab:lex):
nenhum numero da secao de Resultados e transcrito manualmente -- regra de ouro
de docs/PLANO-RELATORIO-FINAL.md.

Entrada: results/{overall,gap_by_family,lexicographic_table}.csv
Saida  : results/tables/{overall,familia,lex}.tex
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "tables")

NOME = {"i1": "Solomon I1", "vnd": "VND", "grasp": "GRASP",
        "rgrasp": "GRASP reativo", "tabu": "Busca Tabu"}
ORDEM = ["i1", "vnd", "grasp", "rgrasp", "tabu"]


def num(x, fmt="%.2f"):
    return (fmt % float(x)).replace(".", "{,}")


def escreve(path, linhas):
    with open(path, "w") as fh:
        fh.write("\n".join(linhas) + "\n")
    print("->", os.path.relpath(path, ROOT))


def tab_overall():
    d = {r["algorithm"]: r for r in csv.DictReader(open(os.path.join(RES, "overall.csv")))}
    L = [r"\begin{table}[H]", r"\centering",
         r"\caption{Desempenho global nas 56 instâncias (gap de distância ao melhor "
         r"conhecido; 30 execuções por instância para GRASP e GRASP reativo, uma para os "
         r"determinísticos). \emph{Iterações} e \emph{tempo} são médias por execução; a "
         r"iteração tem custo diferente em cada método, e os dois números tornam esse "
         r"esforço explícito.}\label{tab:overall}",
         r"\small\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{lccccc}", r"\toprule",
         r"\textbf{Algoritmo} & \textbf{Gap médio (\%)} & \textbf{Gap melhor (\%)} & "
         r"\textbf{Veículos} & \textbf{Iterações} & \textbf{Tempo (s)} \\", r"\midrule"]
    melhor = min(float(d[a]["gap_mean"]) for a in ORDEM)
    for a in ORDEM:
        r = d[a]
        g = num(r["gap_mean"])
        # Sem negrito no gap médio (2026-09-10): GRASP e GRASP reativo são
        # estatisticamente indistinguíveis (Wilcoxon p=0,95); destacar um só
        # contradiria o texto. `melhor` fica calculado para eventual uso.
        deterministico = a in ("i1", "vnd", "tabu")
        gb = "---" if deterministico else num(r["gap_best"])
        it = "---" if a in ("i1", "vnd") else num(r["iters_mean"], "%.0f")
        tm = num(float(r["time_mean_ms"]) / 1000.0, "%.1f") if float(r["time_mean_ms"]) >= 100 \
            else num(float(r["time_mean_ms"]) / 1000.0, "%.3f")
        L.append(f"{NOME[a]} & {g} & {gb} & {num(r['veh_mean'])} & {it} & {tm} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    escreve(os.path.join(OUT, "overall.tex"), L)


def tab_familia():
    d = {r["algorithm"]: r for r in csv.DictReader(open(os.path.join(RES, "gap_by_family.csv")))}
    L = [r"\begin{table}[H]", r"\centering",
         r"\caption{Gap médio de distância por família (\%). As famílias diferem na "
         r"geografia dos clientes (C agrupada, R aleatória, RC mista), e a dificuldade "
         r"relativa dos métodos muda com ela.}\label{tab:familia}",
         r"\begin{tabular}{lccc}", r"\toprule",
         r"\textbf{Algoritmo} & \textbf{C (agrupada)} & \textbf{R (aleatória)} & "
         r"\textbf{RC (mista)} \\", r"\midrule"]
    for a in ORDEM:
        r = d[a]
        L.append(f"{NOME[a]} & {num(r['C'])} & {num(r['R'])} & {num(r['RC'])} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    escreve(os.path.join(OUT, "familia.tex"), L)


def tab_lex():
    rows = list(csv.DictReader(open(os.path.join(RES, "lexicographic_table.csv"))))
    fams = {"C": [], "R": [], "RC": []}
    for r in rows:
        fams[r["family"]].append(r)

    def media(sel, campo):
        return sum(float(r[campo]) for r in sel) / len(sel)

    # "Dinamics" e corruptela historica de DIMACS (nome de pasta mantido por
    # compatibilidade); no relatorio a referencia e citada como CVRPLIB sob a
    # convencao DIMACS -- ver data/reference-solutions/PROVENIENCIA.md.
    L = [r"\begin{table}[H]", r"\centering",
         r"\caption{Visão lexicográfica por família: veículos e distância médios das nossas "
         r"soluções (GRASP, melhor de 30 execuções) e das duas referências --- a de mínima "
         r"distância (CVRPLIB, convenção DIMACS) e a de mínimo número de veículos (SINTEF).}"
         r"\label{tab:lex}",
         r"\begin{tabular}{lcccccc}", r"\toprule",
         r"& \multicolumn{2}{c}{\textbf{Nosso (GRASP)}} & \multicolumn{2}{c}{\textbf{CVRPLIB "
         r"(mín.\ dist.)}} & \multicolumn{2}{c}{\textbf{SINTEF (mín.\ veíc.)}} \\",
         r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
         r"\textbf{Família} & veíc. & dist. & veíc. & dist. & veíc. & dist. \\", r"\midrule"]
    rotulo = {"C": "C (agrupada)", "R": "R (aleatória)", "RC": "RC (mista)"}
    for f in ("C", "R", "RC"):
        s = fams[f]
        L.append(f"{rotulo[f]} & {num(media(s,'our_veh'),'%.1f')} & {num(media(s,'our_dist'),'%.1f')} & "
                 f"{num(media(s,'din_veh'),'%.1f')} & {num(media(s,'din_dist'),'%.1f')} & "
                 f"{num(media(s,'sin_veh'),'%.1f')} & {num(media(s,'sin_dist'),'%.1f')} \\\\")
    L.append(r"\midrule")
    L.append(f"Todas & {num(media(rows,'our_veh'),'%.1f')} & {num(media(rows,'our_dist'),'%.1f')} & "
             f"{num(media(rows,'din_veh'),'%.1f')} & {num(media(rows,'din_dist'),'%.1f')} & "
             f"{num(media(rows,'sin_veh'),'%.1f')} & {num(media(rows,'sin_dist'),'%.1f')} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    escreve(os.path.join(OUT, "lex.tex"), L)


def tab_gain():
    d = {r["algorithm"]: r for r in csv.DictReader(open(os.path.join(RES, "calibration_gain.csv")))}
    P = {"grasp": "0{,}6316", "rgrasp": "0{,}0496", "tabu": "0{,}0431"}   # Wilcoxon pareado (06-ex-post)
    L = [r"\begin{table}[H]", r"\centering",
         r"\caption{A calibração valeu a pena? Parâmetros clássicos da literatura "
         r"($\alpha{=}0{,}30$; $\delta{=}1{,}0$, \textit{block\_frac}$=0{,}1$; "
         r"\textit{tenure}$=15$) contra os calibrados pelo \textit{irace}, nas 28 instâncias "
         r"de \emph{teste} --- nunca vistas pela calibração ---, com 30 sementes por método "
         r"estocástico (a Busca Tabu, determinística, executa uma vez por configuração) e o "
         r"mesmo $K=800$. Ganho positivo = calibrado melhor; $p$ do teste de Wilcoxon pareado.}"
         r"\label{tab:gain}",
         r"\footnotesize\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{lccccc}", r"\toprule",
         r"\textbf{Cenário} & \textbf{Gap clássico (\%)} & \textbf{Gap calibrado (\%)} & "
         r"\textbf{Ganho (pp)} & \textbf{melhor/pior/empate} & $p$ \\", r"\midrule"]
    for a in ("grasp", "rgrasp", "tabu"):
        r = d[a]
        L.append(f"{NOME[a]} & {num(r['gap_default'])} & {num(r['gap_tuned'])} & "
                 f"{num(r['gain_pp'], '%+.2f')} & {r['tuned_better']}/{r['tuned_worse']}/{r['tie']} & {P[a]} \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    escreve(os.path.join(OUT, "gain.tex"), L)


def tab_pi():
    import collections
    d = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(RES, "primal_integral.csv"))):
        d[r["algorithm"]].append(float(r["primal_integral_mean"]))
    m = {a: sum(v) / len(v) for a, v in d.items()}
    ordem = sorted(m, key=m.get)
    frase = ", ".join(f"{NOME[a]} ($\\mathit{{PI}}={num(m[a])}$)" for a in ordem)
    L = [f"% gerado por results_tables.py a partir de primal_integral.csv -- nao editar",
         f"A integral primal média ordena os métodos assim: {frase} (menor é melhor)."]
    escreve(os.path.join(OUT, "pi_frase.tex"), L)


def main():
    os.makedirs(OUT, exist_ok=True)
    tab_overall()
    tab_familia()
    tab_lex()
    tab_gain()
    tab_pi()


if __name__ == "__main__":
    sys.exit(main())
