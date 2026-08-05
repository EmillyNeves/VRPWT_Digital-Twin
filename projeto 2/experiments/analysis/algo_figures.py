#!/usr/bin/env python3
"""Figuras DIDÁTICAS do funcionamento dos algoritmos (para o artigo).

Gera, de forma reprodutível (matplotlib), ilustrações esquemáticas de:
  1. operadores.png      — os 5 operadores de vizinhança (antes/depois);
  2. construcao_i1.png   — a construção por inserção I1, passo a passo;
  3. grasp_rcl.png       — a seleção da Lista Restrita de Candidatos (RCL) do GRASP.

Saída em results/figures/.
"""
import math
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

_HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.abspath(os.path.join(_HERE, "..", "..", "results", "figures"))

# layout fixo: nó 0 = depósito
COORD = {0: (0.0, 0.0), 1: (-2.4, 2.6), 2: (-3.0, 0.4), 3: (-2.0, -2.2),
         4: (2.4, 2.6), 5: (3.0, 0.4), 6: (2.0, -2.2), 7: (0.2, -3.0)}
R_COLORS = ["#2166ac", "#b2182b"]


def draw_routes(ax, routes, title, highlight=frozenset(), faint=False):
    a = 0.25 if faint else 1.0
    # depósito
    dx, dy = COORD[0]
    ax.scatter([dx], [dy], marker="s", s=160, c="#1f4e79", zorder=5, alpha=a)
    if not faint:
        ax.annotate("D", (dx, dy), color="white", ha="center", va="center", fontsize=8, zorder=6)
    for ri, r in enumerate(routes):
        seq = [0] + r + [0]
        col = R_COLORS[ri % len(R_COLORS)]
        for (a0, b0) in zip(seq, seq[1:]):
            x0, y0 = COORD[a0]; x1, y1 = COORD[b0]
            ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                         mutation_scale=11, color=col, lw=1.8, alpha=a,
                         shrinkA=9, shrinkB=9, zorder=3))
        for c in r:
            x, y = COORD[c]
            hl = c in highlight
            ax.scatter([x], [y], s=300 if hl else 170,
                       c=("#ffd92f" if hl else "white"),
                       edgecolors=("black" if hl else col), linewidths=1.8 if hl else 1.3,
                       zorder=4, alpha=a)
            ax.annotate(str(c), (x, y), ha="center", va="center", fontsize=8, zorder=5, alpha=a)
    ax.set_title(title, fontsize=9)
    ax.set_xlim(-4, 4); ax.set_ylim(-3.6, 3.4); ax.set_aspect("equal"); ax.axis("off")


def fig_operadores():
    # (nome, rotas_antes, rotas_depois, destaque)
    ops = [
        ("Relocate (entre rotas): move o cliente 2",
         [[1, 2, 3], [4, 5]], [[1, 3], [4, 2, 5]], {2}),
        ("Swap (entre rotas): troca 2 e 5",
         [[1, 2, 3], [4, 5, 6]], [[1, 5, 3], [4, 2, 6]], {2, 5}),
        ("2-opt (intra rota): inverte o trecho 2-3",
         [[1, 2, 3, 6]], [[1, 3, 2, 6]], {2, 3}),
        ("Or-opt (entre rotas): move a cadeia 2-3",
         [[1, 2, 3], [4, 5]], [[1], [4, 2, 3, 5]], {2, 3}),
        ("Cross-exchange: troca {2} por {5,6}",
         [[1, 2, 3], [4, 5, 6]], [[1, 5, 6, 3], [4, 2]], {2, 5, 6}),
    ]
    fig, axes = plt.subplots(5, 2, figsize=(7.2, 15.5))
    for row, (name, before, after, hl) in enumerate(ops):
        draw_routes(axes[row][0], before, ("antes — " + name), hl)
        draw_routes(axes[row][1], after, "depois", hl)
    fig.suptitle("Operadores de vizinhança (kit compartilhado): efeito de cada movimento",
                 y=0.995, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    fig.savefig(os.path.join(FIG, "operadores.png"), dpi=150, bbox_inches="tight")
    plt.close()


def fig_construcao_i1():
    # passos da I1: semente (mais distante) e inserções sucessivas em UMA rota
    steps = [
        ("1) semente: cliente mais distante do depósito", [4]),
        ("2) insere o melhor (c2): cliente 5", [4, 5]),
        ("3) insere o próximo melhor: cliente 1", [1, 4, 5]),
        ("4) rota cheia (nenhuma inserção viável)", [1, 4, 5, 6]),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(15, 4))
    for ax, (title, route) in zip(axes, steps):
        new = route[-1] if title.startswith(("2", "3", "4")) else (route[0] if route else None)
        draw_routes(ax, [route], title, highlight={new} if new is not None else frozenset())
    fig.suptitle("Construção por inserção I1 de Solomon: uma rota é montada cliente a cliente",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "construcao_i1.png"), dpi=150, bbox_inches="tight")
    plt.close()


def fig_grasp_rcl():
    cands = [("u1", 8.0), ("u2", 6.5), ("u3", 5.0), ("u4", 2.0)]
    cmax, cmin = 8.0, 2.0
    alpha = 0.3
    thr = cmax - alpha * (cmax - cmin)   # 6.2
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    names = [n for n, _ in cands]; vals = [v for _, v in cands]
    colors = ["#2ca02c" if v >= thr - 1e-9 else "#bdbdbd" for v in vals]
    ax.bar(names, vals, color=colors, edgecolor="black", zorder=3)
    ax.axhline(thr, color="#b2182b", ls="--", lw=1.8, zorder=4,
               label=f"limiar $c^{{max}}-\\alpha(c^{{max}}-c^{{min}})={thr:.1f}$  ($\\alpha={alpha}$)")
    ax.axhline(cmax, color="gray", ls=":", lw=1, zorder=2)
    ax.axhline(cmin, color="gray", ls=":", lw=1, zorder=2)
    ax.text(0.5, 0.55, "RCL — sorteio uniforme", color="white", ha="center", va="bottom",
            fontsize=10, fontweight="bold", zorder=5)
    ax.text(2.5, 0.55, "descartados", color="black", ha="center", va="bottom", fontsize=10, zorder=5)
    for n, v in cands:
        ax.annotate(f"{v:.1f}", (n, v), ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("valor $c_2$ do candidato (maior = melhor)")
    ax.set_title("GRASP: seleção da Lista Restrita de Candidatos (RCL)")
    ax.set_ylim(0, 9); ax.legend(loc="upper right", fontsize=8); ax.grid(axis="y", ls=":", alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "grasp_rcl.png"), dpi=150, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    fig_operadores(); fig_construcao_i1(); fig_grasp_rcl()
    print("geradas:", "operadores.png", "construcao_i1.png", "grasp_rcl.png", "em", FIG)
