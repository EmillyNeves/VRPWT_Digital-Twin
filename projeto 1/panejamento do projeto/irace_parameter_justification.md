# Justificativa de Parâmetros (irace)

Este documento define como justificar, de forma auditável, cada escolha de parâmetro:

- **Antes** da execução do irace (justificativa ex-ante, pré-registrada).
- **Depois** da execução do irace (justificativa ex-post, baseada em evidência).

Objetivo: garantir rigor metodológico, evitar tuning ad hoc e manter comparabilidade em pé de igualdade [2][3].

## 1) Regras globais (válidas para todos os cenários)

- Objetivo do solver: `--objective cost` (convenção DIMACS) [1].
- Controle de comparação: mesmo `--time-limit T` para todos os métodos.
- Critérios de parada secundários desativados: `--max-iters 0 --max-no-improve 0`.
- Mesmo conjunto de vizinhanças locais para todos os métodos comparados.
- Mesmo `--mu`, `--eps`, instâncias e política de seeds [2][3].
- Tratamento de determinismo no irace: `tabu_classic` com `deterministic=1`; `grasp_fixed` e `grasp_reactive` com `deterministic=0` [3].

### 1.1 Função de score no target-runner

- Score minimizado pelo irace:
  `score = gap_pct + lambda * time_sec`.
- Regra recomendada: `lambda` pequeno (`1e-4`) para preservar `gap_pct` como objetivo primário e usar `time_sec` apenas como desempate operacional.
- Alternativa estrita DIMACS: usar `lambda = 0` no irace e aplicar desempate por `time_sec` apenas na analise ex-post.
- Penalidade em falhas/infeasibilidade: valor fixo alto (`1e9`) para manter o fluxo do irace e evitar viés de exclusão [3].

## 2) Justificativa ex-ante (pré-registro obrigatório)

Preencher **antes** de iniciar cada corrida do irace.

| Cenário | Parâmetro | Status | Intervalo/Valor | Hipótese ex-ante | Justificativa |
|---|---|---|---|---|---|
| `tabu_classic` | `tenure` | TUNE | `[5, 50]` inteiro | Tenure pequeno intensifica; tenure grande diversifica. Existe faixa intermediária robusta. | Memória de curto prazo do Tabu depende do tenure; escolha clássica para controlar ciclo/diversificação [4]. |
| `tabu_classic` | `tabu-move-policy` | FIXO | `best` | Melhor custo admissível por iteração tende a maior estabilidade de busca. | Versão canônica de TS simples em estudos comparativos; reduz variância de escolha de movimentos [4][8]. |
| `grasp_fixed` | `alpha` | TUNE | `[0.0, 1.0]` real | `alpha` baixo tende a construção mais gulosa; alto tende a mais diversidade. | Parâmetro estrutural da RCL no GRASP clássico [5]. |
| `grasp_fixed` | `grasp-mode` | FIXO | `fixed` | Isolar efeito do `alpha` sem adaptação reativa. | Define cenário específico de calibração. |
| `grasp_reactive` | `reactive-update` | TUNE | `[5, 100]` inteiro | Janela curta reage rápido; janela longa estabiliza probabilidades de `alpha`. | Hiperparâmetro central da atualização reativa do GRASP [6]. |
| `grasp_reactive` | `reactive-alphas` | FIXO | `0.1,0.2,0.3,0.4,0.5` | Conjunto cobre gradiente guloso-aleatório padrão. | Evita explosão combinatória no espaço de busca. |
| `grasp_reactive` | `reactive-gamma` | FIXO | `1.0` | Atualização proporcional sem viés agressivo. | Ponto neutro para focar no efeito de `reactive-update`. |
| `all` | `time-limit` | FIXO | `T` comum | Comparação principal por orçamento de tempo. | Isonomia entre métodos e cenários. |
| `all` | `max-iters` | FIXO | `0` | Desativar limite de iterações. | Evita que a parada secundária interfira na comparação por tempo. |
| `all` | `max-no-improve` | FIXO | `0` | Desativar limite por estagnação. | Evita término precoce não controlado por orçamento de tempo. |
| `all` | `score-lambda` | FIXO | `1e-4` | Priorizar gap e usar tempo apenas para desempate. | Compatibiliza objetivo unico do irace com criterio secundario de ROI computacional [3]. |

