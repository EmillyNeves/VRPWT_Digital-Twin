# Registro de decisões de projeto

**Para que serve.** As decisões metodológicas deste trabalho estão espalhadas por sete documentos, misturadas com referências de implementação obsoletas (`src/main.cpp`, `bin/vrptw`, `--vnd-neighborhoods`). Tratar um documento como obsoleto por causa dos caminhos de arquivo faz perder a decisão que ele carrega. Foi o que aconteceu, repetidamente.

**O que este documento NÃO faz.** Não decide. Onde há conflito entre o planejado e o implementado, ele marca **REQUER DECISÃO** e apresenta as opções — a escolha é da estudante e da orientadora.

**Fontes varridas** (para que a extração seja auditável):
`docs/relatorio-parcial/relatorio-parcial-nomealuno.tex` · `docs/planejamento/{conformance_audit, neighborhood_selection_approach, irace_calibration_plan, irace_parameter_justification, irace_search_space_template, irace_target_runner_template}.md`

**Coluna "Guarda"** — o que impede a decisão de ser violada em silêncio. `teste` é o mais forte (quebra o build); `construção` é ainda mais forte (torna a violação impossível); `—` significa que depende de disciplina.

---

## 1. Algoritmos e implementação

| # | Decisão | Fonte | Guarda |
|---|---|---|---|
| 1.1 | I1 de Solomon, VND, GRASP fixo e reativo, Busca Tabu | parcial, §Materiais e Métodos | — |
| 1.2 | C++20, 56 instâncias Solomon-100, critério DIMACS | parcial, §Materiais e Métodos | `reproduce_dinamics_costs` |
| 1.3 | `objective = cost`; μ = 1,0; ε = 1e-6 | `irace_calibration_plan.md` §2 | **teste** `decisao_1_3_parametros_fixos` |
| 1.4 | **Mesma solução inicial I1 para `nls/vnd/grasp/tabu`** | `conformance_audit.md` §6 | **teste** `decisao_1_4_i1_como_partida_comum` |
| 1.5 | Núcleo de avaliação compartilhado por todos os métodos | `conformance_audit.md` §6 | **construção** — `DistanceMatrix` e `Evaluator` únicos |
| 1.6 | Aspiração por omissão na Busca Tabu | `conformance_audit.md` §5 | **teste** `tabu_aspiration_by_default_prevents_truncation` |
| 1.7 | Memória de longo prazo e oscilação estratégica fora de escopo | `conformance_audit.md` §5 | — (declarado no relatório) |

## 2. Conjunto de vizinhanças

| # | Decisão | Fonte | Guarda |
|---|---|---|---|
| 2.1 | Oito movimentos avaliados (3 intra + 5 inter) | parcial, §Materiais e Métodos | `docs/verificacao/03` §1 |
| 2.2 | **Ordem de exploração por complexidade computacional** | `neighborhood_selection_approach.md`; Hansen & Mladenović (2001) | **teste** `decisao_2_2_ordem_por_complexidade` |
| 2.3 | Papéis dos quatro grupos de operadores | parcial, Quadro 2 | `docs/verificacao/03` §2 |
| 2.4 | ~~Subconjunto pós-seleção de 4 movimentos~~ | `neighborhood_selection_approach.md` | **REVOGADO** — ver Revogações |
| 2.5 | Mesmo conjunto de vizinhanças entre os métodos | `conformance_audit.md` §6 | **construção** — `all_neighborhoods()`, mais `decisao_2_5_mesmo_kit_vnd_e_tabu` |

## 3. Critério de parada e isonomia

