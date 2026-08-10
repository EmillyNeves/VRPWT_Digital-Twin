# Parecer de revisão crítica — Subprojeto de IC "Otimização Dinâmica de Rotas para Coleta de Resíduos Sólidos"

**Data:** 07/08/2026 · **Escopo:** alinhamento parcial↔final, revisão de literatura, calibragem de parâmetros, rigor estatístico, auditoria de código e conformidade formal.
**Método:** auditoria em seis dimensões independentes, seguida de refutação adversarial de cada achado. 72 achados sobreviveram à verificação (5 críticos, 23 altos, 34 médios, 10 baixos).

---

## Verificações executadas (não apenas leitura de código)

Dois achados críticos sobre o Digital Twin foram confirmados por **execução direta**, e não por inspeção. Reproduza com:

```bash
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install numpy
cd digital_twin
```

**(1) As janelas de tempo dinâmicas são inertes.** Variando `urgency_coef` (κ) de 0,0 a 0,9 — e mesmo desligando o mecanismo com `urgency=False` — a simulação de 16 ciclos em Vitória produz **sequências de rotas bit-idênticas** e KPIs idênticos (distância 3550,6; 119 coletas; 16 transbordos; 2,88 veículos/ciclo em todos os casos). Causa: `horizon=5000` (`twin.py:129`) contra rotas de duração muito menor, de modo que `due = H(1-κ·crit) ∈ [2000, 5000]` nunca restringe. O cenário resolvido é, de fato, um CVRP com priorização por demanda — não um VRPTW.

**(2) O contador de transbordos reconta o mesmo transbordo.** Em `sensors.py:43-45`, `overflow_events` soma `new_fill > 1.0` a cada ciclo sobre um `fill` já saturado em 1,0. Teste controlado (38 lixeiras cheias, 10 ciclos, sem coleta): **298 eventos para 38 lixeiras — recontagem de 7,8×**. Contando *episódios* de transbordo (transição de `<1` para `≥1`), a comparação da Tabela do Twin passa de **16 × 25** (a favor do dinâmico) para **24 × 23** (a favor do estático). **A conclusão de que a coleta dinâmica reduz transbordos não sobrevive à métrica corrigida.** O que sobrevive — e é um resultado legítimo e forte — é: mesma distância com **metade das coletas** (119 × 228).

Verificações adicionais feitas por leitura direta e confirmadas: K = 250/250/1400 são o último elemento de cada `KGRID` em `knee_K.py:42-44`; `tenure=39` em (5,40) e `block=199` em (20,200); os agregados do relatório (35,97 / 11,07 / 3,40 / 4,51 e a tabela por família) são exatamente reproduzíveis a partir de `tabela_por_instancia.tex`; a Busca Tabu é de fato determinística; a convenção DIMACS descrita na Seção 2.2 confere com as regras oficiais; a URL do DIMACS citada em `:683` retorna HTTP 404.

---

## 1. Veredito geral

O trabalho está, em engenharia, num nível bem acima do usual para uma Iniciação Científica: o solver em C++20 é limpo, tem 15 testes que passam, reproduz exatamente os 56 custos de referência sob a convenção DIMACS, e o desenho de "núcleo compartilhado" é a decisão metodológica correta. **O que impede o relatório de ser irretocável não é o código — é a distância entre o que o texto afirma e o que os artefatos sustentam.** Três blocos: (i) a camada do Digital Twin, que é a razão de ser do subprojeto aprovado, tem um mecanismo comprovadamente inerte (as janelas dinâmicas não restringem nada) e um KPI que superconta, de modo que a conclusão "coleta dinâmica reduz transbordos" se inverte quando medida corretamente; (ii) a calibragem, apresentada como a contribuição metodológica do capítulo, cai no teto de cada grade e de cada intervalo, não tem baseline, não tem sensibilidade e não é auditável; (iii) a conclusão estatística central é enunciada como equivalência quando é apenas não-rejeição, e é sensível à composição do conjunto de algoritmos comparados. A isso se soma um conjunto de não conformidades formais com o modelo obrigatório do PIIC que, sozinhas, motivam devolução antes mesmo do mérito.

Diagnóstico honesto: **hoje o documento passa em uma banca leniente e é devolvido por um parecerista atento.** As correções que mudam esse quadro são, na maioria, baratas — e estão listadas na Seção 8.

> **Nota de verificabilidade.** O diretório `results/` não está versionado (`git ls-files results/` retorna vazio; `.gitignore:18-19` exclui `results/raw/` e `results/irace/`, mas os agregados simplesmente nunca foram commitados). Portanto **nenhum número de resultado do relatório é verificável a partir do repositório**: gaps 3,40/3,38/4,51, χ²=184,24, ranks médios, PI, TTT, KPIs do Twin. As verificações abaixo são de fórmula, de código, de literatura e de aritmética — não de resultados. A contagem de páginas também é **não verificável** neste ambiente (não há pdflatex instalado).

---

## 2. Alinhamento com o relatório parcial

### 2.1 Etapas do subprojeto aprovado

| Etapa | Prometido (Quadro 2 do subprojeto / parcial) | Entregue (relatório final) | Situação |
|---|---|---|---|
| 1–3 | Revisão bibliográfica; aprofundamento em Solomon e sensores; arquitetura | Feito; arquitetura descrita em `relatorio-final.tex:174-192` | **Cumprida** |
| 4 | Implementação inicial do algoritmo adaptado e do ambiente de simulação | Solver C++20 com 5 métodos, núcleo compartilhado, 15 testes, verificador independente | **Cumprida** |
| 5 | Relatório parcial | Entregue (mar./2026) | **Cumprida** |
| 6 | Digital Twin, interface de visualização e **Simulação Baseada em Agentes** | Twin + `dashboard.py` (375 linhas) + malha viária OSRM; **ABM ausente** (`grep -i agente` = 0 nos dois relatórios); **janelas dinâmicas inoperantes** | **Parcial** |
| 7 | Testes computacionais **e início da coleta/integração de dados reais** | 56 instâncias × 5 algoritmos × 30 sementes; dados reais = apenas localizações dos 38 PEVs (`:596`); as 10 instâncias reais de coleta em `data/instances/wcvrptw/` **nunca citadas** | **Parcial** |
| 8 | Análise dos resultados, **validação do modelo com dados reais** e ajustes | Friedman/Nemenyi + ablação + integral primal; validação com enchimento real declarada trabalho futuro (`:603`) | **Parcial** |
| 9 | Relatório final e documentação | Este documento | **Em curso** |

### 2.2 Objetivos específicos aprovados

| Objetivo específico | Situação | Evidência |
|---|---|---|
| Modelagem do enchimento (NHPP) | Cumprido | `:598-603` |
| Critério Push Forward | Cumprido (com erro de atribuição, §3) | `:164`, `:623-627`; `Route.hpp:67-79` |
| **Simular a comunicação LoRaWAN, avaliando desempenho em baixo consumo** | **NÃO cumprido e silenciado** | `grep -rni lora --include=*.py` retorna apenas `twin.py:34` ("explorando") e uma *string* narrativa em `dashboard.py:53`. Não há duty cycle, SF, payload, perda de pacote nem energia |
| Interface geoespacial em tempo real | Parcial | Figura `fig:road`, `dashboard.py`; sem "tempo real", sem métrica |
| Digital Twin | Cumprido na forma, comprometido no conteúdo | §4 e §5 deste parecer |
| Validação com dados reais | Parcial | `:596` — "localizações são reais, mas o comportamento de enchimento é simulado" |
| **Quantificação de benefícios econômicos/ambientais/sociais** | **NÃO cumprido** | Jogado para trabalhos futuros em `:668` |

### 2.3 Desvios de escopo e compromissos textuais em aberto

**(a) Pergunta de pesquisa trocada, sem uma linha de reconciliação.** Parcial (`:187`): "de que modo a **integração entre monitoramento IoT e heurísticas clássicas** [...]". Final (`:121`): "de que modo a **comparação criteriosa de heurísticas clássicas** [...]". O objeto da pesquisa aprovada virou meio, e o meio virou fim. Agrava-se: `:107` insere um título centrado ("Comparação rigorosa de cinco heurísticas clássicas...") **diferente do título oficial** declarado na própria tabela de identificação em `:101` e no PDF do subprojeto — no modelo (`template/main.tex:126-128`), o título centrado é exatamente o do subprojeto. Um avaliador que compare SAPPG e PDF verá dois títulos.

**(b) Compromisso da convenção lexicográfica: abandonado.** O parcial (`:196`) afirma que "**ambas as abordagens permanecem implementadas para comparação nas próximas etapas**". Doze meses depois, isso virou trabalho futuro (`:668`) e, factualmente, `Evaluator::lex`/`better_lex` (`Evaluator.hpp:41,46-48`) são **código morto** — nenhum uso fora do próprio cabeçalho, e `solve.cpp:97` não expõe flag de objetivo. A Tabela `tab:lex` **não** cumpre a promessa: ela reporta contagem de veículos de soluções otimizadas por distância.

**(c) Kit de vizinhanças: três documentos, três conjuntos.** `:248` chama o kit de cinco de "**o subconjunto selecionado**" no parcial. O único protocolo de seleção escrito (`docs/planejamento/neighborhood_selection_approach.md:291-300`) conclui outro conjunto (4 operadores, **com** `two_opt_inter`, **sem** `or_opt` e **sem** `cross_exchange`), e o parcial (`:251`) coloca o 2-opt inter na linha de "**Maior impacto nas melhorias mais relevantes**". O operador não existe no código (`Neighborhoods.hpp:58`) e a ablação nunca testa reincluí-lo.

**(d) Contradição quantitativa não reconhecida.** O Quadro 2 do parcial (`:249-259`) descreve Or-opt/Cross-exchange como "uso mais localizado e menos recorrente" e Swap como "efeito complementar"; a ablação do final (`:483-488`) mede Or-opt como 2º mais importante (+1,53) e Swap como o menos (+0,11). São medidas diferentes (frequência × contribuição marginal) e podem divergir legitimamente — mas **isso precisa ser dito**, e a afirmação central do parcial (`:237`, inter > intra) não é reavaliada porque a ablação agrega intra e inter.

**(e) C102.** Parcial (`:295`, `:335`): "o GRASP reativo apresentou o melhor resultado". Final (`tabela_por_instancia.tex:25-31`): **empate triplo** — GRASP, GRASP-R e Tabu todos em 827,3 com gap 0,00 em negrito. Basta uma nota de rodapé, mas ela não existe.

