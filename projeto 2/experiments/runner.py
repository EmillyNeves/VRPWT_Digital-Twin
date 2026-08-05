#!/usr/bin/env python3
"""Batch runner for the VRPTW solver.

For each (algorithm, instance, seed) it calls the C++ `solve` binary, saving:
  - one row in the master CSV (results/raw/runs.csv),
  - the final solution as a .sol file (results/raw/sol/),
  - the convergence trace (results/raw/traces/),
  - optionally per-move snapshots for selected instances (route-evolution plots).

Deterministic algorithms (i1, vnd, tabu) run once; stochastic ones (grasp,
rgrasp) run `--runs` times with different seeds. Uses only the standard library.
"""
import argparse
import csv
import json
import os
import re
import shlex
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

DETERMINISTIC = {"i1", "vnd", "tabu"}
STOCHASTIC = {"grasp", "rgrasp"}

CSV_HEADER = ["algorithm", "instance", "family", "type", "seed", "run_idx",
              "distance", "vehicles", "time_ms", "iters", "feasible",
              "ref_dinamics", "gap_pct"]


def parse_family_type(name):
    m = re.match(r"([A-Za-z]+)(\d)", name)
    return (m.group(1).upper(), int(m.group(2))) if m else ("?", 0)


def read_ref_cost(refs_dir, name):
    path = os.path.join(refs_dir, name + ".sol")
    if not os.path.isfile(path):
        return None
    for line in open(path, encoding="utf-8", errors="ignore"):
        if "Cost" in line or "cost" in line:
            try:
                return float(line.split()[-1])
            except ValueError:
                pass
    return None


METAHEURISTICS = {"grasp", "rgrasp", "tabu"}   # use the iterations-without-improvement criterion


def run_one(solver, algo, inst_path, name, seed, budget_ms, sol_dir, trace_dir,
            snapshots_dir, extra, max_no_improve):
    tag = f"{algo}_{name}_s{seed}"
    # `budget-ms` is now only a SAFETY time cap; the primary stop is
    # `max-no-improve` (iterations without improving the best). I1/VND terminate
    # deterministically and ignore both.
    cmd = [solver, "--algo", algo, "--instance", inst_path, "--seed", str(seed),
           "--budget-ms", str(budget_ms), "--csv",
           "--out", os.path.join(sol_dir, tag + ".sol"),
           "--trace", os.path.join(trace_dir, tag + ".csv")]
    if max_no_improve is not None and algo in METAHEURISTICS:
        cmd += ["--max-no-improve", str(max_no_improve)]
    if snapshots_dir is not None:
        cmd += ["--snapshots", os.path.join(snapshots_dir, tag + ".snap")]
    cmd += extra   # tuned per-algo switches (incl. a calibrated --max-no-improve) override the default above
    out = subprocess.run(cmd, capture_output=True, text=True)
    line = out.stdout.strip().splitlines()
    if not line:
        sys.stderr.write(f"[WARN] sem saida: {tag}\n{out.stderr}\n")
        return None
    # solve --csv: algo,instance,seed,distance,vehicles,time_ms,feasible,iters
    f = line[-1].split(",")
    return {"distance": float(f[3]), "vehicles": int(f[4]),
            "time_ms": int(f[5]), "feasible": int(f[6]),
            "iters": int(f[7]) if len(f) > 7 else 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", default="../solver/build/solve")
    ap.add_argument("--instances-dir", default="../input")
    ap.add_argument("--refs-dir", default="../solution (Dinamics)")
    ap.add_argument("--algos", default="i1,vnd,tabu,grasp,rgrasp")
    ap.add_argument("--budget-ms", type=int, default=600000,
                    help="teto de SEGURANCA de tempo (ms); o criterio primario e --max-no-improve")
    ap.add_argument("--max-no-improve", type=int, default=None,
                    help="criterio de parada primario: iteracoes sem melhoria (grasp/rgrasp/tabu). "
                         "Pode ser sobrescrito por algoritmo via --params-file (tuned.json)")
    ap.add_argument("--runs", type=int, default=30, help="runs for stochastic algos")
    ap.add_argument("--instance-list", default=None, help="file with instance names, one per line")
    ap.add_argument("--out", default="../results/raw/runs.csv")
    ap.add_argument("--sol-dir", default="../results/raw/sol")
    ap.add_argument("--trace-dir", default="../results/raw/traces")
    ap.add_argument("--snapshots-for", default="", help="comma list of instances to dump per-move snapshots")
    ap.add_argument("--snapshots-dir", default="../results/raw/snapshots")
    ap.add_argument("--target-gap", type=float, default=None,
                    help="stop each run at best-known*(1+gap); for TTT experiments")
    ap.add_argument("--params-file", default=None,
                    help="JSON {algo: \"--switch val ...\"} of irace-tuned params to apply")
    ap.add_argument("--jobs", type=int, default=1, help="concurrent solve processes")
    args = ap.parse_args()

    algos = [a.strip() for a in args.algos.split(",") if a.strip()]
    tuned = json.load(open(args.params_file)) if args.params_file else {}
    snap_set = {s.strip() for s in args.snapshots_for.split(",") if s.strip()}
    for d in (args.sol_dir, args.trace_dir, args.snapshots_dir, os.path.dirname(args.out)):
        os.makedirs(d, exist_ok=True)

    if args.instance_list and os.path.isfile(args.instance_list):
        names = [l.strip() for l in open(args.instance_list) if l.strip()]
    else:
        names = sorted(os.path.splitext(f)[0] for f in os.listdir(args.instances_dir)
                       if f.endswith(".txt"))

    # build the full task list (one entry per run)
    tasks = []
    for name in names:
        fam, typ = parse_family_type(name)
        ref = read_ref_cost(args.refs_dir, name)
        for algo in algos:
            nruns = args.runs if algo in STOCHASTIC else 1
            for run_idx in range(nruns):
                seed = run_idx + 1
                snaps = args.snapshots_dir if (name in snap_set and run_idx == 0) else None
                extra = shlex.split(tuned.get(algo, ""))
                if args.target_gap is not None and ref:
                    extra += ["--target", f"{ref * (1 + args.target_gap):.1f}"]
                tasks.append((algo, name, fam, typ, ref, seed, run_idx, snaps, extra))

    def work(t):
        algo, name, fam, typ, ref, seed, run_idx, snaps, extra = t
        inst_path = os.path.join(args.instances_dir, name + ".txt")
        return t, run_one(args.solver, algo, inst_path, name, seed, args.budget_ms,
                          args.sol_dir, args.trace_dir, snaps, extra, args.max_no_improve)

    rows, done = [], 0
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for fut in as_completed([ex.submit(work, t) for t in tasks]):
            t, r = fut.result()
            done += 1
            if done % 50 == 0 or done == len(tasks):
                print(f"  {done}/{len(tasks)} runs", flush=True)
            if r is None:
                continue
            algo, name, fam, typ, ref, seed, run_idx, _, _ = t
            gap = (r["distance"] - ref) / ref * 100.0 if ref else ""
            rows.append([algo, name, fam, typ, seed, run_idx,
                         f"{r['distance']:.1f}", r["vehicles"], r["time_ms"], r["iters"],
                         r["feasible"],
                         "" if ref is None else f"{ref:.1f}",
                         "" if gap == "" else f"{gap:.3f}"])

    rows.sort(key=lambda x: (x[1], x[0], x[4]))   # instance, algorithm, seed
    with open(args.out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(CSV_HEADER)
        w.writerows(rows)
    print(f"CSV mestre escrito em {args.out} ({len(rows)} linhas)")


if __name__ == "__main__":
    main()
