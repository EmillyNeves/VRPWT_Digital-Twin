# Seleção de Vizinhanças (NLS, First Improvement)

> **NOTA DE SUPERAÇÃO (ago/2026).** O subconjunto recomendado de quatro
> movimentos registrado na seção "Conjunto operacional pós-seleção" **não se
> sustenta**: dá 11,388 % de gap contra 8,249 % do conjunto completo (+3,14 pp),
> por descartar o Or-opt, que é estatisticamente significativo (p = 0,0216 com
> correção de Holm). A seleção foi reexaminada por busca exaustiva dos 63
> subconjuntos, e nenhum subconjunto próprio domina o completo. Ver
> `docs/verificacao/03-vizinhancas.md`.
>
> A ordenação por complexidade, que este documento define, **permanece válida** —
> mas a lista concreta muda, porque a implementação funde intra e inter em três
> operadores, o que inverte o custo relativo (o 2-opt intra é o mais barato, não
> o sexto). A ordem em uso vem do custo medido, não da ordenação teórica abaixo.


## Escopo

Este protocolo é **apenas** para seleção de vizinhanças (operadores de busca local).
Não compara GRASP, Tabu ou VND nesta etapa — esses métodos herdam o
conjunto de vizinhanças aqui definido.

Para evitar viés de *over-tuning* (Birattari, 2009), esta fase é
executada **estritamente sobre um conjunto de calibração (*Tuning Set*)**
representativo (ex.: 20 % das instâncias de Solomon, estratificado por
família C/R/RC), mantendo as demais instâncias reservadas (*Holdout*)
para a avaliação final.

> **Referências para separação tuning/teste:**
> Birattari, M. (2009). *Tuning Metaheuristics: A Machine Learning
> Perspective*. Springer.
> López-Ibáñez, M. et al. (2016). The irace package: Iterated racing
> for automatic algorithm configuration. *Operations Research
> Perspectives*, 3, 43–58.

## Definição do Tuning Set e Holdout neste repositório

Para evitar ambiguidade, esta implementação fixa explicitamente como o
`input_tuning_set` é construído a partir de `input/`.

### Universo e regra de estratificação

No conjunto Solomon disponível neste repositório há 56 instâncias:

* Família `C`: 17 instâncias
* Família `R`: 23 instâncias
* Família `RC`: 16 instâncias

O *Tuning Set* é definido como 20 % por família, com arredondamento:

* Regra: `n_fam = max(1, round(0.20 * |fam|))`
* Resultado: `C=3`, `R=5`, `RC=3`
* Tamanho final do *Tuning Set*: **11 instâncias**
* *Holdout Set*: **45 instâncias** (complemento exato do tuning)

### Justificativa metodológica

1. **Representatividade estrutural**: estratificar por `C/R/RC` evita que
   o tuning fique enviesado para um único perfil de distribuição
   espacial (clusterizado, aleatório ou misto).
2. **Controle de over-tuning**: usar apenas uma fração (~20 %) para
   calibração preserva a maioria das instâncias para validação externa
   (Birattari, 2009).
3. **Viabilidade estatística mínima**: com 11 instâncias, a fase de
   comparação pareada atende o limiar mínimo usado no script para
   Wilcoxon aproximado (`n_shared >= 10`).
4. **Reprodutibilidade**: a seleção é fixa e declarada; qualquer
   execução futura usa exatamente o mesmo particionamento.

### Instâncias selecionadas (seed de construção = 42)

* `C`: `C101`, `C104`, `C203`
* `R`: `R104`, `R105`, `R108`, `R109`, `R210`
* `RC`: `RC103`, `RC107`, `RC202`

### Construção reprodutível das pastas

```bash
mkdir -p input_tuning_set input_holdout_set

cp input/{C101.txt,C104.txt,C203.txt,R104.txt,R105.txt,R108.txt,R109.txt,R210.txt,RC103.txt,RC107.txt,RC202.txt} input_tuning_set/

for f in input/*.txt; do
  b="$(basename "$f")"
  if [ ! -f "input_tuning_set/$b" ]; then
    cp "$f" input_holdout_set/
  fi
done
```

> **Nota:** o *Holdout Set* é sempre definido como complemento do tuning.
> Trocar instâncias no `input_tuning_set` exige reportar a nova lista e
> repetir toda a seleção de vizinhanças.

## Motor de busca usado

* Algoritmo: `nls` (`bin/vrptw solve --algo nls`).
* Política de melhoria: **First Improvement** em todas as vizinhanças.
  A escolha de FI (em vez de Best Improvement) segue a recomendação de
  Hansen & Mladenović (2001) para VND: FI é computacionalmente mais
  barato e produz resultados de qualidade comparável.