**(f) Vínculo com o projeto guarda-chuva sumiu do texto.** O parcial cumpria (`:187`). No final, "Pesquisa Operacional e Inovação em Logística Regional" aparece **apenas** na tabela de identificação (`:100`); nem a Introdução (`:121`) nem a Metodologia (`:170-192`) o mencionam, contra exigência expressa do modelo (`exemplo:162` e `:200`).

**(g) "Atividades realizadas" é autocontraditória.** `:658` diz que as Etapas 6 e 7 "**encontram-se avançadas**", que 8 e 9 "**estão em finalização**", e que "houve **avanço de cronograma**". No 12º de 12 meses, declarar duas etapas inacabadas e chamar isso de avanço é confissão de entrega incompleta — e é desmentido pelo próprio conteúdo do relatório, que reporta calibração, estudo completo, análise estatística e Twin com resultados.

---

## 3. Revisão metodológica e de literatura

### 3.1 Solomon I1

**Correto:** as equações de $c_{11}$, $c_{12}$, $c_1$ e $c_2$ (`:196-199`) são idênticas a Solomon (1987, p.257), inclusive sinais e o papel de $\mu$ e $\lambda$; $c_2(u)=\lambda d_{0u}-\min c_1$ é a redução correta. A implementação confere (`SolomonI1.cpp:45`).

**Errado (alto).** `:200` chama $(\mu{=}1,\lambda{=}2,\alpha_1{=}1,\alpha_2{=}0)$ de "**configuração canônica**". Solomon não define configuração canônica alguma: na p.259 ele reporta "the best of eight runs", com **quatro** combinações de parâmetros × **dois** critérios de semente por instância. Pior, a combinação adotada é a **inserção por distância**, que Solomon (p.263) conclui ser **inferior**: *"time insertion proved clearly superior to distance insertion. It was used in obtaining the best solution to 21 of 27 problems"*. A justificativa dada — "coerente com o objetivo DIMACS" — é *non sequitur*: o critério de inserção é escolha de construção, não de função-objetivo. Consequência direta: o gap de 35,97% da I1 **não é comparável** aos números publicados da I1 e o relatório não avisa. Falta ainda a restrição de normalização $\alpha_1+\alpha_2=1$ (Solomon, p.257) na equação de `:198`. Corrigir também `TUNING_RATIONALE.md:18`.

**Errado (médio).** `:229` afirma, sem citação, que semear pelo cliente mais distante do depósito "tende a reduzir o número total de veículos". Solomon (p.264) atribui esse argumento ao critério **oposto** (*earliest deadline*), usado por ele em 16 das 27 melhores soluções de horizonte longo (R2/C2/RC2). O trabalho fixa um único critério para as 56 instâncias (`SolomonI1.cpp:21-22`, `Grasp.cpp:28-29`) sem testar a alternativa. Ressalva justa: o ranking de Solomon vale sob a hierarquia lexicográfica dele, não sob distância pura — o que está demonstrado é que **a justificativa contradiz a fonte**, não que o critério seja pior.

### 3.2 VND

**Correto:** a mecânica (melhor-melhora em $N_\ell$, reinício em $\ell{=}1$ na melhora, avanço caso contrário, parada em ótimo local sobre todas) é literalmente a Algorithm 2 do *Handbook of Metaheuristics* (2019, cap. 3, p.61) e fiel a Hansen & Mladenović (2001). `VND.cpp:6-9` confere com `:257`.

**Frágil (baixo).** A ordem $\langle$Relocate, Or-opt, Swap, 2-opt, Cross-exchange$\rangle$ é apresentada **sem uma linha de justificativa**, e o comentário do código (`VND.hpp:17-18`) alega base empírica que a ablação entregue não fornece (`ablation.py:34-42` testa subconjuntos, nunca ordens). Não procede acusar violação de "cardinalidade crescente" — o Handbook admite o ranqueamento por benefício observado como critério legítimo. O que falta é a frase de justificativa, e o teste de 4-6 ordens custa 0,04 s/instância.

### 3.3 GRASP

**Correto:** a RCL de `:290` **não** tem erro de sinal — como $c_2$ é maximizado, $c_2(u)\ge c^{\max}-\alpha(c^{\max}-c^{\min})$ é o espelho exato da forma canônica de Feo & Resende para minimização. $\alpha{=}0$ guloso / $\alpha{=}1$ aleatório está coerente.

**Frágil (médio).** A aleatorização atua **somente** na escolha do cliente: a semente de cada rota permanece determinística (`Grasp.cpp:26-29`) e a posição de inserção é sempre a de melhor $c_1$ (`Grasp.cpp:44-53`). A afirmação de `:322` de que "cada RCL produz uma topologia de rotas diferente" é mais forte do que a construção suporta.

### 3.4 GRASP Reativo

**Correto:** $q_i=(Z^*/\bar{Z}_i)^\delta$ com médias **acumuladas** ao longo de toda a execução é fiel a Prais & Ribeiro (2000) e ao capítulo de Resende & Ribeiro. O aquecimento de $g{=}10$ está implementado (`Grasp.cpp:90,108`).

**Errado como experimento (alto).** Com `block=199` (`tuned.json:3`; `Grasp.cpp:138`: `iter % cfg.block == 0`) e **390 iterações médias** (`:506`), as probabilidades são recalculadas **uma única vez por execução**. Descontado o aquecimento, cerca de metade das iterações amostra $\alpha$ de uma distribuição ainda uniforme. **A comparação "reativo × fixo" não testa o mecanismo de Prais & Ribeiro** — testa um GRASP com $\alpha$ sorteado quase uniformemente. Logo, a conclusão de `:363` ("o efeito líquido sobre o gap é marginal") é **artefato da calibragem**, não achado sobre o método. É o tipo de conclusão que um parecerista rejeita de imediato.

### 3.5 Busca Tabu

**Correto:** determinismo confirmado (`solver/src/TabuSearch.cpp` não consome RNG; `solve.cpp` instancia `Rng` apenas no ramo `grasp|rgrasp`), coerente com `:444`. A aspiração pelo melhor global existe.

**Errado (médio).** `:186`, `:366` e `:427` descrevem o atributo tabu como "algum cliente que ele **toca**". `involved()` (`TabuSearch.cpp:11-30`) registra e testa apenas o(s) **cliente-âncora**: 1 para Relocate/Or-opt (mesmo em cadeias de 3), 2 para Swap/Cross-exchange (mesmo trocando 6). O texto **não permite reproduzir a implementação**, o que fere a alegação de reprodutibilidade. Falta ainda citar a alternativa padrão da literatura de roteamento, o par (cliente, rota) de Cordeau, Laporte & Mercier (2001).

**Desvio menor (baixo).** A busca **encerra** quando não há movimento admissível (`TabuSearch.cpp:64`; Algoritmo 7, `:376-378`), em vez da *aspiration-by-default* ("least tabu") prescrita por Glover & Laguna (1997) — livro que sequer está na bibliografia (só Glover 1989/1990). Os próprios autores registram que a situação é rara; o que falta é (i) uma frase reconhecendo a diferença e (ii) instrumentar e reportar a causa de término. **Não é verificável** a partir do repositório que o impasse ocorra na prática.

### 3.6 Vizinhanças — erro conceitual (alto)

`:248` afirma que a reorganização entre rotas "que seria do 2-opt inter" é exercida pelo Cross-exchange e pelo Or-opt. **Isso é falso.** O 2-opt\* (Bräysy & Gendreau 2005, Parte I) troca **caudas de comprimento arbitrário** entre duas rotas, preserva orientação e **pode fundir duas rotas em uma** — a única operação desta família capaz de reduzir a frota em um movimento, exatamente a capacidade cuja ausência o próprio relatório lamenta em `:158`. O Cross-exchange implementado troca **segmentos internos de no máximo 3 clientes** (`Neighborhoods.cpp:273-276`). Além disso, a ablação invocada como justificativa empírica **só remove** operadores do kit — **nunca testa adicionar** o 2-opt\*, portanto não pode justificar a omissão. Erros de atribuição no mesmo parágrafo: o Or-opt é de Or (1976), o Cross-exchange de Taillard et al. (1997) e o 2-opt\* de Potvin & Rousseau (1995) — este último é justamente o citado como fonte dos cinco operadores.

*Ressalva de justiça:* **não** procede o argumento de que a omissão explique a contagem de veículos — 8,2 do trabalho é menor que os 8,6 da referência de mínima distância (`:588`).

### 3.7 Viabilidade e complexidade

**Erro de atribuição (médio).** `:164` e `:229` creditam a Solomon (1987) um teste de viabilidade em $O(1)$. O Lema 1.1 de Solomon (p.256) é precedido pela afirmação explícita de exame **sequencial**, $O(m)$ no pior caso. O $O(1)$ vem da pré-computação do *forward time slack*, devida a **Savelsbergh (1985)** — ausente da bibliografia. A implementação (`Route.hpp:67-79`) é exatamente a recursão de Savelsbergh; o código está certo, a citação não.

**Contradição interna (médio).** `:423` afirma que "cada operador de melhoria" aplica o teste Push Forward. `:186` e `:248` do mesmo documento dizem o contrário, e o código confirma `:186/:248`: `eval_insert` só é chamado em `SolomonI1.cpp:39` e `Grasp.cpp:45`; **todos** os operadores usam `evaluate_seq` (`Neighborhoods.cpp:128,140,171,177-178,204,234,245,286-287`). Isso corrompe a leitura do custo computacional e desperdiça a oportunidade de discutir avaliação incremental (Kindervater & Savelsbergh; Vidal et al. 2013).

**Omissão (médio).** A busca estritamente viável (`:167`, `:398`; `Neighborhoods.cpp:42`) é apresentada só como garantia. A literatura central de VRPTW (Cordeau et al. 2001; Taillard et al. 1997; Vidal et al. 2013 — **nenhum na bibliografia**) trabalha com inviabilidade penalizada e auto-ajustável, precisamente porque o espaço viável é desconexo sob vizinhanças locais. A banca vai perguntar "vocês testaram permitir inviabilidade penalizada?" e hoje o relatório não reconhece a pergunta.

### 3.8 Benchmark, convenções e baseline

**Correto (e merece crédito):** as três afirmações da Seção 2.2 são literalmente sustentadas pelas regras do 12º DIMACS — minimização só de distância com checagem do limite $V$; $d_{ij}=\lfloor 10 e_{ij}\rfloor/10$ (**truncamento**, como o relatório escreve); tempo igual à distância. A fórmula do integral primal em `:553` coincide com a das regras.

