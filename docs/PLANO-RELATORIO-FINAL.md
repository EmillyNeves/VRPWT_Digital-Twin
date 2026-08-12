                                                                 # Plano de execução — Relatório Final de IC

**Objetivo:** produzir `docs/relatorio-final/` no formato modular exigido (`main.tex` + `topicos/`), cumprindo o planejamento do relatório parcial, com todos os dados corrigidos e verificáveis.

**Regra de ouro que governa este plano:** *nenhum número entra no relatório sem um artefato versionado no repositório que o sustente.* Hoje `results/` não é versionado, então nenhum número do rascunho atual é auditável. Isso se resolve no Bloco 0.

---

## Parte 0 — Três decisões a tomar antes de escrever

Estas decisões mudam materialmente o que será escrito. Decida-as primeiro.

| # | Decisão | Opção A | Opção B | Consequência |
|---|---|---|---|---|
| D1 | **Orçamento de CPU disponível** | Só horas (Bloco 1) | Dias (Bloco 1 + Bloco 2) | Com A, K e o irace entram como *declaração honesta de limitação*; com B, entram como resultado calibrado |
| D2 | **Destino do Digital Twin** | Consertar o horizonte e manter como VRPTW | Reclassificar como CVRP com priorização | A afeta a Seção 5 inteira; B é honesto e custa 20 min |
| D3 | **Escopo do capítulo de resultados** | Só Solomon-100 | Solomon-100 + 3 instâncias WCVRPTW | B fecha a Etapa 7 do cronograma e dá validade externa ao tema do subprojeto |

**Recomendação:** D1 = A se a entrega for em semanas, B se houver mais de um mês. D2 = A se D1 = B, senão B. D3 = B (as 3 menores instâncias custam pouco e o subprojeto se chama "Coleta de Resíduos Sólidos").

---

## Parte 1 — Experimentos e correções de dados

### Bloco 0 — Tornar auditável o que já existe (30 min, faça primeiro)

| Ação | Arquivo | Motivo |
|---|---|---|
| Remover `results/irace/` do `.gitignore` | `.gitignore:19` | `tuned.json` hoje não tem proveniência |
| `git add` dos agregados | `results/{overall,per_instance,gap_by_family,nemenyi_pvalues,ablation_summary,knee_K,primal_integral}.csv` | sem isso nenhum número é verificável |
| `git add` das 12 figuras referenciadas + `runs.csv` comprimido + `irace.log` | `results/figures/`, `results/raw/` | o `.tex` não compila com figuras em clone limpo |
| Criar `data/reference-solutions/PROVENIENCIA.md` | novo | o rótulo "Dinamics" não é definido em lugar nenhum |

### Bloco 1 — Barato (horas de CPU), destrava a maior parte do texto

| # | Experimento | Como | Destrava |
|---|---|---|---|
| 1.1 | **Estatística correta** — Wilcoxon pareado + Holm nas 10 comparações; Nemenyi com e sem a I1; gap treino × teste | **Recomputável a partir de `tabela_por_instancia.tex`**, que já está versionado e tem os 5 algoritmos × 56 instâncias. Não precisa reexecutar o solver | Seção Resultados inteira; corrige o achado crítico do pool de algoritmos |
| 1.2 | **KPI de transbordos** — contar episódios, não bin-ciclos | `sensors.py:43-45`: guardar `was_full` antes do passo; expor `overflow_bin_cycles` à parte | Tabela do Twin; a conclusão inverte |
| 1.3 | **Twin com ≥30 sementes** + média, IC95% e Wilcoxon pareado | `compare_scenarios` em laço de sementes | substitui inferência sobre n=1 |
| 1.4 | **Twin com parâmetros calibrados nos dois regimes** | passar `extra=load_tuned()[algo]` também a `simulate_static`; trocar parada por `--max-no-improve` | hoje o Twin roda GRASP *não calibrado*, parado por relógio |
| 1.5 | **Horizonte do Twin** (se D2 = A) | derivar `H` da escala (H ≈ 300 com `service=5`) e reportar fração de janelas ativas por κ | sem isso as janelas dinâmicas continuam inertes |
| 1.6 | **Ablação com inferência, só no treino** | Wilcoxon + Holm sobre os gaps por instância; contagem piora/empata/melhora; publicar o desenho cumulativo já computado | remove o vazamento e a afirmação "remover qualquer operador piora" (o Swap não sobrevive) |
| 1.7 | **Baseline *default* × calibrado** | criar `experiments/config/default.json` com `--alpha 0.3` / `--delta 1.0 --block 50` / `--tenure 15`; rodar `runner.py --params-file` nas 28 de teste | **a tabela que mais falta**: hoje não há evidência de que calibrar serviu para algo |
| 1.8 | **Tabela lexicográfica correta** | duas colunas — média de 30 e melhor de 30 | hoje reporta best-of-30 chamando de "média" |

