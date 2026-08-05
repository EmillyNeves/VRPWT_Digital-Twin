# irace Search-Space Template

Use this file to lock ranges before launching irace.

Implemented parameter files:

- `scripts/irace/parameters_tabu_classic.txt`
- `scripts/irace/parameters_grasp_fixed.txt`
- `scripts/irace/parameters_grasp_reactive.txt`

Reference rationale:

- `tenure` range: short-term Tabu tenure behavior [Glover & Laguna, 1997]
- `alpha` range: GRASP RCL control [Feo & Resende, 1995]
- `reactive-update` range: reactive GRASP update cadence [Prais & Ribeiro, 2000]
- full citation details: `docs/irace_parameter_justification.md`

Status fields:

- `OPEN`: pending review
- `LOCKED`: approved for race

## Tabu (algo=tabu)

| Parameter | Type | Candidate Range/Values | Status | Notes |
|---|---|---|---|---|
| `tenure` | integer | `[5, 50]` | LOCKED | primary tuned parameter in scenario A |
| `tabu-move-policy` | categorical | `best` | LOCKED | fixed for canonical short-term Tabu |
| `max-iters` | integer | `0` | LOCKED | disabled; time-limit is main budget |
| `max-no-improve` | integer | `0` | LOCKED | disabled; time-limit is main budget |

## GRASP fixed (algo=grasp, grasp-mode=fixed)

| Parameter | Type | Candidate Range/Values | Status | Notes |
|---|---|---|---|---|
| `alpha` | real | `[0.0, 1.0]` | LOCKED | primary tuned parameter in scenario B |
| `max-iters` | integer | `0` | LOCKED | disabled; time-limit is main budget |
| `max-no-improve` | integer | `0` | LOCKED | disabled; time-limit is main budget |

## GRASP reactive (algo=grasp, grasp-mode=reactive)

| Parameter | Type | Candidate Range/Values | Status | Notes |
|---|---|---|---|---|
| `reactive-alphas` | categorical/set design | `0.1,0.2,0.3,0.4,0.5` | LOCKED | fixed alpha pool |
| `reactive-update` | integer | `[5, 100]` | LOCKED | primary tuned parameter in scenario C |
| `reactive-gamma` | real | `1.0` | LOCKED | fixed neutral update factor |
| `max-iters` | integer | `0` | LOCKED | disabled; time-limit is main budget |
| `max-no-improve` | integer | `0` | LOCKED | disabled; time-limit is main budget |

## Global fixed controls (not tuned)

| Parameter | Value |
|---|---|
| `objective` | `cost` |
| `mu` | `1.0` |
| `eps` | `1e-6` |
| `time-limit` | `OPEN` (must be same for all scenarios) |
| `vnd-neighborhoods` | selected set (or explicit fixed list) |
| training set | `input_tuning_set` |
| holdout set | `input_holdout_set` |

## Acceptance checklist before running irace

- All `OPEN` ranges converted to numeric/categorical values.
- Same `time-limit` and neighborhood set across all compared methods.
- Target-runner metric defined: primary `gap_pct`, tie-break `time_sec`.
- Reproducibility seed and budget (`maxExperiments`) locked.
- Ex-ante table filled in `docs/irace_parameter_justification.md`.
