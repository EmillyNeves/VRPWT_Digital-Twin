# Verificação 04 — Critério de parada (iterações sem melhoria)

**Estado:** 🟡 corretamente implementado; **não** equaliza esforço, e o relatório precisa dizer isso
**Artefatos:** `results/{equal_time,primal_integral}.csv` · colunas `time_to_best_ms` e `useful_pct_mean` em `per_instance.csv`

---

## 1. Como está implementado

O critério primário é o número de iterações consecutivas **sem melhorar o incumbente** (K). O mecanismo é idêntico nos três métodos que o usam:

```cpp
if (novo < melhor - 1e-9) { melhor = novo; no_improve = 0; }
else                      { ++no_improve; }
++iter;
if (K >= 0 && no_improve >= K) break;
```

`solver/src/Grasp.cpp` e `solver/src/TabuSearch.cpp` — mesma semântica, mesma tolerância (1e-9). O VND e a I1 **não** usam K: terminam naturalmente, o VND num ótimo local com relação a todas as vizinhanças e a I1 quando todos os clientes estão roteados. O tempo (`--budget-ms`) é apenas teto de segurança.

**Veredito: a implementação está correta.** Nenhuma discrepância entre os métodos.

O que muda entre eles é a **unidade**: uma iteração do GRASP é uma construção seguida de um VND completo (~60 ms); uma iteração da Tabu é **um movimento** (~4 ms). Por isso o K é fixado por método (250 e 1400), pela análise de convergência.

---

## 2. Mas não equaliza esforço

Medição com os parâmetros calibrados, uma semente:

| Instância | Método | iters | melhorias | tempo | até o melhor | útil |
|---|---|---|---|---|---|---|
| C101 | GRASP | 251 | 1 | 2,4 s | 0,0 s | **0 %** |
| C101 | Reativo | 251 | 1 | 5,1 s | 0,0 s | **0 %** |
| C101 | Tabu | 1406 | 6 | 13,5 s | 0,0 s | **0 %** |
| R101 | GRASP | 263 | 4 | 4,5 s | 0,2 s | 4 % |
| R101 | Reativo | 629 | 8 | 10,8 s | 6,5 s | 60 % |
| R101 | Tabu | 1428 | 28 | 5,6 s | 0,1 s | 2 % |
| R201 | GRASP | 474 | 10 | 21,2 s | 10,0 s | 47 % |
| R201 | Tabu | 2296 | 65 | 15,3 s | 5,9 s | 39 % |
| RC205 | GRASP | 415 | 5 | 20,8 s | 8,0 s | 38 % |
| RC205 | Tabu | 1785 | 87 | 12,1 s | 2,6 s | 21 % |

**2.1 — Em C101 os três encontram a melhor solução no instante zero** e depois queimam 2,4 s, 5,1 s e 13,5 s sem produzir nada. A I1 seguida de VND já entrega 827,3, que é o melhor conhecido. Ali o K mede paciência, não busca.

**2.2 — A fração útil difere sistematicamente por método:** GRASP 37 %, Reativo 49 %, **Tabu 17 %**. A Tabu desperdiça proporcionalmente o dobro, e o tempo total dela é o que menos representa busca efetiva.

**2.3 — A razão de tempo entre métodos inverte de instância para instância:**

| | C101 | R101 | R201 | RC101 | RC205 |
|---|---|---|---|---|---|
| Tabu / GRASP | **5,62×** | 1,24× | 0,72× | 0,77× | **0,58×** |

Variação de quase 10× na razão. **Nenhuma afirmação do tipo "a Busca Tabu responde mais rápido" sobrevive a isto** — depende inteiramente da instância.

---

## 3. Consequências para o relatório

**Retirar a alegação de "comparação em pé de igualdade"** do `README.md`. O K não é critério de igualdade de esforço.

**A formulação correta:** *"cada método executa até a própria curva de convergência achatar"* — normalização por convergência, não por orçamento. É defensável, e a escolha se justifica pela **reprodutibilidade**: uma parada por tempo depende da máquina, uma parada por iterações não.

**Acompanhada dos números da Seção 2.** Declarar o critério sem mostrar a dispersão da fração útil seria omitir o que enfraquece a alegação.

---

## 4. A leitura complementar, que passa a ser obrigatória

O `primal_integral_experiment.py` roda todos os métodos sob **orçamento de tempo idêntico** (T = 20 s), com o K **desativado**, nas 28 instâncias de teste e com **sementes uniformes** (10 para os estocásticos; VND e Tabu são determinísticos). Duas saídas:

- **`results/equal_time.csv`** — qualidade final sob tempo igual. Responde "com o mesmo relógio, quem chega mais longe?".
- **`results/primal_integral.csv`** — a integral primal de Berthold, que é o **critério oficial de pontuação do 12º Desafio DIMACS** e mede qualidade ao longo do tempo, não apenas no fim.

Duas correções em relação à versão anterior:

| Antes | Agora |
|---|---|
| 3 instâncias (R101, RC101, R201) | 28 instâncias de teste |
| réplicas 5/5/1/1 | 10/10/1/1 — uniformes entre os estocásticos |
| sequencial (~3,3 h) | paralelo, 14 processos (~15 min) |

Réplicas desiguais não podem entrar numa comparação: dar cinco amostras ao GRASP e uma à Tabu enviesa qualquer média.

**A integral primal deixa de ser "análise complementar" e passa a resultado principal.** É o único instrumento do estudo que fala a língua da competição cujo critério de distância o trabalho adota.

---

## 5. Instrumentação incorporada

Para que a Seção 2 seja reproduzível a cada execução, e não uma medição avulsa:

| Coluna | Onde | O que é |
|---|---|---|
| `iters` | `raw/runs.csv` | iterações realizadas |
| `improvements` | `raw/runs.csv` | quantas delas melhoraram o incumbente |
| `time_to_best_ms` | `raw/runs.csv` | instante em que a melhor solução apareceu |
| `useful_pct_mean` | `per_instance.csv`, `overall.csv` | `time_to_best / time_total` |

`improvements` e `time_to_best_ms` são lidos da curva de convergência que o solver já gravava (`--trace`) e que ninguém agregava.
