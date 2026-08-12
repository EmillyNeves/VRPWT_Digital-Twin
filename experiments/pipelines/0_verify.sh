#!/usr/bin/env bash
# ETAPA 0 — Verificação de fidelidade à literatura.
#
# Confronta cada algoritmo com a fonte que ele diz implementar. É diferente de
# validar o AVALIADOR (que os testes já fazem, reproduzindo os 56 custos de
# referência): aqui se pergunta se o ALGORITMO é o do artigo.
#
# Roda ANTES da calibração: não faz sentido calibrar parâmetros de uma
# implementação cuja fidelidade não foi estabelecida.
#
# Saída : results/solomon-i1/{i1_configs,tables_I_VI}.csv
#         results/neighborhoods/{ablation,summary}.csv
#         docs/verificacao/*.md (escritos à mão, alimentados por estes CSVs)
#
# Uso: bash experiments/pipelines/0_verify.sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
EXP=$(dirname "$HERE")
ROOT=$(dirname "$EXP")
PY=${VRPTW_PY:-$([ -x "$ROOT/.venv/bin/python" ] && echo "$ROOT/.venv/bin/python" || echo python3)}
cd "$EXP"

echo "=== suíte de testes (inclui o portão das 56 referências) ==="
make -C "$ROOT/solver" test 2>&1 | tail -3

echo "=== I1 × Tabelas I–VI de Solomon (1987) ==="
"$PY" analysis/solomon_i1_tables.py

echo "=== seleção do conjunto de vizinhanças (ablação com Wilcoxon + Holm) ==="
"$PY" analysis/neighborhood_ablation.py

echo "=== VERIFICAÇÃO CONCLUÍDA ==="
echo "Artefatos: results/solomon-i1/, results/neighborhoods/"
echo "Leitura  : docs/verificacao/README.md"