* Solução inicial fixa: **Solomon I1** (inserção sequencial por farthest
  seed, puramente determinística com `α₁=1, α₂=0, μ=1, λ=1`).
* Configuração por fase:
  * **Fase A** (isolada): cada vizinhança é aplicada sozinha até
    convergir ao ótimo local. Como há uma única vizinhança no laço, o
    parâmetro `nls_restart` é irrelevante (usado `nls_restart=0` por
    convenção).
  * **Fase B** (combinada): subconjuntos de vizinhanças executados com
    `nls_restart=1`, reproduzindo o laço clássico do VND — ao encontrar
    melhoria, a busca retorna à primeira vizinhança do subconjunto
    (Hansen & Mladenović, 2001, Definição do VND).

> **Referências para VND e First Improvement:**
> Hansen, P. & Mladenović, N. (2001). Variable neighborhood search:
> Principles and applications. *European Journal of Operational
> Research*, 130(3), 449–467.
> Talbi, E.-G. (2009). *Metaheuristics: From Design to Implementation*.
> Wiley. Cap. 2–3.

## Determinismo e seeds

O Solomon I1 com os parâmetros acima é **totalmente determinístico**:
a seleção de seed (farthest customer) e a ordem de inserção não
dependem de gerador aleatório. O NLS com first-improvement também é
determinístico (a ordem de enumeração de movimentos é fixa).

Consequência: **uma seed é suficiente para a fase de seleção de
vizinhanças**, pois repetições produziriam resultados idênticos.
Isso é declarado explicitamente para que o leitor não confunda a
ausência de múltiplas seeds com falta de rigor.

> **Referência:**
> Barr, R. S. et al. (1995). Designing and reporting on computational
> experiments with heuristic methods. *Journal of Heuristics*, 1, 9–32.
> (Seção sobre métodos determinísticos: quando o algoritmo é
> determinístico, uma execução por instância é suficiente.)

## Função objetivo na seleção

Este protocolo adota a convenção do **12º Desafio DIMACS**:

* **Objetivo primário**: minimizar a distância total (custo).
* **Número de veículos**: tratado como **restrição** (≤ V), não como
  objetivo. Entretanto, como salvaguarda de consistência:
  * Qualquer configuração cuja solução final tenha **mais veículos que o
    baseline I1** em qualquer instância é marcada como **dominada** e
    rebaixada no ranking.
  * Na prática, isso é estruturalmente impossível (demonstrado abaixo),
    mas a verificação explícita protege contra bugs e dá transparência
    ao leitor.

> **Referência para a convenção DIMACS:**
> http://dimacs.rutgers.edu/files/8516/3848/0275/VRPTW_Competition_Rules.pdf
>
> **Nota para revisores que usam a hierarquia clássica de Solomon:**
> A hierarquia lexicográfica f(s) = (v(s), d(s)) é rigorosamente
> preservada nas metaheurísticas de nível superior (VND, GRASP, Tabu).
> Na fase de seleção de vizinhanças, operadores intra/inter-rota
> simples raramente possuem a capacidade estrutural de eliminar rotas
> inteiras por si sós, de modo que a métrica de triagem é o gap de
> distância, com tempo computacional como desempate (ROI dos operadores
> de baixo nível).

**Transparência de desempate na busca local.**
Mesmo com `--objective cost` (DIMACS), a aceitação de movimentos na
busca local usa desempate lexicográfico secundário: quando
`|Δcost| ≤ ε`, o movimento só é aceito se reduzir o número de rotas.
Assim, a distância continua sendo o critério primário e as rotas entram
apenas como desempate de estabilidade numérica/estrutural.

## Garantia de que nenhuma vizinhança aumenta veículos

A propriedade é garantida em três níveis:

1. **Enumeração**: todo enumerador calcula `newRoutes ≤ sol.routes.size()`.
   Nenhum cria rotas novas.
2. **Aceitação** (`isLSImprovement`): aceita movimento somente se
   `newCost < oldCost - ε` OU (`|Δcost| ≤ ε` E `newRoutes < oldRoutes`).
   Aumento de rotas é rejeitado.
3. **Limpeza**: `Solution::recompute()` remove rotas triviais
   (`seq.size() ≤ 2`) após cada movimento.

## Garantias de factibilidade

Cada movimento só é aplicado se a solução resultante for rigorosamente
factível (capacidade + janelas de tempo). Ao final de cada execução, a
solução é validada novamente (`validateSolution`).

