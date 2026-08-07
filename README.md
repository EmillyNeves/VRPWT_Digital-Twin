# VRPTW — Heurísticas, Metaheurísticas e Gêmeo Digital

Iniciação Científica — UFES.
Roteamento de veículos com janelas de tempo (VRPTW) aplicado ao planejamento
integrado de alocação de contêineres de resíduos e roteamento de veículos.

Solver em C++20 (sem dependências externas) com Solomon I1, VND, GRASP,
GRASP Reativo e Busca Tabu; calibração por **irace**; análise estatística
não-paramétrica; e um **gêmeo digital** da coleta seletiva de Vitória/ES.

---

## Estrutura

```
.
├── solver/                     Solver em C++20 (g++ + make, zero dependências)
│   ├── apps/                   solve.cpp (resolve) e validate.cpp (valida .sol)
│   ├── include/vrptw/          Cabeçalhos — algorithms/ tem I1, VND, GRASP, Tabu
│   ├── src/                    Implementações
│   └── tests/                  15 testes (make -C solver test)
│
├── data/                       ENTRADAS — nada aqui é gerado por script
│   ├── instances/
│   │   ├── solomon/            56 instâncias Solomon-100 (C1/C2/R1/R2/RC1/RC2)
│   │   └── wcvrptw/            10 instâncias reais de coleta de resíduos
│   ├── reference-solutions/
│   │   ├── dinamics/           Melhor-conhecido por MÍNIMA DISTÂNCIA (critério DIMACS)
│   │   └── sintef/             Melhor-conhecido LEXICOGRÁFICO (veículos → distância)
│   └── vitoria/                Malha viária e PEVs de Vitória (cache OSRM/Overpass)
│
├── experiments/                Orquestração dos experimentos
│   ├── config/                 train.txt, test.txt (28+28), tuned.json, fixed_K.json
│   ├── irace/                  Cenário, espaço de parâmetros e target-runner
│   ├── analysis/               Tabelas, figuras e estatística
│   ├── pipelines/              Scripts que encadeiam tudo (ver abaixo)
│   ├── runner.py               Executor em lote do solver → results/raw/
│   ├── split.py                Gera a divisão treino/teste
│   ├── ablation.py             Estudo de ablação das vizinhanças
│   └── extract_tuned.py        Lê os logs do irace → tuned.json
│
├── digital_twin/               Gêmeo digital da coleta seletiva de Vitória
│   ├── twin.py                 Simulação principal
│   ├── maps.py                 Carrega Solomon / WCVRPTW / Vitória
│   ├── road_network.py         Matriz de distância e tempo REAIS (OSRM + Overpass)
│   ├── road_twin.py            Simulação sobre a malha viária real
│   ├── sensors.py              Simulador de enchimento dos contêineres
│   ├── sensitivity.py          Análise de sensibilidade
│   ├── animate.py              Animação das rotas
│   └── dashboard.py            Painel Streamlit
│
├── results/                    SAÍDAS — tudo aqui é gerado; pode apagar e refazer
│   ├── raw/                    Bruto: runs.csv, sol/, traces/, snapshots/
│   ├── figures/                Figuras do relatório
│   ├── irace/                  Logs das corridas do irace
│   ├── digital_twin/           Saídas da simulação
│   └── *.csv                   Tabelas consolidadas (overall, per_instance, ...)
│
└── docs/
    ├── relatorio-final/        ← O QUE ESTÁ SENDO ESCRITO
    ├── template-relatorio-final/  Modelo de formatação exigido (main.tex + topicos/)
    ├── relatorio-parcial/      Relatório parcial já entregue
    ├── planejamento/           Documentos de planejamento e auditoria
    ├── referencias/            PDFs de apoio (Solomon 1987, Glover, Handbook)
    ├── apresentacao/           Slides
    └── rascunhos-antigos/      Versões anteriores do relatório
```

**Regra de ouro:** `data/` é entrada e nunca muda. `results/` é saída e é
inteiramente regenerável. Nada de arquivo gerado dentro de `data/`.

---

## Instalação

```bash
# Solver C++ (só precisa de g++ com C++20)
make -C solver
make -C solver test          # 15 testes

# Ambiente Python (para análise e gêmeo digital)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Para a calibração é preciso, além disso, o **irace** instalado em `~/R/lib/irace`.

---

## Uso

### Resolver uma instância

```bash
solver/build/solve --algo grasp --instance data/instances/solomon/C101.txt \
                   --seed 1 --budget-ms 5000 --out /tmp/C101.sol
