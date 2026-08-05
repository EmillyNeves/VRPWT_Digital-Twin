#!/usr/bin/env bash
# Calibrate GRASP, Reactive GRASP and Tabu with irace on the TRAIN instances.
# METODOLOGIA DESACOPLADA: o critério de parada K é FIXADO pela análise de
# convergência (joelho; experiments/config/fixed_K.json) e NÃO é calibrado; o
# irace calibra apenas os parâmetros de QUALIDADE (alpha / delta,block / tenure).
# K fixo entra via env VRPTW_K (lido pelo target-runner). CPU é só teto de segurança.
# Usage: bash calibrate.sh [safety_ms] [max_experiments] [parallel]
set -e
SAFETY_MS=${1:-600000}
MAXEXP=${2:-1500}
PAR=${3:-16}

HERE=$(cd "$(dirname "$0")" && pwd)
export R_LIBS="$HOME/R/lib"
IRACE="$HOME/R/lib/irace/bin/irace"
export VRPTW_BUDGET_MS="$SAFETY_MS"   # safety time cap only
FIXED_K="$HERE/config/fixed_K.json"
[ -f "$FIXED_K" ] || { echo "ERRO: $FIXED_K ausente (rode analysis/knee_K.py primeiro)"; exit 1; }

cd "$HERE/irace"
for algo in grasp rgrasp tabu; do
    K=$(python3 -c "import json;print(json.load(open('$FIXED_K'))['$algo'])")
    echo "=== calibrando $algo (K fixo=$K; safety=${SAFETY_MS}ms maxexp=$MAXEXP parallel=$PAR) ==="
    outdir="$HERE/../results/irace/$algo"
    mkdir -p "$outdir"
    VRPTW_ALGO="$algo" VRPTW_K="$K" "$IRACE" \
        --scenario scenario.txt \
        --parameter-file "parameters/$algo.txt" \
        --exec-dir "$outdir" \
        --max-experiments "$MAXEXP" \
        --parallel "$PAR" \
        > "$outdir/irace.log" 2>&1
    echo "   $algo: $(grep -A2 'as commandlines' "$outdir/irace.log" | tail -1)"
done

python3 "$HERE/extract_tuned.py" > "$HERE/config/tuned.json"
echo "=== tuned.json ==="
cat "$HERE/config/tuned.json"
echo "CALIBRACAO CONCLUIDA"