### Bloco 2 — Caro (dias de CPU), faça só se D1 = B

| # | Experimento | Como | Se não fizer |
|---|---|---|---|
| 2.1 | **Grade de K estendida** | `grasp/rgrasp: [20,40,80,160,320,640,1280,2560]`; `tabu: [100,…,12800]`; ≥10 sementes; critério formal (Kneedle) | escrever: *"K foi limitado pelo orçamento computacional, não pela convergência"* e **apagar** a palavra "joelho" e a legenda da figura |
| 2.2 | **irace com intervalos expandidos** | `tenure ∈ (5,80)`; `block` relativo a K (`block_frac ∈ (0,01; 0,5)`); declarar `seed`, `deterministic=1` para tabu | escrever a ressalva: *"tenure e block venceram na fronteira superior; leia-se 'o melhor dentro da faixa testada', não como ótimo"* + a frase de que o Reativo estava degenerado (1 atualização por execução) |
| 2.3 | **Comparação sob tempo de CPU igual** | `--budget-ms T*` (≈20 s), K desativado, 30 sementes, 28 de teste; repetir Friedman | a alegação de isonomia do README fica sem suporte |
| 2.4 | **Integral primal ampliado** | 28 instâncias, sementes uniformes | declarar *"três instâncias, réplicas 5/5/1/1"* e trocar "confirmando" por "sugerindo, em caráter exploratório" |
| 2.5 | **WCVRPTW** (se D3 = B) | 3 menores instâncias (102, 277, 335) contra Kim et al. (2006) | declarar em Limitações por que não foram usadas |
| 2.6 | **2-opt\*** (~20 linhas) + linha na ablação | testar *adicionar*, não só remover | declarar a omissão em Limitações e corrigir a afirmação falsa de que o Cross-exchange faz esse papel |

---

## Parte 2 — Estrutura do relatório, arquivo por arquivo

Migrar de `relatorio-final.tex` monolítico para `main.tex` + `topicos/`, espelhando `docs/template-relatorio-final/`.

### `main.tex`
Copiar o preâmbulo do template **sem alterações** (10pt, `\rmdefault` + `mathptmx`, `babel` brasileiro, `marginsize{30}{20}{30}{20}`, `\linespread{1.25}`). Ajustar apenas:
- `\fancyhead[R]`, 4ª linha → **"Ciências Exatas e da Terra"** (Grande Área, não "Ciência da Computação")
- Título centrado → **o título oficial do subprojeto**, idêntico ao da tabela de identificação
- Tabela de identificação → incluir a linha **"Grande Área do Conhecimento (CNPq)"**, hoje ausente
- `\bibliographystyle{hapalike2-NOand}` + `\bibliography{biblio}` + seção "Referências **Bibliográficas**"

### `topicos/resumo.tex`
`\section*{Resumo}`, **sem citações** (o modelo proíbe; o rascunho atual tem 7). Reescrever o resultado do Twin conforme 1.2/1.3.

### `topicos/introducao.tex`
- Aproveitar `relatorio-final.tex:117-123`, corrigindo:
- **Retirar a alegação de LoRaWAN** (`:121`) → "combina um **modelo de sensoriamento** de enchimento (processo de Poisson não homogêneo) com heurísticas..." e remover as citações que sustentam capacidade inexistente
- **Restaurar o vínculo** com o projeto guarda-chuva "Pesquisa Operacional e Inovação em Logística Regional"
- **Reconciliar a pergunta de pesquisa** com a do parcial: manter a formulação do parcial (integração IoT + heurísticas) e explicar, em uma frase, que o *benchmark* estático é a fundação metodológica da aplicação

### `topicos/objetivos.tex` — **NÃO EXISTE, criar**
Seção obrigatória. Listar o objetivo geral e os **7 objetivos específicos aprovados**, cada um com status honesto:

| Objetivo | Status |
|---|---|
| Modelagem do enchimento (NHPP) | cumprido |
| Critério Push Forward | cumprido |
| Simulação LoRaWAN com avaliação de consumo | **não cumprido** |
| Interface geoespacial | parcialmente cumprido |
| Digital Twin | cumprido (com as ressalvas da Seção de Limitações) |
| Validação com dados reais | parcialmente — localizações reais, enchimento simulado |
| Quantificação de benefícios econômicos/ambientais | **não cumprido** |

### `topicos/embasamento_teorico.tex` — **NÃO EXISTE, criar**
Seção obrigatória. Receber o que hoje está diluído na Metodologia:
- Formulação do VRPTW (hoje `:126-167`)
- **Seção "Trabalhos relacionados"** de meia página, hoje inexistente — três blocos (construção / busca local / meta-heurísticas), fechando com a frase que situa o trabalho: *"não buscamos o estado da arte (hoje na casa de frações de 1% de gap), mas uma comparação controlada de métodos clássicos sob um núcleo compartilhado"*
- Acrescentar à bibliografia: **Savelsbergh (1985)** (é dele o O(1), não de Solomon), Bräysy & Gendreau (2005, I e II), Cordeau et al. (2001), Taillard et al. (1997), Or (1976), Vidal et al. (2013)