**Errado (médio) — taxonomia de convenções.** `:573` fala em "**três** convenções incompatíveis: DIMACS (truncamento), SINTEF (precisão dupla, 2 casas) e euclidiana real (sem arredondamento)". SINTEF **é** a euclidiana em precisão dupla — as 2 casas são regra de **apresentação** das tabelas. O relatório conta a mesma convenção duas vezes e deixa de fora a terceira genuinamente distinta (arredondamento ao inteiro, `nint`/`ceil`, TSPLIB). Prova disponível no próprio repositório: as mesmas rotas de C101 custam **827,3** sob truncagem e **828,94** sob precisão dupla (idem R201: 1143,2 vs 1147,82). Corrigir também `DistanceMatrix.hpp:17`, que afirma que a truncagem reproduz "os 56 custos de referência Dinamics/**SINTEF**" — ela reproduz os do **CVRPLIB**.

**Errado (médio) — baseline.** O rótulo "**Dinamics**" (`:573`, `:580`) não é definido nem citado em ponto algum do relatório, do README ou do código (provável corruptela de "DIMACS"). A fonte real é o CVRPLIB, cuja coluna "Opt" marca *yes* para as 56 Solomon-100 — ou seja, a referência é **ótima** sob a convenção de mínima distância, e o relatório poderia usar o termo mais forte "gap ao ótimo". Além disso, a URL do DIMACS em `:683` retorna **HTTP 404**: a única citação que sustenta as Seções 2.2 e 4.5 aponta hoje para página inexistente.

**Omissão (baixo).** As regras tratam o limite $V$ como restrição de viabilidade; o verificador não o checa (`Validator.cpp:60-61` compõe `feasible` sem termo de frota; `Instance.hpp:26` rotula $V$ como "informational"). Sem impacto prático (máximo observado 21 contra $V{=}25$), mas `:165` diz "as **quatro** restrições" quando são cinco.

**Melhoria (baixo).** Truncar para baixo e usar a distância também como tempo é o "esquema otimista": **aproximação externa** da região viável. Vale registrar que toda solução viável com distâncias reais permanece viável sob truncagem, mas **não** a recíproca, e qualificar `:111/:167/:471` com "sob a convenção DIMACS adotada". *Não* procede o risco no Digital Twin: `road_twin.py:96-97` substitui integralmente as matrizes pelos valores do OSRM.

**Omissão (médio) — o benchmark natural do tema está no repositório e não é usado.** `data/instances/wcvrptw/` contém as 10 instâncias reais de coleta de **Kim, Kim & Sahoo (2006)**, com baselines publicadas (Kim et al. 2006; Benjamin & Beasley 2010/2013) e da **mesma família** da I1 implementada; estão listadas em `README.md:26` e carregáveis (`maps.py:77`). `grep -rli wcvrptw docs/` retorna **zero**. Manter 10 instâncias reais de coleta num subprojeto intitulado "Otimização Dinâmica de Rotas para Coleta de Resíduos Sólidos" e não mencioná-las é indefensável — usar, ou declarar por escrito por que não.

**Omissão (alto) — literatura.** Dos 18 itens da bibliografia (`:679-698`), apenas três tratam de heurísticas de VRPTW. Não há seção de trabalhos relacionados: salta-se da Introdução (quase toda sobre IoT) direto para a formulação. Faltam Bräysy & Gendreau (2005, I e II), Savelsbergh (1985/1992), Cordeau et al. (2001), Taillard et al. (1997), Or (1976), Vidal et al. (2013). Consequência prática: **o leitor não tem como calibrar se 3,4% de gap é bom ou ruim**, porque o estado da arte nunca é informado (o HGS-VRPTW do 12º DIMACS opera em frações de 1%). Agravante: o rascunho anterior da própria autora (`rascunhos-antigos/relatorio-v2/main.tex:111,128`) já continha essas citações — é **regressão**, não lacuna.

---

## 4. Calibragem de parâmetros — a avaliação crítica

### 4.1 Veredito

**A seção de calibragem não é robusta o bastante para pesquisa acadêmica no estado atual, e é o ponto mais frágil do relatório.** Ela enuncia corretamente um princípio (desacoplar orçamento de qualidade) e depois falha em executá-lo em todos os pontos onde a execução importa. Aparência de sofisticação, sem os controles que a tornariam válida. A boa notícia: quase todos os consertos são baratos e o repositório já contém as peças.

### 4.2 Falha 1 — o "joelho" não existe: K é o teto de cada grade (**crítico**)

**Evidência.** `knee_K.py:42-44`:
```
KGRID = {"grasp":[20,40,60,90,130,180,250], "rgrasp":[...,250], "tabu":[100,200,400,600,900,1400]}
```
`knee_K.py:102-104`: `best = min(means)`; `knee = next((K for K,m in ... if m <= best + EPS_PP), Ks[-1])`, com `EPS_PP = 0.10` (`:36`). Resultado em `experiments/config/fixed_K.json`: **250, 250, 1400** — exatamente `Ks[-1]` nos três casos.

**Prova.** O próprio script declara (`:4-5`) que K é um orçamento monótono em qualidade, e K não altera a trajetória (só entra como `max_no_improve`). Logo $m(K)$ é não-crescente e $best = m(K_{\max})$. A regra devolve o teto **se e somente se** $m(K) > m(K_{\max}) + 0{,}10$ para **todo** $K < K_{\max}$ — isto é, **no último degrau da grade a curva ainda caía mais que a própria tolerância**. Não houve joelho: houve truncamento.

**Consequências.** (i) K é propriedade da grade escolhida pela analista, não do algoritmo; estender a grade moveria K para a direita, sempre. (ii) A legenda de `:440` — "a partir do joelho, mais paciência rende retorno desprezível" — é **refutada pelos dados que geraram K**. (iii) O desacoplamento falhou no seu próprio objetivo declarado: `:435` justifica o procedimento dizendo que calibrar K pelo gap "o levaria ao teto do intervalo de busca", e o procedimento adotado caiu **exatamente no teto**. (iv) Divergência código × texto: `:435` diz "do gap obtido com o **maior K testado**", o código usa `min(means)`; com 3 sementes (GRASP/Reativo) e 1 (Tabu) e sem qualquer estimativa de dispersão, os dois critérios podem divergir. (v) `EPS_PP=0,10` não é justificado em lugar algum e é **incoerente com o resto do trabalho**: o relatório trata como digna de nota a diferença de 0,02 p.p. entre GRASP e Reativo (`:505-506`) e declara 0,10 p.p. desprezível para K — cinco vezes maior. (vi) `knee_K.py:91-92` descarta execuções falhas em silêncio (`if g is not None`), de modo que médias em K diferentes podem vir de amostras de tamanhos diferentes sem registro.

**Correção exigida.** Estender em escala log até saturar de fato (GRASP/Reativo até 2560; Tabu até 25600), com ≥10 sementes e IC95%; adotar critério formal e pré-declarado (Kneedle, Satopää et al. 2011, ou máxima distância à corda) **mais** um critério de aceitação verificável ($m(K)-m(K_{\max})\le\varepsilon$ **e** $m(K)-m(2K)\le\varepsilon$, com $\varepsilon$ menor que o menor efeito que o estudo pretende declarar); alinhar `:435` ao código; substituir o descarte mudo por contagem e log. **Se, com a grade estendida, ainda não houver platô, a saída honesta é abandonar a palavra "joelho" e declarar K como decisão de orçamento por fiat** — posição já defendida no próprio `TUNING_RATIONALE.md:44-49`.

### 4.3 Falha 2 — dois vencedores contra o teto do intervalo (**alto**)

`tuned.json:3-4`: `--block 199` num intervalo `(20, 200)` (`rgrasp.txt:5`) e `--tenure 39` num intervalo `(5, 40)` (`tabu.txt:4`). São 99,4% e 97,4% da faixa, em **dois cenários independentes** — o sintoma clássico de região experimental mal posicionada (Box-Wilson: ótimo na fronteira obriga a deslocar a região antes de qualquer conclusão). `:494` reporta ambos **sem uma linha de ressalva**, como se fossem valores interiores e finais. Um parecerista que abra os arquivos de parâmetros derruba a seção em trinta segundos.

**Consequência substantiva** (não apenas formal): `block=199` com ~390 iterações significa **uma única atualização reativa por execução** — o irace, na prática, **desligou o mecanismo reativo**. A equivalência 3,38% × 3,40% é explicada melhor por isso do que pela racionalização de `:363`.

**Correção exigida.** Reexecutar com `tenure ∈ (5,80)` e `block` **relativo a K** (buscar `block_frac ∈ (0,01; 0,5)`, garantindo ≥3-5 atualizações por execução), repetindo até vencedor interior. Acrescentar a tabela de diagnóstico de fronteira. Registrar o atenuante honesto: o teto 40 vinha da regra de literatura *tenure* ≈ 0,1–0,4·n (`TUNING_RATIONALE.md:36-37`).

### 4.4 Falha 3 — circularidade meia-concluída e proveniência ausente (**alto**)

O desenho é $K=f(q_0)$ seguido de $q_1=g(K)$, com $q_1\ne q_0$ e **nenhuma nova iteração**, sem verificação de que $K(q_1)=K(q_0)$ e sem critério de parada declarado. As mudanças não são desprezíveis: $\delta$ 1,7822 → 1,3992 (−21%), *block* 183 → 199, *tenure* 35 → 39, $\alpha$ 0,1596 → 0,1517. E os valores $q_0$ são **constantes escritas à mão** em `knee_K.py:39-41` **sem nenhuma proveniência no repositório** — `grep` em todo o repo e nos 3 commits do histórico os encontra apenas ali. Pior: `run_full_study.sh:6-8` admite **por escrito** que a etapa que define K está fora da cadeia reprodutível, o que **contradiz frontalmente** `:179` ("todo o experimento é reproduzível por um único comando").

**Correção exigida.** Procedimento **alternado** e explícito, partindo dos *defaults* do próprio código ($\alpha{=}0{,}30$; $\delta{=}1{,}0$/`block=50`; `tenure=15` — `Grasp.hpp:22,25,26`, `TabuSearch.hpp:16`), com critério de parada pré-declarado e no mínimo duas rodadas completas publicadas numa tabela rodada | K | parâmetros | gap(treino). Alternativa igualmente defensável e mais barata: **calibrar sob orçamento de tempo fixo e igual**, eliminando K do problema. Colocar `knee_K.py` dentro de `run_full_study.sh` como etapa 0.

### 4.5 Falha 4 — a comparação não é isonômica (**médio**)

