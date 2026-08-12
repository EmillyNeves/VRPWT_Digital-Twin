# Verificação 01 — Heurística de inserção I1 de Solomon (1987)

**Estado:** 🟡 concluída com uma discrepância não resolvida (§7)
**Artefatos:** `results/solomon-i1/i1_configs.csv` (896 execuções) · `results/solomon-i1/tables_I_VI.csv`

---

## 1. Fonte canônica

Solomon, M. M. *Algorithms for the Vehicle Routing and Scheduling Problems with Time Window Constraints.* **Operations Research** 35(2):254–265, 1987. PDF em `docs/referencias/1987_Solomon_VRPTW_Algorithms.pdf`.

**p.257 — o critério de inserção**, transcrito:

> $c_{11}(i,u,j) = d_{iu} + d_{uj} - \mu d_{ij}, \quad \mu \geq 0$
> $c_{12}(i,u,j) = b_{ju} - b_j$
> $c_1(i,u,j) = \alpha_1 c_{11}(i,u,j) + \alpha_2 c_{12}(i,u,j), \quad \alpha_1 + \alpha_2 = 1; \ \alpha_1 \geq 0, \alpha_2 \geq 0$
> $c_2(i,u,j) = \lambda d_{0u} - c_1(i,u,j), \quad \lambda \geq 0$

Onde $b_j$ é o início do atendimento em $j$ antes da inserção e $b_{ju}$ depois — ou seja, $c_{12}$ é o **empurrão temporal** (*push forward*) induzido no sucessor.

**p.259 — o protocolo experimental**, transcrito:

> *"Insertion-Criterion (i). The results are the **best of eight runs**. The parameters used, $(\mu, \lambda, \alpha_1, \alpha_2)$, are: (1, 1, 1, 0), (1, 2, 1, 0), (1, 1, 0, 1), and (1, 2, 0, 1). **Two initialization criteria** were tested: (a) the farthest unrouted customer, and (b) the unrouted customer with the earliest deadline."*

> *"Solution quality is measured in terms of the **minimum number of vehicles, minimum schedule time, minimum distance, and minimum waiting time in that order**, i.e., we use a **lexicographic ordering** of the solutions."*

> *"Travel times between customers are taken to equal the corresponding distances."* · *"we did not use any k-optimal improvement procedures."*

**p.263 — a conclusão paramétrica**, transcrito:

> *"time insertion proved clearly superior to distance insertion. It was used in obtaining the best solution to **21 out of 27** problems."*
> *"Distance insertion, by emphasizing the geographical component, can lead to higher total schedule time from accumulated waiting time and, possibly, additional vehicles."*

**Alvos numéricos** — Tabelas I–VI, médias por conjunto de problemas:

| Conj. | n | schedule | veículos | distância | espera |
|---|---|---|---|---|---|
| R1 | 12 | 2695,5 | 13,6 | 1436,7 | 258,8 |
| C1 | 9 | 10104,2 | 10,0 | 951,9 | 152,3 |
| RC1 | 8 | 2775,0 | 13,5 | 1596,5 | 178,5 |
| R2 | 11 | 2578,1 | 3,3 | 1402,4 | 175,6 |
| C2 | 8 | 9921,4 | 3,1 | 692,7 | 228,6 |
| RC2 | 8 | 2955,4 | 3,9 | 1682,1 | 273,2 |

**Identidade verificada nas próprias tabelas:** `schedule = distância + espera + Σserviço`, com Σserviço constante (9000 nas famílias C, 1000 nas R e RC). R1: 1436,7 + 258,8 + 1000 = 2695,5, exato. Logo **apenas duas das quatro grandezas são independentes**.

> A identidade **não prova** que Solomon mede com partida do depósito em t=0 — ela vale sob as duas convenções, porque atrasar a partida reduz schedule e espera juntos. O que aponta para t=0 é o **valor** da espera bater (§6).

---

## 2. Mapeamento fórmula → código

