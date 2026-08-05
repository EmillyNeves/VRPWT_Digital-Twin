#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch


BASE_DIR = Path(__file__).resolve().parent
OUT_PNG = BASE_DIR / "png"
OUT_SVG = BASE_DIR / "svg"
OUT_PNG.mkdir(parents=True, exist_ok=True)
OUT_SVG.mkdir(parents=True, exist_ok=True)


PALETTE = {
    "canvas": "#f8fafc",
    "panel": "#ffffff",
    "panel_edge": "#cbd5e1",
    "edge": "#334155",
    "node": "#dbeafe",
    "node_edge": "#1e293b",
    "depot": "#e2e8f0",
    "text": "#0f172a",
    "before": "#f59e0b",
    "after": "#10b981",
    "accent": "#2563eb",
}

X_START = 1.45
STEP = 1.3
RADIUS = 0.24


def setup_axis(ax: plt.Axes, x_max: float, y_max: float) -> None:
    ax.set_xlim(0.0, x_max)
    ax.set_ylim(0.0, y_max)
    ax.axis("off")
    ax.set_facecolor(PALETTE["canvas"])


def draw_route_band(ax: plt.Axes, *, y: float, width: float, label: str) -> None:
    band = FancyBboxPatch(
        (0.25, y - 0.42),
        width,
        0.84,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=1.2,
        edgecolor=PALETTE["panel_edge"],
        facecolor=PALETTE["panel"],
        zorder=0,
    )
    ax.add_patch(band)
    ax.text(0.35, y, label, va="center", ha="left", fontsize=10, color=PALETTE["text"], fontweight="bold")


def draw_route(
    ax: plt.Axes,
    *,
    nodes: list[str],
    y: float,
    route_label: str,
    highlights: dict[int, str] | None = None,
) -> None:
    highlights = highlights or {}
    x_coords = [X_START + idx * STEP for idx in range(len(nodes))]
    width = max(8.3, X_START + (len(nodes) - 1) * STEP + 1.0)
    draw_route_band(ax, y=y, width=width, label=route_label)

    for idx in range(len(nodes) - 1):
        x0 = x_coords[idx] + RADIUS
        x1 = x_coords[idx + 1] - RADIUS
        arrow = FancyArrowPatch(
            (x0, y),
            (x1, y),
            arrowstyle="-|>",
            mutation_scale=11,
            linewidth=1.35,
            color=PALETTE["edge"],
            zorder=2,
        )
        ax.add_patch(arrow)

    for idx, (x, label) in enumerate(zip(x_coords, nodes)):
        if label == "0":
            fill = PALETTE["depot"]
        else:
            fill = PALETTE["node"]
        if idx in highlights:
            fill = highlights[idx]
        node = Circle(
            (x, y),
            radius=RADIUS,
            facecolor=fill,
            edgecolor=PALETTE["node_edge"],
            linewidth=1.2,
            zorder=3,
        )
        ax.add_patch(node)
        ax.text(x, y, label, ha="center", va="center", fontsize=10, color=PALETTE["text"], fontweight="bold", zorder=4)


def add_common_legend(fig: plt.Figure, movement_label: str) -> None:
    fig.text(
        0.5,
        0.08,
        movement_label,
        ha="center",
        va="center",
        fontsize=10.5,
        color=PALETTE["text"],
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.04,
        "Laranja: elemento movido no estado Antes | Verde: nova posição/segmento no estado Depois",
        ha="center",
        va="center",
        fontsize=9.2,
        color=PALETTE["text"],
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    png_path = OUT_PNG / f"{stem}.png"
    svg_path = OUT_SVG / f"{stem}.svg"
    fig.savefig(png_path, dpi=260, facecolor=fig.get_facecolor())
    fig.savefig(svg_path, format="svg", facecolor=fig.get_facecolor())


def make_pair_figure(
    *,
    title: str,
    stem: str,
    before_routes: list[tuple[str, list[str], dict[int, str]]],
    after_routes: list[tuple[str, list[str], dict[int, str]]],
    y_positions: list[float],
    x_max: float,
    y_max: float,
    movement_label: str,
) -> None:
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13.4, 5.2))
    fig.patch.set_facecolor(PALETTE["canvas"])
    fig.suptitle(title, fontsize=14, color=PALETTE["text"], fontweight="bold", y=0.96)

    setup_axis(ax_left, x_max=x_max, y_max=y_max)
    setup_axis(ax_right, x_max=x_max, y_max=y_max)
    ax_left.set_title("Antes", fontsize=12, color=PALETTE["accent"], fontweight="bold")
    ax_right.set_title("Depois", fontsize=12, color=PALETTE["accent"], fontweight="bold")

    for y, (label, nodes, highlights) in zip(y_positions, before_routes):
        draw_route(ax_left, nodes=nodes, y=y, route_label=label, highlights=highlights)
    for y, (label, nodes, highlights) in zip(y_positions, after_routes):
        draw_route(ax_right, nodes=nodes, y=y, route_label=label, highlights=highlights)

    fig.text(0.5, 0.505, "\u21d2", ha="center", va="center", fontsize=26, color=PALETTE["accent"], fontweight="bold")
    add_common_legend(fig, movement_label)
    fig.tight_layout(rect=[0.02, 0.10, 0.98, 0.92])
    save_figure(fig, stem)
    plt.close(fig)


