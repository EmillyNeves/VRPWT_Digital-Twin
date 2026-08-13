# Especificação de saídas

Toda afirmação numérica do relatório precisa de um artefato que a sustente. Este documento mapeia **seção do relatório → artefato → script que o produz → do que ele depende**.

**Regra:** nenhum número escrito à mão no `.tex`. Tabelas entram por `\input{}`, figuras por `\includegraphics{}`, e ambas saem de arquivos em `results/`.

---

## Layout

```
results/
├── raw/                        bruto — regenerável, FORA do git (.gitignore)
│   ├── runs.csv                mestre: algoritmo × instância × semente
│   ├── runs_ttt.csv            lote dedicado do time-to-target
│   ├── sol/                    solução final de cada execução
│   ├── traces/                 curva de convergência de cada execução
│   └── snapshots/              estado por movimento (evolução de rotas)
├── figures/                    figuras do relatório
│   └── evolution/              quadros da evolução de rotas
├── irace/                      logs de calibração — FORA do git
├── digital_twin/               saídas da simulação
├── solomon-i1/                 verificação de fidelidade da I1 (Etapa 1)
├── neighborhoods/              ablação das vizinhanças (Etapa 3)
└── *.csv                       tabelas consolidadas — versionadas
```

`results/raw/` e `results/irace/` estão no `.gitignore` por volume. **Todo o resto é versionado** — é o que torna os números auditáveis a partir de um clone limpo.

---

## Mapa: relatório → artefato → script

### Metodologia

| Seção | Artefato | Script | Depende de |
|---|---|---|---|
| Ilustração dos operadores | `figures/operadores.png` | `analysis/algo_figures.py` | — (didática, autocontida) |
| Construção da I1 passo a passo | `figures/construcao_i1.png` | `analysis/algo_figures.py` | — |
| RCL do GRASP | `figures/grasp_rcl.png` | `analysis/algo_figures.py` | — |
| Sustentação do orçamento K | `stopping/convergence.csv`, `stopping/cost.csv`, `stopping/budget_K.tex` | `analysis/stopping_budget.py`, `analysis/stopping_cost.py` | solver + treino |
| Guarda do método de medição de K | placar derivado × executado | `analysis/stopping_derivation_check.py` | solver |
| Calibração (parâmetros e proveniência) | `irace/<algo>/irace.log`, `config/tuned.json` | `pipelines/1_calibrate.sh` | `config/fixed_K.json` |

### Verificação de fidelidade

| Seção | Artefato | Script | Depende de |
|---|---|---|---|
| I1 × Tabelas I–VI de Solomon | `solomon-i1/i1_configs.csv`, `tables_I_VI.csv` | `analysis/solomon_i1_tables.py` | solver |
| Seleção das vizinhanças | `neighborhoods/ablation.csv`, `summary.csv` | `analysis/neighborhood_ablation.py` | solver + treino |
| Convenção de distância (56/56) | saída de `make -C solver test` | `tests/test_evaluator_refs.cpp` | referências |

### Resultados

| Seção | Artefato | Script | Depende de |
|---|---|---|---|
| Dados brutos | `raw/runs.csv` | `runner.py` | solver + `tuned.json` |
| Resumo geral | `overall.csv` | `analysis/aggregate.py` | `runs.csv` |
| Por instância | `per_instance.csv` | `analysis/aggregate.py` | `runs.csv` |
| Por família | `gap_by_family.csv` | `analysis/aggregate.py` | `runs.csv` |
| Apêndice por instância | `docs/relatorio-final/tabela_por_instancia.tex` | `analysis/per_instance_table.py` | `per_instance.csv` |
| Friedman + Nemenyi, diagrama CD | `nemenyi_pvalues.csv`, `figures/cd_diagram*.png` | `analysis/stats.py` | `runs.csv` |
| **Wilcoxon pareado + Holm** | saída de `stats_paired.py` | `analysis/stats_paired.py` | **`tabela_por_instancia.tex`** |
| Convergência | `figures/convergence_<inst>.png` | `analysis/plots.py` | `runs.csv` + `traces/` |
| Evolução de rotas | `figures/evolution/evolution_<inst>.png` | `analysis/route_evolution.py` | `snapshots/` |
| Time-to-target | `figures/ttt_grasp_<inst>.png` | `analysis/ttt.py` | `traces/` |
| Integral primal (critério DIMACS) | `primal_integral.csv`, `figures/primal_integral.png`, `figures/anytime_convergence_<inst>.png` | `primal_integral_experiment.py` | solver |
| Caracterização das duas referências | `baseline_compare.csv` | `analysis/baseline_compare.py` | referências |
| Tabela lexicográfica | `lexicographic_table.csv` | `analysis/lexicographic_table.py` | `per_instance.csv` + `baseline_compare.csv` |

### Digital Twin

| Seção | Artefato | Script | Depende de |
|---|---|---|---|
| Rotas na malha viária real | `digital_twin/vitoria/vitoria_road_routes.png` | `digital_twin/road_twin.py` | `data/vitoria/` (cacheado) |
| Análise de sensibilidade | `digital_twin/sensitivity.{png,csv}` | `digital_twin/sensitivity.py` | `data/vitoria/` |

---

## Duas dependências de ordem que já causaram erro

**`stats_paired.py` lê `tabela_por_instancia.tex`, não `runs.csv`.** Ele tem que rodar **depois** de `per_instance_table.py`. Rodando antes, ele analisa a tabela da execução anterior e produz números plausíveis e errados, sem qualquer aviso.

**`lexicographic_table.py` precisa de `baseline_compare.csv`**, que só existe se `baseline_compare.py` tiver rodado.

---

## Ordem de execução

```
independentes (a qualquer momento)
  analysis/algo_figures.py            figuras didáticas
  analysis/baseline_compare.py        caracteriza dinamics × sintef
  analysis/solomon_i1_tables.py       verificação da I1
  analysis/neighborhood_ablation.py   ablação das vizinhanças

calibração
  analysis/stopping_budget.py         -> results/stopping/convergence.csv
  analysis/stopping_cost.py           -> results/stopping/cost.csv
  pipelines/1_calibrate.sh            -> irace/, config/tuned.json
  (config/fixed_K.json é versionado, não gerado — decisão 3.1b)

estudo
  runner.py                           -> raw/runs.csv, sol/, traces/, snapshots/
  analysis/aggregate.py               -> overall, per_instance, gap_by_family
  analysis/per_instance_table.py      -> tabela_por_instancia.tex
  analysis/stats.py                   -> nemenyi_pvalues, cd_diagram
  analysis/stats_paired.py            -> Wilcoxon + Holm      [depois do per_instance_table]
  analysis/lexicographic_table.py     -> lexicographic_table  [depois do baseline_compare]
  analysis/plots.py                   -> convergence
  analysis/route_evolution.py         -> evolution
  analysis/ttt.py                     -> ttt
  primal_integral_experiment.py       -> primal_integral, anytime_convergence

gêmeo digital
  digital_twin/road_twin.py
  digital_twin/sensitivity.py
```

---

## Estado

O `pipelines/2_run_study.sh` chamava **seis** dos catorze scripts. Oito das doze figuras que o `relatorio-final.tex` referencia não eram produzidas — rodar o pipeline deixava o relatório sem compilar. A ordem acima está implementada em `pipelines/2_run_study.sh` (estudo) e `pipelines/3_digital_twin.sh` (gêmeo digital).
