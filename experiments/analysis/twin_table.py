"""Gera a tabela dinamico x estatico do gemeo digital (tab:twin), executando a
comparacao em 30 SEMENTES PAREADAS (mesma realizacao de enchimento nos dois
regimes, semente a semente) e escrevendo CSV + LaTeX. Nenhum numero copiado a mao.

Protocolo (pendencia 1.3 do PLANO-RELATORIO-FINAL): media +- IC95% sobre as
sementes e teste de Wilcoxon pareado por indicador -- substitui a inferencia
sobre n=1 da versao anterior. Os dois regimes rodam com os parametros FINAIS do
estudo (study_params.json) e parada por iteracoes sem melhora (K), com teto de
tempo apenas como salvaguarda -- pendencia 1.4.

A simulacao usa a camada LoRaWAN com os padroes do modulo (pdr=0.98, duty=1);
o cenario estatico nao usa sensores por definicao (coleta programada).
"""
import csv
import math
import os
import statistics
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "digital_twin"))
os.environ.setdefault("VRPTW_SOLVER", os.path.join(ROOT, "solver", "build", "solve"))

from twin import compare_scenarios, load_map          # noqa: E402

OUT = os.path.join(ROOT, "results", "digital_twin")
SEEDS = 30
CYCLES = 16
FREQUENCY = 3
BUDGET_MS = 60000     # salvaguarda; a parada operativa e K (study_params.json)

INDICADORES = [("distancia_total", "Distância"), ("coletas", "Coletas"),
               ("transbordos", "Transbordos"), ("ciclos_com_rota", "Ciclos com rota")]


def dec(x, nd):
    return f"{x:.{nd}f}".replace(".", "{,}")


def ic95(vals):
    """Media e meia-largura do IC95% (t de Student)."""
    from scipy.stats import t
    m = statistics.mean(vals)
    if len(vals) < 2:
        return m, 0.0
    half = t.ppf(0.975, len(vals) - 1) * statistics.stdev(vals) / math.sqrt(len(vals))
    return m, half


def wilcoxon_p(a, b):
    from scipy.stats import wilcoxon
    diffs = [x - y for x, y in zip(a, b)]
    if all(d == 0 for d in diffs):
        return 1.0
    return float(wilcoxon(a, b, zero_method="zsplit").pvalue)


def main():
    cmap = load_map("vitoria", None)
    rows = []
    for seed in range(SEEDS):
        comp, _, _ = compare_scenarios(cmap, cycles=CYCLES, frequency=FREQUENCY,
                                       seed=seed, budget_ms=BUDGET_MS)
        for regime, k in comp.items():
            rows.append({"seed": seed, "regime": regime, **{c: k[c] for c, _ in INDICADORES}})
        print(f"  semente {seed}: din={comp['dinamico']['transbordos']} "
              f"est={comp['estatico']['transbordos']} transbordos", flush=True)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "compare.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["seed", "regime"] + [c for c, _ in INDICADORES])
        w.writeheader()
        w.writerows(rows)

    din = {c: [r[c] for r in rows if r["regime"] == "dinamico"] for c, _ in INDICADORES}
    est = {c: [r[c] for r in rows if r["regime"] == "estatico"] for c, _ in INDICADORES}
    pvals = {c: wilcoxon_p(din[c], est[c]) for c, _ in INDICADORES}

    def celula(vals, nd):
        m, h = ic95(vals)
        return f"${dec(m, nd)} \\pm {dec(h, nd)}$"

    L = [r"\begin{table}[H]", r"\centering",
         r"\caption{Gêmeo digital (Vitória/ES, " + str(CYCLES) + r" ciclos, canal LoRaWAN com "
         r"$\mathit{pdr}=0{,}98$): coleta dinâmica guiada pelos sensores contra coleta estática "
         r"de frequência fixa (a cada " + str(FREQUENCY) + r" ciclos), sobre " + str(SEEDS) +
         r" realizações independentes de enchimento --- os dois regimes veem a \emph{mesma} "
         r"realização em cada semente (comparação pareada). Células: média $\pm$ IC95\%. "
         r"Transbordos contados por \emph{episódio} (a lixeira atinge a capacidade antes da "
         r"coleta; uma contagem por enchimento). Última linha: $p$ do teste de Wilcoxon "
         r"pareado sobre as " + str(SEEDS) + r" sementes.}\label{tab:twin}",
         r"\begin{tabular}{lcccc}", r"\toprule",
         r"\textbf{Regime} & \textbf{Distância} & \textbf{Coletas} & \textbf{Transbordos} & "
         r"\textbf{Ciclos com rota} \\", r"\midrule",
         "Dinâmico (sob demanda) & " + " & ".join(
             celula(din[c], 1 if c == "distancia_total" else (1 if c != "ciclos_com_rota" else 1))
             for c, _ in INDICADORES) + r" \\",
         "Estático (a cada 3 ciclos) & " + " & ".join(
             celula(est[c], 1) for c, _ in INDICADORES) + r" \\",
         r"\midrule",
         r"$p$ (Wilcoxon pareado) & " + " & ".join(dec(pvals[c], 4) for c, _ in INDICADORES) + r" \\",
         r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    with open(os.path.join(OUT, "compare.tex"), "w") as fh:
        fh.write("\n".join(L) + "\n")

    print("-> results/digital_twin/compare.{csv,tex}")
    for c, nome in INDICADORES:
        md, _ = ic95(din[c])
        me, _ = ic95(est[c])
        print(f"  {nome}: dinamico {md:.1f} x estatico {me:.1f}  (p={pvals[c]:.4f})")


if __name__ == "__main__":
    sys.exit(main())