`:505-507`: Tabu 11,6 s; GRASP 15,3 s; Reativo 18,5 s — o Tabu opera com 75,8% e 62,7% do tempo dos concorrentes, e é justamente o método cortado mais longe da saturação. O relatório reconhece a limitação em `:430`, mas `README.md:153-154` afirma "com todos os algoritmos parando pelo mesmo critério — **comparação em pé de igualdade**", o que é factualmente falso. Note que a assimetria **não** ameaça a conclusão de equivalência (mais orçamento aproximaria o Tabu); ela expõe a observação de rank de `:664`. O experimento sob tempo igual já existe (`primal_integral_experiment.py:38`, `T_MS = 15000`) mas roda **apenas 3 instâncias** — fato omitido do texto.

### 4.6 Falha 5 — a calibragem nunca é mostrada valer a pena (**médio**)

Uma seção de calibragem existe para responder a "a calibragem valeu a pena?". `:432-441` gasta um parágrafo e uma figura no **procedimento** e zero linhas no **efeito**. Não há contraste *default* × calibrado, embora as mudanças propostas sejam enormes ($\alpha$ 0,30→0,15, −49%; *block* 50→199, +298%; *tenure* 15→39, +160%). Sem esse contraste, não se distingue "ganho real" de "ruído" de "algoritmo insensível na faixa" — e a terceira hipótese é perfeitamente plausível, dado que as três meta-heurísticas terminam indistinguíveis. **`runner.py:99-105` já aceita `--params-file`: produzir o baseline é trivial.** Regra de honestidade: se o Δ não for significativo, escrever isso — "a calibragem não produziu ganho detectável, o que indica robustez aos hiperparâmetros na faixa testada" é resultado publicável e mais forte que a narrativa atual.

### 4.7 Falha 6 — precisão espúria e assimetria de padrão (**médio**)

$\alpha=0{,}1517$ e $\delta=1{,}3992$ (`:494`) implicam precisão que nenhuma evidência sustenta; as quatro casas são o *default* `digits=4` do irace, não declarado em `scenario.txt`. Assimetria reveladora: `:648` faz **análise de sensibilidade** para os parâmetros de um cenário **simulado** (limiar, capacidade, urgência do Twin) e **nenhuma** curva desempenho × parâmetro é apresentada para os hiperparâmetros dos algoritmos, que são o objeto central da pesquisa.

### 4.8 Falha 7 — protocolo e proveniência do irace (**médio**)

- **Orçamento indeterminado:** `scenario.txt:18` = 2000 (código morto, pois `1_calibrate.sh:42` sempre passa `--max-experiments`); `1_calibrate.sh:16` = 1500; `run_full_study.sh:22` = 1200. **Nenhum é declarado no relatório**, que também omite iterações do racing, `testType`, `firstTest`, número de elites e semente.
- **Sem `seed`:** `1_calibrate.sh:38-44` não passa `--seed` e `scenario.txt` não o declara — **a corrida do irace não é reproduzível**. Para um trabalho cuja tese é reprodutibilidade (`:430`, `:455-456`), é inconsistência de princípio.
- **Sem `deterministic`:** o *default* é 0; como o Tabu não consome semente, repetições da mesma instância devolvem custo idêntico — orçamento desperdiçado e blocos perfeitamente correlacionados no teste interno do racing.
- **Via documentada errada:** `scenario.txt:9-12` documenta comandos manuais que **não** exportam `VRPTW_K` nem `VRPTW_BUDGET_MS`; quem os seguir calibra com **K desativado** e teto de **5 s** (`target-runner:24,49-50`) — regime incompatível com o do estudo. O caminho canônico (`1_calibrate.sh:25,40`) está correto, mas o repositório documenta o errado.
- **Sem guarda de inviabilidade:** `target-runner:53-58` nunca consulta `out.returncode`, apesar de `solve.cpp:179` sinalizar inviabilidade **depois** de já ter impresso o custo. Uma configuração que produzisse soluções inviáveis seria **premiada**. O `PENALTY` de 1e9 cobre só falha de *parsing*. Mesmo padrão em `knee_K.py:58-69`. Latente (não houve inviabilidade), mas é exatamente a função de um guarda.
- **Documento de apoio contraditório:** `:433` manda o leitor consultar `TUNING_RATIONALE`. Quem seguir o ponteiro encontra `:25` classificando **K como "calibrado"** e `:38-39` dando faixas `(20;150)` e `(50;1000)` que **nem contêm** os K usados (250, 1400). É o próprio relatório apontando para a metodologia oposta.
- **Sem auditoria:** `results/irace/` está no `.gitignore`; `tuned.json` é hoje um arquivo **sem proveniência auditável**, e é dele que saem todos os números da Seção 4.

### 4.9 Falha 8 — vazamento estrutural (**médio**)

O relatório entrega treino e teste (`:528`), o que é correto; a incoerência é com `README.md:147`. Mas há um vazamento substantivo real: a **ablação de vizinhanças** (`:473-491`) foi computada nas **56** instâncias e é usada em `TUNING_RATIONALE.md:19` para justificar uma **decisão de projeto do algoritmo**. Decisão de arquitetura validada com dados de teste é vazamento clássico. Refazer só nas 28 de treino custa quase nada (as deltas vão de +0,11 a +4,56 p.p., a hierarquia é robusta) e fecha a brecha.

### 4.10 Esboço da seção reescrita

> **3.x Calibração de parâmetros e definição do orçamento de busca**
>
> **3.x.1 Protocolo.** Regra única e declarada: toda decisão — hiperparâmetros, kit de vizinhanças e orçamento K — é tomada **exclusivamente** sobre as 28 instâncias de treino; o conjunto de teste é tocado uma única vez, para produzir a tabela principal. **Tabela 1** — "O que é calibrado e o que é fixado": Elemento | Decisão (calibrado / fixado por justiça / **fixado por orçamento**) | Valor ou faixa | Justificativa | Referência. *K entra como "fixado por orçamento", nunca como "calibrado".*
>
> **3.x.2 Definição do orçamento K.** Enunciar em uma linha a monotonicidade de $gap(K)$ e a consequência lógica (um orçamento monótono não pode ser escolhido minimizando o objetivo). Descrever a varredura em grade **log estendida até saturação**, 10 sementes, só no treino. Declarar **antes** o critério formal de joelho e o critério de aceitação. **Figura 1** — gap × K em escala log, uma linha por método, IC95% sombreado, joelho marcado, platô hachurado; painel inferior com tempo médio × K. **Tabela 2** — K | gap médio (IC95%) | Δ vs. K anterior | tempo médio | iterações | iteração da última melhoria. *Frase obrigatória:* se o platô não for atingido, dizer que K é decisão de orçamento por fiat e abandonar a palavra "joelho".
>
> **3.x.3 Equalização de esforço.** Declarar $T^*$ e mostrar que os K adotados produzem tempos médios de CPU estatisticamente indistinguíveis — ou adotar parada por tempo como regime primário. **Tabela 3** — método | K | tempo médio | IC95% | teste de igualdade.
>
> **3.x.4 Configuração automática (irace).** **Tabela 4** — parâmetro | tipo | faixa inicial | vencedor | **posição (interior/borda)** | faixa expandida | vencedor final | posição. **Tabela 5** ("Configuração da corrida") — nº de parâmetros | maxExperiments | iterações do racing | firstTest | testType | confidence | **deterministic** (1 para Tabu) | **seed** | digits | nº de elites | CPU total. Declarar a política de fronteira *ex ante* e mostrar que foi aplicada.
>
> **3.x.5 Procedimento alternado K ↔ qualidade.** Pseudocódigo: $q_0$ = *defaults* da literatura → $K_1=\text{joelho}(q_0)$ → $q_1=\text{irace}(K_1)$ → $K_2=\text{joelho}(q_1)$ → … até $|K_{t+1}-K_t|\le 10\%$ e $|gap(q_{t+1})-gap(q_t)|\le\varepsilon$. **Tabela 6** — rodada | K | parâmetros | gap(treino), com ≥2 rodadas, demonstrando estabilidade.
>
> **3.x.6 A calibragem valeu a pena?** **Tabela 7** (28 instâncias de teste, 30 sementes, mesmo K) — Algoritmo | config. *default* | gap *default* ± IC95 | config. calibrada | gap calibrado ± IC95 | Δ (p.p.) | **Wilcoxon pareado (p)** | tamanho de efeito. Opcional: ablação de configuração (Fawcett & Hoos, 2016).
>
> **3.x.7 Sensibilidade.** **Figura 2** — 4 painéis ($\alpha$, $\delta$, *block*, *tenure*), gap médio no treino com IC95%, valor do irace marcado, **faixa de indiferença** sombreada. **Tabela 8** — parâmetro | valor irace | intervalo de indiferença | *default* | o *default* está dentro? Reportar $\alpha=0{,}15$, com nota explicando que a 4ª casa é o `digits` do irace.
>
> **3.x.8 Ameaças à validade da calibragem.** Parágrafo curto e honesto: orçamento por fiat se não houve platô; circularidade residual; grade discreta; 28 instâncias; ruído entre sementes; não generalização para $n\ne 100$, para as instâncias WCVRPTW e para o Digital Twin.
>
> Com essa estrutura, o resultado **primário** passa a ser: 28 instâncias de teste, sob tempo de CPU igual, com Friedman/Nemenyi e CD recalculado para $N{=}28$ ($CD=1{,}153$, não 0,815); as 56 instâncias e a parada por K viram análises secundárias declaradamente contaminadas pela calibragem.

---

## 5. Rigor estatístico

**Correto (e reproduzi):** a fórmula do fator de correção de empates coincide com a implementação do `scipy.stats.friedmanchisquare`; $q_{0,05}(k{=}5,\infty)/\sqrt2 = 2{,}728$; $CD = 2{,}728\sqrt{30/336} = 0{,}8152$; $\chi^2_{sf}(184{,}24;4)=9{,}16\times10^{-39}$; $p(\text{GRASP}\times\text{Tabu})=0{,}176$; os ranks somam exatamente 15. A divisão treino/teste é estratificada e balanceada (C1 4/5, C2 4/4, R1 6/6, R2 6/5, RC1 4/4, RC2 4/4).

