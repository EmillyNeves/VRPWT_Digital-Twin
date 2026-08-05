#!/usr/bin/env bash
# Re-execução completa do estudo sob o NOVO critério de parada (iterações sem
# melhoria) + regeneração de todas as tabelas e figuras.
# Pré-requisito: experiments/config/tuned.json atualizado pela recalibração.
# Uso: bash rerun_all.sh [jobs] [runs]
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
PY="$HERE/.venv/bin/python"
JOBS=${1:-14}
RUNS=${2:-30}

[ -f config/tuned.json ] || { echo "ERRO: config/tuned.json ausente (rode calibrate.sh)"; exit 1; }
echo "=== tuned.json (parâmetros calibrados, incl. K) ==="; cat config/tuned.json; echo

# preserva o estudo antigo (critério de tempo) antes de sobrescrever
[ -f ../results/raw/runs.csv ] && cp ../results/raw/runs.csv ../results/raw/runs_timebudget_backup.csv

echo "=== re-execução: 56 instâncias × 5 algoritmos × $RUNS sementes (jobs=$JOBS) ==="
"$PY" runner.py --algos i1,vnd,tabu,grasp,rgrasp --runs "$RUNS" \
   --params-file config/tuned.json --jobs "$JOBS" \
   --snapshots-for C101,R101,RC101 \
   --out ../results/raw/runs.csv

# NB: os scripts de análise têm defaults relativos a experiments/analysis/; como
# rodamos a partir de experiments/, passamos --out-dir/--fig-dir/--trace-dir EXPLÍCITOS.
FIG=../results/figures
echo "=== agregação + estatística (completo 56 e teste 28) ==="
"$PY" analysis/aggregate.py --runs-csv ../results/raw/runs.csv --out-dir ../results
"$PY" analysis/stats.py --runs-csv ../results/raw/runs.csv --metric gap_pct \
   --out-dir ../results --fig-dir "$FIG" || true
cp "$FIG/cd_diagram.png" "$FIG/cd_diagram_full.png" 2>/dev/null || true
cp ../results/nemenyi_pvalues.csv ../results/nemenyi_pvalues_full.csv 2>/dev/null || true
"$PY" analysis/stats.py --runs-csv ../results/raw/runs.csv --metric gap_pct --instance-list config/test.txt \
   --out-dir ../results --fig-dir "$FIG" || true
cp "$FIG/cd_diagram.png" "$FIG/cd_diagram_test.png" 2>/dev/null || true

echo "=== figuras: convergência + evolução de rotas (por movimento) ==="
"$PY" analysis/plots.py --runs-csv ../results/raw/runs.csv --instance C101 --fig-dir "$FIG" --trace-dir ../results/raw/traces || true
"$PY" analysis/plots.py --runs-csv ../results/raw/runs.csv --instance R101 --fig-dir "$FIG" --trace-dir ../results/raw/traces || true
for I in C101 R101 RC101; do
  "$PY" analysis/route_evolution.py --instance ../input/$I.txt \
     --snapshots ../results/raw/snapshots/vnd_${I}_s1.snap --out-dir "$FIG/evolution" --gif || true
done

echo "=== TTT (lote dedicado, 1 instância representativa) ==="
printf "R101\n" > /tmp/ttt_list.txt
"$PY" runner.py --instance-list /tmp/ttt_list.txt --algos grasp --runs 100 \
   --params-file config/tuned.json --target-gap 0.01 --jobs "$JOBS" \
   --out ../results/raw/runs_ttt.csv --trace-dir ../results/raw/traces || true
REF=$(grep -i cost "../solution (Dinamics)/R101.sol" | awk '{print $NF}')
TARGET=$("$PY" -c "print(f'{float('"$REF"')*1.01:.1f}')")
"$PY" analysis/ttt.py --algo grasp --instance R101 --target-cost "$TARGET" \
   --trace-dir ../results/raw/traces --fig-dir "$FIG" || true

echo "=== RE-EXECUÇÃO COMPLETA ==="
echo "Tabelas: results/overall.csv, results/per_instance.csv, results/gap_by_family.csv"
echo "Figuras: results/figures/"