* Toda linha de resultado em `neighborhood_runs.csv` corresponde a
  solução factível.
* Se alguma execução gerar infeasibilidade, o solver interrompe com
  erro explícito e não registra resultado válido.

## Vizinhanças candidatas (8)

Ordenadas por complexidade computacional, conforme recomendação de
Hansen & Mladenović (2001): "the neighbourhoods should be ordered so
that the simplest is explored first":

| # | Nome | Escopo | Pode reduzir rotas? |
|---|------|--------|---------------------|
| 1 | `relocate_intra` | Intra-rota | Não |
| 2 | `swap_intra` | Intra-rota | Não |
| 3 | `relocate_inter` | Inter-rotas | Sim (esvazia rota-fonte) |
| 4 | `or_opt` | Intra + Inter | Sim (caso inter) |
| 5 | `swap_inter` | Inter-rotas | Não (troca 1×1) |
| 6 | `two_opt_intra` | Intra-rota | Não |
| 7 | `two_opt_inter` | Inter-rotas | Sim (troca de caudas) |
| 8 | `cross_exchange` | Inter-rotas | Sim (troca de segmentos) |

## Desenho experimental

### Mitigação de viés computacional

Para mitigar distorções no tempo medido (*wall-clock*, via
`std::chrono::steady_clock`) causadas por ruídos do sistema operacional
(processos em segundo plano, flutuações de cache), a fila de execuções
(instância × configuração) é **randomizada** antes da execução
(`--randomize-queue`), aplicando um *randomized block design*.

> **Referências:**
> Barr, R. S. et al. (1995). *Journal of Heuristics*, 1, 9–32.
> McGeoch, C. C. (2012). *A Guide to Experimental Algorithmics*.
> Cambridge University Press. Cap. 3 (System Environment).

### Fase A — Avaliação isolada

* Executar **1 vizinhança por vez** no *Tuning Set*.
* Orçamento: `--time-limit 0` (executar até estagnar no ótimo local).
* Coletar por instância:
  * `cost` (distância total),
  * `num_routes` (veículos),
  * `time_sec` (tempo wall-clock),
  * `gap_pct` (em relação ao BKS).
* Ranking:
  1. **Dominância**: configs que piorem veículos vs I1 → fundo do ranking.
  2. **Métrica primária**: menor `mediana(gap_pct)`.
  3. **Desempate**: menor `mediana(time_sec)`.
  4. **Robustez**: menor `IQR(gap_pct)`.
* **Ação**: selecionar **Top-5 não-dominadas** para a Fase B.

> **Justificativa do ranking por mediana:**
> Demšar, J. (2006). Statistical comparisons of classifiers over
> multiple data sets. *JMLR*, 7, 1–30.

### Fase B — Sinergia: incremental + ablação

* Utilizar apenas as Top-5 da Fase A.
* Orçamento: `--time-limit 0`.
* Mecânica interna: vizinhanças executadas **na ordem de complexidade**
  com reinício ao melhorar (`nls_restart=1`), reproduzindo o VND
  clássico.
* **Teste incremental**:
  * C1: melhor da Fase A.
  * C2: melhores 1+2.
  * C3: melhores 1+2+3.
  * C4: melhores 1+2+3+4.
  * C5: Top-5 completo.
* **Teste ablativo**:
  * Top-5 menos viz₁, ..., Top-5 menos viz₅.

O teste incremental revela o **ganho marginal** de cada adição; o
teste ablativo revela a **contribuição insubstituível** de cada
vizinhança. A combinação dos dois é mais informativa do que qualquer
um isoladamente (Hooker, 1995).

> **Referência para experimentação controlada:**
> Hooker, J. N. (1995). Testing heuristics: We have it all wrong.
> *Journal of Heuristics*, 1, 33–42.

### Escolha final e validação estatística

1. **Seleção por parcimônia**: preferir o melhor conjunto de tamanho 3
   ou 4, desde que o ganho marginal de adicionar mais vizinhanças seja
   insignificante. Isso segue o princípio de que vizinhanças em excesso
   aumentam custo computacional sem melhoria proporcional
   (Hansen & Mladenović, 2001).

2. **Teste de Wilcoxon pareado** (por instância do *Tuning Set*) entre
   as configurações finalistas, com **correção de Holm** para múltiplas
   comparações (α = 0.05).

3. **Confirmação**: submeter a configuração escolhida ao *Holdout Set*
   para verificar generalização fora do tuning.