| # | Decisão | Fonte | Guarda |
|---|---|---|---|
| 3.1 | **Critério de parada: número de iterações sem melhoria (K)** | orientação da orientadora, ago/2026 | ✅ implementado; ver nota |
| 3.1b | **K = 800, igual para os três métodos** | orçamento declarado; ver nota | `experiments/config/fixed_K.json` |
| 3.2 | Mesmo teto de tempo por execução para todos | `conformance_audit.md` §6 | — (600 s no pipeline) |
| 3.3 | Mesmo esquema de sementes por algoritmo | `conformance_audit.md` §6 | — (`runner.py`) |
| 3.4 | Perfis de tempo por algoritmo (Quadro 3) | parcial, Quadro 3 | ✅ resolvido — ver Divergências ~~D2~~ |

> ### 3.1 — resolvido
>
> **O critério é o número de iterações sem melhoria (K)**, conforme orientação recebida. É o que está implementado.
>
> O relatório parcial **não menciona critério de parada** — a busca por "critério de parada", "parada", "tempo limite", "iterações", "orçamento" e "sem melhoria" no `.tex` entregue retorna zero ocorrências. A regra de tempo igual aparece apenas em dois documentos internos de planejamento (`irace_calibration_plan.md` §2 e `irace_parameter_justification.md` §4.1), que nunca foram entregues e antecedem esta orientação. **Não há, portanto, desvio a declarar**: o critério é definido pela primeira vez no relatório final.
>
> A leitura sob tempo igual (`results/equal_time.csv`, `primal_integral.csv`) permanece como **análise complementar** — não como resultado co-primário. Ela já está implementada e não custa nada reportar.

> ### 3.1b — o valor de K
>
> **K = 800 iterações sem melhoria, igual para os três métodos.**
>
> Não existe valor ótimo a descobrir: a qualidade do GRASP é monotonicamente não decrescente no número de iterações (Resende & Ribeiro, 2003), e a medição confirma que não há joelho na curva com os parâmetros calibrados. K é, portanto, **orçamento computacional declarado** — que é como a literatura de GRASP e de Busca Tabu trata o assunto.
>
> Gap médio nas 28 instâncias de treino, semente única (`results/stopping/convergence.csv`):
>
> | K | GRASP | Reativo | Tabu | ranking | GRASP×Reativo | GRASP×Tabu |
> |---|---|---|---|---|---|---|
> | 50 | 3,487 | 3,107 | 5,990 | Reativo < GRASP < Tabu | p = 0,2675 | p = 0,0029 |
> | 100 | 3,150 | 2,713 | 5,471 | Reativo < GRASP < Tabu | p = 0,1531 | p = 0,0015 |
> | 200 | 2,391 | 2,267 | 4,682 | Reativo < GRASP < Tabu | p = 0,9544 | p = 0,0003 |
> | 400 | 2,173 | 1,925 | 4,279 | Reativo < GRASP < Tabu | p = 0,9181 | p = 0,0006 |
> | **800** | **1,863** | **1,652** | **4,042** | Reativo < GRASP < Tabu | p = 0,7060 | p = 0,0009 |
> | 1600 | 1,674 | 1,524 | 3,636 | Reativo < GRASP < Tabu | p = 0,1591 | p = 0,0012 |
> | 3200 | 1,469 | 1,201 | 3,284 | Reativo < GRASP < Tabu | p = 0,7481 | p = 0,0005 |
>
> Custo por execução em K = 800, medido sem concorrência (`results/stopping/cost.csv`): mediana de **15,6 s** no GRASP, **22,7 s** no Reativo e **6,8 s** na Tabu; pior caso **76 s**, contra o teto de segurança de 600 s. Dobrar para K = 1600 rende 0,19 pp no GRASP e custa 1,8× mais tempo (2,3× no Reativo).
>
> **O ranking dos métodos e o resultado dos testes par a par são idênticos numa faixa de 64×** — nenhuma conclusão do estudo depende dessa escolha. Essa invariância vai para o apêndice, como resposta antecipada à objeção "e se outro K desse outra conclusão?".
>
> Ressalva a declarar: semente única. O "não significativo" entre GRASP e Reativo pode ser falta de poder, não equivalência — o p-valor oscila entre 0,15 e 0,95, assinatura de ruído. O estudo final, com 30 sementes, é quem decide isso.
>
> **Como estes números foram obtidos.** GRASP e Tabu: uma execução em K = 3200 por instância, com os orçamentos menores derivados por truncamento do traço de convergência. Reativo: reexecutado em cada K, porque `--block-frac` faz o intervalo de reponderação escalar com o orçamento e sua trajetória não é truncável. A premissa de truncamento é conferida por `experiments/analysis/stopping_derivation_check.py` — GRASP 24/24, Tabu 24/24, Reativo 22/24 — e a igualdade derivado ≡ executado foi verificada nas 28 instâncias em K = 800.
>
> K uniforme entre os métodos preserva a isonomia da regra de parada. A contrapartida é que a iteração custa coisas diferentes em cada método, e o tempo de parede difere — o que é reportado, e complementado pela leitura sob tempo igual.

