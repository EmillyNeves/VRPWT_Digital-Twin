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

echo "=== execução: 56 instâncias × 5 algoritmos × $RUNS sementes (jobs=$JOBS) ==="
"$PY" runner.py --algos i1,vnd,tabu,grasp,rgrasp --runs "$RUNS" \
   --solver "$SOLVER" --instances-dir "$INST" --refs-dir "$REFS" \
   --params-file config/tuned.json --jobs "$JOBS" \
   --snapshots-for C101,R101,RC101 \
   --out "$RAW/runs.csv" --sol-dir "$RAW/sol" \
   --trace-dir "$RAW/traces" --snapshots-dir "$RAW/snapshots"

echo "=== agregação + estatística (completo 56 e teste 28) ==="
"$PY" analysis/aggregate.py --runs-csv "$RAW/runs.csv" --out-dir "$ROOT/results"
"$PY" analysis/stats.py --runs-csv "$RAW/runs.csv" --metric gap_pct \
   --out-dir "$ROOT/results" --fig-dir "$FIG" || true
cp "$FIG/cd_diagram.png" "$FIG/cd_diagram_full.png" 2>/dev/null || true
cp "$ROOT/results/nemenyi_pvalues.csv" "$ROOT/results/nemenyi_pvalues_full.csv" 2>/dev/null || true
"$PY" analysis/stats.py --runs-csv "$RAW/runs.csv" --metric gap_pct --instance-list config/test.txt \
   --out-dir "$ROOT/results" --fig-dir "$FIG" || true
cp "$FIG/cd_diagram.png" "$FIG/cd_diagram_test.png" 2>/dev/null || true

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

echo "=== tabela por instância (entra no relatório final) ==="
"$PY" analysis/per_instance_table.py || true

echo "=== ESTUDO COMPLETO ==="
echo "Tabelas: results/overall.csv, results/per_instance.csv, results/gap_by_family.csv"
echo "Figuras: results/figures/"
