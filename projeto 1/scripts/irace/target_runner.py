#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _fmt_float(x: float) -> str:
    text = f"{x:.10f}".rstrip("0").rstrip(".")
    return text if text else "0"


def _safe_float(value: str) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return x


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _has_option(tokens: List[str], option: str) -> bool:
    for tok in tokens:
        if tok == option or tok.startswith(option + "="):
            return True
    return False


def _parse_args(argv: List[str]) -> Tuple[Dict[str, str], argparse.Namespace, List[str]]:
    if len(argv) < 4:
        raise RuntimeError(
            "Uso: target_runner.py <config_id> <instance_id> <seed> <instance> <bound> [params...]"
        )

    bound = ""
    args_offset = 4
    if len(argv) >= 5 and not argv[4].startswith("--"):
        bound = argv[4]
        args_offset = 5

    meta = {
        "config_id": argv[0],
        "instance_id": argv[1],
        "seed": argv[2],
        "instance": argv[3],
        "bound": bound,
    }

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--bin", required=True)
    parser.add_argument("--algo", required=True, choices=["tabu", "grasp"])
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--bks-dir", default="./solution")
    parser.add_argument("--objective", default="cost")
    parser.add_argument("--mu", type=float, default=1.0)
    parser.add_argument("--eps", type=float, default=1e-6)
    parser.add_argument("--time-limit", type=float, required=True)
    parser.add_argument("--vnd-neighborhoods", required=True)
    parser.add_argument("--max-iters", type=int, default=0)
    parser.add_argument("--max-no-improve", type=int, default=0)
    parser.add_argument("--tabu-move-policy", default="best")
    parser.add_argument("--grasp-mode", default="fixed", choices=["fixed", "reactive"])
    parser.add_argument("--reactive-alphas", default="0.1,0.2,0.3,0.4,0.5")
    parser.add_argument("--reactive-gamma", default="1.0")
    parser.add_argument("--score-lambda", type=float, default=0.0)
    parser.add_argument("--penalty", type=float, default=1e9)
    parser.add_argument("--keep-artifacts", action="store_true")
    parsed, cand_params = parser.parse_known_args(argv[args_offset:])
    return meta, parsed, cand_params


def _validate_scenario_contract(args: argparse.Namespace, cand_params: List[str]) -> str | None:
    if args.objective != "cost":
        return "--objective deve ser cost"

    if args.algo == "tabu":
        if not _has_option(cand_params, "--tenure"):
            return "cenario tabu sem parametro --tenure vindo do irace"
    elif args.algo == "grasp":
        if args.grasp_mode == "fixed" and not _has_option(cand_params, "--alpha"):
            return "cenario grasp fixed sem parametro --alpha vindo do irace"
        if args.grasp_mode == "reactive" and not _has_option(cand_params, "--reactive-update"):
            return "cenario grasp reactive sem parametro --reactive-update vindo do irace"
    return None


def _read_execution_csv(csv_path: Path) -> Dict[str, str]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f), None)
    if row is None:
        raise RuntimeError(f"CSV vazio: {csv_path}")
    return row


def _write_run_log(log_path: Path, payload: Dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=True, indent=2)


def main(argv: List[str]) -> int:
    try:
        meta, args, cand_params = _parse_args(argv)
    except Exception as exc:
        print("1000000000")
        print(f"[target-runner] parse error: {exc}", file=sys.stderr)
        return 0

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tmp_root = out_dir / "tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(
        tempfile.mkdtemp(
            prefix=f"c{meta['config_id']}_i{meta['instance_id']}_s{meta['seed']}_",
            dir=tmp_root,
        )
    )
    run_tag = f"irace_c{meta['config_id']}_i{meta['instance_id']}_s{meta['seed']}"

    failure_reason = _validate_scenario_contract(args, cand_params)

    cmd = [
        args.bin,
        "solve",
        "--algo",
        args.algo,
        "--instance",
        meta["instance"],
        "--seed",
        meta["seed"],
        "--out",
        str(run_dir),
        "--tag",
        run_tag,
        "--bks-dir",
        args.bks_dir,
        "--objective",
        args.objective,
        "--mu",
        _fmt_float(args.mu),
        "--eps",
        _fmt_float(args.eps),
        "--time-limit",
        _fmt_float(args.time_limit),
        "--vnd-neighborhoods",
        args.vnd_neighborhoods,
        "--max-iters",
        str(args.max_iters),
        "--max-no-improve",
        str(args.max_no_improve),
    ]

    if args.algo == "tabu":
        cmd += ["--tabu-move-policy", args.tabu_move_policy]
    if args.algo == "grasp":
        cmd += ["--grasp-mode", args.grasp_mode]
        if args.grasp_mode == "reactive":
            cmd += ["--reactive-alphas", args.reactive_alphas, "--reactive-gamma", args.reactive_gamma]

    cmd += cand_params

    proc = None
    row: Dict[str, str] = {}
    score = float(args.penalty)
    gap_pct = None
    time_sec = None
    num_routes = None

    if failure_reason is None:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            failure_reason = f"solver_return_code={proc.returncode}"
        else:
            exec_dir = run_dir / "logs" / "execution"
            csv_files = sorted(exec_dir.glob("*.csv"))
            if not csv_files:
                failure_reason = f"sem CSV de execucao em {exec_dir}"
            else:
                try:
                    row = _read_execution_csv(csv_files[0])
                    gap_pct = _safe_float(row.get("gap_pct", ""))
                    time_sec = _safe_float(row.get("time_sec", ""))
                    num_routes = _safe_float(row.get("num_routes", ""))
                    if gap_pct is None:
                        failure_reason = "gap_pct ausente/invalidado no CSV"
                    else:
                        if time_sec is None:
                            time_sec = 0.0
                        score = gap_pct + (args.score_lambda * time_sec)
                except Exception as exc:
                    failure_reason = str(exc)

    log_suffix = f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_{os.getpid()}"
    log_path = out_dir / "runner_logs" / (
        f"c{meta['config_id']}_i{meta['instance_id']}_s{meta['seed']}_{log_suffix}.json"
    )
    _write_run_log(
        log_path,
        {
            "timestamp_utc": _utc_now(),
            "meta": meta,
            "status": "ok" if failure_reason is None else "penalized",
            "failure_reason": failure_reason,
            "solver_cmd": cmd,
            "candidate_params": cand_params,
            "score": score,
            "gap_pct": gap_pct,
            "time_sec": time_sec,
            "num_routes": num_routes,
            "csv_row": row,
            "stdout": None if proc is None else proc.stdout,
            "stderr": None if proc is None else proc.stderr,
        },
    )

    if not args.keep_artifacts:
        shutil.rmtree(run_dir, ignore_errors=True)

    sys.stdout.write(_fmt_float(score) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