> ### ⚠️ 3.4 — o Quadro 3 do parcial precisa de um ajuste
>
> O parcial não fixa critério de parada, mas o Quadro 3 caracteriza os métodos por tempo de resposta. Duas linhas se sustentam, uma não:
>
> | Algoritmo | Afirmação | Medido |
> |---|---|---|
> | VND | "baixo tempo de resposta" | ✅ 40 ms contra segundos |
> | GRASP fixo | "maior esforço computacional" | ✅ |
> | Busca Tabu | "resposta mais ágil do que abordagens mais intensivas" | ❌ razão Tabu/GRASP vai de 5,62× a 0,58× conforme a instância |
>
> A afirmação sobre a Tabu não vale como característica do método, e ela sustenta o "potencial de uso: replanejamento mais frequente" na mesma linha. Reformular para algo do tipo "tempo de resposta dependente da estrutura da instância", com os números da execução nova.

## 4. Calibração (irace)

| # | Decisão | Fonte | Guarda |
|---|---|---|---|
| 4.1 | Calibrar só os hiperparâmetros canônicos; fixar o resto | `irace_search_space_template.md` §Global fixed controls | — |
| 4.2 | Divisão treino/holdout fixada **antes** da corrida | `irace_calibration_plan.md` §2 | — (28/28 estratificada) |
| 4.3 | Score = `gap_pct + λ·time_sec`; λ = 1e-4 recomendado, **λ = 0 permitido** (DIMACS estrito) | `irace_parameter_justification.md` §1.1 | — |
| 4.4 | Penalidade fixa 1e9 em falha ou inviabilidade | idem §1.1 | — (`target-runner`) |
| 4.5 | **Vencedor na borda do intervalo ⇒ abrir novo intervalo e repetir a corrida** | idem §2.1 (**ação obrigatória**) | — |
| 4.6 | `maxExperiments` = 1000 por cenário; aumentar e **registrar** se não convergir | idem §2.2 | — |
| 4.7 | **Pré-registro ex-ante obrigatório**: parâmetros ajustáveis, intervalos, fixos | idem §2 | — |
| 4.8 | **Justificativa ex-post obrigatória** com checklist: posição no intervalo, impacto na mediana, custo, IQR | idem §3 e §3.1 | — |

## 5. Validação

| # | Decisão | Fonte | Guarda |
|---|---|---|---|
| 5.1 | Toda solução validada: cobertura, capacidade, janelas de tempo | parcial, §Materiais e Métodos | **teste** — 56/56 em I1, VND, GRASP, Tabu |
| 5.2 | Protocolo final: congelar parâmetros, rodar no holdout, **comparar contra baseline não calibrado** | `irace_calibration_plan.md` §6 | — (`analysis/calibration_gain.py`) |
| 5.3 | Testes não paramétricos com controle de comparações múltiplas | parcial, §Materiais e Métodos | — (`stats.py`, `stats_paired.py`) |

## 6. Dados e convenções

