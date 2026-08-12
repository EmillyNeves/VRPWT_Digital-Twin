# Proveniência das soluções de referência

Duas coleções, com **critérios de otimização diferentes e incomparáveis entre si**. Confundi-las invalida qualquer cálculo de gap.

## `dinamics/` — melhor-conhecido por MÍNIMA DISTÂNCIA

**É o conjunto do CVRPLIB** (<https://galgos.inf.puc-rio.br/cvrplib/en/instances/2>), sob a convenção do 12º Desafio DIMACS. Conferido em 2026-08-12:

| Instância | CVRPLIB | `dinamics/` |
|---|---|---|
| C101 | 827,30 | 827,3 |
| R101 | 1637,70 | 1637,7 |
| R201 | 1143,20 | 1143,2 |
| RC101 | 1619,80 | 1619,8 |
| RC205 | 1154,00 | 1154,0 |

O rótulo "Dinamics" é corruptela de **DIMACS**. O nome da pasta foi mantido por compatibilidade com o código; ao citar no relatório, use **"CVRPLIB (convenção DIMACS)"**.

**Convenção:** distância euclidiana **truncada a 1 casa decimal** por aresta, tempo de viagem igual à distância, objetivo = distância total apenas (o número de veículos não entra). É esta a referência usada para calcular `gap_pct` no estudo comparativo.

**Formato:** `Route #k: <ids><espaço>` + linha final `Cost <valor com 1 casa>`. LF puro.

**Verificação automática:** `solver/tests/test_evaluator_refs.cpp` alimenta as 56 soluções no nosso avaliador e exige viabilidade e reprodução do `Cost` a ±0,05. Passa 56/56 — é o portão que sustenta a convenção de distância.

## `sintef/` — melhor-conhecido LEXICOGRÁFICO

Do SINTEF/TOP (<https://www.sintef.no/projectweb/top/vrptw/100-customers/>). Minimiza **primeiro o número de veículos**, depois a distância. Por isso usa menos veículos e percorre mais distância que o `dinamics/` — R201 tem 4 rotas aqui e 8 lá.

**Convenção:** distância e tempo em **precisão dupla**, com o total reportado a 2 casas. **Não é** a convenção DIMACS.

**Formato:** cabeçalho de 4 linhas (`Instance name`, `Authors`, `Date`, `Reference`) + `Solution` + linhas `Route k : <ids>`. CRLF, nomes de arquivo em minúsculas. **Não tem linha `Cost`.**

### Os sete arquivos com custo numérico

Sete arquivos trazem, no campo `Reference`, um float de precisão total em vez de uma citação bibliográfica:

| Arquivo | `Reference` |
|---|---|
| `r112.txt` | 982.1396794793056 |
| `r203.txt` | 939.5033196327306 |
| `r207.txt` | 890.6082953143249 |
| `r211.txt` | 885.7113902423863 |
| `rc107.txt` | 1230.4774501448198 |
| `rc202.txt` | 1365.6450311683866 |
| `rc203.txt` | 1049.6242367397954 |

São o custo euclidiano em **precisão dupla** das próprias rotas do arquivo, e constituem a única âncora exata disponível para validar o modo `--dist-mode double`. Recomputá-las bate a ≤1e-6; sob truncamento erram por 3 a 4 unidades, o que faz delas um discriminador inequívoco entre as duas convenções.

Lidas por `read_solution_file` no campo `ParsedSolution::reference`, que só aceita um token único e integralmente numérico após os dois-pontos — os outros 49 arquivos trazem prosa ali (`"... Springer 2007."`, `"N/A"`, uma URL) e um parse frouxo leria `2007.` como custo. Verificado por `reference_field_rejects_prose`: exatamente 7 de 56.

## Regra de uso

| Para | Use | Convenção |
|---|---|---|
| `gap_pct` do estudo comparativo | `dinamics/` | truncada (DIMACS) |
| Confronto com Solomon (1987) | Tabelas I–VI do artigo | precisão dupla |
| Contexto lexicográfico (veículos → distância) | `sintef/` | precisão dupla |

Calcular gap contra `dinamics/` com `--dist-mode double` **não tem significado**: são convenções numéricas distintas. Ver `docs/verificacao/01-solomon-i1.md`, §3, S4.