def fig_relocate_intra() -> None:
    make_pair_figure(
        title="VND - relocate_intra (movimento dentro da mesma rota)",
        stem="vnd_relocate_intra",
        before_routes=[
            ("Rota", ["0", "2", "7", "4", "9", "0"], {2: PALETTE["before"]}),
        ],
        after_routes=[
            ("Rota", ["0", "2", "4", "9", "7", "0"], {4: PALETTE["after"]}),
        ],
        y_positions=[1.65],
        x_max=9.3,
        y_max=3.0,
        movement_label="Cliente 7 removido da posição original e reinserido ao final da rota.",
    )


def fig_swap_intra() -> None:
    make_pair_figure(
        title="VND - swap_intra (troca de dois clientes na mesma rota)",
        stem="vnd_swap_intra",
        before_routes=[
            ("Rota", ["0", "3", "8", "5", "11", "0"], {2: PALETTE["before"], 4: PALETTE["before"]}),
        ],
        after_routes=[
            ("Rota", ["0", "3", "11", "5", "8", "0"], {2: PALETTE["after"], 4: PALETTE["after"]}),
        ],
        y_positions=[1.65],
        x_max=9.3,
        y_max=3.0,
        movement_label="Clientes 8 e 11 trocados para reduzir custo sem alterar o conjunto da rota.",
    )


def fig_relocate_inter() -> None:
    make_pair_figure(
        title="VND - relocate_inter (movimento entre rotas)",
        stem="vnd_relocate_inter",
        before_routes=[
            ("Rota A", ["0", "4", "10", "6", "0"], {2: PALETTE["before"]}),
            ("Rota B", ["0", "2", "9", "7", "0"], {}),
        ],
        after_routes=[
            ("Rota A", ["0", "4", "6", "0"], {}),
            ("Rota B", ["0", "2", "9", "10", "7", "0"], {3: PALETTE["after"]}),
        ],
        y_positions=[2.35, 1.0],
        x_max=9.8,
        y_max=3.4,
        movement_label="Cliente 10 removido da Rota A e inserido na Rota B na melhor posição factível.",
    )


def fig_or_opt() -> None:
    make_pair_figure(
        title="VND - or_opt (realocação de cadeia consecutiva)",
        stem="vnd_or_opt",
        before_routes=[
            ("Rota A", ["0", "5", "8", "12", "6", "0"], {2: PALETTE["before"], 3: PALETTE["before"]}),
            ("Rota B", ["0", "3", "9", "7", "0"], {}),
        ],
        after_routes=[
            ("Rota A", ["0", "5", "6", "0"], {}),
            ("Rota B", ["0", "3", "8", "12", "9", "7", "0"], {2: PALETTE["after"], 3: PALETTE["after"]}),
        ],
        y_positions=[2.35, 1.0],
        x_max=10.9,
        y_max=3.4,
        movement_label="Bloco [8,12] deslocado da Rota A para a Rota B preservando adjacência do segmento.",
    )


def main() -> int:
    fig_relocate_intra()
    fig_swap_intra()
    fig_relocate_inter()
    fig_or_opt()
    print(f"PNG: {OUT_PNG}")
    print(f"SVG: {OUT_SVG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
