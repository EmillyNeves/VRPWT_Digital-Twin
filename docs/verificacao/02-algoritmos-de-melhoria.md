# Verificação 02 — VND, GRASP, GRASP reativo e Busca Tabu

**Estado:** 🟡 três reproduzidos; o GRASP reativo está degenerado *na configuração calibrada*
**Testes:** `solver/tests/test_algorithms_fidelity.cpp` (4 testes; suíte total 27)

Princípio: um teste por algoritmo, cobrindo a **propriedade estrutural** que a fonte garante e que independe da qualidade da solução.

---

## VND — Hansen & Mladenović (2001) 🟢

**Propriedade.** O VND termina em um ótimo local com relação a **todas** as vizinhanças, não apenas à última. É a definição do método.

**Teste.** Após `vnd_local_search`, procurar movimento melhorante em cada uma das 5 vizinhanças e exigir que não exista.

**Resultado: 56/56.** Nenhuma instância termina com movimento melhorante pendente.

> Isto **nunca havia sido testado**. O `test_vnd.cpp` existente só verifica monotonicidade (o VND não piora a solução), que é bem mais fraco — uma implementação que parasse na primeira vizinhança sem melhora passaria nele.

---

## GRASP — Feo & Resende (1995) 🟢

**Propriedade.** Com α = 0 a RCL colapsa no argmax de c₂ e a construção gulosa-aleatorizada degenera na construção gulosa pura — que neste projeto é a I1.

**Teste.** Comparar `grasp_construct(α=0)` com `solomon_i1()` nas 56. Onde divergirem, a única fonte legítima é o RNG escolhendo entre candidatos **empatados** no argmax; isso se confirma variando a semente.

**Resultado: 47/56 idênticas, 9 divergentes por empate confirmado, 0 inexplicadas.**

O critério do teste é `identical + seed_dependent == 56`, não um limiar arbitrário: **toda divergência tem que ter explicação**. A primeira versão usava "≥ 50 idênticas", reprovou com 47, e o limiar não foi afrouxado — a causa foi investigada.

---

## Busca Tabu — Glover (1989/1990) 🟡

**Propriedades testadas.** (a) O método devolve o **melhor incumbente**, nunca o último visitado — é o que justifica aceitar movimentos de piora. (b) O *tenure* proíbe o atributo pelo número de iterações declarado.

**Resultado (a): 5/5.** Nunca pior que a solução de partida.

**Resultado (b): off-by-one confirmado.** `TabuSearch.cpp` grava `tabu_until[c] = iter + tenure` e testa `tabu_until > iter'`; como `iter` só incrementa depois, a proibição efetiva dura **t − 1 iterações**, não t. A consequência observável, verificada em 3/3 instâncias: **`tenure = 1` é idêntico a `tenure = 0`** — não proíbe nada.

Não é erro de correção (o `tenure` é calibrado, então o irace simplesmente encontra o valor deslocado em 1), mas **o relatório precisa declarar a convenção**: "tenure = t proíbe por t − 1 iterações". O valor calibrado 39 corresponde a 38 iterações de proibição.

---

## GRASP reativo — Prais & Ribeiro (2000) 🔴

**Propriedade.** As probabilidades dos α são reponderadas periodicamente por qᵢ = (melhor/médiaᵢ)^δ, a cada `block` iterações. Para o mecanismo operar, uma execução precisa conter **várias** atualizações.

**Medição** com os parâmetros calibrados (`block = 199`, K = 250):

| Instância | iterações | atualizações de probabilidade |
|---|---|---|
| C101 | 251 | **1** |
| R101 | 458 | 2 |
| RC101 | 359 | **1** |
| R201 | 342 | **1** |

**O mecanismo reativo praticamente não opera.** As 10 primeiras iterações são *round-robin* fixo sobre a grade de α (`Grasp.cpp`, fase de aquecimento); depois disso as probabilidades são atualizadas **uma única vez** na maioria das execuções. O que roda é, essencialmente, um GRASP com α sorteado de uma distribuição quase uniforme.

**Causa.** O intervalo de busca do irace para `block` é (20, 200) e o valor escolhido foi **199** — a fronteira superior. Combinado com K = 250, sobra menos de uma atualização e meia por execução.

**Isto explica um resultado do relatório.** A conclusão de que GRASP e GRASP reativo são estatisticamente equivalentes é esperada se o componente que os distingue mal é acionado. A comparação atual **não testa o GRASP reativo**; testa duas variantes de GRASP com sorteio de α.

### Correção aplicada

`block` deixou de ser calibrado em **iterações absolutas** e passou a ser **fração de K**: `block = round(block_frac × K)`. Isso fixa o *número* de reponderações, qualquer que seja a escala do critério de parada.

- `solver/apps/solve.cpp`: nova opção `--block-frac F`, que exige `--max-no-improve` (o K de referência) e rejeita F fora de (0, 1].
- `experiments/irace/parameters/rgrasp.txt`: `block` → `block_frac ∈ (0,02; 0,40)`. O teto garante ≥ 2 reponderações; o piso mantém ~4 amostras por α em cada bloco (a grade tem 10 α).
- `experiments/extract_tuned.py` não precisou de mudança — copia os *switches* que o irace emitir.

**Efeito medido**, mesma semente, mesmo K = 250:

| Instância | iterações | reponderações (block=199) | reponderações (block_frac=0,1 → 25) |
|---|---|---|---|
| C101 | 251 | 1 | **10** |
| R101 | 458 | 2 | **18** |
| RC101 | 359 → 606 | 1 | **24** |
| R201 | 342 | 1 | **13** |

Em RC101 a busca ainda passa a render por mais tempo (359 → 606 iterações), o que é o efeito esperado de uma adaptação que de fato opera.

**Teste de regressão:** `reactive_grasp_actually_reacts` exige ≥ 5 reponderações por execução. Impede que a degeneração volte em silêncio.

---

## Consequência para o estudo

| Item | Estado |
|---|---|
| VND, GRASP, Busca Tabu | fiéis; podem ser executados como estão |
| Convenção do *tenure* | declarar no relatório: "t proíbe por t − 1 iterações"; o 39 calibrado equivale a 38 |
| GRASP reativo | parametrização corrigida; **`tuned.json` ainda traz `--block 199`** e precisa ser regenerado |

O `tuned.json` atual foi produzido sob a parametrização antiga. Executar o estudo com ele reproduziria o reativo degenerado. **Recalibrar o `rgrasp` é obrigatório**; `grasp` (`--alpha`) e `tabu` (`--tenure`) não foram afetados e podem ser reaproveitados.

