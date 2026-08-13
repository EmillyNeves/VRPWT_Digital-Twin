# Pré-registro da calibração (irace) — ex-ante

**Data:** 12/08/2026 · **Estado:** FECHADO antes da corrida · **Commit do solver:** ver §7

> **Para que serve.** Declarar, **antes** de rodar o irace, o que vai ser calibrado, em que
> intervalos, o que fica fixo e qual o critério de aceitação do resultado. Sem isso a
> justificativa dos valores é escrita depois de vê-los, que é racionalização, não método.
> Exigido pela decisão 4.7 (`docs/DECISOES-DE-PROJETO.md`), que vem de
> `docs/planejamento/irace_parameter_justification.md` §2.
>
> **Regra de alteração.** Depois de iniciada a primeira corrida, este documento só muda por
> **adendo datado** ao final, nunca por edição do que está acima. A única exceção prevista é a
> política de fronteira (§4), que já está declarada aqui e por isso não é mudança de plano.

---

## 1. O que é calibrado

Apenas os hiperparâmetros de **qualidade** de cada método — os que a fonte canônica de cada
algoritmo define como parâmetro do método.

| Cenário | Parâmetro | Intervalo | Hipótese ex-ante | Fonte |
|---|---|---|---|---|
| `grasp` | `alpha` | (0,0 · 0,5) real | α baixo constrói mais guloso, α alto mais diverso; o ótimo fica na metade inferior porque acima de 0,5 a construção perde estrutura da I1 | Feo & Resende (1995) |
| `rgrasp` | `delta` | (0,5 · 3,0) real | expoente da reponderação: δ baixo mantém as probabilidades próximas do uniforme, δ alto concentra rápido no melhor α | Prais & Ribeiro (2000) |
| `rgrasp` | `block_frac` | (0,02 · 0,40) real | cadência de reponderação como **fração de K**; 0,02 dá ~50 reponderações, 0,40 dá ~2,5 | idem |
| `tabu` | `tenure` | (5 · 80) inteiro | tenure pequeno intensifica, grande diversifica; a literatura sugere 0,1–0,4·n para n=100, e a corrida anterior venceu em 39 dentro de (5,40) — fronteira, daí o teto dobrado | Glover (1989, 1990) |

**Grade de α do reativo:** fixa em 10 valores uniformes, não calibrada — calibrar a grade
junto com δ confundiria o mecanismo reativo com o conjunto sobre o qual ele opera.

## 2. O que fica fixo, e por quê

| Elemento | Valor | Razão |
|---|---|---|
| Critério de parada `K` | **800**, uniforme | orçamento declarado, não parâmetro (decisão 3.1b). Um orçamento monótono não pode ser escolhido minimizando o objetivo |
| Teto de tempo | 600 000 ms | apenas segurança; o pior caso medido em K=800 é 76 s |
| Parâmetros da I1 | μ=1,0 · λ=2,0 · α₁=1,0 · α₂=0 · semente mais distante | partida comum a todos os métodos (decisão 1.4); calibrá-los daria a um método uma solução inicial melhor que a dos outros |
| Conjunto de vizinhanças | as seis de `all_neighborhoods()` | mesmo kit entre métodos (decisão 2.5), garantido por construção |
| Ordem das vizinhanças | complexidade crescente | decisão 2.2, guardada por teste |
| `objective` · μ · ε | cost · 1,0 · 1e-6 | decisão 1.3, guardada por teste |
| Convenção de distância | DIMACS, truncada a 1 casa | decisão 6.1, guardada por teste |

## 3. Função de score

```
score = gap_pct          (λ = 0)
```

**λ = 0 é escolha, não omissão** — e aqui ela é a única defensável. O template do projeto
recomendava `score = gap_pct + λ·time_sec` com λ = 1e-4, desenhado para um estudo em que a
parada é por **tempo igual**. Com parada por **K iterações sem melhoria**, esse termo se
inverte: uma configuração que estagna cedo atinge K mais rápido e **termina antes**, de modo
que penalizar tempo passaria a **premiar a busca pior**. Fecha também a decisão 4.3, que
permitia λ = 0 como alternativa DIMACS estrita.

Desempate por tempo, se necessário, fica para a análise ex-post, onde não pode contaminar a
seleção.

**Penalidade:** `1e9` fixa em falha de execução **ou solução inviável** (decisão 4.4). O
`target-runner` consulta o código de saída de `solve` — sem isso, uma configuração que
violasse janela de tempo ou capacidade seria premiada por ter custo baixo.

## 4. Política de fronteira (ação obrigatória, declarada antes)

