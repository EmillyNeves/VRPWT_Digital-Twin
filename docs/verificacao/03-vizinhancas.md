# Verificação 03 — Conjunto de vizinhanças do VND

**Estado:** 🟢 os oito movimentos localizados; a caracterização do relatório parcial foi quantificada e confirmada
**Artefatos:** `results/neighborhoods/{ablation.csv, summary.csv}` · `experiments/analysis/neighborhood_ablation.py`

---

## 1. Onde estão os oito movimentos

O relatório parcial lista oito movimentos de busca local. Três dos operadores implementados cobrem **tanto a variante intra quanto a inter** — o que se lê nos limites dos laços em `solver/src/Neighborhoods.cpp`:

| Movimento (relatório parcial) | Operador | Evidência no código |
|---|---|---|
| Relocate intra · Relocate inter | `relocate` | `for r2 = 0..R` — inclui `r2 == r1` |
| Swap intra · Swap inter | `swap` | `for r2 = r1..R` — inclui `r2 == r1` |
| 2-opt intra | `twoopt` | `for r` — rota única |
| Or-opt | `oropt` | `for r2 = 0..R` — intra e inter |
| Cross-exchange | `cross` | `for r2 = r1+1..R` — segmentos de até 3 |
| 2-opt inter (2-opt\*) | `twooptstar` | implementado nesta verificação |

**Oito movimentos em seis operadores.** O 2-opt\* (Potvin & Rousseau, 1995) era o único ausente; ele troca as **caudas** de duas rotas, de comprimento arbitrário, enquanto o Cross-exchange desta implementação troca segmentos limitados a três clientes.

---

## 2. A caracterização do relatório parcial, quantificada

O Quadro 2 do relatório parcial descreve quatro grupos de operadores por seu **papel**, não por exclusão. A ablação sobre as 28 instâncias de treino quantifica cada afirmação:

| Grupo (Quadro 2) | O que o parcial afirma | Medido (Δ gap ao remover) |
|---|---|---|
| Entre rotas — Relocate inter, 2-opt inter | "maior impacto nas melhorias mais relevantes" | Relocate **+3,152 pp** (o maior) · 2-opt\* **+1,417 pp** (2º) |
| Intra-rota — Relocate intra, 2-opt intra | "contribuição frequente em ajustes finos" | 2-opt intra +1,001 pp, concentrado em C1 e RC |
| Troca — Swap intra, Swap inter | "efeito complementar ao longo da busca" | Swap +0,984 pp, concentrado em RC |
| Mais complexos — Or-opt, Cross-exchange | "**uso mais localizado e menos recorrente**" | Or-opt +0,759 pp (significativo) · Cross-exchange atua em **4 de 28** instâncias |

**As quatro afirmações se confirmam.** O caso do Cross-exchange é literal: o Quadro diz "menos recorrente", e a tabela de frequência do estudo anterior registra **20 aplicações em 580 tentativas — taxa de 3,45 %**, a menor de todas.

### Contribuição marginal e significância

Leave-one-out contra o conjunto completo, Wilcoxon pareado com correção de Holm sobre as 28 instâncias de treino:

| Removido | Δ gap | piora | melhora | empata | p (Holm) | significativo |
|---|---|---|---|---|---|---|
| Relocate | **+3,152 pp** | 23 | 4 | 1 | 0,0015 | **sim** |
| 2-opt\* | +1,417 pp | 16 | 6 | 6 | 0,1745 | não |
| 2-opt intra | +1,001 pp | 8 | 8 | 12 | 0,7476 | não |
| Swap | +0,984 pp | 13 | 8 | 7 | 0,5349 | não |
| Or-opt | **+0,759 pp** | 12 | 1 | 15 | 0,0216 | **sim** |
| Cross-exchange | +0,501 pp | 4 | 0 | 24 | 0,5349 | não |

### Por família — cada operador tem seu regime

| Removido | C1 | C2 | R1 | R2 | RC |
|---|---|---|---|---|---|
| 2-opt intra | **+2,48** | 0,00 | +0,53 | −1,29 | **+2,84** |
| Swap | 0,00 | 0,00 | +0,18 | +0,37 | **+3,03** |
| 2-opt\* | 0,00 | −2,54 | +1,08 | +1,31 | **+4,43** |
| Relocate | +0,30 | **+4,70** | +1,76 | +2,94 | **+5,00** |
| Or-opt | +1,28 | +0,78 | +0,01 | +0,67 | +1,12 |
| Cross-exchange | 0,00 | 0,00 | +0,68 | +0,24 | +1,06 |

Valores negativos indicam que **remover melhora**: o 2-opt\* prejudica C2 e o 2-opt intra prejudica R2. É consequência da ordenação por complexidade (§4) — operadores baratos entram primeiro, disparam muito, e em famílias específicas conduzem a busca para uma bacia pior.

---

## 3. Conjunto adotado

