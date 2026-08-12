# Verificação de fidelidade à literatura

Cada algoritmo do solver é confrontado com a fonte que ele diz implementar. Isto é diferente de validar o *avaliador* (que `solver/tests/test_evaluator_refs.cpp` já faz, reproduzindo 56/56 custos do CVRPLIB): aqui se pergunta se o **algoritmo** é o do artigo.

| # | Algoritmo | Fonte | Estado | Resultado |
|---|---|---|---|---|
| [01](01-solomon-i1.md) | Inserção I1 | Solomon (1987), Tabelas I–VI | 🟡 | 457 veículos contra 453 em 56 instâncias; C2 com 1 discrepância localizada |
| [02](02-algoritmos-de-melhoria.md) | VND | Hansen & Mladenović (2001) | 🟢 | ótimo local em todas as 6 vizinhanças, 56/56 |
| [02](02-algoritmos-de-melhoria.md) | GRASP | Feo & Resende (1995) | 🟢 | α=0 degenera na I1; 47 idênticas + 9 empates, 0 inexplicadas |
| [02](02-algoritmos-de-melhoria.md) | GRASP reativo | Prais & Ribeiro (2000) | 🟡 | degeneração corrigida (`block` → fração de K: 1 → 10-24 reponderações); **exige recalibrar** |
| [02](02-algoritmos-de-melhoria.md) | Busca Tabu | Glover (1989/1990) | 🟡 | devolve o melhor incumbente; *tenure* proíbe por t−1 iterações (off-by-one) |
| [03](03-vizinhancas.md) | Conjunto de vizinhanças | Potvin & Rousseau (1995), Or (1976), Taillard et al. (1997) | 🟢 | os 8 movimentos localizados; 2-opt\* implementado e justificado; operadores se repartem por família |
| [04](04-criterio-de-parada.md) | Critério de parada (K) | — | 🟡 | corretamente implementado, mas **não** equaliza esforço: fração útil de 0 % a 60 %, razão de tempo entre métodos inverte por instância |

🟢 reproduzido · 🟡 reproduzido com discrepância declarada · 🔴 não reproduzido · ⚪ não iniciada

O protocolo comum está em [00-metodologia.md](00-metodologia.md). Cada documento segue o mesmo esqueleto de oito seções, e as §§1–5 são escritas **antes** de rodar os experimentos.
