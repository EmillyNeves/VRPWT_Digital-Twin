#!/usr/bin/env bash
# ETAPA 2 — Estudo completo sob o critério de parada por iterações sem melhoria,
# + regeneração de todas as tabelas e figuras do relatório.
#
# Pré-requisito: experiments/config/tuned.json (gerado pela etapa 1_calibrate.sh).
#
# Entrada : data/instances/solomon/, data/reference-solutions/dinamics/, config/tuned.json
# Saída   : results/raw/ (bruto), results/*.csv (tabelas), results/figures/ (figuras)
#
# Uso: bash experiments/pipelines/2_run_study.sh [jobs] [runs]
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
EXP=$(dirname "$HERE")             # experiments/
ROOT=$(dirname "$EXP")             # raiz do repositório
cd "$EXP"

# Python: usa o .venv da raiz se existir, senão o python3 do sistema.
# Sobrescreva com: VRPTW_PY=/caminho/do/python bash experiments/pipelines/2_run_study.sh
PY=${VRPTW_PY:-$([ -x "$ROOT/.venv/bin/python" ] && echo "$ROOT/.venv/bin/python" || echo python3)}
JOBS=${1:-14}
RUNS=${2:-30}

SOLVER="$ROOT/solver/build/solve"
[ -x "$SOLVER" ]          || { echo "ERRO: solver nao compilado. Rode: make -C solver"; exit 1; }
[ -f config/tuned.json ]  || { echo "ERRO: config/tuned.json ausente (rode 1_calibrate.sh)"; exit 1; }
echo "=== tuned.json (parâmetros calibrados, incl. K) ==="; cat config/tuned.json; echo

INST="$ROOT/data/instances/solomon"
REFS="$ROOT/data/reference-solutions/dinamics"
RAW="$ROOT/results/raw"
FIG="$ROOT/results/figures"
mkdir -p "$RAW/sol" "$RAW/traces" "$RAW/snapshots" "$FIG/evolution"

# preserva o estudo anterior antes de sobrescrever
[ -f "$RAW/runs.csv" ] && cp "$RAW/runs.csv" "$RAW/runs_backup.csv"

# ---- independentes dos dados de execução: podem rodar já -------------------
echo "=== ambiente de execução (reprodutibilidade) ==="
"$PY" analysis/environment.py > /dev/null && echo "  results/environment.{json,tex}"

echo "=== figuras didáticas + caracterização das referências ==="
"$PY" analysis/algo_figures.py || true          # operadores, construcao_i1, grasp_rcl
"$PY" analysis/baseline_compare.py || true      # baseline_compare.csv (dinamics x sintef)

echo "=== execução: 56 instâncias × 5 algoritmos × $RUNS sementes (jobs=$JOBS) ==="
"$PY" runner.py --algos i1,vnd,tabu,grasp,rgrasp --runs "$RUNS" \
   --solver "$SOLVER" --instances-dir "$INST" --refs-dir "$REFS" \
   --params-file config/tuned.json --jobs "$JOBS" \
   --snapshots-for C101,R101,RC101 \
   --out "$RAW/runs.csv" --sol-dir "$RAW/sol" \
   --trace-dir "$RAW/traces" --snapshots-dir "$RAW/snapshots"

echo "=== agregação ==="
"$PY" analysis/aggregate.py --runs-csv "$RAW/runs.csv" --out-dir "$ROOT/results"

# ORDEM OBRIGATÓRIA: stats_paired.py lê tabela_por_instancia.tex, não runs.csv.
# Rodando antes de per_instance_table.py ele analisa a tabela da execução
# ANTERIOR e devolve números plausíveis e errados, sem aviso. Ver docs/SAIDAS.md.
echo "=== tabela por instância (entra no apêndice e alimenta o Wilcoxon) ==="
"$PY" analysis/per_instance_table.py

echo "=== estatística: Friedman + Nemenyi (completo 56 e teste 28) ==="
"$PY" analysis/stats.py --runs-csv "$RAW/runs.csv" --metric gap_pct \
   --out-dir "$ROOT/results" --fig-dir "$FIG" || true