**⟨2-opt intra, Swap, 2-opt\*, Relocate, Or-opt, Cross-exchange⟩** — os seis operadores, cobrindo os oito movimentos avaliados.

O mesmo conjunto é usado por VND, GRASP, GRASP reativo e Busca Tabu: `default_vnd_order()` e `find_best_admissible()` contêm exatamente os mesmos seis, o que é verificado por inspeção direta e sustenta a comparação em pé de igualdade entre os métodos.

### Por que não um subconjunto menor

Três razões, em ordem de força:

**(a) Os melhores subconjuntos por família diferem, e sua união é o conjunto completo.** Busca exaustiva dos 63 subconjuntos, em cada família:

| Família | melhor subconjunto |
|---|---|
| C1 | 2opt · 2opt\* · Reloc · Oropt |
| C2 | 2opt · Swap · Reloc · Oropt · Cross |
| R1 | 2opt\* · Reloc · Oropt · Cross |
| R2 | Swap · 2opt\* · Reloc · Oropt · Cross |
| RC1 | Swap · 2opt\* · Reloc · Oropt · Cross |
| RC2 | os seis |

**União = os seis.** Não é acaso: Solomon construiu o benchmark para ser heterogêneo (agrupada, aleatória, mista × horizonte curto e longo). Um conjunto único que sirva às seis estruturas é a união do que cada uma precisa.

**(b) O teste não pode remover o Cross-exchange.** Ele afeta 4 instâncias de 28; as outras 24 empatam exatamente. Com quatro observações não-nulas, o Wilcoxon **não atinge p < 0,05 nem no melhor cenário possível** — o p obtido (0,1908) é idêntico ao p mínimo alcançável. Excluí-lo com base nesse valor seria tratar falha em rejeitar como demonstração de equivalência.

**(c) O subconjunto menor é mais lento.** O melhor de quatro operadores custa 1143 ms contra 997 ms do completo. Sem 2-opt intra e Swap, que são baratos e resolvem muito rapidamente, o VND alcança o ótimo local usando só operadores caros. Os baratos reduzem o trabalho dos caros — é o mecanismo por trás da recomendação de Hansen & Mladenović.

---

## 4. Ordem de exploração

O planejamento do projeto define que as vizinhanças são percorridas **em ordem de complexidade computacional**, citando Hansen & Mladenović (2001): *"the neighbourhoods should be ordered so that the simplest is explored first"*.

A implementação anterior usava uma ordem "por promessa empírica". Corrigido. A ordem vem do custo **medido** de uma varredura completa (teste `neighborhood_scan_cost_ordering`), não da ordenação teórica do planejamento — aquele documento ordena oito operadores separados, e esta implementação **funde** intra e inter em três deles, o que inverte o custo relativo:

| Operador | µs por varredura | escopo |
|---|---|---|
| 2-opt intra | ~10 | R rotas × L² |
| Swap | ~170 | R²/2 pares × L² |
| 2-opt\* | ~300 | R² pares × L² |
| Relocate | ~320 | R² pares × L² |
| Or-opt | ~1000 | R² × L² × cadeias 2–3 |
| Cross-exchange | ~1700 | R² × L² × 9 combinações |

Efeito da correção nas 56 instâncias: gap médio de 11,0713 % para 10,6007 % (**−0,47 pp**), com +3,8 % de tempo. O aumento de tempo é o comportamento esperado: explorando primeiro o barato, o VND encontra mais movimentos melhorantes, reinicia mais vezes e chega a um ótimo local melhor.

**Ressalva a declarar:** a regra canônica é de *eficiência*, não de qualidade, e ela custa qualidade em duas famílias (C2 e R2, §2). Foi mantida por fidelidade metodológica.

---

## 5. Correção a um documento interno

`docs/planejamento/neighborhood_selection_approach.md` registra um subconjunto recomendado de quatro movimentos — `relocate_intra`, `swap_intra`, `relocate_inter`, `two_opt_inter`. Esse conjunto **não se sustenta**: dá 11,388 % de gap contra 8,249 % do completo (**+3,14 pp**), por descartar o Or-opt, que é um dos dois operadores estatisticamente significativos (p = 0,0216 com Holm).

O subconjunto de quatro nunca chegou ao relatório parcial — o parcial descreve papéis, não exclusões. A correção é interna e está registrada aqui.

---

## 6. Rastro

- Operador novo: `solver/src/Neighborhoods.cpp` (`find_twoopt_star`, `apply_move`), `solver/include/vrptw/Neighborhoods.hpp`, `solver/src/TabuSearch.cpp` (`involved`), `solver/apps/solve.cpp` (token `twooptstar`)
- Ordem: `solver/src/VND.cpp` (`default_vnd_order`)
- Script: `experiments/analysis/neighborhood_ablation.py` — 28 instâncias × 13 configurações
- Testes: `neighborhood_scan_cost_ordering`, `vnd_is_local_optimum_in_all_neighborhoods` (56/56 nas seis vizinhanças)