**F1 — a conclusão central é sensível à composição do pool (alto).** O rank médio da I1 é **exatamente 5,00** (`:528`), o que só é possível se a I1 for pior em **todas** as 56 instâncias — o que é estrutural, já que o VND parte da I1 e só aplica movimentos melhorantes. Remover essa coluna constante **não altera nenhum rank** dos outros quatro, mas muda $k$ de 5 para 4. Recomputei: $q_{0,05}(4,\infty)/\sqrt2 = 2{,}5689$, $CD = 2{,}5689\sqrt{20/336} = \mathbf{0{,}6268}$ — e a diferença observada GRASP × Tabu é **0,66 > 0,6268**, ou seja, **significativa**. A conclusão que sustenta a seção de resultados depende de ter incluído no pool um método estruturalmente dominado — exatamente a crítica de Benavoli, Corani & Mangili (2016) ao pós-teste de *mean-ranks*. *Correção:* adotar Wilcoxon pareado + Holm sobre as 10 comparações (decisão independente do pool) e, como diagnóstico mínimo, reportar o Nemenyi restrito aos 4 declarando que a conclusão muda. *Ressalva de verificabilidade:* a aritmética acima é minha e confere; a matriz de ranks por instância **não é verificável** (results/ não versionado).

**F2 — "estatisticamente equivalentes" é erro de inferência (alto).** `:664` converte não-rejeição em afirmação positiva de equivalência, sem teste de equivalência, sem tamanho de efeito e sem análise de poder. A diferença prática é grande: 4,51 − 3,40 = **1,11 p.p.**, ou **+33% relativos**, consistente em direção nas **três** famílias (`:521-523`). E o poder é baixo por construção: com $k{=}5$, $N{=}56$, a menor diferença detectável é 0,815 — 20% de toda a escala de ranks. Pior, `:528` apresenta o teste em 28 instâncias como "confirmação": com $N{=}28$, $CD=1{,}153$ (recalculei), então a não-rejeição é consequência **mecânica** da perda de poder, e os dois testes nem são independentes (um é subconjunto do outro). *Correção:* trocar por "não foi possível rejeitar a hipótese de igualdade com o poder disponível ($N{=}56$, $k{=}5$; diferença mínima detectável 0,815)"; reportar diferença mediana com IC bootstrap e proporção de vitórias; se quiser afirmar equivalência, TOST com margem declarada ou ROPE bayesiano (Benavoli et al., 2017).

**F3 — esforço desigual e mistura de estatísticas (médio/alto).** A coluna "Gap melhor" compara o **mínimo sobre 30 execuções** do GRASP (1,92, em negrito) com o valor de **uma única** execução do Tabu (4,51) — erro clássico apontado por Barr et al. (1995). Pior, a mesma mistura corrompe a Tabela lexicográfica: `:573` afirma "nossas soluções (GRASP) **dominam o SINTEF** em distância (**média** 992,2 contra 1017,8)", mas 992,2 é o *best-of-30* (`lexicographic_table.py:36` usa `dist_best`); a **média real**, recomputável do apêndice, é **1007,1**, e na família C o GRASP passa a ser **pior** que o SINTEF (715,4 contra 714,1). A palavra "dominam" e a palavra "médios" da legenda são ambas insustentáveis. *Correção:* duas colunas explícitas (média de 30 / melhor de 30); remover o negrito de 1,92 ou isolá-lo em tabela de "melhor solução encontrada" com o número de execuções em cada linha.

**F4 — vazamento nas tabelas de manchete (médio).** Tabelas de gap global (`:498`), por família (`:514`), lexicográfica (`:577`), apêndice e o diagrama CD exibido (`cd_diagram_full`, `:532`) são todos sobre as **56**, das quais 28 o irace viu. O relatório repete no teste **apenas** o teste de Friedman, nunca os gaps — de modo que **falta a medida direta do superajuste**. *Correção:* publicar gap(treino) × gap(teste) por algoritmo e rotular as tabelas de 56 como "inclui as instâncias de calibração".

**F5 — ablação sem inferência (médio).** `:474` e `:248` afirmam que "remover **qualquer** operador piora". O dado por instância já existe (`ablation.py:79-81`), e refeita a conta: remover o Swap **piora em 15, empata em 36 e melhora em 5**, com mediana nula e Wilcoxon pareado $p\approx0{,}086$ — **não significativo**. Nem o 2-opt sobrevive com folga ($p\approx0{,}012$ bruto). Além disso: sem controle de multiplicidade (5 comparações), o desenho **cumulativo** foi computado e **não** reportado (seleção parcial de resultados), e a ablação foi feita **só com VND** e transportada às meta-heurísticas sem ressalva. *Correção:* Wilcoxon + Holm, tamanho de efeito, contagem piora/empata/melhora, publicar o cumulativo, restringir a afirmação aos operadores com efeito detectável.

**F6 — integral primal (alto).** Foi medido em **3 instâncias** (`primal_integral_experiment.py:39`: R101, RC101, R201 — nenhuma da família C) com réplicas desbalanceadas (5/5/1/1, `:63`), sem dispersão e sem teste; `:555` diz apenas "Reexecutamos os métodos", depois de um parágrafo inteiro sobre as 56, e `:557` conclui "**confirmando** o ordenamento". A própria legenda da figura gerada exibe o número que o texto omite. Falta ainda quantificar o descasamento com o protocolo oficial (T=1.800 s padronizados por PassMark 2.000 para $n\le201$) e registrar que PI=10 é o pior valor possível — necessário para dar escala ao 7,66 do VND. *Correção:* declarar $n{=}3$ e as réplicas; trocar "confirmando" por "sugerindo, em caráter exploratório"; idealmente estender às 28 de teste com sementes uniformes.

**F7 — TTT sem função (médio).** 100% de sucesso significa alvo trivial: a curva descreve tempo de execução, não discrimina nada. Falta o essencial do instrumento (Aiex, Resende & Ribeiro, 2007): **comparar** algoritmos e testar a exponencial deslocada por QQ-plot. Há um algoritmo, uma instância, nenhum ajuste. Além disso, as execuções herdam `--max-no-improve 250` **junto com** `--target`, misturando dois mecanismos de censura, e gravam traços com o mesmo padrão de nome do estudo principal (`$RAW/traces`), **sobrescrevendo** `grasp_R101_s1..s30`. *Correção:* três alvos (3%/1%/0,2%), três métodos na mesma figura, ≥3 instâncias, QQ-plot, desativar K nas execuções de TTT, diretório separado.

**F8 — coerência dos testes (baixo).** A estatística ômnibus corrige empates; `posthoc_nemenyi_friedman` **não** (fonte: `qval = dif/sqrt(k(k+1)/(6n))`, sem fator de empates). Com o $C$ implícito (167,1/184,24 = 0,9070), a CD corrigida seria 0,776 — não inverte a conclusão, mas a inconsistência precisa ser declarada. Demšar (2006) recomenda a estatística $F$ de Iman-Davenport; o relatório cita Demšar e usa a versão $\chi^2$. E não há controle de multiplicidade **entre** análises (56, 28, por família, por instância).

**F9 — reprodutibilidade estatística declarada e não realizável (alto).** Nada de `results/` versionado; sem `irace.log`; protocolo de semente descrito (`:188`, `:456`: "base + hash da instância + **índice da execução**") **não é o implementado** (`solve.cpp:126` passa a constante literal `0`; a variação vem só de `--seed`), e `std::hash<std::string>` é *implementation-defined*, restringindo a reprodutibilidade à mesma libstdc++. A contagem de execuções aparece de duas formas incompatíveis: "**dezenas de milhares**" (`:167`) e "**mais de sete mil**" (`:471`) — o estudo principal tem **3.528** (56 × [1+1+1+30+30]); somando ablação, joelho e TTT chega-se a ~5,5 mil.

**F10 — Digital Twin: inferência sobre n=1 (crítico, ver §7).** `:633` extrai "evidência de que coletar sob demanda é mais eficiente" de **uma única realização** de um processo estocástico, com diferença de distância de 0,44% e contagens de transbordo cujo desvio-padrão, sob Poisson, é da ordem de 4–5. A sensibilidade é *one-at-a-time* com uma semente, incapaz de detectar as interações que o próprio `:629` diz existirem. E `:633` extrapola — "as distinções observadas no benchmark de 100 clientes manifestam-se em escala maior" — afirmação sobre escalabilidade que **nenhum experimento do trabalho testa** ($n{=}38$ e $n{=}100$ apenas).

---

## 6. Estrutura e conformidade formal

**O preâmbulo é o do relatório PARCIAL, não o do FINAL.** `relatorio-final.tex:12` = `\documentclass[12pt, a4paper]` e `:60-65` = `helvet` + `\sfdefault` (Arial). O modelo exige "fonte Times New Roman, tamanho 10 [...] títulos das seções tamanho 12" (`template/exemplo:158`) e o template implementa `10pt` (`main.tex:8`), `\rmdefault` (`:35`) e `mathptmx` (`:73`). **Verificado por leitura direta dos dois arquivos.**

Demais não conformidades verificadas:

| Item | Exigido | Estado atual |
|---|---|---|
| Seções obrigatórias | resumo, introdução, **objetivos**, **referencial teórico**, metodologia, resultados, conclusões, referências (`exemplo:156`) | Faltam `\section{Objetivos}` e `\section{Embasamento Teórico}` |
| Cabeçalho, 4ª linha | **Grande Área** CNPq ("Ciências Exatas e da Terra", `main.tex:104`) | "Ciência da Computação" (`:79`) |
| Tabela de identificação | linha "Grande Área do Conhecimento (CNPq)" (`main.tex:139`) | ausente (`:95-104` traz só Área e Subárea) |
| Resumo | `\section*{Resumo}`, sem citações (`exemplo:144,146`) | texto corrido `\noindent\textbf{Resumo.}` (`:111`) com **7 citações** |
| Fonte das ilustrações | "elemento obrigatório, mesmo que seja produção do próprio autor" (`exemplo:220`) | **`grep -c "Fonte:"` = 0** em 13 figuras e 6 tabelas — e o **parcial cumpria** (`:228,261,289,334`) |
| Impessoalidade | 3ª pessoa (`exemplo:160`) | ~26 ocorrências de 1ª pessoa (`:111` Avaliamos, `:148` Adotamos, `:200` Usamos, `:573` "nossas soluções", `:580` "Nosso (GRASP)"…) |
| Extensão | 15 páginas A4 | 700 linhas densas + 13 figuras + 6 tabelas + 5 algoritmos + apêndice `longtable` de **410 linhas** — **estouro não verificável por compilação** (sem pdflatex no ambiente), mas praticamente inevitável |
| Bibliografia | `\bibliographystyle{hapalike2-NOand}` + `\bibliography{biblio}`, seção "Referências **Bibliográficas**" (`main.tex:178-181`) | `thebibliography` manual com 18 `\bibitem`, seção "Referências"; `biblio.bib` tem **14** entradas — faltam `dimacs12vrptw`, `cvrplib`, `potvin1995exchange`, `toth2002vehicle`, isto é, ao migrar, **4 citações viram "[?]"**, inclusive a do DIMACS |