| # | Decisão | Fonte | Guarda |
|---|---|---|---|
| 6.1 | Convenção DIMACS: euclidiana truncada a 1 casa | parcial, §Materiais e Métodos | **teste** `reproduce_dinamics_costs` (56/56) |
| 6.2 | Hierarquia lexicográfica de Solomon também implementada | parcial, §Materiais e Métodos | — (`LexKey` de 4 níveis) |
| 6.3 | "Duas casas decimais" de Solomon também implementada | parcial, §Materiais e Métodos | **teste** `double_precision_refs` (7 âncoras) |
| 6.4 | SINTEF/TOP como benchmark complementar | parcial, §Resultados | — (`baseline_compare.py`) |

## 7. Gêmeo digital e IoT

| # | Decisão | Fonte | Guarda |
|---|---|---|---|
| 7.1 | Enchimento com variação pico/fora de pico | parcial, Quadro 1 | — (Poisson não homogêneo) |
| 7.2 | Acionamento por limiar configurável | parcial, Quadro 1 | — |
| 7.3 | Lixeiras ativas viram clientes com janela de tempo | parcial, Quadro 1 | — |
| 7.4 | Interface com o solver a cada ciclo | parcial, Quadro 1 | — |
| 7.5 | **Comunicação LoRaWAN (simulada)** | parcial, Quadro 1 | ✅ **decidido: opção A** — implementar |

> ### 7.5 — resolvido: opção A
>
> Hoje não existe camada de comunicação — a palavra aparece uma vez, numa string de dashboard.
> **Decidido implementar** uma camada mínima, para que o Quadro 1 do parcial permaneça
> verdadeiro sem ressalva. Escopo mínimo suficiente: latência de entrega, perda de pacote e
> ciclo de *duty* (limite de transmissões por período), aplicados sobre as leituras dos
> sensores antes de chegarem ao acionamento por limiar.
>
> **Condição de guarda.** Enquanto não estiver implementado, o Quadro 1 afirma algo que o
> código não faz. Se a entrega chegar sem a camada, isto volta a ser divergência (D4) e a
> saída passa a ser a opção B — corrigir o Quadro para "modelo de sensoriamento" e declarar
> em Limitações. A decisão não pode ficar implícita até o último dia.

---

## Revogações

| # | Decisão revogada | Data | Motivo |
|---|---|---|---|
| 2.4 | Subconjunto de 4 movimentos (`relocate_intra`, `swap_intra`, `relocate_inter`, `two_opt_inter`) | ago/2026 | 11,388 % de gap contra 8,249 % do conjunto completo (+3,14 pp); descartava o Or-opt, estatisticamente significativo (p = 0,0216 com Holm). Busca exaustiva dos 63 subconjuntos: nenhum domina o completo. Ver `docs/verificacao/03-vizinhancas.md` §3 |

---

## Divergências do relatório parcial ENTREGUE

Distintas das Revogações acima. Uma revogação desfaz decisão de documento interno de
planejamento e se resolve por escrito, aqui. **Uma divergência do parcial é compromisso
público**: tem que ser declarada no texto do relatório final, com a evidência que a motivou.
Confundir as duas foi o modo de falha que originou este registro.

| # | O parcial diz | O trabalho faz | Onde declarar |
|---|---|---|---|
| ~~D1~~ | `:200` — oito movimentos avaliados, *"seguida da seleção de um subconjunto mais promissor"* | **não é divergência**: o procedimento de seleção foi executado e sua resposta foi o conjunto completo. Ver nota abaixo | reportar como resultado da seleção |
| ~~D2~~ | Quadro 3 — Busca Tabu tem *"resposta mais ágil"* | ✅ **resolvido no relatório final**: caracterizada como propriedade *média* (mediana 7,4× mais rápida que o GRASP sob K=800), não garantida por instância (faixa 0,57×–17,3×). Está na leitura da Tabela de desempenho global | — |
| ~~D3~~ | `:295` — Figura da C102, *"o GRASP reativo apresentou o melhor resultado"* | ✅ **verificado com o estudo novo**: I1 = 1039,7 e TODOS os métodos de melhoria empatam no ótimo (827,3). O "vencedor" do parcial era artefato do solver antigo; o relatório final usa a figura de evolução da C101 e não repete a alegação | — |
| ~~D4~~ | Quadro 1 — comunicação **LoRaWAN** no gêmeo digital | **deixa de ser divergência**: decidido implementar (opção A). Vira divergência de novo apenas se não for implementado até a entrega | — |

