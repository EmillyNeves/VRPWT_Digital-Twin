# VRPTW (Solomon) – Heurísticas e Metaheurísticas

Implementação em C++ (C++20) de heurísticas para VRPTW com:

- Solomon I1 (construtivo)
- Solomon I1 + VND (first improvement)
- GRASP (fixo e reativo)
- Busca Tabu clássica de curto prazo (tenure fixo)

## Build

Requer `g++` com suporte a C++20.

```bash
make
```

Binário: `bin/vrptw`

## Execução (exemplos)

Resolver uma instância com Solomon I1:

```bash
bin/vrptw solve --algo i1 --instance input/C101.txt --seed 42 --out results/runs/quick_i1
```

Rodar GRASP com `alpha=0.3` e parada por estagnação:

```bash
bin/vrptw solve --algo grasp --alpha 0.3 --max-no-improve 500 --instance input/C101.txt --seed 42 --out results/runs/quick_grasp
```

Rodar GRASP reativo:

```bash
bin/vrptw solve --algo grasp --grasp-mode reactive --reactive-alphas 0.1,0.2,0.3,0.4,0.5 --reactive-update 25 --reactive-gamma 1.0 --instance input/C101.txt --seed 42 --out results/runs/quick_grasp_reactive
```

Rodar Tabu:

```bash
bin/vrptw solve --algo tabu --tenure 20 --max-iters 500 --max-no-improve 100 --instance input/C101.txt --seed 42 --out results/runs/quick_tabu
```

Comparar Tabu `best` vs `first`:

```bash
bin/vrptw solve --algo tabu --tabu-move-policy best --tenure 20 --max-iters 500 --max-no-improve 100 --instance input/C101.txt --seed 42 --out results/runs/tabu_best
bin/vrptw solve --algo tabu --tabu-move-policy first --tenure 20 --max-iters 500 --max-no-improve 100 --instance input/C101.txt --seed 42 --out results/runs/tabu_first
```

Nota: para comparacao estrita por tempo, use `--time-limit T` comum entre metodos e
defina `--max-iters 0 --max-no-improve 0` (desativados).

Comparar `VND`, `GRASP` e `Tabu` com baseline `I1` (Solomon), com consolidacao automatica dos CSVs:

```bash
python3 scripts/compare_solomon_methods.py \
  --instances C101,R101,RC101 \
  --seeds 42-51 \
  --grasp-mode fixed \
  --grasp-alpha 0.3 \
  --tabu-tenure 15 \
  --out results/runs
```

Arquivos principais gerados em `results/runs/compare_solomon_<run_id>/_summary/`:

- `all_results.csv`
- `summary_by_instance.csv`
- `summary_by_type.csv`
- `improvement_vs_i1_by_algorithm.csv`

Conjunto de vizinhancas locais atualmente implementado (8):

1. `relocate_intra`
2. `swap_intra`
3. `relocate_inter`
4. `or_opt`
5. `swap_inter`
6. `two_opt_intra`
7. `two_opt_inter` (`two_opt_star_inter`)
8. `cross_exchange`

Conjunto **ativo padrao** apos selecao de vizinhancas (usado por `nls`, `vnd`, `grasp` e `tabu`):

1. `relocate_intra`
2. `swap_intra`
3. `relocate_inter`
4. `two_opt_inter`

Para forcar o conjunto completo de 8 no `nls`/`vnd`, use:

```bash
--vnd-neighborhoods all
```

Observação de auditoria:

- a flag `--vnd-neighborhoods` é tratada como configuração global da busca local para `nls`, `vnd`, `grasp` e `tabu`;
- o campo `vnd_neighborhoods` em `logs/execution/*.csv` registra esse conjunto para comparação em pé de igualdade;
- para `tabu`, o CSV também registra `tenure_min`, `tenure_max` e `tabu_tenure_mode` (sempre `fixed` neste protocolo).

## Selecao de vizinhancas (somente NLS)

Para selecionar vizinhancas, use apenas `nls` (busca local) com `first improvement`,
sem comparar heuristicas/metaheuristicas nesta etapa.

Execucao recomendada:

```bash
python3 scripts/run_neighborhood_selection.py \
  --bin bin/vrptw \
  --input-dir input \
  --out results/neighborhood_selection \
  --seed 42 \
  --top-a 5 \
  --phase-b-restart 1 \
  --time-limit 0
```

Regra por fase:

- Fase A: vizinhancas isoladas com `nls_restart=0`.
- Fase B: incremental + ablativa com `nls_restart=1` e ordem por complexidade.

Saidas principais:

- `results/neighborhood_selection/neighborhood_runs.csv` (por instancia/configuracao, com custo real, tempo e numero de veiculos)
- `results/neighborhood_selection/phase_a_summary.csv`
- `results/neighborhood_selection/phase_b_summary.csv`
- `results/neighborhood_selection/recommended_set.csv`
- `results/neighborhood_selection/report.md`

Documentacao metodologica completa: `docs/neighborhood_selection_approach.md`.

## Calibração com irace

Infraestrutura implementada:

- `scripts/irace/target_runner.py` (contrato do irace -> chama `bin/vrptw` e devolve score numerico)
- `scripts/irace/run_irace.py` (orquestrador para os 3 cenarios)
- `scripts/irace/scenario_*.txt` e `scripts/irace/parameters_*.txt`
- `scripts/tuning_set.txt` e `scripts/holdout_set.txt`

Checklist rapido (sem rodar corrida final):

```bash
python3 scripts/irace/run_irace.py --algo tabu_classic --check
python3 scripts/irace/run_irace.py --algo grasp_fixed --check
python3 scripts/irace/run_irace.py --algo grasp_reactive --check
```

Execucao da calibracao (exemplos):

Tabu classico (`tenure`):

```bash
python3 scripts/irace/run_irace.py \
  --algo tabu_classic \
  --instances-file scripts/tuning_set.txt \
  --max-experiments 1000 \
  --time-limit 30 \
  --seed 42
```

GRASP fixo (`alpha`):

```bash
python3 scripts/irace/run_irace.py \
  --algo grasp_fixed \
  --instances-file scripts/tuning_set.txt \
  --max-experiments 1000 \
  --time-limit 30 \
  --seed 42
```

GRASP reativo (`reactive-update`):

```bash
python3 scripts/irace/run_irace.py \
  --algo grasp_reactive \
  --instances-file scripts/tuning_set.txt \
  --max-experiments 1000 \
  --time-limit 30 \
  --seed 42
```

Nota de comparabilidade:

- Use o mesmo `--time-limit` e o mesmo `--vnd-neighborhoods` nos 3 cenarios.
- O runner usa `score = gap_pct + lambda * time_sec` (`lambda` pequeno, default `1e-4`).
- Se quiser criterio estritamente DIMACS no irace, use `--score-lambda 0` e deixe `time_sec` apenas como desempate ex-post.

## Analise de impacto das vizinhancas do VND (selecao 4 de 8)

Gerar execucoes `vnd` para todas as instancias Solomon com seeds `42-51`:

```bash
python3 scripts/run_experiments.py \
  --algos vnd \
  --seeds 42-51 \
  --out results/runs/vnd_impact_all56_seed42_51
```

Consolidar impacto global e por familia (`C`, `R`, `RC`) e gerar relatorio `.md`:

```bash
python3 scripts/summarize_vnd_impact.py \
  --input <RUN_DIR_COM_LOGS_VND> \
  --out results/runs/vnd_impact_all56_seed42_51_current/vnd_impact_summary.csv \
  --out-by-family results/runs/vnd_impact_all56_seed42_51_current/vnd_impact_summary_by_family.csv \
  --report-md results/runs/vnd_impact_all56_seed42_51_current/vnd_impact_report.md
```

Arquivos gerados:

- `results/runs/vnd_impact_all56_seed42_51_current/vnd_impact_summary.csv`
- `results/runs/vnd_impact_all56_seed42_51_current/vnd_impact_summary_by_family.csv`
- `results/runs/vnd_impact_all56_seed42_51_current/vnd_impact_report.md`

Documentacao detalhada: `docs/vnd_impact_analysis.md`
Varredura de aderencia classica + irace: `docs/algorithm_sweep_classical_irace.md`

## Validação (correção / consistência)

Durante o `solve`, toda solução passa por validação (cobertura de clientes, capacidade, janelas de tempo e custo recomputado).

Validar um arquivo `.sol`:

```bash
bin/vrptw validate --instance input/C101.txt --solution solution/C101.sol
```

Validar um run inteiro (gera `validation_report.csv`):

```bash
python3 scripts/validate_run.py --run results/runs/latest_tabu_eval
```

## Output organizado (instância/algoritmo + gráficos)

Gera `output/runs/<run_id>/<INST>/<ALGO>/...` com:
`solution.sol`, `execution.csv`, `convergence.csv` (quando aplicável), `plots/routes.svg`, `plots/convergence.svg` e tabelas agregadas em `_summary/`.

```bash
python3 scripts/make_output.py --out output --seeds 42 --jobs 6
```

## Objetivo

`--objective cost`: minimiza custo total; em empate (tolerância numérica), desempata por menor número de rotas.

Distância/tempo (Solomon): Euclidiana truncada (floor) para 1 casa decimal por aresta (consistente com `solution/*.sol`).