### 2.1 Política de fronteira (boundary policy)

- Se o vencedor ficar na borda inferior/superior do intervalo, registrar como **evidência de intervalo curto**.
- Ação obrigatória: abrir novo intervalo e repetir a corrida daquele cenário.

### 2.2 Política de orçamento

- `maxExperiments`: `1000` por cenário (ponto de partida).
- Se não houver convergência clara: aumentar orçamento em etapas e registrar decisão.
- O desenho da corrida segue o fluxo de configuração automática do irace [3].

## 3) Justificativa ex-post (obrigatória após o irace)

Preencher **após** a corrida de cada cenário.

| Cenário | Parâmetro | Valor final | Posição no intervalo | Efeito em `gap_pct` | Efeito em `time_sec` | Robustez (`IQR gap`) | Decisão final |
|---|---|---|---|---|---|---|---|
| `tabu_classic` | `tenure` | `PREENCHER` | `interior/borda` | `PREENCHER` | `PREENCHER` | `PREENCHER` | `aceitar/repetir` |
| `grasp_fixed` | `alpha` | `PREENCHER` | `interior/borda` | `PREENCHER` | `PREENCHER` | `PREENCHER` | `aceitar/repetir` |
| `grasp_reactive` | `reactive-update` | `PREENCHER` | `interior/borda` | `PREENCHER` | `PREENCHER` | `PREENCHER` | `aceitar/repetir` |

### 3.1 Checklist ex-post

- Valor vencedor está no interior do intervalo (ou houve rerun com intervalo expandido).
- Ganho não depende de 1-2 instâncias atípicas.
- Desempenho consistente nas famílias de instância (C/R/RC), quando aplicável.
- Reprodutibilidade confirmada com mesmas seeds/contratos de execução.
- Configuração final congelada antes do holdout.
- Resumo estatístico com mediana e IQR por cenário (robustez) [7].

## 4) Texto padrão para o artigo

### 4.1 Antes (métodos)

> A calibração foi pré-registrada por cenário, com definição explícita de parâmetros ajustáveis, intervalos de busca e parâmetros fixos. Em todos os cenários, adotou-se orçamento temporal uniforme por execução (`time-limit`), com limites secundários (`max-iters`, `max-no-improve`) desativados para assegurar isonomia entre métodos.

### 4.2 Depois (resultados de calibração)

> Após o irace, cada escolha de parâmetro foi justificada ex-post por posição do valor selecionado no intervalo, impacto na mediana de `gap_pct`, custo temporal (`time_sec`) e robustez (`IQR`), com política explícita para casos de solução na borda do intervalo. O score do configurador foi definido como `gap_pct + lambda*time_sec` com `lambda` pequeno, garantindo prioridade do gap e desempate por custo computacional.

## 5) Referências

[1] DIMACS VRPTW Challenge Rules.  
http://dimacs.rutgers.edu/files/8516/3848/0275/VRPTW_Competition_Rules.pdf

[2] Birattari, M. (2009). *Tuning Metaheuristics: A Machine Learning Perspective*. Springer.

[3] López-Ibáñez, M. et al. (2016). The irace package: Iterated racing for automatic algorithm configuration. *Operations Research Perspectives*, 3, 43-58.

[4] Glover, F. and Laguna, M. (1997). *Tabu Search*. Kluwer Academic Publishers.

[5] Feo, T. A. and Resende, M. G. C. (1995). Greedy randomized adaptive search procedures. *Journal of Global Optimization*, 6(2), 109-133.

[6] Prais, M. and Ribeiro, C. C. (2000). Reactive GRASP. *INFORMS Journal on Computing*, 12(3), 164-176.

[7] Demšar, J. (2006). Statistical comparisons of classifiers over multiple data sets. *JMLR*, 7, 1-30.

[8] Gendreau, M. and Potvin, J.-Y. (eds.) (2019). *Handbook of Metaheuristics* (3rd ed.). Springer.
