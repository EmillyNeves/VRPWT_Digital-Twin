# Racional da calibração de parâmetros (irace)

Documento de apoio ao relatório, justificando **o que é calibrado, o que é fixado e por quê**.
A calibração usa o pacote **irace** (López-Ibáñez et al., 2016), padrão de fato para configuração
automática de algoritmos, sobre a divisão **treino/teste 28/28** estratificada por família (C/R/RC)
e tipo (1/2). O irace só vê o conjunto de **treino**; os resultados são reportados no teste e no
conjunto completo, evitando superajuste (*tuning leak*).

## Princípio: calibrar o mínimo, fixar o resto por justiça

A comparação é entre **estratégias de busca**, não entre implementações. Por isso, tudo que é
compartilhado é **fixado** identicamente para todos os métodos, e só os hiperparâmetros **canônicos**
de cada meta-heurística (aqueles que os próprios autores expõem) são calibrados.

| Elemento | Decisão | Justificativa |
|---|---|---|
| Convenção de distância (trunc. 1 casa) | **fixo** | Convenção DIMACS; verificada contra as 56 referências. |
| Parâmetros da I1 (μ=1, λ=2, α₁=1, α₂=0) | **fixo** | Configuração canônica de Solomon (1987); a I1 é semente comum, não objeto de comparação. |
| Kit de 5 vizinhanças | **fixo** | Justificado por ablação (`results/ablation_summary.csv`); o mesmo para todos = justiça. |
| Ordem do VND | **fixo** | Determinística; mesma para todos. |
| Nº de execuções (30 estocásticas) | **fixo** | Prática padrão em meta-heurísticas para estabilidade estatística. |
| **GRASP: α (RCL)** | **calibrado** | Único parâmetro do GRASP clássico (Feo & Resende, 1995). |
| **Reativo: δ, block** | **calibrado** | Expoente e cadência de atualização de probabilidades (Prais & Ribeiro, 2000). |
| **Tabu: tenure** | **calibrado** | Único parâmetro da Busca Tabu clássica (Glover, 1989/1990). |
| **K (iterações sem melhoria)** | **calibrado** | Critério de parada primário; ver nota abaixo. |

## Faixas de busca (e por quê)

- **GRASP `--alpha` ∈ (0,0; 0,5).** α=0 é guloso, α=1 é aleatório; valores úteis para construção
  gulosa-aleatorizada concentram-se na metade inferior do intervalo (RCL ainda seletiva). Faixa
  compatível com o uso reportado por Feo & Resende.
- **Reativo `--delta` ∈ (0,5; 3,0).** δ controla a agressividade da reponderação dos α; δ=1 é o valor
  do artigo original, e a faixa permite tanto suavizar (δ<1) quanto acentuar (δ>1) o contraste.
- **Reativo `--block` ∈ (20; 200).** Número de iterações entre atualizações de probabilidade; deve ser
  grande o bastante para estimar a qualidade média de cada α e pequeno o bastante para adaptar.
- **Tabu `--tenure` ∈ (5; 40).** Para n=100 clientes, a literatura sugere *tenure* da ordem de 0,1–0,4·n;
  a faixa cobre desde memória curta até memória longa.
- **K `--max-no-improve`:** GRASP/Reativo ∈ (20; 150) — cada iteração é cara (construção + VND); Tabu
  ∈ (50; 1000) — cada iteração é um único movimento, muito mais barato.

## Nota sobre a calibração de K

K é um **orçamento de busca**: mais iterações sem melhoria nunca pioram a qualidade (só custam tempo).
Por isso o irace tende a escolher K próximo do limite superior da faixa. As faixas acima codificam,
portanto, uma decisão consciente de **orçamento computacional** por algoritmo (mantendo o tempo de
execução em uma janela razoável), e não um ótimo de qualidade interno. Reportamos, junto com a
qualidade, o **tempo de relógio** e o **número de iterações** efetivamente realizados, além das curvas
tempo-alvo (TTT), para que o esforço fique transparente e a comparação permaneça honesta apesar de uma
"iteração" custar coisas diferentes em métodos diferentes.

## Reprodução

```bash
cd experiments
bash calibrate.sh 600000 1200 14   # safety_ms  max_experiments  parallel
# gera results/irace/<algo>/irace.log e experiments/config/tuned.json
```