| Fórmula do artigo | Onde | Observação |
|---|---|---|
| $c_{11} = d_{iu} + d_{uj} - \mu d_{ij}$ | `solver/src/SolomonI1.cpp` · `i1_best_insertion` | escrito na forma literal do artigo |
| $c_{12} = b_{ju} - b_j$ | `solver/src/Neighborhoods.cpp` · `eval_insert`, campo `InsertEval::dtime` | já era calculado como teste de viabilidade O(1) e **descartado** |
| $c_1 = \alpha_1 c_{11} + \alpha_2 c_{12}$ | `solver/src/SolomonI1.cpp` · `i1_best_insertion` | `alpha1 + alpha2 = 1` é imposto em `solve.cpp` · `parse_i1` |
| $c_2 = \lambda d_{0u} - c_1$ | `solver/src/SolomonI1.cpp` · `i1_best_insertion` | |
| semente (a) mais distante / (b) prazo mais cedo | `solver/src/SolomonI1.cpp` · `i1_select_seed` | |
| ordem lexicográfica de 4 níveis | `solver/include/vrptw/Evaluator.hpp` · `LexKey` | usada **só** no confronto; a busca otimiza distância (DIMACS) |
| schedule / espera / serviço | `solver/src/Validator.cpp` · `validate` | recaminha a rota sem confiar em cache |
| tempo de viagem = distância | `solver/include/vrptw/DistanceMatrix.hpp` · `time()` | padrão quando não há matriz de tempo |

**Achado estrutural:** antes desta verificação, `I1Params::alpha2` era **campo morto** — declarado e nunca lido em lugar nenhum do repositório. O termo temporal de Solomon não estava implementado, embora o valor `b_{ju} - b_j` já fosse computado e jogado fora a cada avaliação de inserção. O `GRASP` duplicava literalmente o critério; hoje ambos passam por `i1_best_insertion`.

---

## 3. Escolhas subdeterminadas pelo artigo

Esta é a seção de maior valor científico: o artigo não especifica sete pontos, e cada um foi medido em vez de assumido.

| # | Escolha | Adotado | Alternativa | Impacto medido |
|---|---|---|---|---|
| **S1** | desempate de $c_1$ | primeira posição varrida | menor $c_{11}$ | **≤0,15pp**; 36/448 execuções mudam, totais de veículos idênticos |
| **S2** | ordem de varredura de $u$ | id crescente | — | **não medido** |
| **S3** | empate no prazo (semente b) | menor id | mais distante do depósito | **≤0,03pp**; veículos idênticos |
| **S4** | convenção de distância | **precisão dupla** | truncamento a 1 casa | resolvido, ver abaixo |
| **S5** | $c_{12}$ na última posição | atraso do retorno ao depósito | zero | resolvido, ver abaixo |
| **S6** | arredondamento das médias publicadas | — | — | ±0,011%; mas permite reconstruir o **total inteiro** de veículos |
| **S7** | escopo do "best of eight" | **por instância** | por conjunto | resolvido, ver abaixo |

**S4 resolvida por evidência externa, não por ajuste.** Solomon (p.259) relata a melhor solução que encontrou para C1 como *"10 vehicles, a total schedule of 9,829 units, a distance of **829** units and no waiting time"*. A solução de referência de C101 custa **827,30** truncada a 1 casa e **828,94** em precisão dupla. 828,94 → 829; 827,3 → 827. **Solomon usou precisão dupla.** Adotada como convenção primária do confronto; o estudo comparativo continua truncado (DIMACS).

**S5 resolvida por degradação uniforme.** Tratar $c_{12} = 0$ no fim da rota piora 4 dos 6 conjuntos (R2 de +0,53% para +8,28%; RC2 de +1,63% para +7,45%) e infla os veículos de 456 para 463. A leitura "atraso do retorno" está certa.

**S7 resolvida por implausibilidade da alternativa.** Selecionar uma única configuração por conjunto nos deixaria +2,44% a +16,07% piores que Solomon em **todos** os seis, o que é incompatível com uma reimplementação fiel. "Best of eight" é **por instância**.

**Correção de premissa.** O levantamento inicial afirmava que "dezenas de clientes compartilham o mesmo prazo nas famílias C". É **falso**: o maior grupo empatado é 6 (C204), a maioria 2–3. Foi isso que reduziu S3 à irrelevância.

---

## 4. Protocolo experimental

```bash
make -C solver
.venv/bin/python experiments/analysis/solomon_i1_tables.py
```

56 instâncias × 8 configurações × 2 convenções = **896 execuções**, todas viáveis e completas (o script aborta se alguma não for). Sensibilidades pelo mesmo script:

```bash
python3 experiments/analysis/solomon_i1_tables.py --sensitivity --i1-tiebreak-c11       # S1
python3 experiments/analysis/solomon_i1_tables.py --sensitivity --i1-seed-tie-farthest  # S3
python3 experiments/analysis/solomon_i1_tables.py --sensitivity --i1-c12-zero-at-end    # S5
```

A agregação é dupla e deliberadamente separada: **I1-Solomon** (chave lexicográfica de 4 níveis, o critério dele) para o confronto, e **I1-DIMACS** (menor distância, o critério nosso) como linha de baseline do estudo.

---

## 5. Critério de aceitação

