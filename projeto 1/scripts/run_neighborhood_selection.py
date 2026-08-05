#!/usr/bin/env python3
from __future__ import annotations

"""
Selecao de vizinhancas em tres fases (baseline I1, A isolada, B incremental/ablativa)
usando apenas NLS (first-improvement), sem comparar meta-heuristicas.

Metodologia fundamentada em:
- Hansen & Mladenovic (2001): VND, ordem por complexidade, first improvement.
- Barr et al. (1995): randomized block design, reporte de metodos deterministicos.
- Demsar (2006): ranking por mediana, Wilcoxon signed-rank, correcao de Holm.
- Birattari (2009): separacao tuning/holdout para evitar over-tuning.
- Hooker (1995): experimentacao controlada (incremental + ablacao).

Criterio de dominancia: qualquer configuracao que piore o numero de veiculos
em relacao ao baseline I1 e marcada como dominada e rebaixada no ranking.
"""

import argparse
import csv
import itertools
import json
import math
import random
import statistics
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


NEIGHBORHOODS: List[str] = [
    "relocate_intra",
    "swap_intra",
    "relocate_inter",
    "or_opt",
    "swap_inter",
    "two_opt_intra",
    "two_opt_inter",
    "cross_exchange",
]


# ── Helpers estatisticos ─────────────────────────────────────────────────

def median(xs: Sequence[float]) -> float:
    return statistics.median(xs) if xs else math.nan


