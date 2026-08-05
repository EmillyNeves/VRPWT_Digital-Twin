# irace Calibration Plan

Status: infrastructure implemented; final races still pending.

Companion document (mandatory):

- `docs/irace_parameter_justification.md` (pre-registration ex-ante + ex-post report, with citations).

## 1) Objective

Calibrate `tabu` and `grasp` parameters on `input_tuning_set`, then validate chosen configurations on `input_holdout_set`, under equal execution conditions [1][2].

Primary score in irace:

- minimize `gap_pct` (vs BKS).

Tie-break:

- minimize `time_sec` via `score = gap_pct + lambda * time_sec` (small `lambda`).

Implemented script path:

- `scripts/irace/run_irace.py` (orchestration + irace CLI invocation).

## 2) Common execution contract

Shared fixed settings for all candidates:

- `--objective cost`
- `--mu 1.0`
- `--eps 1e-6` (or project-wide epsilon)
- same `--time-limit T`
- `--max-iters 0` and `--max-no-improve 0` (disabled; time is the main budget)
- same neighborhood set via `--vnd-neighborhoods` (default selected set unless explicitly overridden)
- split tuning/holdout fixed before racing to avoid over-tuning [1]

Instance split:

- train/tuning: `input_tuning_set`
- holdout/final check: `input_holdout_set`
- instance lists used by scripts: `scripts/tuning_set.txt` and `scripts/holdout_set.txt`

Implemented irace artifacts:

- scenarios: `scripts/irace/scenario_tabu_classic.txt`, `scripts/irace/scenario_grasp_fixed.txt`, `scripts/irace/scenario_grasp_reactive.txt`
- parameter files: `scripts/irace/parameters_tabu_classic.txt`, `scripts/irace/parameters_grasp_fixed.txt`, `scripts/irace/parameters_grasp_reactive.txt`
- target runner: `scripts/irace/target_runner.py`

## 3) Calibration scenarios

### 3.1 Scenario A: Tabu (classical short-term)

Algorithm:

- `bin/vrptw solve --algo tabu ...`

Tune:

- `tenure` (integer)

Keep fixed:

- `tabu-move-policy=best`
- `max-iters=0`
- `max-no-improve=0`
- local neighborhoods (`--vnd-neighborhoods`)
- `time-limit`
- deterministic setting in irace: `1` (fixed-tenure short-term Tabu in this implementation)

### 3.2 Scenario B: GRASP (fixed)

Algorithm:

- `bin/vrptw solve --algo grasp --grasp-mode fixed ...`

Tune:

- `alpha`

Keep fixed:

- `max-iters=0`
- `max-no-improve=0`
- local neighborhoods (`--vnd-neighborhoods`)
- `time-limit`
- deterministic setting in irace: `0`

### 3.3 Scenario C: GRASP (reactive)

Algorithm:

- `bin/vrptw solve --algo grasp --grasp-mode reactive ...`

Tune:

- `reactive-update`

Keep fixed:

- `reactive-alphas=0.1,0.2,0.3,0.4,0.5`
- `reactive-gamma=1.0`
- `max-iters=0`
- `max-no-improve=0`
- local neighborhoods (`--vnd-neighborhoods`)
- `time-limit`
- deterministic setting in irace: `0`

## 4) Budgeting and stopping in irace

Suggested control knobs:

- `maxExperiments=1000` per scenario (starting point)
- optional `maxTime`
- deterministic setting per scenario (Tabu classical here: deterministic; GRASP fixed/reactive: stochastic) [2]

Recommended policy:

- start with `1000` and increase only if scenario shows unstable winners or boundary hits;
- if winner is at interval boundary, expand interval and rerun scenario.

## 5) Deliverables per scenario

- best configuration(s) from irace.
- full race logs and tested configurations.
- reproducible command line used.
- short summary table: parameter values + tuning performance.
- ex-post justification table filled in `docs/irace_parameter_justification.md`.

## 6) Final validation protocol

After selecting tuned configs:

1. freeze tuned params;
2. run once on holdout with same budget rule;
3. report holdout gap/time and compare against untuned baseline.

## 7) Command templates

Pre-flight check only:

```bash
python3 scripts/irace/run_irace.py --algo tabu_classic --check
python3 scripts/irace/run_irace.py --algo grasp_fixed --check
python3 scripts/irace/run_irace.py --algo grasp_reactive --check
```

Race execution:

```bash
python3 scripts/irace/run_irace.py --algo tabu_classic --max-experiments 1000 --time-limit 30 --seed 42
python3 scripts/irace/run_irace.py --algo grasp_fixed --max-experiments 1000 --time-limit 30 --seed 42
python3 scripts/irace/run_irace.py --algo grasp_reactive --max-experiments 1000 --time-limit 30 --seed 42
```

## 8) References

[1] Birattari, M. (2009). *Tuning Metaheuristics: A Machine Learning Perspective*. Springer.  
[2] López-Ibáñez, M. et al. (2016). The irace package: Iterated racing for automatic algorithm configuration. *Operations Research Perspectives*, 3, 43-58.
