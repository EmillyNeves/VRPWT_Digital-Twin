#!/usr/bin/env bash
# ETAPA 1 — Calibração de GRASP, GRASP Reativo e Busca Tabu com irace,
# sobre as instâncias de TREINO (experiments/config/train.txt).
#
# METODOLOGIA DESACOPLADA: o critério de parada K é um ORÇAMENTO DECLARADO
# (experiments/config/fixed_K.json, decisão 3.1b) e NÃO é calibrado; o irace
# calibra apenas os parâmetros de QUALIDADE (alpha / delta,block_frac / tenure).
# K fixo entra via env VRPTW_K (lido pelo target-runner). CPU é só teto de segurança.
#
# Entrada : data/instances/solomon/ + experiments/config/fixed_K.json
# Saída   : results/irace/<algo>/ e experiments/config/tuned.json
#
# Uso: bash experiments/pipelines/1_calibrate.sh [safety_ms] [max_experiments] [parallel]
set -e
SAFETY_MS=${1:-600000}
MAXEXP=${2:-1500}
PAR=${3:-16}

HERE=$(cd "$(dirname "$0")" && pwd)
EXP=$(dirname "$HERE")             # experiments/
ROOT=$(dirname "$EXP")             # raiz do repositório

export R_LIBS="$HOME/R/lib"
IRACE="$HOME/R/lib/irace/bin/irace"
export VRPTW_BUDGET_MS="$SAFETY_MS"   # apenas teto de tempo de segurança

FIXED_K="$EXP/config/fixed_K.json"
[ -f "$FIXED_K" ] || { echo "ERRO: $FIXED_K ausente — ele é versionado; restaure do repositório"; exit 1; }
[ -x "$IRACE" ]   || { echo "ERRO: irace nao encontrado em $IRACE"; exit 1; }
[ -x "$ROOT/solver/build/solve" ] || { echo "ERRO: solver nao compilado. Rode: make -C solver"; exit 1; }

cd "$EXP/irace"
for algo in grasp rgrasp tabu; do
    K=$(python3 -c "import json;print(json.load(open('$FIXED_K'))['$algo'])")
    echo "=== calibrando $algo (K fixo=$K; safety=${SAFETY_MS}ms maxexp=$MAXEXP parallel=$PAR) ==="
    outdir="$ROOT/results/irace/$algo"
    mkdir -p "$outdir"
    # A Busca Tabu nao tem fonte de aleatoriedade: mesma instancia e mesma
    # configuracao dao sempre o mesmo custo. Sem --deterministic 1 o irace gasta
    # orcamento reexecutando o identico com sementes diferentes.
    # (docs/planejamento/irace_parameter_justification.md §1; pre-registro §5)
    DET=(); [ "$algo" = tabu ] && DET=(--deterministic 1)

    VRPTW_ALGO="$algo" VRPTW_K="$K" "$IRACE" \
        --scenario scenario.txt \
        --parameter-file "parameters/$algo.txt" \
        --exec-dir "$outdir" \
        --max-experiments "$MAXEXP" \
        --parallel "$PAR" \
        "${DET[@]}" \
        > "$outdir/irace.log" 2>&1
    echo "   $algo: $(grep -A2 'as commandlines' "$outdir/irace.log" | tail -1)"
done

python3 "$EXP/extract_tuned.py" > "$EXP/config/tuned.json"
echo "=== tuned.json ==="
cat "$EXP/config/tuned.json"
echo "CALIBRACAO CONCLUIDA"