### `topicos/metodologia.tex`
Base: `:170-456`. Correções obrigatórias:

| Onde | Correção |
|---|---|
| `:200` | retirar **"configuração canônica"** — é uma das quatro combinações de Solomon, e é a que ele conclui ser inferior (*"time insertion proved clearly superior to distance insertion"*, p.263). Acrescentar a restrição $\alpha_1+\alpha_2=1$ |
| `:229` | a justificativa da semente (reduzir veículos) é atribuída por Solomon ao critério **oposto** (*earliest deadline*) — reescrever ou remover |
| `:248` | **"Cross-exchange faz o papel do 2-opt inter" é falso** — o 2-opt\* troca caudas de comprimento arbitrário e pode fundir rotas. Corrigir também as atribuições: Or-opt é de Or (1976), Cross-exchange de Taillard et al. (1997), 2-opt\* de Potvin & Rousseau (1995) |
| `:164`, `:229` | o teste O(1) é de **Savelsbergh (1985)**, não de Solomon |
| `:423` | **falso**: os operadores usam `evaluate_seq` (simulação completa), não o teste O(1). Declarar o custo real por varredura |
| `:186`, `:366` | o atributo tabu é o **cliente-âncora** (1 para Relocate/Or-opt, 2 para Swap/Cross-exchange), não "todo cliente que o movimento toca" |
| `:188`, `:456` | o protocolo de semente descrito não é o implementado (o índice da execução está fixo em 0) |
| `:165` | "as quatro restrições" → cinco (falta o limite de frota), ou implementar a checagem |
| `:435`, `:440` | **reescrever a subseção de K** conforme 2.1 — se o joelho não existir, dizer que K é decisão de orçamento |
| `:494` | acrescentar a **ressalva de fronteira** para `tenure` e `block` |
| Nova subseção | **"A calibragem valeu a pena?"** com a tabela de 1.7 |

### `topicos/resultados.tex`
Base: `:459-654`. Correções obrigatórias:

- **Resultado primário passa a ser o conjunto de TESTE (28)**; as 56 vão para apêndice rotulado *"inclui as instâncias de calibração"*. CD recalculado para N=28 é **1,153**, não 0,815
- **Substituir Nemenyi por Wilcoxon pareado + Holm** e reescrever a conclusão. Texto sugerido: *"O pós-teste de Nemenyi não rejeita a igualdade entre GRASP e Busca Tabu (p=0,18); essa decisão, contudo, depende do conjunto de algoritmos incluído — excluindo a construção I1, dominada em todas as instâncias, a mesma diferença de rank torna-se significativa. Adotamos, portanto, Wilcoxon pareado com correção de Holm."*
- **"Estatisticamente equivalentes" → "não foi possível rejeitar a hipótese de igualdade com o poder disponível"**, com tamanho de efeito e IC
- **Ablação** com os testes de 1.6; restringir a afirmação aos operadores com efeito detectável
- **Tabela lexicográfica** com as duas colunas de 1.8; retirar "dominam" (não vale na família C sob a média)
- **Integral primal**: declarar n=3 e as réplicas
- **TTT**: ou refazer com 3 alvos / 3 métodos / QQ-plot, ou remover (com 100% de sucesso o gráfico não discrimina nada)
- **Seção do Twin**: reescrever a conclusão. O que sobrevive é *"mesma distância com metade das coletas"*; o que **não** sobrevive é *"menos transbordos"*
- **"Fonte:"** em todas as ilustrações (hoje são 19 sem nenhuma)

### `topicos/conclusao.tex`
- Retirar "estatisticamente equivalentes"
- **Novo parágrafo "Objetivos não atingidos e por quê"**: LoRaWAN, benefícios econômicos/ambientais, Simulação Baseada em Agentes, validação com enchimento real
- Limitações ampliadas: busca estritamente viável (a literatura de VRPTW usa inviabilidade penalizada), ausência de 2-opt\*, ausência de avaliação incremental

### `topicos/agradecimentos.tex`
Criar (PIIC/UFES, orientadora).

### Apêndice
Mover a tabela por instância (410 linhas) e as "leituras passo a passo" para material suplementar — **necessário para caber em 15 páginas**.

---

## Parte 3 — Correções que não dependem de experimento (~4 h no total)

Estas podem ser feitas em paralelo, hoje:

1. `:658` **Atividades realizadas** — reescrever etapa a etapa, no passado, com status honesto; **remover** "houve avanço de cronograma" (é o 12º de 12 meses com duas etapas declaradas inacabadas)
2. Contagem de execuções — hoje aparece como "dezenas de milhares" (`:167`) e "mais de sete mil" (`:471`); o estudo principal tem **3.528** (56 × [1+1+1+30+30])
3. Taxonomia de convenções (`:573`) — SINTEF **é** a euclidiana em precisão dupla; são duas convenções contadas como três, e falta a terceira genuína (arredondamento inteiro). Usar o exemplo do próprio repositório: C101 custa 827,3 truncado e 828,94 em precisão dupla
4. Rótulo "Dinamics" — sem referente em lugar nenhum; renomear para "CVRPLIB (convenção DIMACS)"
5. URL do DIMACS (`:683`) retorna **HTTP 404** — citar via `web.archive.org`
6. `README.md:153-154` — retirar "comparação em pé de igualdade" (Tabu opera com 76% do tempo do GRASP)
7. `experiments/TUNING_RATIONALE.md` — é para lá que o relatório manda o leitor, e ele diz o **oposto**: K "calibrado", faixas (20;150)/(50;1000) que nem contêm 250/1400. Reescrever
8. `docs/planejamento/` — marcar `irace_calibration_plan.md`, `conformance_audit.md`, `irace_search_space_template.md`, `irace_target_runner_template.md` e `neighborhood_selection_approach.md` como `Status: SUPERSEDED`, ou remover. Descrevem outro código (`src/main.cpp`, `bin/vrptw`, `--vnd-neighborhoods`) e a metodologia oposta
9. Preencher a tabela ex-post de `irace_parameter_justification.md:60-64` (hoje toda "PREENCHER")
10. Nota de reconciliação com o parcial: (a) Quadro 2 × ablação são medidas diferentes (frequência × contribuição marginal); (b) C102 é **empate triplo** sob os parâmetros calibrados, não vitória do Reativo

---

## Parte 4 — Checklist de conformidade formal

| Item | Exigido | Hoje | Ação |
|---|---|---|---|
| Corpo | 10pt Times (`main.tex:8,73`) | 12pt Arial (preâmbulo do **parcial**) | trocar preâmbulo |
| Seções | resumo, introdução, **objetivos**, **referencial teórico**, metodologia, resultados, conclusões, referências | faltam duas | criar |
| Cabeçalho, 4ª linha | Grande Área CNPq | "Ciência da Computação" | corrigir |
| Tabela de identificação | linha "Grande Área" | ausente | acrescentar |
| Resumo | `\section*`, sem citações | texto corrido, 7 citações | reescrever |
| **"Fonte:" nas ilustrações** | obrigatório, mesmo sendo produção própria | **0 de 19** | acrescentar (o parcial cumpria) |
| Impessoalidade | 3ª pessoa | ~26 ocorrências de 1ª pessoa | revisão linha a linha, **não** find/replace |
| Extensão | 15 páginas | 700 linhas + 13 figuras + 6 tabelas + 5 algoritmos + apêndice de 410 linhas | mover para suplementar; **instalar `texlive-latex-recommended` e compilar para conferir** |
| Bibliografia | `hapalike2-NOand` + `biblio.bib` | `thebibliography` manual; `biblio.bib` tem 14 de 18 entradas | migrar e acrescentar `dimacs12vrptw`, `cvrplib`, `potvin1995exchange`, `toth2002vehicle` — senão **4 citações viram "[?]"** |

---

## Parte 5 — Sequência recomendada

```
Semana 1   Bloco 0 (versionar evidências)          ─┐
           Parte 3 (correções de texto)             ├─ em paralelo
           Parte 4 (conformidade formal)           ─┘
           Decidir D1, D2, D3

Semana 2   Bloco 1 — experimentos baratos
           1.1 estatística (recomputável da tabela versionada, comece por aqui)
           1.2→1.5 Twin
           1.6 ablação
           1.7 baseline default × calibrado
           1.8 tabela lexicográfica

Semana 3   Bloco 2, se D1 = B (rodar em background enquanto escreve)
           Migração para main.tex + topicos/
           Escrever objetivos.tex e embasamento_teorico.tex (os dois novos)

Semana 4   Reescrever metodologia.tex e resultados.tex com os dados novos
           Compilar, conferir 15 páginas, revisar impessoalidade
           Revisão da orientadora
```

---

## Parte 6 — O que **não** mexer

Preserve integralmente: o núcleo compartilhado do solver; a verificação da convenção de distância contra as 56 referências; a divisão treino/teste estratificada; a camada viária real OSM/OSRM (fator de circuito 1,53 medido, matrizes explícitas sem contaminar o *benchmark* euclidiano); os 15 testes unitários; e o hábito, já presente no texto, de declarar limitações — é ele que resolve a maior parte deste plano.