**Conforma (registre-se):** margens 30/20/30/20 mm (`:76`), `\onehalfspacing` e ausência de recuo de parágrafo já atendem `exemplo:158`.

**Repositório e reprodutibilidade.** (i) `results/` não versionado ⇒ os 12 `\includegraphics{../../results/...}` apontam para arquivos ausentes: **o documento não compila com figuras a partir de um clone limpo**. (ii) `results/irace/` no `.gitignore` ⇒ `tuned.json` sem proveniência. (iii) O "portão de corretude" **não fecha em lugar nenhum**: `runner.py:67` não lê `returncode`, `target-runner:53-58` idem, `twin.py:117-119` idem, e `solve.cpp:162` grava o `.sol` **antes** do teste — a coluna `feasible` é gravada e **nunca conferida** por `aggregate.py`/`stats.py`. A afirmação de `:471` não tem artefato que a sustente. (iv) `docs/planejamento/*` mantém **três documentos inteiramente obsoletos** que descrevem a metodologia **oposta** (`irace_calibration_plan.md:33`: "`--max-no-improve 0` (disabled; time is the main budget)"), com caminhos (`scripts/irace/`, `bin/vrptw`, `src/main.cpp`) e flags (`--grasp-mode`, `--vnd-neighborhoods`) inexistentes. Higiene, mas um avaliador que abra o repositório encontra dois protocolos vivos e conflitantes.

---

## 7. Diagnóstico consolidado

| # | Sev. | Dimensão | Problema | Onde | O que fazer |
|---|---|---|---|---|---|
| 1 | **crítico** | Digital Twin | Janelas dinâmicas **inertes**: κ ∈ {0; 0,3; 0,6; 0,9} produz rotas bit-idênticas (H=5000 vs. rota ≤180 em escala 0–100); o Twin resolve um CVRP, não um VRPTW | `twin.py:39-40,129-130`; `maps.py:48`; texto `:627,:648` | Derivar H da escala (H≈300 com serviço 5) e reportar fração de janelas ativas por κ; **ou** remover a alegação de acoplamento com Push Forward e reclassificar o cenário |
| 2 | **crítico** | Digital Twin | KPI de transbordos reconta o mesmo bin cheio a cada ciclo; com episódios distintos o dinâmico perde em **10/10** sementes e é pior em distância em **8/10** | `sensors.py:43-45`; texto `:619,:633,:664` | Contar episódios (`was_full` antes do passo); ≥30 réplicas + Wilcoxon pareado; reescrever `:633` e `:664` |
| 3 | **crítico** | Calibragem | Não há joelho: K = 250/250/1400 são **o último ponto das três grades**; a legenda `:440` é refutada pelos dados que geraram K | `knee_K.py:36,42-44,102-104`; `fixed_K.json`; `:435,:440` | Grades log estendidas + ≥10 sementes + critério formal e de aceitação; se persistir, declarar K como orçamento por fiat |
| 4 | alto | Estatística | "Estatisticamente equivalentes" ≠ não-rejeição; diferença de 1,11 p.p. (**+33% rel.**) consistente nas 3 famílias; teste em N=28 apresentado como confirmação | `:664`, `:505-507`, `:521-523`, `:528` | Reescrever como não-rejeição com poder declarado; tamanho de efeito + IC; TOST/ROPE se quiser equivalência |
| 5 | alto | Estatística | Nemenyi depende do pool: com a I1 (rank **5,00**) fora, CD cai de 0,815 (k=5) para **0,627** (k=4) e GRASP×Tabu (0,66) vira **significativo** | `:528,:451-453`; `stats.py:53` | Wilcoxon pareado + Holm nas 10 comparações; reportar o Nemenyi restrito aos 4 e declarar que a conclusão muda |
| 6 | alto | Calibragem | Vencedores contra o teto: `tenure=39` em (5,40) e `block=199` em (20,200), reportados sem ressalva | `tuned.json:3-4`; `tabu.txt:4`; `rgrasp.txt:5`; `:494` | Reexecutar com tenure∈(5,80) e block relativo a K, até vencedor interior; tabela de diagnóstico de fronteira |
| 7 | alto | Calibragem | GRASP Reativo **degenerado**: 1 atualização de probabilidades por execução; a conclusão "efeito marginal" (`:363`) é artefato | `Grasp.cpp:138`; `tuned.json:3`; `:363,:506` | Buscar `block_frac` garantindo ≥3-5 atualizações; recalibrar; reportar nº médio de atualizações por execução |
| 8 | alto | Calibragem | Circularidade K↔qualidade meia-concluída; $q_0$ (α 0,1596 / δ 1,7822, block 183 / tenure 35) **sem proveniência** no repo; `knee_K` fora da cadeia reprodutível, contradizendo `:179` | `knee_K.py:39-41`; `run_full_study.sh:6-8` vs `:179` | Procedimento alternado com critério de parada, partindo dos *defaults* do código; pôr `knee_K.py` como etapa 0 do pipeline |
| 9 | alto | Reprodutib. | Nada de `results/` versionado ⇒ **nenhum número é verificável** e o `.tex` não compila com figuras em clone limpo | `.gitignore:18-19`; `:235,…,:652` (12 `\includegraphics`) | Commitar agregados + 12 figuras + `runs.csv` comprimido + `irace.log`; tirar `results/irace/` do `.gitignore` |
| 10 | alto | Código | Tabela lexicográfica reporta **best-of-30** e a chama de "média"; com a média (1007,1) o GRASP **não domina** o SINTEF na família C | `:573,:577,:584-588`; `lexicographic_table.py:36` | Duas colunas (média / melhor de 30) com legenda explícita; retirar ou qualificar "dominam" |
| 11 | alto | Código | Twin roda GRASP **não calibrado**, parado só por relógio (800 ms), com esforço desigual entre regimes; 3566,3 não sai com os defaults do repositório | `twin.py:117-119,144-145,170-176`; `:596,:627` | Repassar `extra` (tuned) a **ambos** os regimes; trocar parada por `--max-no-improve`; igualar defaults com `sensitivity.py`; regenerar `tab:twin` |
| 12 | alto | Alinhamento | Introdução afirma "sensoriamento IoT via **LoRaWAN**"; não existe camada de comunicação alguma (objetivo específico aprovado, não cumprido e silenciado) | `:121,:666`; `digital_twin/*.py` | Reescrever `:121` para "modelo de sensoriamento (NHPP)" e declarar em Limitações que LoRaWAN não foi implementada; ou implementar SF/duty cycle/payload/energia |
| 13 | alto | Alinhamento | Faltam `\section{Objetivos}` e `\section{Embasamento Teórico}`; 3 objetivos aprovados nunca são confrontados | estrutura de `relatorio-final.tex`; `exemplo:156,170,178`; `main.tex:165,167` | Criar `topicos/objetivos.tex` com status honesto por objetivo e `topicos/embasamento_teorico.tex`; parágrafo "objetivos não atingidos" na Conclusão |
| 14 | alto | Formal | Preâmbulo do relatório **parcial** (12pt/Arial) em vez do final (10pt/Times); **zero** "Fonte:"; 1ª pessoa sistemática; cabeçalho sem Grande Área; estouro de 15 páginas | `:12,:60-65,:79,:95-104,:111`; `main.tex:8,35,73,104,139` | Adotar o preâmbulo do template; "Fonte:" em todas as 19 ilustrações; passar a 3ª pessoa; cortar para 15 páginas |
| 15 | alto | Literatura | I1: variante chamada "**canônica**" é uma das quatro de Solomon e é a que ele conclui ser **inferior**; falta α₁+α₂=1 | `:198,:200`; `TUNING_RATIONALE.md:18` | Retirar "canônica", declarar a escolha e a inferioridade reportada, ou testar as 4 combinações (<0,01 s/instância) |
| 16 | alto | Literatura | "Cross-exchange faz o papel do 2-opt inter" é **falso**; a ablação só remove, nunca adiciona — não pode justificar a omissão | `:248`; `Neighborhoods.cpp:273-285`; parcial `:251` | Implementar 2-opt\* e acrescentar linha à ablação; ou declarar a omissão em Limitações e corrigir as citações (Or 1976; Taillard 1997; Potvin & Rousseau 1995) |
| 17 | alto | Literatura | Sem revisão de literatura; 3 de 18 referências tratam heurísticas de VRPTW; **nenhum** posicionamento frente ao estado da arte ⇒ 3,4% não é interpretável | `:117-126,:679-698` | Seção "Trabalhos relacionados" (Bräysy & Gendreau I/II; Savelsbergh; Cordeau; Taillard; Or; Vidal) + frase situando o gap frente ao HGS |
| 18 | alto | Estatística | Integral primal medido em **3 instâncias** com réplicas 5/5/1/1, não declarado, e usado como "confirmando" | `primal_integral_experiment.py:39,63`; `:89,:555,:557` | Declarar n=3 e as réplicas; trocar "confirmando" por "sugerindo, em caráter exploratório"; quantificar o descasamento com T=1.800 s/PassMark |
| 19 | médio | Estatística | Esforço desigual (Tabu 11,6 s × 1 execução vs. 15,3/18,5 s × 30); "Gap melhor" compara best-of-30 com best-of-1; README afirma isonomia | `:444,:505-507`; `README.md:153-154` | Teste de robustez sob tempo de CPU igual **em escala**; isolar a coluna "melhor" com nº de execuções; corrigir o README |
| 20 | médio | Estatística | Vazamento: tabelas de manchete e ablação nas 56 (28 vistas pelo irace); gaps *out-of-sample* nunca reportados | `:433,:478,:498,:514,:532`; `ablation.py:71` | Publicar gap(treino) × gap(teste) por algoritmo; refazer a ablação só no treino; rotular as tabelas de 56 |
| 21 | médio | Estatística | Ablação sem teste pareado, sem dispersão, sem multiplicidade; **Swap não sobrevive** (15/36/5; Wilcoxon p≈0,086); desenho cumulativo computado e omitido | `:248,:474,:483-488`; `ablation.py:34-42,79-81` | Wilcoxon + Holm, tamanho de efeito, contagem piora/empata/melhora; publicar o cumulativo; restringir a afirmação |
| 22 | médio | Calibragem | Protocolo do irace não reportado; orçamento divergente (2000/1500/1200); sem `seed`, sem `deterministic`; `scenario.txt` documenta via com 5 s e sem K; `target-runner` sem guarda de inviabilidade | `scenario.txt:9-18`; `1_calibrate.sh:16,42`; `run_full_study.sh:22`; `target-runner:24,49-58` | Unificar orçamento; declarar seed/testType/`deterministic=1` (tabu); corrigir os comandos do scenario; `if returncode != 0: print(PENALTY)` |
| 23 | médio | Calibragem | `TUNING_RATIONALE.md` — apontado pelo próprio relatório como fonte da justificativa — declara K "**calibrado**" e dá faixas (20;150)/(50;1000) que **nem contêm** 250/1400 | `TUNING_RATIONALE.md:18,19,25,38-39,55`; `:433` | Reescrever: K "fixado por orçamento"; grades efetivamente varridas; corrigir a linha da I1 e o comando de reprodução |
| 24 | médio | Calibragem | Sem baseline *default* × calibrado e sem curva de sensibilidade; α=0,1517/δ=1,3992 com 4 casas que são o `digits=4` do irace | `:432-441,:494`; `Grasp.hpp:22,25,26`; `TabuSearch.hpp:16` | Rodar `config/default.json` nas 28 de teste + Wilcoxon pareado; varredura univariada de sensibilidade; reportar α=0,15 |
| 25 | médio | Código/Lit. | Contradição sobre o teste O(1): `:423` diz que todo operador o aplica; `:186/:248` e o código dizem `evaluate_seq` | `:423` vs `:186,:248`; `Neighborhoods.cpp:128…286`; `SolomonI1.cpp:39`; `Grasp.cpp:45` | Corrigir a frase de `:423`; declarar o custo Θ(n²·L̄) por varredura; registrar ausência de avaliação incremental em Limitações |
| 26 | médio | Literatura | Atribuições incorretas a Solomon: o O(1) é de **Savelsbergh (1985)**; a hierarquia lex tem **4** critérios; o truncamento é do DIMACS; a justificativa da semente (`:229`) é do critério oposto | `:148,:153-157,:164,:229` | Reatribuir e incluir Savelsbergh na bibliografia; corrigir a Eq. (5); reescrever `:229` com a citação correta |
| 27 | médio | Benchmark | "Três convenções": SINTEF **é** a euclidiana em precisão dupla; falta o inteiro; comentário do código falso; "Dinamics" sem referente (são **ótimos** do CVRPLIB); URL DIMACS **404** | `:573,:683`; `DistanceMatrix.hpp:17`; `data/reference-solutions/dinamics/` | Corrigir a taxonomia com o exemplo 827,3 × 828,94; renomear para "CVRPLIB (ótimo, conv. DIMACS)" + `PROVENIENCIA.md`; citar o PDF de regras via web.archive |
| 28 | médio | Alinhamento | Compromissos do parcial em aberto: convenção lexicográfica prometida virou trabalho futuro com `better_lex` morto; kit "selecionado" contraria o único protocolo escrito; C102 é empate triplo | parcial `:196,:251,:295`; `Evaluator.hpp:41,46-48`; `solve.cpp:97`; `tabela_por_instancia.tex:25-31`; `:248` | Flag `--objective {dist|lex}` + subseção comparativa, ou declaração sem eufemismo em Limitações; nota de rodapé sobre C102; reescrever `:248` |
| 29 | médio | Alinhamento | 10 instâncias reais de coleta (Kim et al. 2006) no repo e no README, **ausentes dos dois relatórios**; "Atividades realizadas" declara Etapas 6-7 "avançadas" e alega "avanço de cronograma" | `data/instances/wcvrptw/`; `README.md:26`; `:658` | Rodar as 3 menores e reportar, **ou** declarar em Limitações por que não; reescrever `:658` etapa a etapa, no passado e fechado |
| 30 | baixo | Código/Rigor | Portão de corretude não fecha (`returncode` ignorado em 3 consumidores; `.sol` gravado antes do teste); limite de frota V nunca checado; semente descrita ≠ implementada; atributo tabu descrito ≠ implementado | `runner.py:67`; `solve.cpp:126,162,179`; `Validator.cpp:60-61`; `TabuSearch.cpp:11-30`; `:148,:165,:186,:188,:366,:456` | Consumir `returncode`; `fleet_ok` no `ValidationResult`; corrigir `:188/:456` e `:186/:366`; `:165` "quatro" → cinco restrições |

