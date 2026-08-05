#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path
from typing import Dict, List


SCENARIOS: Dict[str, Dict[str, object]] = {
    "tabu_classic": {
        "algo": "tabu",
        "scenario_file": "scripts/irace/scenario_tabu_classic.txt",
        "parameter_file": "scripts/irace/parameters_tabu_classic.txt",
        "deterministic": 1,
        "extra_fixed": ["--tabu-move-policy", "best"],
    },
    "grasp_fixed": {
        "algo": "grasp",
        "scenario_file": "scripts/irace/scenario_grasp_fixed.txt",
        "parameter_file": "scripts/irace/parameters_grasp_fixed.txt",
        "deterministic": 0,
        "extra_fixed": ["--grasp-mode", "fixed"],
    },
    "grasp_reactive": {
        "algo": "grasp",
        "scenario_file": "scripts/irace/scenario_grasp_reactive.txt",
        "parameter_file": "scripts/irace/parameters_grasp_reactive.txt",
        "deterministic": 0,
        "extra_fixed": [
            "--grasp-mode",
            "reactive",
            "--reactive-alphas",
            "0.1,0.2,0.3,0.4,0.5",
            "--reactive-gamma",
            "1.0",
        ],
    },
}


def _fmt_float(x: float) -> str:
    s = f"{x:.10f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _shell_join(parts: List[str]) -> str:
    return " ".join(shlex.quote(x) for x in parts)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Runner de conveniencia para irace (tabu_classic, grasp_fixed, grasp_reactive)."
    )
    p.add_argument(
        "--algo",
        required=True,
        choices=sorted(SCENARIOS.keys()),
        help="Cenario de calibracao.",
    )
    p.add_argument(
        "--instances-file",
        default="scripts/tuning_set.txt",
        help="Arquivo com instancias de tuning (uma por linha).",
    )
    p.add_argument("--max-experiments", type=int, default=1000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--time-limit", type=float, default=30.0)
    p.add_argument("--eps", type=float, default=1e-6)
    p.add_argument(
        "--vnd-neighborhoods",
        default="relocate_intra,swap_intra,relocate_inter,two_opt_inter",
        help="Conjunto local fixo usado em todos os cenarios.",
    )
    p.add_argument(
        "--out-dir",
        default="results/irace",
        help="Raiz de saida do irace (subpasta por cenario).",
    )
    p.add_argument(
        "--score-lambda",
        type=float,
        default=1e-4,
        help="Peso pequeno para desempate por tempo: score = gap_pct + lambda*time_sec.",
    )
    p.add_argument(
        "--penalty",
        type=float,
        default=1e9,
        help="Penalidade devolvida pelo target runner em falhas/infeasibilidade.",
    )
    p.add_argument("--parallel", type=int, default=0, help="Paralelismo no irace (0/1 = sem paralelo).")
    p.add_argument("--target-runner-timeout", type=int, default=0, help="Timeout (s) por chamada do target runner.")
    p.add_argument("--debug-level", type=int, default=0)
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--check", action="store_true", help="Roda apenas validacao de configuracao do irace.")
    p.add_argument("--dry-run", action="store_true", help="Somente imprime o comando final.")
    return p.parse_args()


def build_target_cmdline(args: argparse.Namespace, scenario: Dict[str, object]) -> str:
    out_root = f"./{args.out_dir}/{args.algo}"
    fixed = [
        "--bin",
        "./bin/vrptw",
        "--algo",
        str(scenario["algo"]),
        "--out-dir",
        out_root,
        "--bks-dir",
        "./solution",
        "--objective",
        "cost",
        "--mu",
        "1.0",
        "--eps",
        _fmt_float(args.eps),
        "--time-limit",
        _fmt_float(args.time_limit),
        "--vnd-neighborhoods",
        args.vnd_neighborhoods,
        "--max-iters",
        "0",
        "--max-no-improve",
        "0",
        "--score-lambda",
        _fmt_float(args.score_lambda),
        "--penalty",
        _fmt_float(args.penalty),
    ]
    fixed += list(scenario["extra_fixed"])  # type: ignore[arg-type]
    fixed_str = _shell_join(fixed)
    return (
        "{configurationID} {instanceID} {seed} {instance} {bound} "
        + fixed_str
        + " {targetRunnerArgs}"
    )


def main() -> int:
    args = parse_args()
    scenario = SCENARIOS[args.algo]
    repo = _repo_root()

    scenario_file = repo / str(scenario["scenario_file"])
    parameter_file = repo / str(scenario["parameter_file"])
    instances_file = (repo / args.instances_file).resolve()
    log_dir = (repo / args.out_dir / args.algo).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "irace.Rdata"

    if not scenario_file.exists():
        raise SystemExit(f"Cenario nao encontrado: {scenario_file}")
    if not parameter_file.exists():
        raise SystemExit(f"Arquivo de parametros nao encontrado: {parameter_file}")
    if not instances_file.exists():
        raise SystemExit(f"Arquivo de instancias nao encontrado: {instances_file}")

    target_cmdline = build_target_cmdline(args, scenario)

    cmd = [
        "Rscript",
        "-e",
        "irace::irace_cmdline(commandArgs(TRUE))",
        "--scenario",
        str(scenario_file),
        "--exec-dir",
        ".",
        "--parameter-file",
        str(parameter_file),
        "--train-instances-file",
        str(instances_file),
        "--target-runner",
        "./scripts/irace/target_runner.py",
        "--target-cmdline",
        target_cmdline,
        "--deterministic",
        str(scenario["deterministic"]),
        "--max-experiments",
        str(args.max_experiments),
        "--seed",
        str(args.seed),
        "--log-file",
        str(log_file),
    ]

    if args.parallel > 1:
        cmd += ["--parallel", str(args.parallel)]
    if args.target_runner_timeout > 0:
        cmd += ["--target-runner-timeout", str(args.target_runner_timeout)]
    if args.debug_level > 0:
        cmd += ["--debug-level", str(args.debug_level)]
    if args.quiet:
        cmd += ["--quiet"]
    if args.check:
        cmd += ["--check"]

    printable = _shell_join(cmd)
    print("irace command:", flush=True)
    print(printable, flush=True)
    print(f"working directory: {repo}", flush=True)

    if args.dry_run:
        return 0

    proc = subprocess.run(cmd, cwd=repo)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
