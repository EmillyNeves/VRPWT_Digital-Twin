#!/usr/bin/env python3
"""Figura ciclo a ciclo do gemeo digital: o que torna o roteamento dinamico.

Roda UMA realizacao de enchimento (semente 0) nos dois regimes, exatamente com os
parametros da comparacao pareada (experiments/analysis/twin_table.py: 16 ciclos,
estatico a cada 3 ciclos, parametros finais do estudo, capacidade 30), e desenha:

  (a) tamanho da instancia VRPTW gerada em cada ciclo (lixeiras roteadas) nos dois
      regimes -- o conjunto de clientes muda de ciclo para ciclo no regime dinamico;
  (b) transbordos acumulados (episodios) nos dois regimes;
  (c) prazo de coleta em funcao do enchimento (janela dinamica, equacao do relatorio),
      calculado pela MESMA funcao que gera as instancias (bin_window_demand).

Saidas: results/digital_twin/cycles_seed0.csv (dados de (a) e (b), rastreaveis)
        results/digital_twin/cycles_seed0.png

Uso (com o venv): .venv/bin/python digital_twin/cycles_figure.py [--seed 0]
"""
import argparse
import csv
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from twin import compare_scenarios, load_map, bin_window_demand   # noqa: E402

OUT = os.path.join(ROOT, "results", "digital_twin")
CYCLES = 16          # iguais a twin_table.py
FREQUENCY = 3
BUDGET_MS = 60000
THRESHOLD = 0.7
HORIZON = 5000       # padrao de twin.simulate (grafo euclidiano normalizado)
KAPPAS = (0.3, 0.6, 0.9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    cmap = load_map("vitoria", None)
    _, dyn, sta = compare_scenarios(cmap, cycles=CYCLES, frequency=FREQUENCY,
                                    seed=args.seed, budget_ms=BUDGET_MS)

    os.makedirs(OUT, exist_ok=True)
    csv_path = os.path.join(OUT, f"cycles_seed{args.seed}.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ciclo", "periodo", "regime", "lixeiras_roteadas", "veiculos",
                    "distancia", "transbordos_acum"])
        for regime, hist in (("dinamico", dyn), ("estatico", sta)):
            for h in hist:
                w.writerow([h["cycle"], h["period"], regime, len(h["served"]),
                            h["vehicles"], f"{h['distance']:.1f}", h["overflow"]])
    print(f"dados por ciclo salvos em {csv_path}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cycles = [h["cycle"] for h in dyn]
    peak = [h["period"] == "pico" for h in dyn]
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))

    def shade_peaks(ax):
        first = True
        for c, p in zip(cycles, peak):
            if p:
                ax.axvspan(c - 0.5, c + 0.5, color="0.92", zorder=0,
                           label="ciclo de pico" if first else None)
                first = False

    # (a) tamanho da instancia por ciclo
    ax = axes[0]
    shade_peaks(ax)
    ax.bar([c - 0.2 for c in cycles], [len(h["served"]) for h in dyn], width=0.4,
           color="seagreen", label="dinâmico (sob demanda)")
    ax.bar([c + 0.2 for c in cycles], [len(h["served"]) for h in sta], width=0.4,
           color="0.45", label=f"estático (a cada {FREQUENCY} ciclos)")
    ax.set_xlabel("ciclo"); ax.set_ylabel("lixeiras roteadas no ciclo")
    ax.set_title("(a) instância VRPTW gerada a cada ciclo")
    ax.set_xticks(cycles); ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", ls=":", alpha=0.5)

    # (b) transbordos acumulados
    ax = axes[1]
    shade_peaks(ax)
    ax.step(cycles, [h["overflow"] for h in dyn], where="post", color="seagreen",
            lw=2, label="dinâmico")
    ax.step(cycles, [h["overflow"] for h in sta], where="post", color="0.45",
            lw=2, ls="--", label="estático")
    ax.set_xlabel("ciclo"); ax.set_ylabel("transbordos acumulados (episódios)")
    ax.set_title("(b) falhas de serviço ao longo dos ciclos")
    ax.set_xticks(cycles); ax.legend(fontsize=8, loc="upper left")
    ax.grid(axis="y", ls=":", alpha=0.5)

    # (c) janela dinamica: prazo relativo em funcao do enchimento
    ax = axes[2]
    fills = [i / 200 for i in range(0, 201)]
    for kappa, style in zip(KAPPAS, (":", "-", "--")):
        dues = [bin_window_demand(f, THRESHOLD, HORIZON, True, kappa)[2] / HORIZON
                for f in fills]
        ax.plot(fills, dues, style, color="crimson", lw=2, label=rf"$\kappa={kappa}$")
    ax.axvline(THRESHOLD, color="0.3", lw=1, ls="-.")
    ax.text(THRESHOLD + 0.01, 0.42, rf"limiar $\tau={THRESHOLD}$", fontsize=8, color="0.3")
    ax.set_xlabel("enchimento $f$ da lixeira"); ax.set_ylabel("prazo de coleta  $due/H$")
    ax.set_ylim(0, 1.05); ax.set_xlim(0, 1)
    ax.set_title("(c) janela de tempo que encolhe com a criticidade")
    ax.legend(fontsize=8, loc="lower left"); ax.grid(ls=":", alpha=0.5)

    fig.suptitle(f"Gêmeo digital (Vitória/ES, semente {args.seed}, $\\tau={THRESHOLD}$): "
                 "roteamento sob demanda e janelas dinâmicas")
    fig.tight_layout()
    fig_path = os.path.join(OUT, f"cycles_seed{args.seed}.png")
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    print(f"figura salva em {fig_path}")


if __name__ == "__main__":
    main()