Declarado **antes** de olhar o resultado, e **corrigido duas vezes** durante a verificação — as duas correções estão registradas porque são parte do achado.

**Tier A — invariantes exatos.** Falha = bug, bloqueia tudo. Nenhuma tolerância.

| Teste | Asserção | Resultado |
|---|---|---|
| `i1_default_bit_identical` | hash FNV-1a das rotas nas 56, congelado antes da refatoração | ✅ 56/56 |
| `i1_schedule_identity` | `schedule = distância + espera + serviço` a 1e-6 | ✅ 56 |
| `i1_service_time_is_family_constant` | 9000 (C) / 1000 (R, RC) | ✅ |
| `insert_eval_dtime_matches_bruteforce` | $c_{12}$ O(1) ≡ recálculo O(n) | ✅ 789 inserções |
| `double_precision_refs` | 7 âncoras SINTEF a 1e-6, e truncamento distinguível | ✅ 7/7 e 7/7 |
| `reference_field_rejects_prose` | nenhuma das 49 citações lida como número | ✅ 7/56 |

**Tier B — concordância com as Tabelas I–VI.**

> **Correção 1.** A primeira versão media o desvio no *schedule bruto*. Mas o Σserviço é constante e representa 89% da grandeza nas famílias C — o critério era quase vazio justamente onde mais importava. Em C2 ele mostrava −0,66% onde o desvio real era −6,24%. Passou-se a medir a **parte variável** (distância + espera).

> **Correção 2.** A tolerância de 3% foi ancorada somando o que S1, S3 e S5 explicariam. Medidos, eles explicam **~0,2pp combinados**, não 2pp. A ancoragem ruiu e a tolerância ficou indefensável.

**Critério final — o total INTEIRO de veículos.** É a primeira chave lexicográfica de Solomon, é reconstruível sem ambiguidade a partir das médias publicadas (S6), e **não precisa de tolerância**. A parte variável passa a ser **descritiva**, não critério: ela vem confundida pela diferença de veículos, e a direção dessa confusão não é constante (regressão em C2 dá o sinal oposto ao esperado).

---

## 6. Resultado

Convenção **precisão dupla**, sem sensibilidades (S1−, S3−, S5−):

| Conj. | veículos (nosso / Solomon) | dif. | dist+espera (nosso / Solomon) | desvio |
|---|---|---|---|---|
| R1 | 166 / 163 | +3 | 1736,2 / 1695,5 | +2,40 % |
| C1 | **90 / 90** | **0** | 1104,6 / 1104,2 | **+0,04 %** |
| RC1 | **108 / 108** | **0** | 1803,5 / 1775,0 | +1,61 % |
| R2 | 35 / 36 | −1 | 1539,2 / 1578,0 | −2,46 % |
| C2 | 26 / 25 | +1 | 886,9 / 921,3 | −3,74 % |
| RC2 | 32 / 31 | +1 | 1968,6 / 1955,3 | +0,68 % |
| **Total** | **457 / 453** | **+4** | | |

Sob truncamento: **456 / 453 (+3)**.

**Veredito: quatro veículos de diferença em 453, sobre 56 instâncias — 0,88%.** C1 e RC1 batem exatamente; C1 ainda reproduz a parte variável a +0,04%.

**A patologia da p.263 foi medida no nosso próprio código.** A configuração que o repositório usava — $(1,2,1,0)$ + semente mais distante, execução única — apresenta os três sintomas que Solomon atribui à inserção por distância:

| Conj. | espera nossa (config única) | espera dele | veículos |
|---|---|---|---|
| R2 | 539,2 | 175,6 | 3,73 vs 3,3 |
| C2 | 523,1 | 228,6 | 3,50 vs 3,1 |
| RC2 | 512,2 | 273,2 | 4,12 vs 3,9 |

Espera de 2 a 3 vezes a dele e mais veículos em todos os seis conjuntos — enquanto a **distância** é competitiva ou melhor (R2: 1333,7 contra 1402,4). É exatamente *"higher total schedule time from accumulated waiting time and, possibly, additional vehicles"*.

**Nenhuma configuração domina por instância.** A vencedora se distribui pelas oito (13, 10, 9, 8, 5, 5, 3, 3 de 56). Chamar $(1,2,1,0)$ de "configuração canônica de Solomon" não se sustenta.

### 6.1 Decisão para o estudo: uma configuração fixa, não o melhor-de-8

O melhor-de-8 é o protocolo de **Solomon**, e serve para verificar fidelidade. Ele **não** serve como I1 do estudo comparativo, porque a configuração vencedora varia por instância — e o que a comparação entre VND, GRASP, GRASP reativo e Busca Tabu exige é exatamente o oposto: **uma solução inicial única e idêntica para todos**.

