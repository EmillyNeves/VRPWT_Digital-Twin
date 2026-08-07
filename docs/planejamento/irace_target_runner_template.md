# irace Target-Runner Template (Contract)

This is a contract template for the future runner script.  
No execution logic is implemented in this file.

Implemented version in this repository:

- `scripts/irace/target_runner.py`

## Input contract

Runner receives:

- instance path
- seed
- candidate parameters (from irace)

Runner must enforce fixed controls:

- algorithm (`tabu` or `grasp`)
- `--objective cost`
- fixed `--time-limit T`
- `--max-iters 0` and `--max-no-improve 0` (disabled)
- fixed neighborhood set (`--vnd-neighborhoods ...`)
- fixed `--mu`, `--eps`

## Solver call pattern

Generic:

```bash
bin/vrptw solve --algo <tabu|grasp> --instance <inst> --seed <seed> --out <tmp_out> [candidate params...]
```

For `tabu`, candidates should include only:

- fixed tenure: `--tenure <t>` (dynamic tenure flags disabled in this protocol)

For `grasp` scenarios:

- fixed mode: candidate includes only `--alpha <a>`
- reactive mode: candidate includes only `--reactive-update <u>`

## Output contract to irace

Runner must print one numeric value (to stdout):

- objective for minimization (recommended: `gap_pct`)

Fallback policy:

- infeasible/error/timeouts -> return large penalty value.

## Suggested scoring policy

Primary:

- `score = gap_pct`

Optional tie-break integration:

- `score = gap_pct + lambda * time_sec` with small `lambda`
- or keep tie-break external in post-selection (preferred for clarity).

## Logging requirements

Persist per run:

- raw command line
- solver execution CSV path
- parsed `gap_pct`, `time_sec`, `num_routes`
- stopping contract actually used (`time-limit`, `max-iters`, `max-no-improve`)
- failure reason if any

## Validation checklist

- same instance and seed schedule across scenarios
- same fixed controls across algorithms
- deterministic penalty policy
- no hidden overrides of tuned parameters