def iqr(xs: Sequence[float]) -> float:
    if not xs:
        return math.nan
    ys = sorted(xs)
    n = len(ys)
    if n == 1:
        return 0.0
    q1 = statistics.median(ys[: n // 2])
    if n % 2 == 0:
        q3 = statistics.median(ys[n // 2 :])
    else:
        q3 = statistics.median(ys[n // 2 + 1 :])
    return float(q3 - q1)


def wilcoxon_signed_rank(x: Sequence[float], y: Sequence[float]) -> float:
    """Wilcoxon signed-rank test (two-sided). Retorna p-value aproximado.

    Implementacao simplificada baseada em aproximacao normal para n >= 10.
    Para n < 10, retorna NaN (amostras insuficientes).
    Referencia: Demsar (2006), Secao 3.1.
    """
    diffs = [a - b for a, b in zip(x, y) if abs(a - b) > 1e-12]
    n = len(diffs)
    if n < 10:
        return math.nan

    abs_diffs = [(abs(d), i) for i, d in enumerate(diffs)]
    abs_diffs.sort(key=lambda t: t[0])

    # Atribui ranks (com ties = media)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and abs(abs_diffs[j][0] - abs_diffs[i][0]) < 1e-12:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[abs_diffs[k][1]] = avg_rank
        i = j

    w_plus = sum(ranks[i] for i in range(n) if diffs[i] > 0)
    w_minus = sum(ranks[i] for i in range(n) if diffs[i] < 0)
    w = min(w_plus, w_minus)

    # Aproximacao normal
    mean_w = n * (n + 1) / 4.0
    std_w = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    if std_w < 1e-12:
        return 1.0
    z = (w - mean_w) / std_w
    # Aproximacao CDF normal (two-sided)
    p = 2.0 * _normal_cdf(-abs(z))
    return min(p, 1.0)


def _normal_cdf(x: float) -> float:
    """Aproximacao da CDF normal padrao (Abramowitz & Stegun 26.2.17)."""
    if x < -8.0:
        return 0.0
    if x > 8.0:
        return 1.0
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    d = 0.3989422804014327  # 1/sqrt(2*pi)
    p = d * math.exp(-x * x / 2.0) * (
        t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    )
    return p if x < 0 else 1.0 - p


def holm_correction(pvalues: Dict[str, float], alpha: float = 0.05) -> Dict[str, Dict[str, object]]:
    """Aplica correcao de Holm (step-down) a um dicionario de p-values.

    Retorna dict com p_raw, p_adjusted, significant.
    Referencia: Demsar (2006), Secao 3.3; Garcia et al. (2010).
    """
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    result: Dict[str, Dict[str, object]] = {}
    max_adj = 0.0
    for rank_idx, (key, p_raw) in enumerate(items):
        adj = p_raw * (m - rank_idx)
        adj = max(adj, max_adj)  # monotonizacao step-down
        adj = min(adj, 1.0)
        max_adj = adj
        result[key] = {
            "p_raw": p_raw,
            "p_adjusted": adj,
            "significant": adj < alpha,
        }
    return result


# ── Argumentos ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Selecao de vizinhancas (Fase 0 + A + B) com NLS. "
        "Ref: Hansen & Mladenovic (2001), Demsar (2006), Barr et al. (1995)."
    )
    p.add_argument("--bin", default="bin/vrptw", help="Caminho do binario")
    p.add_argument("--input-dir", default="input", help="Diretorio de instancias (tuning set)")
    p.add_argument("--instances", default="", help="Lista separada por virgula; vazio = todas do input-dir")
    p.add_argument("--out", default="results/neighborhood_selection", help="Diretorio de saida")
    p.add_argument("--seed", type=int, default=42, help="Seed (mantida fixa; I1 e NLS sao deterministicos)")
    p.add_argument("--top-a", type=int, default=5, help="Top N da Fase A para formar Fase B")
    p.add_argument("--k-neighbors", type=int, default=20)
    p.add_argument("--eps", type=float, default=1e-6)
    p.add_argument("--time-limit", type=float, default=0.0, help="0 = sem limite (ate otimo local)")
    p.add_argument(
        "--phase-b-restart",
        type=int,
        choices=[0, 1],
        default=1,
        help="Restart na Fase B (1 = VND classico). Ref: Hansen & Mladenovic (2001).",
    )
    p.add_argument(
        "--randomize-queue",
        action="store_true",
        help="Randomiza ordem de execucao (instancia x config) para mitigar "
        "vies computacional. Ref: Barr et al. (1995), McGeoch (2012).",
    )
    p.add_argument(
        "--queue-seed",
        type=int,
        default=0,
        help="Seed para randomizacao da fila (0 = usa --seed).",
    )
    p.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Nivel de significancia para testes estatisticos (Wilcoxon+Holm).",
    )
    p.add_argument(
        "--statistical-tests",
        dest="statistical_tests",
        action="store_true",
        default=True,
        help="Executa validacao estatistica (Wilcoxon+Holm). Padrao: ativado.",
    )
    p.add_argument(
        "--no-statistical-tests",
        dest="statistical_tests",
        action="store_false",
        help="Desativa validacao estatistica (Wilcoxon+Holm).",
    )
    return p.parse_args()


# ── Utilidades ───────────────────────────────────────────────────────────

def list_instances(input_dir: Path, instances_arg: str) -> List[Path]:
    if instances_arg.strip():
        names = [x.strip() for x in instances_arg.split(",") if x.strip()]
        return [input_dir / f"{name}.txt" if not name.endswith(".txt") else input_dir / name for name in names]
    return sorted(input_dir.glob("*.txt"))


def cfg_label(neighborhoods: Sequence[str]) -> str:
    if not neighborhoods:
        return "all"
    return "|".join(neighborhoods)


def by_complexity(neighborhoods: Sequence[str]) -> List[str]:
    """Ordena vizinhancas pela ordem canonica de complexidade.
    Ref: Hansen & Mladenovic (2001) - simplest first."""
    s = set(neighborhoods)
    return [n for n in NEIGHBORHOODS if n in s]


# ── Solver wrappers ──────────────────────────────────────────────────────

def run_solver(
    bin_path: Path,
    out_dir: Path,
    instance_path: Path,
    seed: int,
    neighborhoods: Sequence[str],
    nls_restart: int,
    k_neighbors: int,
    eps: float,
    time_limit: float,
    tag: str,
) -> Dict[str, str]:
    inst_name = instance_path.stem
    ordered = by_complexity(neighborhoods)
    neigh_arg = "all" if not ordered else ",".join(ordered)
    cmd = [
        str(bin_path),
        "solve",
        "--algo",
        "nls",
        "--instance",
        str(instance_path),
        "--seed",
        str(seed),
        "--out",
        str(out_dir),
        "--tag",
        tag,
        "--vnd-neighborhoods",
        neigh_arg,
        "--nls-restart",
        str(nls_restart),
        "--k-neighbors",
        str(k_neighbors),
        "--eps",
        str(eps),
        "--time-limit",
        str(time_limit),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    base = f"nls_{inst_name}_seed{seed}_{tag}"
    csv_path = out_dir / "logs" / "execution" / f"{base}.csv"
    with csv_path.open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    row["ordered_neighborhoods"] = cfg_label(ordered)
    return row


def run_i1_baseline(
    bin_path: Path,
    out_dir: Path,
    instance_path: Path,
    seed: int,
    k_neighbors: int,
    eps: float,
) -> Dict[str, str]:
    """Executa apenas o construtivo I1 para obter baseline de veiculos e custo."""
    inst_name = instance_path.stem
    tag = "I1_baseline"
    cmd = [
        str(bin_path),
        "solve",
        "--algo",
        "i1",
        "--instance",
        str(instance_path),
        "--seed",
        str(seed),
        "--out",
        str(out_dir),
        "--tag",
        tag,
        "--k-neighbors",
        str(k_neighbors),
        "--eps",
        str(eps),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    base = f"i1_{inst_name}_seed{seed}_{tag}"
    csv_path = out_dir / "logs" / "execution" / f"{base}.csv"
    with csv_path.open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    return row


# ── Agregacao e ranking ──────────────────────────────────────────────────

def summarize(
    rows: List[Dict[str, str]],
    i1_routes: Optional[Dict[str, int]] = None,
) -> List[Dict[str, object]]:
    """Agrega metricas por configuracao com filtro de dominancia por veiculos."""
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for r in rows:
        grouped.setdefault(str(r["config_id"]), []).append(r)

    out: List[Dict[str, object]] = []
    for cfg, rs in grouped.items():
        gaps = [float(x["gap_pct"]) for x in rs]
        times = [float(x["time_sec"]) for x in rs]
        routes = [int(x["num_routes"]) for x in rs]

        dominated = False
        routes_worsened = 0
        if i1_routes is not None:
            for x in rs:
                inst = str(x["instance"])
                nr = int(x["num_routes"])
                i1_nr = i1_routes.get(inst, nr)
                if nr > i1_nr:
                    dominated = True
                    routes_worsened += 1

        out.append(
            {
                "config_id": cfg,
                "phase": rs[0]["phase"],
                "kind": rs[0]["kind"],
                "set_size": int(rs[0]["set_size"]),
                "neighborhoods": rs[0]["neighborhoods"],
                "n_instances": len(rs),
                "median_gap_pct": median(gaps),
                "iqr_gap_pct": iqr(gaps),
                "median_time_sec": median(times),
                "mean_gap_pct": statistics.mean(gaps),
                "mean_time_sec": statistics.mean(times),
                "median_routes": median(routes),
                "dominated": dominated,
                "routes_worsened": routes_worsened,
            }
        )

    # Ranking lexicografico: (dominada, mediana gap, mediana tempo, IQR gap)
    # Ref: Demsar (2006) recomenda mediana como estatistica robusta para rankings.
    out.sort(
        key=lambda x: (
            1 if x["dominated"] else 0,
            x["median_gap_pct"],
            x["median_time_sec"],
            x["iqr_gap_pct"],
            x["config_id"],
        )
    )
    for i, r in enumerate(out, start=1):
        r["rank"] = i
    return out


# ── Testes estatisticos ──────────────────────────────────────────────────

def run_statistical_tests(
    run_rows: List[Dict[str, str]],
    phase: str,
    alpha: float,
) -> Tuple[List[Dict[str, object]], Dict[str, Dict[str, object]]]:
    """Wilcoxon signed-rank pareado + correcao de Holm entre configs de uma fase.

    Ref: Demsar (2006), Garcia et al. (2010).
    """
    grouped: Dict[str, Dict[str, float]] = {}
    for r in run_rows:
        if r["phase"] != phase:
            continue
        cfg = str(r["config_id"])
        inst = str(r["instance"])
        grouped.setdefault(cfg, {})[inst] = float(r["gap_pct"])

    configs = sorted(grouped.keys())
    instances = sorted(set().union(*grouped.values()))

    pairwise: List[Dict[str, object]] = []
    raw_pvalues: Dict[str, float] = {}

    for i, ca in enumerate(configs):
        for cb in configs[i + 1 :]:
            shared = [inst for inst in instances if inst in grouped[ca] and inst in grouped[cb]]
            if len(shared) < 10:
                p = math.nan
            else:
                xa = [grouped[ca][inst] for inst in shared]
                xb = [grouped[cb][inst] for inst in shared]
                p = wilcoxon_signed_rank(xa, xb)
            key = f"{ca}_vs_{cb}"
            raw_pvalues[key] = p
            pairwise.append({"config_a": ca, "config_b": cb, "n_shared": len(shared), "p_raw": p})

    holm_results = holm_correction(
        {k: v for k, v in raw_pvalues.items() if not math.isnan(v)},
        alpha=alpha,
    )

    for row in pairwise:
        key = f"{row['config_a']}_vs_{row['config_b']}"
        if key in holm_results:
            row["p_adjusted"] = holm_results[key]["p_adjusted"]
            row["significant"] = holm_results[key]["significant"]
        else:
            row["p_adjusted"] = math.nan
            row["significant"] = False

    return pairwise, holm_results


# ── CSV / LaTeX ──────────────────────────────────────────────────────────

def write_csv(path: Path, rows: Iterable[Dict[str, object]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        # Algumas linhas carregam colunas auxiliares extras do CSV bruto do solver;
        # ignoramos essas chaves para manter o schema de saida estavel.
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def latex_escape(s: str) -> str:
    return (
        s.replace("\\", "\\textbackslash{}")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
        .replace("#", "\\#")
        .replace("{", "\\{")
        .replace("}", "\\}")
    )


def to_latex_table(path: Path, caption: str, label: str, rows: Sequence[Dict[str, object]], max_rows: int = 12) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("\\begin{table}[htbp]\n\\centering\n")
        f.write(f"\\caption{{{latex_escape(caption)}}}\n")
        f.write(f"\\label{{{label}}}\n")
        f.write("\\begin{tabular}{rllrrrl}\n\\hline\n")
        f.write(
            "Rank & Config & Vizinhancas & Mediana gap (\\%) & IQR gap (\\%) "
            "& Mediana tempo (s) & Dom. \\\\\n\\hline\n"
        )
        for r in rows[:max_rows]:
            dom_flag = "\\textbf{D}" if r.get("dominated") else "--"
            f.write(
                f"{r['rank']} & {latex_escape(str(r['config_id']))} & {latex_escape(str(r['neighborhoods']))} & "
                f"{float(r['median_gap_pct']):.3f} & {float(r['iqr_gap_pct']):.3f} & "
                f"{float(r['median_time_sec']):.4f} & {dom_flag} \\\\\n"
            )
        f.write("\\hline\n\\end{tabular}\n\\end{table}\n")


SUMMARY_FIELDS: List[str] = [
    "rank",
    "config_id",
    "phase",
    "kind",
    "set_size",
    "neighborhoods",
    "n_instances",
    "median_gap_pct",
    "iqr_gap_pct",
    "median_time_sec",
    "mean_gap_pct",
    "mean_time_sec",
    "median_routes",
    "dominated",
    "routes_worsened",
]

RUN_FIELDS: List[str] = [
    "phase",
    "kind",
    "config_id",
    "set_size",
    "neighborhoods",
    "instance",
    "algorithm",
    "seed",
    "feasible",
    "ordered_neighborhoods",
    "nls_restart",
    "time_sec",
    "num_routes",
    "cost",
    "bks_cost",
    "gap_pct",
    "i1_routes",
    "delta_routes",
]

STAT_FIELDS: List[str] = [
    "config_a",
    "config_b",
    "n_shared",
    "p_raw",
    "p_adjusted",
    "significant",
]


# ── Execucao de fase com randomizacao opcional ───────────────────────────

def run_phase(
    cfgs: List[Dict[str, object]],
    instances: List[Path],
    bin_path: Path,
    out_dir: Path,
    args: argparse.Namespace,
    nls_restart: int,
    i1_routes: Dict[str, int],
    phase_label: str,
    randomize: bool,
) -> List[Dict[str, str]]:
    """Executa todas as combinacoes (config x instancia) de uma fase.

    Se randomize=True, embaralha a fila de execucao para mitigar vies
    computacional (Barr et al., 1995; McGeoch, 2012).
    """
    # Monta fila: lista de (cfg_index, instance_path)
    queue: List[Tuple[int, Path]] = list(itertools.product(range(len(cfgs)), instances))
    if randomize:
        rng_seed = args.queue_seed if args.queue_seed != 0 else args.seed
        random.Random(rng_seed).shuffle(queue)

    # Pre-aloca resultados indexados por (cfg_idx, inst_stem)
    results: Dict[Tuple[int, str], Dict[str, str]] = {}

    total = len(queue)
    for idx, (cfg_i, inst) in enumerate(queue, 1):
        cfg = cfgs[cfg_i]
        neighborhoods = list(cfg["neighborhoods"])
        tag = str(cfg["config_id"])
        inst_name = inst.stem

        if idx % 20 == 1 or idx == total:
            print(f"  [{phase_label}] {idx}/{total}: {tag} x {inst_name}")

        raw = run_solver(
            bin_path=bin_path,
            out_dir=out_dir,
            instance_path=inst,
            seed=args.seed,
            neighborhoods=neighborhoods,
            nls_restart=nls_restart,
            k_neighbors=args.k_neighbors,
            eps=args.eps,
            time_limit=args.time_limit,
            tag=tag,
        )
        raw["phase"] = str(cfg["phase"])
        raw["kind"] = str(cfg["kind"])
        raw["config_id"] = tag
        raw["set_size"] = str(len(neighborhoods))
        raw["neighborhoods"] = cfg_label(neighborhoods)
        raw["nls_restart"] = str(nls_restart)
        raw["feasible"] = "1"
        raw["i1_routes"] = str(i1_routes.get(inst_name, -1))
        raw["delta_routes"] = str(int(raw["num_routes"]) - i1_routes.get(inst_name, int(raw["num_routes"])))
        results[(cfg_i, inst_name)] = raw

    # Reconstroi na ordem original (config, instancia) para CSV determinístico
    rows: List[Dict[str, str]] = []
    for cfg_i in range(len(cfgs)):
        for inst in instances:
            key = (cfg_i, inst.stem)
            if key in results:
                rows.append(results[key])
    return rows


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    bin_path = Path(args.bin)
    input_dir = Path(args.input_dir)
    out_dir = Path(args.out)
    instances = list_instances(input_dir, args.instances)
    if not instances:
        raise SystemExit("Nenhuma instancia encontrada.")

    out_dir.mkdir(parents=True, exist_ok=True)

    randomize = args.randomize_queue
    if randomize:
        q_seed = args.queue_seed if args.queue_seed != 0 else args.seed
        print(f"[Config] Randomizacao da fila ativada (seed={q_seed}).")

    # ── Fase 0: baseline I1 ──────────────────────────────────────────────
    print(f"\n[Fase 0] Coletando baseline I1 para {len(instances)} instancias...")
    i1_routes: Dict[str, int] = {}
    i1_costs: Dict[str, float] = {}
    for inst in instances:
        raw = run_i1_baseline(
            bin_path=bin_path,
            out_dir=out_dir,
            instance_path=inst,
            seed=args.seed,
            k_neighbors=args.k_neighbors,
            eps=args.eps,
        )
        inst_name = inst.stem
        i1_routes[inst_name] = int(raw["num_routes"])
        i1_costs[inst_name] = float(raw["cost"])
        print(f"  {inst_name}: cost={raw['cost']} routes={raw['num_routes']}")

    baseline_path = out_dir / "i1_baseline.json"
    with baseline_path.open("w", encoding="utf-8") as f:
        json.dump({"routes": i1_routes, "costs": i1_costs}, f, indent=2)
    print(f"[Fase 0] Baseline salvo em {baseline_path}")

    # ── Fase A: isolada ──────────────────────────────────────────────────
    phase_a_cfgs: List[Dict[str, object]] = []
    for n in NEIGHBORHOODS:
        phase_a_cfgs.append({"config_id": f"A_{n}", "phase": "A", "kind": "isolated", "neighborhoods": [n]})

    print(f"\n[Fase A] Avaliando {len(NEIGHBORHOODS)} vizinhancas isoladas ({len(instances)} instancias)...")
    phase_a_rows = run_phase(
        cfgs=phase_a_cfgs,
        instances=instances,
        bin_path=bin_path,
        out_dir=out_dir,
        args=args,
        nls_restart=0,
        i1_routes=i1_routes,
        phase_label="Fase A",
        randomize=randomize,
    )

    run_rows: List[Dict[str, str]] = list(phase_a_rows)

    phase_a_summary = summarize(phase_a_rows, i1_routes)
    top_n = max(1, min(args.top_a, len(phase_a_summary)))
    non_dominated_a = [r for r in phase_a_summary if not r["dominated"]]
    top_a = non_dominated_a[:top_n]
    top_neighborhoods = [str(r["neighborhoods"]) for r in top_a]

    print(f"\n[Fase A] Top-{top_n} nao-dominadas:")
    for r in top_a:
        print(f"  {r['rank']}. {r['config_id']} | gap={float(r['median_gap_pct']):.3f}%")

    # ── Fase B: incremental + ablacao ────────────────────────────────────
    phase_b_cfgs: List[Dict[str, object]] = []
    for i in range(1, len(top_neighborhoods) + 1):
        neigh = top_neighborhoods[:i]
        phase_b_cfgs.append(
            {"config_id": f"B_INC_{i}", "phase": "B", "kind": "incremental", "neighborhoods": neigh}
        )
    for removed in top_neighborhoods:
        neigh = [x for x in top_neighborhoods if x != removed]
        if neigh:
            phase_b_cfgs.append(
                {"config_id": f"B_ABL_rm_{removed}", "phase": "B", "kind": "ablation", "neighborhoods": neigh}
            )

    print(f"\n[Fase B] Avaliando {len(phase_b_cfgs)} configuracoes ({len(instances)} instancias)...")
    phase_b_rows = run_phase(
        cfgs=phase_b_cfgs,
        instances=instances,
        bin_path=bin_path,
        out_dir=out_dir,
        args=args,
        nls_restart=args.phase_b_restart,
        i1_routes=i1_routes,
        phase_label="Fase B",
        randomize=randomize,
    )
    run_rows.extend(phase_b_rows)

    phase_b_summary = summarize(phase_b_rows, i1_routes)
    non_dominated_b = [r for r in phase_b_summary if not r["dominated"]]
    target = [r for r in non_dominated_b if int(r["set_size"]) in (3, 4)]
    if target:
        recommended = target[0]
    elif non_dominated_b:
        recommended = non_dominated_b[0]
    else:
        recommended = phase_b_summary[0] if phase_b_summary else None

    best_gap_b = float(phase_b_summary[0]["median_gap_pct"]) if phase_b_summary else math.nan
    recommended_equals_best_gap = (
        recommended is not None and not math.isnan(best_gap_b) and
        abs(float(recommended["median_gap_pct"]) - best_gap_b) <= 1e-12
    )

    # ── Testes estatisticos (Wilcoxon + Holm) ────────────────────────────
    stat_b: List[Dict[str, object]] = []
    n_sig = 0
    n_tests = 0
    n_nan = 0
    if args.statistical_tests:
        print(f"\n[Estatistica] Executando Wilcoxon signed-rank + correcao de Holm (alpha={args.alpha})...")
        stat_b, _holm_b = run_statistical_tests(run_rows, phase="B", alpha=args.alpha)
        n_nan = sum(1 for r in stat_b if math.isnan(float(r["p_raw"])))
        n_sig = sum(1 for r in stat_b if r.get("significant"))
        n_tests = sum(1 for r in stat_b if not math.isnan(float(r["p_raw"])))
        print(f"  {n_sig}/{n_tests} pares significativamente diferentes (alpha={args.alpha}); NaN={n_nan}.")
    else:
        print("\n[Estatistica] Desativado por --no-statistical-tests.")

    # ── Escrita de resultados ────────────────────────────────────────────
    runs_path = out_dir / "neighborhood_runs.csv"
    phase_a_path = out_dir / "phase_a_summary.csv"
    phase_b_path = out_dir / "phase_b_summary.csv"
    stat_path = out_dir / "statistical_tests.csv"
    rec_path = out_dir / "recommended_set.csv"

    write_csv(runs_path, run_rows, RUN_FIELDS)
    write_csv(phase_a_path, phase_a_summary, SUMMARY_FIELDS)
    write_csv(phase_b_path, phase_b_summary, SUMMARY_FIELDS)
    write_csv(stat_path, stat_b, STAT_FIELDS)
    if recommended is not None:
        write_csv(rec_path, [recommended], SUMMARY_FIELDS)

    to_latex_table(
        out_dir / "phase_a_summary.tex",
        "Fase A (vizinhancas isoladas) -- ranking por mediana de gap com filtro de dominancia",
        "tab:neigh_phase_a",
        phase_a_summary,
    )
    to_latex_table(
        out_dir / "phase_b_summary.tex",
        "Fase B (incremental/ablativa) -- ranking por mediana de gap com filtro de dominancia",
        "tab:neigh_phase_b",
        phase_b_summary,
    )

    # ── Relatorio ────────────────────────────────────────────────────────
    n_dom_a = sum(1 for r in phase_a_summary if r["dominated"])
    n_dom_b = sum(1 for r in phase_b_summary if r["dominated"])

    report = out_dir / "report.md"
    with report.open("w", encoding="utf-8") as f:
        f.write("# Selecao de vizinhancas (Fase 0 + Fase A + Fase B)\n\n")

        f.write("## Protocolo executado\n")
        f.write("- Motor de busca: `algo=nls` (first-improvement). Ref: Hansen & Mladenovic (2001).\n")
        f.write("- **Fase 0**: baseline I1 deterministico para referencia de veiculos e custo.\n")
        f.write("- **Fase A**: `nls_restart=0` (triagem isolada ate otimo local).\n")
        f.write(
            f"- **Fase B**: `nls_restart={args.phase_b_restart}` "
            f"(comportamento VND classico com restart). Ref: Hansen & Mladenovic (2001).\n"
        )
        f.write("- Vizinhancas ordenadas por complexidade (simplest first). "
                "Ref: Hansen & Mladenovic (2001).\n")
        f.write("- Solucao inicial fixa: Solomon I1 (deterministico; 1 seed suficiente). "
                "Ref: Barr et al. (1995).\n")
        f.write("- Tempo medido como **elapsed time (wall-clock)** via `std::chrono::steady_clock`.\n")
        if randomize:
            f.write("- Fila de execucao **randomizada** (randomized block design). "
                    "Ref: Barr et al. (1995), McGeoch (2012).\n")
        f.write("- Criterio de ranking: **(1)** dominancia por veiculos; **(2)** mediana do gap "
                "(Demsar, 2006); **(3)** mediana do tempo; **(4)** IQR do gap.\n")
        if args.statistical_tests:
            f.write("- Validacao estatistica: Wilcoxon signed-rank + correcao de Holm "
                    f"(alpha={args.alpha}). Ref: Demsar (2006), Garcia et al. (2010).\n")
        else:
            f.write("- Validacao estatistica: **desativada** por `--no-statistical-tests`.\n")
        f.write(f"- Instancias: {len(instances)}.\n")
        f.write(f"- Fase A: {len(NEIGHBORHOODS)} configs isoladas; "
                f"top-{top_n} nao-dominadas para Fase B.\n")
        f.write(f"- Fase B: {len(phase_b_cfgs)} configs (incremental + ablacao).\n\n")

        f.write("## Baseline I1\n")
        i1_total_cost = sum(i1_costs.values())
        i1_total_routes = sum(i1_routes.values())
        f.write(f"- Custo total (soma): {i1_total_cost:.1f}\n")
        f.write(f"- Veiculos totais (soma): {i1_total_routes}\n")
        f.write(f"- Instancias: {len(i1_routes)}\n\n")

        f.write("## Dominancia por veiculos\n")
        f.write(f"- Fase A: {n_dom_a} de {len(phase_a_summary)} configs dominadas.\n")
        f.write(f"- Fase B: {n_dom_b} de {len(phase_b_summary)} configs dominadas.\n")
        if n_dom_a == 0 and n_dom_b == 0:
            f.write("- **Nenhuma configuracao piorou o numero de veiculos do I1** "
                    "(salvaguarda de dominancia satisfeita).\n")
        f.write("\n")

        f.write("## Top Fase A\n")
        for r in phase_a_summary[:8]:
            dom = " **[DOM]**" if r["dominated"] else ""
            f.write(
                f"- {r['rank']}. `{r['config_id']}` | `{r['neighborhoods']}` | "
                f"med_gap={float(r['median_gap_pct']):.3f}% | "
                f"med_t={float(r['median_time_sec']):.4f}s | "
                f"med_routes={float(r['median_routes']):.0f}{dom}\n"
            )

        f.write("\n## Top Fase B\n")
        for r in phase_b_summary[:10]:
            dom = " **[DOM]**" if r["dominated"] else ""
            f.write(
                f"- {r['rank']}. `{r['config_id']}` ({r['kind']}) | size={r['set_size']} | "
                f"`{r['neighborhoods']}` | med_gap={float(r['median_gap_pct']):.3f}% | "
                f"med_t={float(r['median_time_sec']):.4f}s | "
                f"med_routes={float(r['median_routes']):.0f}{dom}\n"
            )

        f.write("\n## Testes estatisticos (Fase B)\n")
        if args.statistical_tests:
            f.write(f"- Teste: Wilcoxon signed-rank pareado (por instancia). Ref: Demsar (2006).\n")
            f.write(f"- Correcao: Holm (step-down). Ref: Garcia et al. (2010).\n")
            f.write(f"- Alpha: {args.alpha}\n")
            f.write(f"- Pares testados: {n_tests}\n")
            f.write(f"- Pares significativos: {n_sig}\n")
            f.write(f"- Pares com `p_raw = NaN`: {n_nan}\n")
            if n_nan > 0:
                f.write(
                    "- Nota: em VRPTW com janelas de tempo rigidas, e comum haver muitos empates entre configuracoes "
                    "(mesmo otimo local). O Wilcoxon descarta empates; assim, parte dos pares pode ficar com "
                    "amostra efetiva abaixo do minimo e gerar `NaN`.\n"
                )
            if n_sig == 0 and recommended is not None:
                if recommended_equals_best_gap:
                    f.write(
                        "- Sem dominancia estatistica estrita apos Holm; a escolha final segue parcimonia "
                        "(menor cardinalidade que iguala o melhor gap mediano no tuning).\n"
                    )
                else:
                    f.write(
                        "- Sem dominancia estatistica estrita apos Holm; a escolha final segue parcimonia "
                        "computacional entre os finalistas nao-dominados.\n"
                    )
            if stat_b:
                f.write("\n| Config A | Config B | p_raw | p_adj | Sig. |\n")
                f.write("|----------|----------|-------|-------|------|\n")
                for r in sorted(stat_b, key=lambda x: float(x["p_adjusted"]) if not math.isnan(float(x["p_adjusted"])) else 999):
                    p_raw = float(r["p_raw"])
                    p_adj = float(r["p_adjusted"])
                    sig = "**SIM**" if r["significant"] else "nao"
                    f.write(
                        f"| `{r['config_a']}` | `{r['config_b']}` | "
                        f"{p_raw:.4f} | {p_adj:.4f} | {sig} |\n"
                    )
        else:
            f.write("- Desativado por `--no-statistical-tests`.\n")

        if recommended is not None:
            f.write(f"\n## Conjunto recomendado (size 3-4, nao-dominado)\n")
            f.write(
                f"- `{recommended['config_id']}` | size={recommended['set_size']} | "
                f"`{recommended['neighborhoods']}` | med_gap={float(recommended['median_gap_pct']):.3f}% | "
                f"med_t={float(recommended['median_time_sec']):.4f}s\n"
            )

        f.write("\n## Arquivos gerados\n")
        f.write("- `i1_baseline.json`\n")
        f.write("- `neighborhood_runs.csv`\n")
        f.write("- `phase_a_summary.csv` / `phase_a_summary.tex`\n")
        f.write("- `phase_b_summary.csv` / `phase_b_summary.tex`\n")
        f.write("- `statistical_tests.csv`\n")
        f.write("- `recommended_set.csv`\n")

    print(f"\n[Concluido] Relatorio em {report}")
    if recommended is not None:
        print(
            f"[Recomendacao] {recommended['config_id']} | size={recommended['set_size']} | "
            f"{recommended['neighborhoods']} | gap={float(recommended['median_gap_pct']):.3f}%"
        )


if __name__ == "__main__":
    main()