Como configuração única, medida nas 56 instâncias sob a convenção do estudo:

| config (μ=1) | veículos | distância média | espera média |
|---|---|---|---|
| λ=1, α₂=0, far | 478 | 1303,5 | 389,7 |
| **λ=2, α₂=0, far** | **474** | **1314,3** | **377,3** |
| λ=1, α₂=0, deadline | 496 | 1453,3 | 490,5 |
| λ=2, α₂=1, deadline | 502 | 1524,6 | 337,4 |
| (demais quatro) | 499–505 | 1479–1620 | 359–541 |

**A configuração já em uso — $(\mu{=}1, \lambda{=}2, \alpha_1{=}1, \alpha_2{=}0)$ + semente mais distante — é a melhor escolha única:** menos veículos que todas as outras, com distância a 0,8% da menor. **Mantida.** O que muda é apenas como ela é descrita: uma das quatro combinações de Solomon, escolhida por evidência, não "a canônica".

O padrão de comparação fica assim:

| Método | Ponto de partida |
|---|---|
| VND | I1 com a configuração fixa acima |
| Busca Tabu | a **mesma** solução I1 |
| GRASP / Reativo | construção randomizada própria — mas pelo **mesmo** critério de Solomon, agora em código compartilhado (`i1_best_insertion`) |

A assimetria do GRASP é inerente ao método (a construção randomizada é o que ele é), não uma escolha do estudo, e deve ser declarada no relatório. Antes desta etapa o GRASP tinha uma **cópia duplicada** do critério, que podia divergir em silêncio; hoje há uma só implementação.

---

## 7. Discrepâncias não resolvidas

**7.1 — C2: um veículo, localizado.** As oito instâncias C2 têm melhor-conhecido com 3 veículos. Solomon fecha o conjunto em 25 (7×3 + 1×4); nós em 26. **C203 e C204 exigem 4 veículos em todas as oito configurações nossas**; Solomon consegue 3 em uma delas. Não é desvio difuso — é uma instância específica.

Hipóteses testadas e **refutadas**: convenção de distância (H3 — melhora de −6,24% para −3,74%, não resolve), $c_{12}$ no fim da rota (H1 — piora), desempate de $c_1$ (H2/S1 — nulo), troca veículos↔distância (H5 — a regressão dá o sinal **oposto**: a diferença de veículos deveria nos deixar +153 unidades piores, e observamos −57,5).

Hipótese aberta: **S2**, a ordem de varredura de $u$, não foi medida. Custo estimado: 1 dia.

**7.2 — Não reproduzimos a superioridade da inserção por tempo.** Solomon relata que $\alpha_2 = 1$ produziu a melhor solução em **21 de 27** problemas. Na nossa varredura, $\alpha_2 = 1$ vence em **25 de 56** e $\alpha_2 = 0$ em 31. Hipóteses: (i) a análise da p.263 usa um subconjunto de 27 problemas, não os 56; (ii) algum detalhe da inserção por tempo que o artigo não especifica.

**7.3 — Resíduo não explicado.** Somadas, as ambiguidades que conseguimos identificar e medir (S1, S3, S6) explicam ~0,2 ponto percentual. Os desvios residuais chegam a 3,74%. **O resíduo não é atribuível à ambiguidade documentada** — é preciso dizer isso, e não escondê-lo atrás de uma tolerância generosa.

---

## 8. Rastro

- Código: `solver/src/SolomonI1.cpp`, `solver/include/vrptw/algorithms/SolomonI1.hpp`, `solver/src/Neighborhoods.cpp` (`eval_insert`), `solver/src/Validator.cpp`, `solver/include/vrptw/Evaluator.hpp`, `solver/include/vrptw/DistanceMatrix.hpp` (`make_euclid_matrix`), `solver/src/SolutionIO.cpp`, `solver/apps/solve.cpp`
- Testes: `solver/tests/test_i1_solomon.cpp` — 6 testes novos; suíte total **23 passando**
- Script: `experiments/analysis/solomon_i1_tables.py`
- Artefatos: `results/solomon-i1/i1_configs.csv` (896 linhas), `results/solomon-i1/tables_I_VI.csv`

**Lição de protocolo, registrada por ter custado uma varredura inteira:** uma edição malfeita quebrou o build de `solve`, mas os testes compilaram (linkam só a biblioteca) e 896 execuções rodaram com o binário antigo, ignorando silenciosamente a flag nova. A tabela resultante era plausível e vazia. **Toda flag nova exige um teste "isto muda alguma coisa?" antes de qualquer varredura.**
