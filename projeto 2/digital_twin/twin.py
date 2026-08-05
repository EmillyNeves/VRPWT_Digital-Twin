#!/usr/bin/env python3
"""Digital Twin orchestrator.

Each monitoring cycle: advance the (non-homogeneous Poisson) bin-fill sensors;
the bins above the threshold become collection demands with DYNAMIC time windows
(fuller = more critical = earlier due, exploiting the solver's Push Forward); a
VRPTW instance is built and the C++ solver (re)plans the routes; the served bins
are emptied. Also supports a STATIC scenario (collect all bins on a fixed
frequency) so dynamic vs static can be compared (distance, collections, overflow).
"""
import argparse
import json
import math
import os
import shlex
import subprocess
import tempfile

from maps import load_solomon, load_wcvrptw, load_vitoria
from sensors import FillSimulator

_HERE = os.path.dirname(os.path.abspath(__file__))
SOLVER = os.environ.get("VRPTW_SOLVER", os.path.join(_HERE, "..", "solver", "build", "solve"))


def bin_window_demand(fill, threshold, horizon, urgency=True, urgency_coef=0.6, demand_max=9):
    """Demanda e janela de tempo dinâmica de uma lixeira a partir do seu enchimento.

    MODELO DE DEMANDA (heurística de PRIORIDADE, não peso físico): uma lixeira mais
    cheia recebe demanda maior, fazendo o roteador tratá-la como "maior carga" e,
    assim, priorizá-la — não porque pese mais, mas para refletir sua criticidade.

    JANELA DINÂMICA (criticidade -> prazo): quanto mais cheia (mais crítica) a
    lixeira, mais cedo o prazo (`due`), explorando o critério Push Forward do solver.
    `urgency_coef` (0..1) controla a intensidade dessa antecipação (era fixo em 0,6;
    agora é um parâmetro de modelagem, exposto para análise de sensibilidade)."""
    demand = max(1, round(fill * demand_max) + 1)
    if urgency:
        crit = min(1.0, max(0.0, (fill - threshold) / max(1e-9, 1.0 - threshold)))
        due = int(horizon * (1.0 - urgency_coef * crit))
    else:
        due = horizon
    return demand, 0, due


def write_instance(path, cmap, active_idx, fills, capacity, horizon, service,
                   urgency=True, threshold=0.7, urgency_coef=0.6):
    depot = cmap.depot
    with open(path, "w") as f:
        f.write("DT\n\nVEHICLE\nNUMBER     CAPACITY\n")
        f.write(f" {max(1, len(active_idx))}  {capacity}\n\n")
        f.write("CUSTOMER\nCUST NO.  XCOORD.  YCOORD.  DEMAND  READY  DUE  SERVICE\n\n")
        f.write(f"0 {depot.rx:.4f} {depot.ry:.4f} 0 0 {horizon} 0\n")
        for j, i in enumerate(active_idx, start=1):
            demand, ready, due = bin_window_demand(float(fills[i]), threshold, horizon, urgency, urgency_coef)
            b = cmap.bins[i]
            f.write(f"{j} {b.rx:.4f} {b.ry:.4f} {demand} {ready} {due} {service}\n")
    return {j + 1: active_idx[j] for j in range(len(active_idx))}


def route_schedules(cmap, routes, fills, threshold=0.7, horizon=5000, service=5, urgency=True,
                    urgency_coef=0.6):
    """Replay each route to expose the SCHEDULE: arrival/start/wait per stop, the
    bin's time window [ready,due], demand, plus route distance/load/return time.
    Travel time = truncated Euclidean distance (same convention as the solver)."""
    def trunc1(d):
        return math.trunc(d * 10) / 10.0

    out = []
    for r in routes:
        stops, t, dist, load, prev = [], 0.0, 0.0, 0, cmap.depot
        for bi in r:
            b = cmap.bins[bi]
            leg = trunc1(math.hypot(b.rx - prev.rx, b.ry - prev.ry))
            dist += leg
            arrival = t + leg
            demand, ready, due = bin_window_demand(float(fills[bi]), threshold, horizon, urgency, urgency_coef)
            start = max(arrival, ready)
            stops.append({"bin": bi, "label": b.label, "arrival": arrival, "start": start,
                          "wait": start - arrival, "departure": start + service,
                          "ready": ready, "due": due, "demand": demand})
            t = start + service
            load += demand
            prev = b
        dist += trunc1(math.hypot(cmap.depot.rx - prev.rx, cmap.depot.ry - prev.ry))
        out.append({"stops": stops, "distance": dist, "load": load,
                    "return": t + trunc1(math.hypot(cmap.depot.rx - prev.rx, cmap.depot.ry - prev.ry))})
    return out


