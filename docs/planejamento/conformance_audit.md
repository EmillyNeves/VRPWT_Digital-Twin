# Conformance Audit (Static, No Runs)

This document audits implementation conformance against:

- DIMACS VRPTW cost convention (primary objective = total distance, vehicles as feasibility constraint).
- Canonical logic described in literature for Solomon I1, VND/NLS (first improvement), GRASP, and Tabu Search.

Scope:

- Static code audit only (no benchmark runs in this stage).
- Target codebase state after neighborhood selection integration.

## 1) DIMACS and comparability baseline

Checklist:

- Primary objective fixed to cost: `src/main.cpp` rejects objectives other than `cost`.
- Feasibility validation at end of each solve: `validateSolution` called in `runSolve`.
- Vehicle count treated as hard constraint: `validateSolution` enforces `routes <= vehicleCount`.
- Unified logging schema for all methods: one CSV format in `runSolve`.
- Unified local-search neighborhood set configurable by `--vnd-neighborhoods` for `nls`, `vnd`, `grasp`, `tabu`.

Status: **Implemented**.

## 2) Solomon I1

Expected from literature:

- Farthest-seed initialization.
- Sequential insertion with feasible checks.
- Classical `c1/c2` ranking logic.

Code evidence:

- `src/heuristics/solomon_i1.cpp` (`selectSeedFarthest`, insertion scoring, feasibility checks).
- Parameters in `src/heuristics/solomon_i1.h` (`alpha1`, `alpha2`, `lambdaCoef`, `mu`).

Status: **Implemented (classical deterministic baseline variant)**.

## 3) VND / NLS local search

Expected from literature:

- First-improvement policy.
- Ordered neighborhood sequence.
- Restart to first neighborhood on improvement (VND behavior) when configured.

Code evidence:

- First-improvement acceptance in `src/heuristics/local_search.cpp`.
- VND control loop in `src/heuristics/vnd.cpp`.
- NLS restart/no-restart in `src/heuristics/neighborhood_descent.cpp`.

Status: **Implemented**.

## 4) GRASP

Expected (canonical):

- Greedy randomized construction (RCL controlled by `alpha`).
- Iterative improvement with local search.
- Optional reactive alpha adaptation.
- Budget-aware stopping.

Code evidence:

- RCL construction in `src/metaheuristics/grasp.cpp`.
- Reactive probabilities update in `src/metaheuristics/grasp.cpp`.
- Internal VND call with configured neighborhood set and remaining time budget.

Status: **Implemented (fixed + reactive)**.

Notes:

- Current implementation is a pragmatic GRASP variant (I1-aligned insertion backbone, then VND).
- This is methodologically valid for comparative VRPTW studies, provided it is explicitly documented as implemented.

## 5) Tabu Search

Expected (short-term canonical core):

- Tabu restrictions (recency memory).
- Aspiration criterion.
- Aspiration-by-default fallback when no admissible move exists.
- Admissible move selection (`best` or `first` policy).
- Fixed tabu tenure (`--tenure`) for strict comparability in this protocol.
- Stopping rules by budget/iterations/stagnation.

Code evidence:

- Recency tabu list (`tabuUntil`) in `src/metaheuristics/tabu.cpp`.
- Aspiration check (`isAspired`) in `src/metaheuristics/tabu.cpp`.
- Aspiration-by-default fallback in `src/metaheuristics/tabu.cpp` (best tabu move).
- Fixed tenure usage in `src/main.cpp` (blocking `--tenure-min/--tenure-max`).
- Move policy and stopping in `src/metaheuristics/tabu.cpp`.

Status: **Implemented (classical short-term Tabu core, fixed tenure)**.

Known simplifications vs full Glover framework:

- Long-term memory (frequency/intensification/diversification) not implemented.
- Strategic oscillation not implemented.

These simplifications are acceptable if explicitly stated in methods as "classical short-term Tabu variant".

Scope justification (for paper text):

- The implementation intentionally targets short-term Tabu Search to preserve structural comparability with VND and GRASP.
- The comparative objective is to isolate the contribution of recency memory + aspiration under equal computational budgets.

## 6) Equality-of-conditions checklist (for upcoming experiments)

Must hold in every comparative run:

- Same instance set and same seed schedule per algorithm.
- Same global time limit per run (`--time-limit`).
- Same initial baseline policy where applicable (I1-based starts in `nls/vnd/grasp/tabu`).
- Same local neighborhood set (`--vnd-neighborhoods`) across compared methods.
- Same epsilon and parsing/validation pipeline.
- Same output fields for post-hoc audit (`objective`, `time_sec`, `gap_pct`, `num_routes`, `vnd_neighborhoods`, etc.).

Status: **Infrastructure ready**; experiment execution pending.

## 7) irace calibration infrastructure

Checklist:

- Dedicated scenario files exist per method variant (`tabu_classic`, `grasp_fixed`, `grasp_reactive`).
- Dedicated parameter files exist with one tuned parameter per scenario.
- Target-runner enforces fixed controls (`objective`, `mu`, `eps`, `time-limit`, neighborhood set, disabled secondary stops).
- Target-runner returns a single numeric score and applies deterministic penalty policy on failures.
- Tuning and holdout instance lists are explicitly separated.

Code evidence:

- `scripts/irace/scenario_tabu_classic.txt`
- `scripts/irace/scenario_grasp_fixed.txt`
- `scripts/irace/scenario_grasp_reactive.txt`
- `scripts/irace/parameters_tabu_classic.txt`
- `scripts/irace/parameters_grasp_fixed.txt`
- `scripts/irace/parameters_grasp_reactive.txt`
- `scripts/irace/target_runner.py`
- `scripts/irace/run_irace.py`
- `scripts/tuning_set.txt`
- `scripts/holdout_set.txt`

Status: **Implemented and ready for pre-flight checks**.