> **Interpretação de empates e p-values NaN (Wilcoxon):**
> Em VRPTW com janelas de tempo rígidas, o espaço viável tende a ser
> altamente fragmentado. Na prática, diferentes subconjuntos de
> vizinhanças frequentemente convergem para os mesmos ótimos locais em
> várias instâncias, gerando muitos empates (Δgap = 0). Como o Wilcoxon
> signed-rank descarta empates, o tamanho amostral efetivo pode cair
> abaixo do mínimo adotado na implementação (`n_shared >= 10` após
> remover empates), produzindo p-values `NaN` em parte dos pares.
> Nesses casos, na ausência de dominância estatística estrita após Holm,
> a decisão é feita por **parcimônia computacional** (Navalha de Occam),
> priorizando o subconjunto de menor cardinalidade que iguala o melhor
> gap mediano observado no tuning.

> **Referências para testes estatísticos:**
> Demšar, J. (2006). *JMLR*, 7, 1–30.
> García, S. et al. (2010). Advanced nonparametric tests for multiple
> comparisons. *Information Sciences*, 180, 2044–2064.

### Conjunto operacional pós-seleção

Após o término da seleção, os métodos de nível superior (`vnd`,
`grasp`, `tabu`) passam a herdar o subconjunto recomendado, em ordem de
complexidade:

* `relocate_intra`
* `swap_intra`
* `relocate_inter`
* `two_opt_inter`

No binário, esse conjunto é o padrão. Para reproduzir o conjunto
completo de 8 vizinhanças em `nls`/`vnd`, usar explicitamente:
`--vnd-neighborhoods all`.

## Execução padrão

```bash
python3 scripts/run_neighborhood_selection.py \
  --bin bin/vrptw \
  --input-dir input_tuning_set \
  --out results/neighborhood_selection \
  --seed 42 \
  --top-a 5 \
  --phase-b-restart 1 \
  --time-limit 0 \
  --randomize-queue
```

## Arquivos gerados

* `results/neighborhood_selection/i1_baseline.json` — baseline I1 de referência
* `results/neighborhood_selection/neighborhood_runs.csv` — granularidade por instância/configuração
* `results/neighborhood_selection/phase_a_summary.csv` / `.tex`
* `results/neighborhood_selection/phase_b_summary.csv` / `.tex`
* `results/neighborhood_selection/statistical_tests.csv` — matriz de p-values Wilcoxon+Holm
* `results/neighborhood_selection/recommended_set.csv`
* `results/neighborhood_selection/report.md`

## Reprodutibilidade mínima

* Separar instâncias de *Tuning* vs. *Holdout* (Birattari, 2009).
* Fixar seed da bateria (42).
* Fixar solução inicial (I1 determinístico).
* Randomizar ordem da fila de execução (Barr et al., 1995).
* Em Fase B, ordenar vizinhanças internamente por complexidade
  (Hansen & Mladenović, 2001).
* Manter `nls_restart=0` em Fase A e `nls_restart=1` em Fase B.
* Reportar mediana, IQR e p-values (Demšar, 2006).

## Referências consolidadas

* Barr, R. S., Golden, B. L., Kelly, J. P., Resende, M. G. C. &
  Stewart, W. R. (1995). Designing and reporting on computational
  experiments with heuristic methods. *Journal of Heuristics*, 1, 9–32.
* Birattari, M. (2009). *Tuning Metaheuristics: A Machine Learning
  Perspective*. Springer (Studies in Computational Intelligence, 197).
* Demšar, J. (2006). Statistical comparisons of classifiers over
  multiple data sets. *JMLR*, 7, 1–30.
* García, S., Fernández, A., Luengo, J. & Herrera, F. (2010). Advanced
  nonparametric tests for multiple comparisons in the design of
  experiments in computational intelligence and data mining.
  *Information Sciences*, 180, 2044–2064.
* Hansen, P. & Mladenović, N. (2001). Variable neighborhood search:
  Principles and applications. *European Journal of Operational
  Research*, 130(3), 449–467.
* Hooker, J. N. (1995). Testing heuristics: We have it all wrong.
  *Journal of Heuristics*, 1, 33–42.
* López-Ibáñez, M. et al. (2016). The irace package: Iterated racing
  for automatic algorithm configuration. *Operations Research
  Perspectives*, 3, 43–58.
* McGeoch, C. C. (2012). *A Guide to Experimental Algorithmics*.
  Cambridge University Press.
* Solomon, M. M. (1987). Algorithms for the vehicle routing and
  scheduling problems with time window constraints. *Operations
  Research*, 35(2), 254–265.
* Talbi, E.-G. (2009). *Metaheuristics: From Design to Implementation*.
  Wiley.