---

## 8. Plano de ação

### Bloqueadores — fazer **antes** de entregar

1. **Corrigir o horizonte do Digital Twin e refazer a Tabela 8.** Em `twin.py:129-130`, trocar `horizon=5000` por um horizonte derivado da escala (H ≈ 300 com `service=5` na caixa 0–100, ou `H = 2,5·(ida-e-volta máxima) + service·|active|`). Rodar com κ ∈ {0; 0,3; 0,6; 0,9} e reportar a **fração de janelas ativas** por κ. Se não houver tempo, **remover de `:627` e `:648` toda a alegação de acoplamento com o Push Forward** e reclassificar o cenário como CVRP com priorização por demanda. *Esforço: 2–4 h (correção) ou 20 min (declaração honesta).*
2. **Corrigir o KPI de transbordos e replicar.** Em `sensors.py:43-45`, guardar `was_full = self.fill >= 1.0-1e-9` antes do passo e contar `(new_fill >= 1.0-1e-9) & ~was_full`; expor separadamente `overflow_bin_cycles`. Rodar `compare_scenarios` com **≥30 sementes**, reportar média/IC e Wilcoxon pareado. Reescrever `:633` e `:664` com o resultado que sobreviver — pelos dados atuais, a conclusão honesta é "o dinâmico reduz o número de coletas pela metade, mas **não** reduz transbordos nem distância". *Esforço: 3–5 h.*
3. **Repassar os parâmetros calibrados e a parada por K ao Twin.** Dar a `simulate_static` o parâmetro `extra`; em `compare_scenarios`, passar `extra=load_tuned().get(algo,"")` a **ambos** os regimes; incluir `--max-no-improve` em `plan_routes` e em `road_twin.py:96-97`; igualar os defaults com `sensitivity.py` (capacidade e orçamento). Regenerar `tab:twin`. *Esforço: 1–2 h.*
4. **Estender as grades de K e reescrever a Seção 3.8.** Rodar `knee_K.py` com `grasp/rgrasp: [20,40,80,160,320,640,1280,2560]` e `tabu: [100,200,400,800,1600,3200,6400,12800]`, `SEEDS≥10`, publicando a **tabela completa** (K | gap | IC95 | Δ | tempo). Se o joelho continuar no teto, escrever: *"K foi limitado pelo orçamento computacional, não pela convergência"*, e apagar a legenda de `:440`. Alinhar `:435` a `best = min(means)`. *Esforço: algumas horas de CPU + 1 h de texto.*
5. **Reexecutar o irace com intervalos expandidos** (`tenure ∈ (5,80)`; `block` relativo a K) e acrescentar a tabela de diagnóstico de fronteira. Se não houver tempo de máquina, **o mínimo aceitável** é a ressalva explícita em `:494`: *"tenure e block venceram na fronteira superior dos intervalos; devem ser lidos como 'o melhor dentro da faixa testada', não como ótimos"*, **mais** a frase sobre o Reativo estar degenerado (1 atualização/execução), substituindo a conclusão de `:363`. *Esforço: 1 dia de CPU, ou 30 min na versão mínima.*
6. **Trocar Nemenyi por Wilcoxon pareado + Holm** nas 10 comparações e reescrever `:664`. Texto sugerido: *"O pós-teste de Nemenyi não rejeita a igualdade entre GRASP e Busca Tabu (p=0,18); essa decisão, contudo, depende do conjunto de algoritmos incluído — excluindo a construção I1, dominada em todas as instâncias, a mesma diferença de rank (0,66) torna-se significativa (CD=0,627). Adotamos, portanto, o teste de Wilcoxon pareado com correção de Holm, cuja decisão independe do pool."* Substituir "estatisticamente equivalentes" por "não foi possível rejeitar a hipótese de igualdade com o poder disponível". *Esforço: 2 h (script) + 1 h (texto).*
7. **Corrigir a Tabela lexicográfica.** Duas colunas — "GRASP (média de 30)" e "GRASP (melhor de 30)" — e reescrever `:573`: *"nossas soluções GRASP têm distância média 1007,1 e melhor 992,2, contra 1017,8 do SINTEF e 973,2 da referência de mínima distância"*, retirando "dominam" (não vale na família C sob a média). *Esforço: 1 h.*
8. **Declarar o tamanho de amostra do integral primal.** Em `:555`: *"em três instâncias representativas (R101, RC101 e R201), com 5 execuções para GRASP/Reativo e 1 para VND/Tabu"*; trocar "confirmando" por "sugerindo, em caráter exploratório". *Esforço: 15 min.*
9. **Converter o documento ao formato do relatório FINAL.** Substituir o preâmbulo pelo de `docs/template-relatorio-final/main.tex` (10pt, `\rmdefault` + `mathptmx`), corrigir a 4ª linha do `\fancyhead` para "Ciências Exatas e da Terra", incluir "Grande Área do Conhecimento (CNPq)" na tabela de identificação, converter o resumo em `\section*{Resumo}` sem citações, restaurar o título oficial em `:107`. **Migrar para `main.tex` + `topicos/`**, criando `objetivos.tex` (os 7 objetivos com status honesto) e `embasamento_teorico.tex` (formulação + literatura hoje diluída na Metodologia). *Esforço: 4–6 h.*
10. **Adicionar "Fonte:" a todas as 13 figuras e 6 tabelas** (`\caption*{Fonte: Produção da própria autora.}`; OSM/OSRM na figura viária; CVRPLIB nas tabelas com referências) e **passar todo o texto para 3ª pessoa** (26 ocorrências mapeadas). *Esforço: 3 h — revisão linha a linha, não find/replace.*
11. **Migrar a bibliografia** para `\bibliographystyle{hapalike2-NOand}` + `\bibliography{biblio}` com seção "Referências Bibliográficas"; **acrescentar as 4 entradas faltantes** ao `biblio.bib` (`dimacs12vrptw`, `cvrplib`, `potvin1995exchange`, `toth2002vehicle`) e compilar `pdflatex → bibtex → pdflatex → pdflatex` conferindo o `.blg`. *Esforço: 1–2 h.*
12. **Cortar para 15 páginas.** Mover o apêndice por instância (410 linhas) e as leituras passo a passo (`:229,:277,:322,:363,:393`) para material suplementar; reduzir os 5 pseudocódigos a 2 (I1 e esqueleto GRASP). **Instalar `texlive-latex-recommended` e compilar para conferir a contagem real.** *Esforço: 2–3 h.*
13. **Versionar as evidências.** `git add` de `results/{overall,per_instance,gap_by_family,nemenyi_pvalues,ablation_summary,knee_K,primal_integral}.csv`, das 12 figuras referenciadas e de `results/raw/runs.csv` comprimido; remover `results/irace/` do `.gitignore` e commitar os `irace.log`. Sem isso, **nenhum número do relatório é auditável**. *Esforço: 30 min.*
14. **Corrigir as afirmações factualmente falsas sobre o código** (edições de texto, ~1 h no total): `:423` (teste O(1) só na construção); `:186/:366` (atributo é o **cliente-âncora**); `:188/:456` (a semente combina `--seed` com o hash da instância — o índice está fixo em 0); `:165` ("quatro" → cinco restrições, ou implementar `fleet_ok`); `:167` e `:471` (contagem única e correta: **3.528 execuções** no estudo principal).
15. **Reescrever `:658` (Atividades realizadas)** etapa a etapa, no passado e no fechado, com status honesto por etapa, e **remover** a frase "houve avanço de cronograma". Acrescentar na Conclusão o parágrafo "Objetivos não atingidos e por quê" (LoRaWAN, benefícios econômicos/ambientais/sociais, Simulação Baseada em Agentes, validação com enchimento real). *Esforço: 1 h.*
16. **Resolver o LoRaWAN por escrito.** Reescrever `:121` para "combina um **modelo de sensoriamento** de enchimento de lixeiras (processo de Poisson não homogêneo) com heurísticas..." e acrescentar em Limitações: *"A camada de comunicação LoRaWAN prevista no subprojeto não foi implementada nem simulada; o modelo assume comunicação ideal e instantânea a cada ciclo de monitoramento."* Retirar `\citep{ramson2021lorawan,de2021plataforma}` do ponto em que sustentam capacidade inexistente. *Esforço: 20 min.*
17. **Reescrever `TUNING_RATIONALE.md`** (é para lá que `:433` manda o leitor): K passa a "**fixado por orçamento**"; apagar as faixas fictícias de K; substituir a "Nota sobre a calibração de K" por uma nota sobre a **fixação** de K; corrigir a linha da I1 e o comando de reprodução. *Esforço: 45 min.*