def parse_sol(path, mapping):
    routes, cost = [], None
    for line in open(path, encoding="utf-8", errors="ignore"):
        s = line.strip()
        if not s:
            continue
        if s.lower().startswith("route"):
            nums = [int(x) for x in s.split(":", 1)[1].split()] if ":" in s else []
            routes.append([mapping[n] for n in nums if n in mapping])
        elif s.lower().startswith("cost"):
            try:
                cost = float(s.split()[-1])
            except ValueError:
                pass
    return routes, cost


def plan_routes(cmap, active_idx, fills, algo, budget_ms, capacity, horizon, service,
                urgency=True, threshold=0.7, extra="", urgency_coef=0.6):
    if not active_idx:
        return [], 0.0
    with tempfile.TemporaryDirectory() as td:
        inst = os.path.join(td, "cycle.txt")
        sol = os.path.join(td, "cycle.sol")
        mapping = write_instance(inst, cmap, active_idx, fills, capacity, horizon, service,
                                 urgency, threshold, urgency_coef)
        subprocess.run([SOLVER, "--algo", algo, "--instance", inst,
                        "--budget-ms", str(budget_ms), "--out", sol] + shlex.split(extra),
                       capture_output=True, text=True)
        return parse_sol(sol, mapping)


def _record(sim, c, period, served, routes, cost):
    return {"cycle": c, "period": period, "fills": [float(x) for x in sim.fill],
            "active": list(served), "full": sim.full_bins(), "routes": [list(r) for r in routes],
            "distance": cost or 0.0, "vehicles": len(routes), "overflow": sim.overflow_events}


def simulate(cmap, cycles=24, threshold=0.7, algo="grasp", budget_ms=800, capacity=30,
             horizon=5000, service=5, urgency=True, seed=0, extra="", urgency_coef=0.6):
    """DYNAMIC scenario: collect bins above the threshold on demand each cycle."""
    sim = FillSimulator(len(cmap.bins), threshold=threshold, seed=seed)
    history = []
    for c in range(cycles):
        sim.step(c)
        active = sim.active()
        routes, cost = plan_routes(cmap, active, sim.fill, algo, budget_ms, capacity,
                                   horizon, service, urgency, threshold, extra, urgency_coef)
        history.append(_record(sim, c, sim.period_label(c), active, routes, cost))
        sim.collect([b for r in routes for b in r])
    return history


def simulate_static(cmap, cycles=24, frequency=3, threshold=0.7, algo="grasp", budget_ms=800,
                    capacity=30, horizon=5000, service=5, seed=0):
    """STATIC scenario: collect ALL bins every `frequency` cycles, ignoring fill."""
    sim = FillSimulator(len(cmap.bins), threshold=threshold, seed=seed)
    allbins = list(range(len(cmap.bins)))
    history = []
    for c in range(cycles):
        sim.step(c)
        if c % frequency == 0:
            routes, cost = plan_routes(cmap, allbins, sim.fill, algo, budget_ms, capacity,
                                       horizon, service, urgency=False, threshold=threshold)
            served = allbins
        else:
            routes, cost, served = [], 0.0, []
        history.append(_record(sim, c, sim.period_label(c), served, routes, cost))
        sim.collect(served)
    return history


def kpis(history):
    return {"distancia_total": round(sum(h["distance"] for h in history), 1),
            "coletas": sum(len(h["active"]) for h in history),
            "transbordos": history[-1]["overflow"] if history else 0,
            "ciclos_com_rota": sum(1 for h in history if h["routes"])}


