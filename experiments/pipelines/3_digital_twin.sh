#!/usr/bin/env bash
# ETAPA 3 — Gêmeo digital da coleta seletiva de Vitória/ES.
#
# Produz as duas figuras do capítulo de aplicação do relatório. Usa a malha
# viária REAL já cacheada em data/vitoria/ (matrizes de distância e tempo do
# OSRM + geometria das ruas da Overpass), portanto NÃO depende de rede.
#
# Entrada : data/vitoria/, solver compilado, experiments/config/tuned.json
# Saída   : results/digital_twin/vitoria/vitoria_road_routes.png
#           results/digital_twin/sensitivity.{png,csv}
#
# Uso: bash experiments/pipelines/3_digital_twin.sh [algo] [ciclos]
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
EXP=$(dirname "$HERE")
ROOT=$(dirname "$EXP")

PY=${VRPTW_PY:-$([ -x "$ROOT/.venv/bin/python" ] && echo "$ROOT/.venv/bin/python" || echo python3)}
ALGO=${1:-grasp}
CYCLES=${2:-16}

[ -x "$ROOT/solver/build/solve" ] || { echo "ERRO: solver nao compilado. Rode: make -C solver"; exit 1; }
[ -f "$ROOT/data/vitoria/vitoria_road_matrix.json" ] || {
  echo "ERRO: cache da malha viaria ausente em data/vitoria/."
  echo "      Regenere com: cd digital_twin && $PY road_network.py   (requer rede)"; exit 1; }

mkdir -p "$ROOT/results/digital_twin/vitoria"
cd "$ROOT/digital_twin"

echo "=== rotas sobre a malha viária real de Vitória (algo=$ALGO) ==="
"$PY" road_twin.py --algo "$ALGO"

echo "=== análise de sensibilidade ($CYCLES ciclos) ==="
"$PY" sensitivity.py --algo "$ALGO" --cycles "$CYCLES"

echo "=== GÊMEO DIGITAL CONCLUÍDO ==="
echo "Figuras: results/digital_twin/vitoria/vitoria_road_routes.png"
echo "         results/digital_twin/sensitivity.png"
echo "Dados  : results/digital_twin/sensitivity.csv"
echo
echo "RESSALVA: o PLANO-RELATORIO-FINAL lista quatro correções pendentes no"
echo "gêmeo digital (KPI de transbordo, >=30 sementes, parâmetros calibrados nos"
echo "dois regimes, horizonte). Estas figuras saem com os defeitos conhecidos."