Se o vencedor de um cenário cair na **borda** de um intervalo, isso é evidência de intervalo
curto, não de ótimo. Ação: **abrir novo intervalo e repetir a corrida daquele cenário**, e
registrar as duas corridas. Aplicada uma vez já: `tenure` venceu em 39 dentro de (5,40); o
teto foi para 80. `block` venceu em 199 dentro de (20,200) e foi substituído por `block_frac`,
livre de escala.

Um valor de fronteira, se persistir após o alargamento, é reportado como *"o melhor dentro da
faixa testada"*, nunca como ótimo.

## 5. Protocolo

| Item | Valor |
|---|---|
| Instâncias | **28 de treino** (`experiments/config/train.txt`), estratificadas por família e tipo |
| Holdout | 28 de teste — **não** vistas pelo irace, nem por nenhuma decisão anterior (inclusive a de K) |
| `maxExperiments` | **1500** por cenário (decisão 4.6; o plano previa 1000, o aumento fica registrado aqui *antes*, não depois). O valor estava em três lugares com três números diferentes — 2000 no `scenario.txt`, 1500 e 1200 nos pipelines, e o da linha de comando vencia; os três foram alinhados |
| Determinismo | `deterministic=1` para `tabu` (não tem fonte de aleatoriedade; sem isso o irace gasta orçamento reexecutando o idêntico), `0` para `grasp` e `rgrasp` |
| Sementes | geridas pelo irace; a semente entra no solver via `--seed` |

## 6. Critério de aceitação — declarado antes de ver o resultado

A calibração é aceita se **todas** as condições valerem:

1. **Nenhum vencedor na borda** de intervalo, após aplicada a política de §4.
2. **O calibrado supera o não calibrado no holdout** — comparação contra os *defaults* da
   literatura (α=0,30 · δ=1,0 · tenure=15), mesmas instâncias, mesmo K, mesmo número de
   sementes (decisão 5.2, `analysis/calibration_gain.py`).
3. **A vantagem não é ruído**: Wilcoxon pareado no holdout com p < 0,05.

Se (2) ou (3) falharem, o resultado honesto é **reportar que a calibração não rendeu ganho
demonstrável** e usar os *defaults* da literatura — não repetir a corrida até dar certo.

## 7. Rastro

Preencher no momento da corrida:

- Commit `git HEAD`: `41e42ecb` **com modificações não commitadas** em `Logger.hpp`, `Grasp.cpp`, `TabuSearch.cpp` (acréscimo da coluna `iter` no traço de convergência)
- Hash SHA-256 do fonte do solver (16 dígitos): `081d291455320de3` — é ele, e não o commit, que identifica o binário desta corrida
- Suíte de testes na largada: **34/34**
- Início: `2026-08-12T22:58` · fim: `________`
- Logs: `results/irace/<cenário>/irace.log` (versionados)
- Saída: `experiments/config/tuned.json`

---

## Adendos

### Adendo 1 — 13/08/2026: corrida reiniciada por correção do gerador de sementes

**O que aconteceu.** Com a corrida do cenário `grasp` em andamento (~625 experimentos), uma
auditoria de reprodutibilidade encontrou dois defeitos no protocolo de sementes, ambos já
apontados pelo parecer de revisão crítica e ainda não corrigidos:

1. O texto do relatório descrevia a mistura de um "índice da execução" que o código passava
   como constante `0` — a descrição não correspondia ao implementado.
2. O hash da instância usava `std::hash`, que é *implementation-defined*: os fluxos
   aleatórios só se reproduziriam na mesma biblioteca padrão, contradizendo a
   reprodutibilidade declarada.

**Correção.** `make_seed` passou a usar FNV-1a (especificado byte a byte, portátil) e a
assinatura perdeu o parâmetro morto; o texto do relatório foi corrigido para descrever o
protocolo real. Suíte de testes após a mudança: **34/34**.

**Por que reiniciar em vez de seguir.** A correção altera os fluxos aleatórios do GRASP e do
Reativo; deixar a corrida seguir produziria parâmetros calibrados com um binário diferente do
que executará o estudo — exatamente o vínculo que o §7 deste documento existe para garantir.
O custo do reinício (~2,5 h de computação) é menor que o custo metodológico de um binário de
calibração distinto do binário de medição.

**Identidade nova.** Hash SHA-256 do fonte (16 dígitos): `b3b81e0cb0c3bb1c`. Este hash
substitui o do §7 como identificador do binário da corrida. Os artefatos da corrida
interrompida foram descartados (`results/irace/grasp/` recriado na relargada).

Nenhum intervalo, parâmetro, critério de aceitação ou instância mudou — as seções 1–6
permanecem exatamente como pré-registradas.