```

Algoritmos: `i1` (construtivo), `vnd`, `grasp`, `rgrasp` (reativo), `tabu`.
Saída legível por padrão; use `--csv` para uma linha CSV ou `--print-cost` só para o custo.

### Validar uma solução

O `validate` recebe os dois caminhos **por posição** (diferente do `solve`):

```bash
solver/build/validate data/instances/solomon/C101.txt /tmp/C101.sol
```

Ele refaz as rotas de forma independente e reporta cobertura dos clientes,
capacidade, janelas de tempo, retorno ao depósito e a distância recomputada.

### Estudo completo

Os três scripts em `experiments/pipelines/`:

| Script | O que faz | Saída |
|---|---|---|
| `1_calibrate.sh` | Calibra alpha / delta+block / tenure com irace nas 28 instâncias de treino | `results/irace/`, `config/tuned.json` |
| `2_run_study.sh` | 56 instâncias × 5 algoritmos × 30 sementes + tabelas + figuras | `results/raw/`, `results/*.csv`, `results/figures/` |
| `run_full_study.sh` | Encadeia 1 → 2 | `results/pipeline_status.txt` |

```bash
# tudo de uma vez, destacado do terminal
nohup bash experiments/pipelines/run_full_study.sh 14 30 > /tmp/full_study.log 2>&1 &
tail -f results/pipeline_status.txt
```

Os argumentos são `[jobs] [runs]` — processos concorrentes e sementes por
algoritmo estocástico.

### Gêmeo digital

```bash
cd digital_twin
python twin.py --source vitoria          # simulação
streamlit run dashboard.py               # painel interativo
```

---

## Metodologia

**Divisão treino/teste.** As 56 instâncias são divididas 28/28
(`experiments/config/train.txt` e `test.txt`), estratificadas por família.
A calibração usa **só** o treino; os resultados reportados usam o teste.

**Critério de parada desacoplado.** O K (iterações sem melhoria) é *fixado*
pela análise de joelho da curva de convergência
(`analysis/knee_K.py` → `config/fixed_K.json`), e **não** é calibrado junto com
os demais parâmetros. O irace então calibra apenas os parâmetros de qualidade,
com todos os algoritmos parando pelo mesmo critério — comparação em pé de
igualdade. O tempo (`--budget-ms`) é só teto de segurança.

Valores atuais: `grasp` K=250, `rgrasp` K=250, `tabu` K=1400.
O raciocínio completo está em [experiments/TUNING_RATIONALE.md](experiments/TUNING_RATIONALE.md).

**Duas baselines.** As instâncias Solomon têm duas referências distintas e
incomparáveis entre si:
- `data/reference-solutions/dinamics/` — mínima **distância** (critério DIMACS);
  é a usada para calcular o `gap_pct`.
- `data/reference-solutions/sintef/` — mínimo **lexicográfico** (primeiro
  veículos, depois distância). Rotas mais longas, menos veículos.

`analysis/baseline_compare.py` documenta a diferença.

**Estatística.** Teste de Friedman seguido de pós-teste de Nemenyi
(Demšar, 2006), com diagrama de diferença crítica. Reportado para as 56
instâncias e só para as 28 de teste.

---

## Relatório final

O que vai ser escrito fica em `docs/relatorio-final/`:

- `relatorio-final.tex` — o texto (puxa figuras de `../../results/figures/`)
- `tabela_por_instancia.tex` — gerado por `analysis/per_instance_table.py`
- `biblio.bib` — bibliografia

O **formato exigido** está em `docs/template-relatorio-final/`: um `main.tex`
modular que inclui `topicos/{resumo,introducao,objetivos,embasamento_teorico,
metodologia,resultados,conclusao,agradecimentos}.tex`, com o estilo
`hapalike2-NOand.bst`. O `docs/template-relatorio-final/exemplo/` traz um
relatório completo de exemplo.

```bash
cd docs/relatorio-final && pdflatex relatorio-final && bibtex relatorio-final && pdflatex relatorio-final
```

> As figuras referenciadas pelo `.tex` só existem depois de rodar
> `experiments/pipelines/2_run_study.sh`.