cp "$FIG/cd_diagram.png" "$FIG/cd_diagram_full.png" 2>/dev/null || true
cp "$ROOT/results/nemenyi_pvalues.csv" "$ROOT/results/nemenyi_pvalues_full.csv" 2>/dev/null || true
"$PY" analysis/stats.py --runs-csv "$RAW/runs.csv" --metric gap_pct --instance-list config/test.txt \
   --out-dir "$ROOT/results" --fig-dir "$FIG" || true
cp "$FIG/cd_diagram.png" "$FIG/cd_diagram_test.png" 2>/dev/null || true

echo "=== estatística: Wilcoxon pareado + Holm (não depende do conjunto de algoritmos) ==="
"$PY" analysis/stats_paired.py | tee "$ROOT/results/stats_paired.txt" || true

echo "=== prova de viabilidade: janelas de tempo e capacidade, com as margens ==="
"$PY" analysis/validation_report.py --sol-dir "$RAW/sol" --out-dir "$ROOT/results"

echo "=== tabela lexicográfica (veículos -> distância) ==="
"$PY" analysis/lexicographic_table.py || true

# Leitura complementar e OBRIGATORIA: sob a parada por iteracoes sem melhoria,
# cada metodo gasta de 0% a 60% do tempo produzindo (medido em
# docs/verificacao/04-criterio-de-parada.md) e a razao de tempo entre metodos
# inverte de instancia para instancia. A integral primal e a qualidade final sob
# TEMPO IGUAL sao o que responde a pergunta de esforco que o K nao responde.
echo "=== tempo igual + integral primal (criterio de pontuacao do 12o DIMACS) ==="
"$PY" primal_integral_experiment.py --instances-file config/test.txt \
   --budget-ms 20000 --runs 10 --jobs "$JOBS" || true

echo "=== figuras: convergência + evolução de rotas (por movimento) ==="
for I in C101 R101; do
  "$PY" analysis/plots.py --runs-csv "$RAW/runs.csv" --instance "$I" \
     --fig-dir "$FIG" --trace-dir "$RAW/traces" || true
done
for I in C101 R101 RC101; do
  "$PY" analysis/route_evolution.py --instance "$INST/$I.txt" \
     --snapshots "$RAW/snapshots/vnd_${I}_s1.snap" --out-dir "$FIG/evolution" --gif || true
done

echo "=== TTT (lote dedicado, 1 instância representativa) ==="
TTT_LIST=$(mktemp); printf "R101\n" > "$TTT_LIST"
"$PY" runner.py --instance-list "$TTT_LIST" --algos grasp --runs 100 \
   --solver "$SOLVER" --instances-dir "$INST" --refs-dir "$REFS" \
   --params-file config/tuned.json --target-gap 0.01 --jobs "$JOBS" \
   --out "$RAW/runs_ttt.csv" --sol-dir "$RAW/sol" --trace-dir "$RAW/traces" || true
rm -f "$TTT_LIST"
REF=$(grep -i cost "$REFS/R101.sol" | awk '{print $NF}')
TARGET=$("$PY" -c "print(f'{float('"$REF"')*1.01:.1f}')")
"$PY" analysis/ttt.py --algo grasp --instance R101 --target-cost "$TARGET" \
   --trace-dir "$RAW/traces" --fig-dir "$FIG" || true

echo "=== ESTUDO COMPLETO ==="
echo "Tabelas : results/{overall,per_instance,gap_by_family,lexicographic_table,primal_integral}.csv"
echo "          results/{nemenyi_pvalues,baseline_compare}.csv, results/stats_paired.txt"
echo "Viabil. : results/{validation_summary,validation_routes}.csv"
echo "Generz. : results/generalization.csv (treino x teste), results/run_counts.csv"
echo "Esforco : results/{equal_time,primal_integral}.csv"
echo "Ambiente: results/environment.{json,tex}"
echo
echo "A tabela default x calibrado NAO entra aqui (custa outra rodada). Depois:"
echo "  .venv/bin/python experiments/analysis/calibration_gain.py"
echo "Figuras : results/figures/  (ver docs/SAIDAS.md para o mapa completo)"
echo "Apendice: docs/relatorio-final/tabela_por_instancia.tex"
echo
echo "Falta ainda o gemeo digital: bash experiments/pipelines/3_digital_twin.sh"
