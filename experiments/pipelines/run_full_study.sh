#!/usr/bin/env bash
# Encadeia o estudo inteiro pelo método DESACOPLADO de parada/calibração:
#   (1) calibra só os parâmetros de qualidade, com K fixo   -> 1_calibrate.sh
#   (2) executa o estudo completo e regenera tabelas/figuras -> 2_run_study.sh
#
# O K fixo vem da análise de joelho (experiments/config/fixed_K.json), que é
# gerada por `python3 experiments/analysis/knee_K.py` a partir de um estudo
# anterior — por isso ela NÃO faz parte desta cadeia.
#
# Pensado para rodar destacado:
#   nohup bash experiments/pipelines/run_full_study.sh > /tmp/full_study.log 2>&1 &
# Acompanhe o progresso em: results/pipeline_status.txt
#
# Uso: bash experiments/pipelines/run_full_study.sh [jobs] [runs] [max_experiments]
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
EXP=$(dirname "$HERE")
ROOT=$(dirname "$EXP")

JOBS=${1:-14}
RUNS=${2:-30}
MAXEXP=${3:-1200}

mkdir -p "$ROOT/results"
STATUS="$ROOT/results/pipeline_status.txt"
: > "$STATUS"
log() { echo "[$(date +%H:%M:%S)] $*" | tee -a "$STATUS"; }

# --- pré-requisitos ---
if [ ! -x "$ROOT/solver/build/solve" ]; then
  log "compilando o solver..."
  make -C "$ROOT/solver" || { log "BUILD FALHOU"; echo PIPELINE_FAILED >> "$STATUS"; exit 1; }
fi
[ -f "$EXP/config/fixed_K.json" ] || {
  log "ERRO: config/fixed_K.json ausente. Rode antes: python3 experiments/analysis/knee_K.py"
  echo PIPELINE_FAILED >> "$STATUS"; exit 1; }
log "K fixo: $(tr -d '\n' < "$EXP/config/fixed_K.json")"

# --- (0) verificação de fidelidade ---
# Nao se calibra o que nao foi verificado: os parametros calibrados descrevem o
# algoritmo IMPLEMENTADO, e se ele nao corresponde ao da literatura a calibracao
# apenas afina o objeto errado.
log "etapa 0/3 — verificação de fidelidade à literatura..."
if bash "$HERE/0_verify.sh" > "$ROOT/results/0_verify.log" 2>&1; then
  log "verificação OK (results/solomon-i1/, results/neighborhoods/)"
else
  log "verificação FALHOU (ver results/0_verify.log)"
  echo PIPELINE_FAILED >> "$STATUS"; exit 1
fi

# --- (1) calibração ---
log "etapa 1/3 — calibrando com irace (só qualidade, K fixo)..."
if bash "$HERE/1_calibrate.sh" 600000 "$MAXEXP" "$JOBS" > "$ROOT/results/1_calibrate.log" 2>&1; then
  log "calibração OK: $(tr -d '\n' < "$EXP/config/tuned.json")"
else
  log "calibração FALHOU (ver results/1_calibrate.log)"
  echo PIPELINE_FAILED >> "$STATUS"; exit 1
fi

# --- (2) estudo completo ---
log "etapa 2/3 — executando o estudo completo (jobs=$JOBS runs=$RUNS)..."
if bash "$HERE/2_run_study.sh" "$JOBS" "$RUNS" > "$ROOT/results/2_run_study.log" 2>&1; then
  log "estudo OK — tabelas em results/*.csv, figuras em results/figures/"
else
  log "estudo FALHOU (ver results/2_run_study.log)"
  echo PIPELINE_FAILED >> "$STATUS"; exit 1
fi

# --- (3) gêmeo digital ---
# Etapas 6 e 7 do cronograma do relatorio parcial. Duas figuras do relatorio
# dependem dele. Nao aborta o pipeline se falhar: o benchmark ja esta pronto.
log "etapa 3/3 — gêmeo digital de Vitória..."
if bash "$HERE/3_digital_twin.sh" > "$ROOT/results/3_digital_twin.log" 2>&1; then
  log "gêmeo digital OK (results/digital_twin/)"
else
  log "gêmeo digital FALHOU (ver results/3_digital_twin.log) -- o benchmark ficou pronto"
fi
echo PIPELINE_DONE >> "$STATUS"