> ### D1 — por que NÃO é divergência
>
> O parcial promete um **procedimento**: avaliar oito movimentos e, a partir deles, selecionar
> um subconjunto ordenado para compor as vizinhanças do VND. Ele não promete um resultado
> específico. O procedimento foi executado, e refeito depois que o kit e a ordem mudaram:
>
> 1. **Ablação leave-one-out** dos seis operadores, Wilcoxon pareado com correção de Holm, nas
>    28 instâncias de treino
> 2. **Busca exaustiva** sobre os $2^6-1 = 63$ subconjuntos próprios
>
> **Resposta da seleção: nenhum subconjunto próprio supera o conjunto completo.** O
> subconjunto de 4 movimentos previamente cogitado custa +3,14 pp e descarta o Or-opt, cuja
> contribuição é significativa (p = 0,0216 com Holm). O subconjunto selecionado é, portanto, o
> conjunto todo — os seis operadores que cobrem os oito movimentos.
>
> O segundo requisito do parcial, **ordenação por complexidade**, também está cumprido: a
> ordem vem do custo medido de uma varredura, é garantida por construção
> (`all_neighborhoods()`) e por teste (`decisao_2_2_ordem_por_complexidade`).
>
> **Armadilha de redação a evitar.** Escrever "usamos o conjunto completo" soa como se a
> seleção não tivesse sido feita. O correto é reportar o procedimento e a resposta: *"a
> seleção foi conduzida por ablação e busca exaustiva, e indicou que nenhum subconjunto
> próprio supera o conjunto completo"*. A ablação por família é o dado que sustenta isso e
> vale como resultado por si — cada operador tem seu regime, e o que é dispensável numa
> família não é em outra.

---

## Pendências abertas — revisão de ago/2026

Itens sem guarda e ainda não executados. **Esta seção envelhece**; reveja a data antes de confiar nela.

| # | Pendência | Bloqueia |
|---|---|---|
| 4.5 | Conferir os três intervalos do irace quanto à borda antes de recalibrar | a recalibração |
| 4.7 | Escrever o pré-registro ex-ante | a recalibração |
| 4.3 | Declarar λ = 0 como escolha (alternativa DIMACS estrita) | — |
| 4.6 | Registrar `maxExperiments` = 1200–1500 em vez de 1000 | — |
| 4.8 | Justificativa ex-post com checklist | fecha após a recalibração |
| 5.2 | Comparar contra baseline não calibrado no holdout | fecha após o estudo |
| 3.4 | Refazer a caracterização de tempo da Busca Tabu no Quadro 3 do parcial | o texto de resultados |
| 7.5 | Decidir A / B | o Quadro 1 do relatório final |

---

## Regra de uso

1. **Antes de implementar** — procure aqui. Se a decisão existe, siga; se discordar, **revogue por escrito** na tabela de Revogações.
2. **Antes de calibrar ou executar** — confira as Pendências da área envolvida.
3. **Ao mudar de rumo** — registre. Um desvio declarado é aceitável; um desvio silencioso não é.
4. **Ao ler um documento de planejamento** — separe **referência de implementação** (envelhece) de **decisão de projeto** (permanece). Foi a confusão entre as duas que produziu este documento.
5. **O que puder virar teste, vira teste.** Um documento é lido uma vez; um teste quebra o build.