### Fortalecimento — eleva de aprovado para excelente

18. **A tabela que falta: "A calibragem valeu a pena?"** Criar `experiments/config/default.json` (`{"grasp":"--alpha 0.3","rgrasp":"--delta 1.0 --block 50","tabu":"--tenure 15"}` + o mesmo K), rodar `runner.py --params-file config/default.json --instance-list config/test.txt` e publicar: Algoritmo | *default* | gap ± IC95 | calibrado | gap ± IC95 | Δ | Wilcoxon pareado | tamanho de efeito. **Se o Δ não for significativo, dizer isso** — é resultado publicável.
19. **Curva de sensibilidade dos hiperparâmetros** (α, δ, block, tenure), 28 instâncias de treino, 10 sementes, IC95% e **faixa de indiferença** marcada. É um script de ~40 linhas reaproveitando a estrutura de `knee_K.py`, e resolve de vez a assimetria com `:648`.
20. **Comparação sob tempo de CPU igual, em escala.** Rodar os cinco métodos com `--budget-ms T*` (T* ≈ 20 s) e K desativado, 30 sementes, nas 28 de teste, e repetir Friedman/Nemenyi. Publicar lado a lado "parada por K" × "parada por tempo T*" — é a análise de robustez que a banca vai pedir.
21. **Reportar as tabelas de manchete no conjunto de TESTE** (CD recalculado: 1,153 para N=28) e as 56 em apêndice rotulado "inclui as instâncias de calibração"; publicar gap(treino) × gap(teste). Trocar `cd_diagram_full` por `cd_diagram_test` em `:532` (o arquivo já é gerado).
22. **Ablação com inferência:** Wilcoxon pareado + Holm sobre os gaps por instância, contagem piora/empata/melhora, publicar o desenho **cumulativo** já computado, e refazer só no treino. Restringir a afirmação de `:474/:248` aos operadores com efeito detectável.
23. **Implementar o 2-opt\*** (~20 linhas: para cada par (r1,r2) e corte (i,j), montar `c1 = s1[0..i]+s2[j+1..]`, `c2 = s2[0..j]+s1[i+1..]`, avaliar por `evaluate_seq`) e acrescentar a linha "kit completo + 2-opt\*" à Tabela 3. Se melhorar, incorpore; se não, você passa a ter a evidência que hoje não tem — e fecha a divergência com o parcial.
24. **Rodar as 3 menores instâncias WCVRPTW** (102, 277, 335) e reportar contra Kim et al. (2006) e Benjamin & Beasley (2010), declarando a variante reduzida. Converte a Etapa 7 de "parcial" em "cumprida" e dá validade externa ao capítulo do Twin.
25. **Seção "Trabalhos relacionados"** de meia página, em três blocos (construção / busca local / meta-heurísticas), fechando com a frase que situa o trabalho: *"não buscamos o estado da arte (hoje na casa de frações de 1% de gap), mas uma comparação controlada de métodos clássicos sob um núcleo compartilhado"*. Acrescentar Savelsbergh, Bräysy & Gendreau, Cordeau, Taillard, Or e Vidal à bibliografia; atualizar o Handbook para a 3ª ed. (2019, já em `docs/referencias/`).
26. **Fechar o portão de corretude:** consumir `returncode` em `runner.py`, `target-runner` (com `PENALTY`) e `twin.py`; gravar `results/feasibility.csv` e citá-lo em `:471`; mover a escrita do `.sol` para depois do teste; acrescentar `fleet_ok` ao `ValidationResult`.
27. **Higiene do repositório:** marcar `docs/planejamento/irace_calibration_plan.md`, `irace_search_space_template.md`, `irace_target_runner_template.md`, `conformance_audit.md` e `neighborhood_selection_approach.md` com cabeçalho `Status: SUPERSEDED em <data>` ou removê-los. Preservar e **preencher** `irace_parameter_justification.md` (a tabela ex-post das linhas 60-64 segue com "PREENCHER").
28. **Nota de reconciliação com o parcial** (dois parágrafos curtos): (a) sobre o Quadro 2 × Tabela de ablação — declarar que são medidas diferentes (frequência de aplicação × contribuição marginal) e que, sob o desenho atual, Or-opt e Cross-exchange revelam-se muito mais relevantes e o Swap quase dispensável; (b) sobre C102 — empate triplo sob os parâmetros calibrados. Restaurar o vínculo com "Pesquisa Operacional e Inovação em Logística Regional" na Introdução e na Metodologia.

### Opcional / trabalho futuro

29. Testar o segundo critério de semente de Solomon (*earliest deadline*, 5 linhas atrás de um *flag*) e reportar por família — transforma uma fragilidade em contribuição.
30. Testar as 4 combinações de parâmetros da I1 (custo desprezível) e reportar tabela 4 linhas × 3 famílias.
31. Testar o VND com 4-6 ordens de vizinhança (0,04 s/instância) — resultado publicável em IC.
32. Aspiração por omissão ("least tabu") na Busca Tabu e instrumentação da causa de término (K / impasse / teto de tempo).
33. Atributo tabu por par (cliente, rota), à la Cordeau et al. (2001) — matriz `tabu_until[n][R]`.
34. Avaliação incremental por concatenação de sequências (Vidal et al., 2013) e reuso de buffer em vez de `std::vector` por candidato.
35. Inviabilidade penalizada e auto-ajustável (Cordeau; Taillard; Vidal) — a extensão natural mais promissora do trabalho, hoje sequer reconhecida.
36. Flag `--objective {dist|lex}` acionando `Evaluator::better_lex` e subseção "Comparação entre convenções" — fecha, com evidência, a promessa do parcial.
37. TTT com três alvos, três métodos e QQ-plot exponencial, em diretório de traços separado.
38. Verificação em segunda passada com distâncias em precisão dupla, reportando quantas soluções permanecem viáveis fora da convenção truncada.
39. Simulação Baseada em Agentes (Etapa 6) e camada LoRaWAN mensurável (SF, duty cycle 1%, tempo no ar, energia por transmissão, autonomia estimada).

---

## 9. O que já está bom (e deve ser preservado)

- **O núcleo compartilhado é a decisão metodológica certa** e está implementado como anunciado: um só leitor, uma só matriz de distâncias, um só conjunto de vizinhanças, um só RNG. É isso que dá sentido à comparação, e não é comum nesse nível de formação.
- **A convenção de distância é verificável e foi verificada.** `std::trunc(v*10)/10`, tempo igual à distância, e a reprodução exata dos 56 custos de referência é um portão de qualidade real — poucos trabalhos de IC têm um.
- **As fórmulas estão corretas.** $c_{11}$, $c_{12}$, $c_1$, $c_2$ conferem com Solomon (p.257); a RCL do GRASP não tem erro de sinal; $q_i=(Z^*/\bar{Z}_i)^\delta$ com médias acumuladas é fiel a Prais & Ribeiro; o VND é literalmente a Algorithm 2 do Handbook; o exemplo numérico do Push Forward está aritmeticamente correto e a recursão de `Route.hpp:71-79` implementa o *forward time slack* corretamente. O `eval_insert` O(1) concorda 100% com `evaluate_seq` em 193.642 casos testados.
- **A aritmética estatística está certa** — correção de empates, $q_\alpha$, CD, $\chi^2$, p do range estudentizado: reproduzi todos. O problema é de desenho e de interpretação, não de cálculo.
- **A divisão treino/teste é genuinamente estratificada e balanceada** (28/28, equilibrada por família e tipo). É um cuidado que muitos artigos publicados não têm.
- **A camada viária real (OSM/OSRM) é uma contribuição de valor** — matrizes explícitas de distância e tempo, fator de circuito 1,53 medido, e o solver estendido sem contaminar o benchmark euclidiano. Preserve integralmente.
- **A ablação de vizinhanças e a análise de sensibilidade do Twin existem**, o que já coloca o trabalho acima da média — só precisam de inferência (a primeira) e de replicação (a segunda).
- **O relatório reconhece explicitamente várias de suas limitações** (`:430`, `:494`, `:552`, `:555`, `:569`, `:596`, `:603`, `:666`). Essa disposição é o ativo mais importante que você tem: quase tudo neste parecer se resolve estendendo esse mesmo hábito aos pontos onde o texto hoje afirma mais do que os dados sustentam.