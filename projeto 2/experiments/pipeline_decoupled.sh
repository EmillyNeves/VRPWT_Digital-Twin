#!/usr/bin/env bash
# Encadeia o método DESACOPLADO de parada/calibração:
#   (1) espera a análise de joelho (config/fixed_K.json) terminar;
#   (2) recalibra SÓ os parâmetros de qualidade ao K fixo (calibrate.sh);
#   (3) re-executa o estudo completo e regenera tabelas/figuras (rerun_all.sh).
# Pensado para rodar destacado (nohup ... &). Status em /tmp/pipeline_decoupled_status.
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
STATUS=/tmp/pipeline_decoupled_status
: > "$STATUS"

echo "[$(date +%H:%M:%S)] aguardando joelho (config/fixed_K.json)..." >> "$STATUS"
waited=0
while [ ! -f config/fixed_K.json ]; do
  sleep 15; waited=$((waited+15))
  [ "$waited" -gt 5400 ] && { echo "[$(date +%H:%M:%S)] TIMEOUT joelho" >> "$STATUS"; exit 1; }
done
echo "[$(date +%H:%M:%S)] joelho OK: $(cat config/fixed_K.json | tr -d '\n')" >> "$STATUS"

# preserva o estudo anterior (K conjunto) antes de sobrescrever
[ -f ../results/raw/runs.csv ] && cp ../results/raw/runs.csv ../results/raw/runs_jointK_backup.csv

echo "[$(date +%H:%M:%S)] recalibrando (só qualidade, K fixo)..." >> "$STATUS"
if bash calibrate.sh 600000 1200 14 > /tmp/recalib_decoupled.log 2>&1; then
  echo "[$(date +%H:%M:%S)] recalibração OK: $(tr -d '\n' < config/tuned.json)" >> "$STATUS"
else
  echo "[$(date +%H:%M:%S)] recalibração FALHOU (ver /tmp/recalib_decoupled.log)" >> "$STATUS"; exit 1
fi

echo "[$(date +%H:%M:%S)] re-executando o estudo completo..." >> "$STATUS"
if bash rerun_all.sh 14 30 > /tmp/rerun_decoupled.log 2>&1; then
  echo "[$(date +%H:%M:%S)] RE-RUN OK" >> "$STATUS"
  echo "PIPELINE_DONE" >> "$STATUS"
else
  echo "[$(date +%H:%M:%S)] RE-RUN FALHOU (ver /tmp/rerun_decoupled.log)" >> "$STATUS"
  echo "PIPELINE_FAILED" >> "$STATUS"
fi
