#!/usr/bin/env bash
# Espera a recalibração (calibrate.sh) terminar e então dispara o re-run completo
# + análises automaticamente. Pensado para rodar destacado (nohup ... &).
HERE=$(cd "$(dirname "$0")" && pwd)
CALIB_LOG=/tmp/recalibracao.log
STATUS=/tmp/pipeline_status
: > "$STATUS"

echo "[$(date +%H:%M:%S)] aguardando recalibração..." >> "$STATUS"
waited=0
while ! grep -q "CALIBRACAO CONCLUIDA" "$CALIB_LOG" 2>/dev/null; do
  sleep 20; waited=$((waited+20))
  if [ "$waited" -gt 9000 ]; then
    echo "[$(date +%H:%M:%S)] TIMEOUT esperando recalibração (>2.5h); abortando" >> "$STATUS"
    exit 1
  fi
  # se o irace morreu sem concluir, aborta
  if ! pgrep -f "max-experiments" >/dev/null 2>&1 && ! grep -q "CALIBRACAO CONCLUIDA" "$CALIB_LOG" 2>/dev/null; then
    sleep 30
    if ! pgrep -f "max-experiments" >/dev/null 2>&1 && ! grep -q "CALIBRACAO CONCLUIDA" "$CALIB_LOG" 2>/dev/null; then
      echo "[$(date +%H:%M:%S)] recalibração parou sem concluir; abortando re-run" >> "$STATUS"
      exit 1
    fi
  fi
done

echo "[$(date +%H:%M:%S)] recalibração CONCLUÍDA; iniciando re-run completo" >> "$STATUS"
if bash "$HERE/rerun_all.sh" 14 30 > /tmp/rerun.log 2>&1; then
  echo "[$(date +%H:%M:%S)] RE-RUN CONCLUÍDO com sucesso" >> "$STATUS"
  echo "PIPELINE_DONE" >> "$STATUS"
else
  echo "[$(date +%H:%M:%S)] RE-RUN FALHOU (ver /tmp/rerun.log)" >> "$STATUS"
  echo "PIPELINE_FAILED" >> "$STATUS"
fi
