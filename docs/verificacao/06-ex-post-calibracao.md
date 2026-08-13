# Justificativa ex-post da calibração — decisão 4.8

**Data:** 13/08/2026 · **Pré-registro:** `05-pre-registro-calibracao.md` (fechado antes da corrida; Adendo 1 registra o reinício pela correção do gerador de sementes) · **Binário:** hash `b3b81e0cb0c3bb1c`, testes 34/34

## 1. Resultado da corrida (irace, 1500 experimentos por cenário, 28 instâncias de treino)

| Cenário | Parâmetro | Intervalo | Vencedor | Posição no intervalo |
|---|---|---|---|---|
| grasp | alpha | (0; 0,5) | 0,2191 | interior (44 % da faixa) |
| rgrasp | delta | (0,5; 3,0) | 1,8517 | interior (54 %) |
| rgrasp | block_frac | (0,02; 0,40) | 0,0275 | interior (2 %) — ver §4 |
| tabu | tenure | (5; 80) | 49 | interior (59 %) |

**Política de fronteira (4.5): aprovada.** Nenhum vencedor em borda. O tenure = 49 valida o
alargamento pré-registrado: na corrida anterior o vencedor (39) estava na borda de (5, 40) —
com o teto em 80, o ótimo apareceu acima da borda antiga e longe da nova.

## 2. Portão de aceitação (§6 do pré-registro): calibrado × default no holdout

Regime clássico (α=0,30 · δ=1,0, block_frac=0,1 · tenure=15) contra o calibrado, **28
instâncias de teste** — nunca vistas pelo irace —, 30 sementes, mesmo K=800, mesmo binário.
Wilcoxon pareado sobre os gaps médios por instância.

| Cenário | Ganho (pp) | melhor/pior/empate | p | Critérios 2+3 | Decisão pré-registrada |
|---|---|---|---|---|---|
| grasp | **−0,022** | 9/11/8 | 0,6316 | **falha** | **usar o default α = 0,30** |
| rgrasp | +0,026 | 14/6/8 | 0,0496 | passa | manter δ=1,8517, block_frac=0,0275 |
| tabu | **+1,256** | 13/6/9 | 0,0431 | passa | manter tenure=49 |

A regra do §6 era: *"se (2) ou (3) falharem, reportar que a calibração não rendeu ganho
demonstrável e usar os defaults da literatura — não repetir a corrida até dar certo."*
Aplicada por cenário. O resultado do GRASP não é falha do estudo — é um achado: **o GRASP é
insensível a α na faixa (0,2–0,3)** nas instâncias de Solomon, o que o relatório reporta como
resultado. O Reativo passa no limiar por 0,0004; o valor exato é reportado e o efeito
(+0,026 pp) é descrito como pequeno — a leitura honesta é "não pior que o default, com
indício fraco de vantagem".

**Consequência operacional.** Os parâmetros finais do estudo estão em
`experiments/config/study_params.json` (com proveniência no próprio arquivo); `tuned.json`
permanece intocado como registro bruto do irace. O estudo completo foi reexecutado com os
parâmetros finais.

## 3. Checklist exigido pela decisão 4.8

| Item | Estado |
|---|---|
| Posição de cada vencedor no intervalo | §1 — todos interiores |
| Impacto no gap (holdout, mediana/média) | §2 — por cenário, com placar por instância |
| Custo de tempo | K=800 mediana 15,6 s (GRASP) · 22,7 s (Reativo) · 6,8 s (Tabu); pior caso 76 s ≪ teto 600 s (`results/stopping/cost.csv`) |
| Robustez | placar por instância em §2; elites do irace por cenário em `results/irace/*/irace.log` |
| Decisão final | study_params.json, com a regra que a produziu |

## 4. Observações que uma leitura crítica faria, respondidas antes

**block_frac venceu a 2 % da borda inferior — por que não alargar?** A política de fronteira
dispara para vencedor **na** borda, não perto dela; e o piso 0,02 tem justificativa ex-ante
própria (garante ~2 amostras por α em cada bloco de reponderação — abaixo disso as médias
$\bar Z_i$ do mecanismo reativo degeneram). As elites do cenário (0,0209–0,0275) sugerem que
reponderar com frequência é bom; o piso impede que "com frequência" vire "sem amostra".

**O p = 0,0496 do Reativo não é frágil?** É limítrofe, e é reportado como tal. A decisão de
manter o calibrado segue a regra mecânica pré-registrada — o mesmo mecanismo que rebaixou o
GRASP ao default. Aplicar a regra nos dois sentidos é o que a protege de viés de quem a aplica.

**A análise de K (04-criterio-de-parada) usou os parâmetros da calibração anterior.** Sim —
ela foi feita antes desta corrida, com α=0,1517/δ=1,3992/tenure=39. Sua conclusão (ranking e
significância invariantes de K=50 a 3200) é sobre a *insensibilidade da comparação ao
orçamento*, não sobre os valores dos parâmetros; o estudo final, com os parâmetros novos,
reproduz o mesmo ranking, o que é a confirmação prática. Registrado aqui para que a
divergência de parâmetros entre as duas análises não pareça descuido.