def compare_scenarios(cmap, cycles=24, frequency=3, threshold=0.7, algo="grasp",
                      budget_ms=800, capacity=30, seed=0):
    dyn = simulate(cmap, cycles=cycles, threshold=threshold, algo=algo, budget_ms=budget_ms,
                   capacity=capacity, seed=seed)
    sta = simulate_static(cmap, cycles=cycles, frequency=frequency, threshold=threshold,
                          algo=algo, budget_ms=budget_ms, capacity=capacity, seed=seed)
    return {"dinamico": kpis(dyn), "estatico": kpis(sta)}, dyn, sta


def load_tuned(path=None):
    """irace-tuned per-algorithm switches (so the Twin uses the calibrated solver)."""
    path = path or os.path.join(_HERE, "..", "experiments", "config", "tuned.json")
    try:
        return json.load(open(path))
    except Exception:
        return {}


def compare_algorithms(cmap, cycles=24, algos=("i1", "vnd", "grasp", "rgrasp", "tabu"),
                       threshold=0.7, budget_ms=800, capacity=30, seed=0, tuned=None,
                       urgency_coef=0.6):
    """Apply each algorithm to the SAME dynamic simulation (same fill realization)
    and compare routing KPIs — the benchmark study carried into the application."""
    tuned = tuned if tuned is not None else load_tuned()
    out = {}
    for algo in algos:
        hist = simulate(cmap, cycles=cycles, threshold=threshold, algo=algo, budget_ms=budget_ms,
                        capacity=capacity, seed=seed, extra=tuned.get(algo, ""), urgency_coef=urgency_coef)
        out[algo] = {"kpis": kpis(hist), "per_cycle": [h["distance"] for h in hist]}
    return out


def load_map(source, arg):
    if source == "solomon":
        return load_solomon(arg or "R101")
    if source == "wcvrptw":
        default = os.path.join(_HERE, "..", "wcvrptw-instances-main", "instances", "444_stop.txt")
        return load_wcvrptw(arg or default)
    return load_vitoria()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["solomon", "wcvrptw", "vitoria"], default="vitoria")
    ap.add_argument("--arg", default=None)
    ap.add_argument("--cycles", type=int, default=24)
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--algo", default="grasp")
    ap.add_argument("--budget-ms", type=int, default=800)
    ap.add_argument("--capacity", type=int, default=30)
    ap.add_argument("--compare", action="store_true", help="dynamic vs static comparison")
    ap.add_argument("--frequency", type=int, default=3, help="static collection frequency (cycles)")
    ap.add_argument("--compare-algos", action="store_true", help="apply each algorithm in the Twin and compare")
    ap.add_argument("--algos", default="i1,vnd,grasp,rgrasp,tabu")
    args = ap.parse_args()

    cmap = load_map(args.source, args.arg)
    print(f"mapa: {cmap.name} ({len(cmap.bins)} lixeiras)")
    if args.compare_algos:
        algos = [a.strip() for a in args.algos.split(",") if a.strip()]
        comp = compare_algorithms(cmap, cycles=args.cycles, algos=algos, threshold=args.threshold,
                                  budget_ms=args.budget_ms, capacity=args.capacity)
        print(f"{'algoritmo':10s} {'distancia':>10s} {'coletas':>8s} {'transbordos':>12s}")
        for algo, r in comp.items():
            k = r["kpis"]
            print(f"{algo:10s} {k['distancia_total']:>10.1f} {k['coletas']:>8d} {k['transbordos']:>12d}")
    elif args.compare:
        comp, _, _ = compare_scenarios(cmap, cycles=args.cycles, frequency=args.frequency,
                                       threshold=args.threshold, algo=args.algo,
                                       budget_ms=args.budget_ms, capacity=args.capacity)
        print(f"{'cenario':10s} {'distancia':>10s} {'coletas':>8s} {'transbordos':>12s} {'ciclos_rota':>12s}")
        for name, k in comp.items():
            print(f"{name:10s} {k['distancia_total']:>10.1f} {k['coletas']:>8d} "
                  f"{k['transbordos']:>12d} {k['ciclos_com_rota']:>12d}")
    else:
        hist = simulate(cmap, cycles=args.cycles, threshold=args.threshold, algo=args.algo,
                        budget_ms=args.budget_ms, capacity=args.capacity)
        k = kpis(hist)
        print(f"ciclos: {len(hist)} | coletas: {k['coletas']} | "
              f"distancia: {k['distancia_total']} | transbordos: {k['transbordos']}")
