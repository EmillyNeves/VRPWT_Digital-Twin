#!/usr/bin/env python3
"""Figuras do banner da XXXVI Jornada de IC da Ufes (2026).

Redesenha, em escala de pôster (fontes grandes, 300 dpi), os gráficos que
podem ser reconstruídos exatamente a partir dos CSVs já gravados em results/.
Nenhum algoritmo é reexecutado, de modo que os números do banner são
necessariamente os mesmos do relatório final.

Uso:  .venv/bin/python banner/figuras/gerar_figuras.py
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(_HERE, "..", "..", "results")
OUT = _HERE

# Paleta do banner (azul-marinho + ciano Ufes + apoios)
NAVY = "#17365D"
CYAN = "#1BA1E2"
GRAY = "#8C8C8C"
ORANGE = "#E07A1F"
GREEN = "#2E8B57"
RED = "#C0392B"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 26,
    "axes.titlesize": 30,
    "axes.labelsize": 28,
    "xtick.labelsize": 26,
    "ytick.labelsize": 26,
    "legend.fontsize": 25,
    "axes.linewidth": 2.0,
    "xtick.major.width": 2.0,
    "ytick.major.width": 2.0,
    "xtick.major.size": 8,
    "ytick.major.size": 8,
    "lines.linewidth": 4.0,
    "savefig.dpi": 300,
    "figure.dpi": 300,
})

NOMES = {"i1": "Solomon I1", "vnd": "VND", "tabu": "Busca Tabu",
         "grasp": "GRASP", "rgrasp": "GRASP reativo"}
ORDEM = ["i1", "vnd", "tabu", "grasp", "rgrasp"]


def _read(path):
    with open(os.path.join(RES, path), newline="") as fh:
        return list(csv.DictReader(fh))


def _save(fig, nome):
    p = os.path.join(OUT, nome)
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("gerada:", nome)


# --------------------------------------------------------------- 1. cascata
def fig_cascata():
    """Gap medio por metodo: a queda construcao -> busca local -> meta-heuristica."""
    linhas = {r["algorithm"]: r for r in _read("overall.csv")}
    vals = [float(linhas[a]["gap_mean"]) for a in ORDEM]
    cores = [GRAY, CYAN, ORANGE, NAVY, NAVY]

    fig, ax = plt.subplots(figsize=(13, 8))
    x = np.arange(len(ORDEM))
    b = ax.bar(x, vals, color=cores, edgecolor="white", linewidth=2.5, zorder=3)
    ax.set_yscale("log")
    ax.set_ylim(0.6, 90)
    ax.set_xticks(x)
    ax.set_xticklabels([NOMES[a] for a in ORDEM], rotation=18, ha="right")
    ax.set_ylabel("Gap médio de distância (%)\nescala logarítmica")
    ax.grid(axis="y", linestyle=":", linewidth=1.6, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    for rect, v in zip(b, vals):
        ax.annotate(f"{v:.2f}".replace(".", ","),
                    (rect.get_x() + rect.get_width() / 2, v),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=28, fontweight="bold", color=NAVY)
    from matplotlib.ticker import FixedLocator, FuncFormatter
    ax.yaxis.set_major_locator(FixedLocator([1, 2, 5, 10, 20, 50]))
    ax.yaxis.set_minor_locator(FixedLocator([]))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.text(0.985, 0.96,
            "cada camada contribui\n"
            "busca local: $-$27,5 pp\n"
            "meta-heurística: $-$6,5 pp",
            transform=ax.transAxes, ha="right", va="top", fontsize=25,
            color=RED, fontweight="bold", linespacing=1.4,
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                      edgecolor=RED, linewidth=2.5))
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    _save(fig, "cascata_gap.png")


# --------------------------------------------------------------- 2. familias
def fig_familia():
    """Gap por familia, so os metodos de melhoria (a I1 esta na figura da cascata)."""
    linhas = {r["algorithm"]: r for r in _read("gap_by_family.csv")}
    fams = [("C", "C\nagrupada"), ("R", "R\naleatória"), ("RC", "RC\nmista")]
    sel = ["vnd", "tabu", "grasp", "rgrasp"]
    cores = {"vnd": CYAN, "tabu": ORANGE, "grasp": NAVY, "rgrasp": GREEN}

    fig, ax = plt.subplots(figsize=(13, 7.0))
    x = np.arange(len(fams))
    w = 0.20
    for i, a in enumerate(sel):
        v = [float(linhas[a][f[0]]) for f in fams]
        b = ax.bar(x + (i - 1.5) * w, v, w, label=NOMES[a], color=cores[a],
                   edgecolor="white", linewidth=1.5, zorder=3)
        for rect, val in zip(b, v):
            ax.annotate(f"{val:.2f}".replace(".", ","),
                        (rect.get_x() + rect.get_width() / 2, val),
                        textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=21, color=cores[a],
                        fontweight="bold", rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels([f[1] for f in fams])
    ax.set_ylabel("Gap médio (%)")
    ax.set_xlabel("Família de instâncias (geografia dos clientes)")
    ax.legend(ncol=4, frameon=False, loc="upper left", columnspacing=1.0,
              handletextpad=0.5)
    ax.set_ylim(0, 15.5)
    ax.grid(axis="y", linestyle=":", linewidth=1.6, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    _save(fig, "familia_gap.png")


# --------------------------------------------- 3. diagrama de diferenca critica
def fig_cd():
    """Postos medios de Friedman nas 56 instancias + barra de Nemenyi (CD)."""
    linhas = _read("per_instance.csv")
    por_inst = {}
    for r in linhas:
        por_inst.setdefault(r["instance"], {})[r["algorithm"]] = float(r["gap_mean"])
    inst = sorted(por_inst)
    N = len(inst)
    postos = {a: 0.0 for a in ORDEM}
    for i in inst:
        v = sorted(((por_inst[i][a], a) for a in ORDEM))
        # postos com empates medios
        j = 0
        while j < len(v):
            k = j
            while k + 1 < len(v) and abs(v[k + 1][0] - v[j][0]) < 1e-12:
                k += 1
            media = (j + k) / 2.0 + 1
            for t in range(j, k + 1):
                postos[v[t][1]] += media
            j = k + 1
    postos = {a: postos[a] / N for a in ORDEM}
    k = len(ORDEM)
    q05 = 2.728  # range estudentizado, k=5, alfa=0,05
    CD = q05 * np.sqrt(k * (k + 1) / (6.0 * N))

    ordenado = sorted(postos.items(), key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(14, 4.0))
    lo, hi = 1, 5
    ax.set_xlim(lo - 0.55, hi + 0.55)   # 1 (melhor) a esquerda
    ax.set_ylim(0.10, 1.0)
    ax.axis("off")
    yb = 0.66
    ax.plot([lo, hi], [yb, yb], color="black", lw=3)
    for t in np.arange(lo, hi + 0.001, 0.5):
        ax.plot([t, t], [yb, yb + 0.05], color="black", lw=3)
        ax.text(t, yb + 0.085, f"{t:g}".replace(".", ","), ha="center",
                fontsize=25)
    for idx, (a, p) in enumerate(ordenado):
        esquerda = idx < k / 2.0
        nivel = idx if esquerda else (k - 1 - idx)
        y = yb - 0.17 - 0.16 * nivel
        xr = lo - 0.5 if esquerda else hi + 0.5
        ax.plot([p, p], [yb, y], color=NAVY, lw=3)
        ax.plot([p, xr], [y, y], color=NAVY, lw=3)
        ax.text(xr, y + 0.04, f"{NOMES[a]} ({p:.2f})".replace(".", ","),
                ha="left" if esquerda else "right", fontsize=26,
                fontweight="bold", color=NAVY)
    grupos, i = [], 0
    while i < k:
        j = i
        while j + 1 < k and ordenado[j + 1][1] - ordenado[i][1] <= CD:
            j += 1
        if j > i:
            grupos.append((ordenado[i][1], ordenado[j][1]))
        i += 1
    maximais = [g for g in grupos
                if not any(h != g and h[0] <= g[0] and h[1] >= g[1] for h in grupos)]
    for n, (a, b) in enumerate(maximais):
        y = yb - 0.062 - 0.062 * n
        ax.plot([a - 0.045, b + 0.045], [y, y], color=RED, lw=10,
                solid_capstyle="butt")
    ax.plot([hi - CD, hi], [yb + 0.21, yb + 0.21], color=RED, lw=5)
    for xx in (hi - CD, hi):
        ax.plot([xx, xx], [yb + 0.19, yb + 0.23], color=RED, lw=5)
    ax.text(hi - CD / 2, yb + 0.245, f"CD = {CD:.3f}".replace(".", ","),
            ha="center", fontsize=26, color=RED, fontweight="bold")

    _save(fig, "cd_diagrama.png")
    print(f"   postos: {postos}, N={N}, CD={CD:.3f}")


# ------------------------------------------------------- 4. limiar (trade-off)
def fig_limiar():
    linhas = [r for r in _read("digital_twin/sensitivity.csv")
              if r["parametro"] == "threshold"]
    tau = [float(r["valor"]) for r in linhas]
    col = [int(float(r["coletas"])) for r in linhas]
    tra = [int(float(r["transbordos"])) for r in linhas]

    fig, ax = plt.subplots(figsize=(13, 8))
    ax.plot(tau, col, "-o", color=NAVY, markersize=16, label="coletas (esforço)")
    ax.set_xlabel("Limiar de acionamento  $\\tau$")
    ax.set_ylabel("Coletas no horizonte", color=NAVY)
    ax.tick_params(axis="y", colors=NAVY)
    ax.set_ylim(80, 250)
    ax.axhline(228, color=NAVY, linestyle="--", lw=3, alpha=0.65)
    ax.text(0.885, 232, "228 = regime estático", color=NAVY, fontsize=24,
            ha="right", fontweight="bold")

    ax2 = ax.twinx()
    ax2.plot(tau, tra, "-s", color=RED, markersize=16,
             label="transbordos (falha de serviço)")
    ax2.set_ylabel("Transbordos (episódios)", color=RED)
    ax2.tick_params(axis="y", colors=RED)
    ax2.set_ylim(0, 70)

    ax.axvspan(0.68, 0.72, color=ORANGE, alpha=0.18, zorder=0)
    ax.text(0.70, 95, "padrão", ha="center", fontsize=24, color=ORANGE,
            fontweight="bold")
    for t, c in zip(tau, col):
        ax.annotate(str(c), (t, c), textcoords="offset points", xytext=(0, 16),
                    ha="center", fontsize=23, color=NAVY)
    for t, v in zip(tau, tra):
        ax2.annotate(str(v), (t, v), textcoords="offset points", xytext=(0, -34),
                     ha="center", fontsize=23, color=RED)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, loc="center right",
              bbox_to_anchor=(1.0, 0.62))
    ax.set_xticks(tau)
    ax.set_xticklabels([f"{t:.1f}".replace(".", ",") for t in tau])
    ax.grid(axis="y", linestyle=":", linewidth=1.6, alpha=0.5)
    ax.set_axisbelow(True)
    _save(fig, "limiar_tradeoff.png")


# ------------------------------------------------------------- 5. regimes
def fig_regimes():
    linhas = _read("digital_twin/compare.csv")
    din = {k: [] for k in ("distancia_total", "coletas", "transbordos")}
    est = {k: [] for k in din}
    for r in linhas:
        alvo = din if r["regime"] == "dinamico" else est
        for k in alvo:
            alvo[k].append(float(r[k]))

    def mic(v):
        v = np.asarray(v)
        m = v.mean()
        s = v.std(ddof=1) / np.sqrt(len(v)) * 1.96 if len(v) > 1 else 0.0
        return m, s

    rot = ["Distância\ntotal", "Coletas\n(esvaziamentos)", "Transbordos\n(episódios)"]
    chaves = ["distancia_total", "coletas", "transbordos"]
    md, sd = zip(*[mic(din[k]) for k in chaves])
    me, se = zip(*[mic(est[k]) for k in chaves])
    # normaliza pelo estatico, para as tres grandezas caberem no mesmo eixo
    nd = [100.0 * a / b for a, b in zip(md, me)]
    ed = [100.0 * a / b for a, b in zip(sd, me)]

    fig, ax = plt.subplots(figsize=(13, 7.5))
    x = np.arange(3)
    w = 0.34
    ax.bar(x - w / 2, [100, 100, 100], w, color=GRAY, edgecolor="white",
           linewidth=2, label="Estático (a cada 3 ciclos)", zorder=3)
    ax.bar(x + w / 2, nd, w, yerr=ed, capsize=10, color=NAVY, edgecolor="white",
           linewidth=2, label="Dinâmico (sob demanda)", zorder=3,
           error_kw=dict(lw=3, ecolor="black"))
    ax.axhline(100, color="black", lw=2.5)
    ax.set_xticks(x)
    ax.set_xticklabels(rot)
    ax.set_ylabel("Relativo ao regime estático (%)")
    ax.set_ylim(0, 192)
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="y", linestyle=":", linewidth=1.6, alpha=0.6, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    frases = [f"+{nd[0]-100:.1f} %".replace(".", ","),
              f"$-${abs(nd[1]-100):.0f} %",
              f"+{nd[2]-100:.0f} %"]
    cores = [ORANGE, GREEN, RED]
    for xi, v, f, c in zip(x, nd, frases, cores):
        ax.annotate(f, (xi + w / 2, v), textcoords="offset points",
                    xytext=(0, 26), ha="center", fontsize=30,
                    fontweight="bold", color=c)

    _save(fig, "regimes.png")
    print("   medias dinamico:", md, "estatico:", me)


# ------------------------------------------------- 6. operadores de vizinhanca
# Mesma geometria de experiments/analysis/algo_figures.py, redesenhada em
# escala de poster e sem travessoes nos rotulos.
_COORD = {0: (0.0, 0.0), 1: (-2.4, 2.6), 2: (-3.0, 0.4), 3: (-2.0, -2.2),
          4: (2.4, 2.6), 5: (3.0, 0.4), 6: (2.0, -2.2)}
_RCOL = ["#2166ac", "#b2182b"]


def _rotas(ax, rotas, titulo, destaque=frozenset()):
    dx, dy = _COORD[0]
    ax.scatter([dx], [dy], marker="s", s=760, c="#1f4e79", zorder=5)
    ax.annotate("D", (dx, dy), color="white", ha="center", va="center",
                fontsize=19, zorder=6)
    for ri, r in enumerate(rotas):
        seq = [0] + r + [0]
        col = _RCOL[ri % len(_RCOL)]
        for a0, b0 in zip(seq, seq[1:]):
            x0, y0 = _COORD[a0]
            x1, y1 = _COORD[b0]
            ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                         mutation_scale=22, color=col, lw=4.0,
                                         shrinkA=20, shrinkB=20, zorder=3))
        for c in r:
            x, y = _COORD[c]
            hl = c in destaque
            ax.scatter([x], [y], s=1200 if hl else 760,
                       c=("#ffd92f" if hl else "white"),
                       edgecolors=("black" if hl else col),
                       linewidths=3.5 if hl else 2.6, zorder=4)
            ax.annotate(str(c), (x, y), ha="center", va="center",
                        fontsize=19, zorder=5)
    ax.set_title(titulo, fontsize=24)
    ax.set_xlim(-4, 4)
    ax.set_ylim(-3.6, 3.4)
    ax.set_aspect("equal")
    ax.axis("off")


def fig_operadores():
    ops = [
        ("2-opt (intrarrota)", [[1, 3, 2, 6]], [[1, 2, 3, 6]], {2, 3}),
        ("Swap (entre rotas)", [[1, 5, 3], [4, 2, 6]], [[1, 2, 3], [4, 5, 6]], {2, 5}),
        ("2-opt* (entre rotas)", [[1, 2, 6], [4, 5, 3]], [[1, 2, 3], [4, 5, 6]], {3, 6}),
        ("Relocate (dominante)", [[1, 3], [4, 2, 5]], [[1, 2, 3], [4, 5]], {2}),
        ("Or-opt", [[1], [4, 2, 3, 5]], [[1, 2, 3], [4, 5]], {2, 3}),
        ("Cross-exchange", [[1, 5, 6, 3], [4, 2]], [[1, 2, 3], [4, 5, 6]], {2, 5, 6}),
    ]
    fig, axes = plt.subplots(3, 4, figsize=(17.0, 11.6))
    for i, (nome, antes, depois, hl) in enumerate(ops):
        linha, col = divmod(i, 2)
        _rotas(axes[linha][2 * col], antes, nome + "\nantes", hl)
        _rotas(axes[linha][2 * col + 1], depois, " \ndepois", hl)
    fig.tight_layout(h_pad=2.0, w_pad=0.6)
    _save(fig, "operadores_banner.png")


if __name__ == "__main__":
    fig_cascata()
    fig_familia()
    fig_cd()
    fig_limiar()
    fig_regimes()
    fig_operadores()
