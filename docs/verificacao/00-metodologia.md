# Protocolo de verificação

Como cada algoritmo é confrontado com sua fonte. Escrito uma vez; os documentos `0X-*.md` o instanciam.

## Princípio

Verificar fidelidade é diferente de medir qualidade. A pergunta é *"este código é o algoritmo daquele artigo?"*, e a resposta tem que ser auditável por alguém que só tenha o repositório e o PDF.

Disso decorrem três regras:

1. **O oráculo é o artigo**, nunca um protótipo ou uma implementação de referência não testada. Protótipos servem para depurar, não para aprovar.
2. **Não se calibra o que se verifica.** Otimizar parâmetros para longe da especificação do autor produz outro algoritmo. Quando o espaço declarado é discreto e pequeno e o algoritmo é determinístico, "calibrar" degenera em enumerar — e a enumeração já é o protocolo do autor.
3. **O critério de aceitação é declarado antes do resultado.** Se ele mudar, a mudança e o motivo entram no documento; corrigir o critério depois de ver o número, sem registrar, é pós-racionalização.

## Esqueleto de oito seções

| § | Conteúdo |
|---|---|
| 1 | **Fonte canônica** — página, equações transcritas *verbatim*, alvos numéricos, PDF em `docs/referencias/` |
| 2 | **Mapeamento fórmula → código** — tabela equação ↔ arquivo/função |
| 3 | **Escolhas subdeterminadas** — o que o artigo não especifica, o que adotamos, a alternativa, e o **impacto medido** de cada uma |
| 4 | **Protocolo experimental** — comando exato, nº de execuções, artefato gerado |
| 5 | **Critério de aceitação** — Tier A (invariantes exatos, sem tolerância) e Tier B (concordância), com a **ancoragem** de cada tolerância |
| 6 | **Resultado** — lado a lado com a fonte, veredito por linha |
| 7 | **Discrepâncias não resolvidas** — cada uma com hipóteses testadas, refutadas e abertas |
| 8 | **Rastro** — arquivos tocados, testes, artefatos |

§§1–5 antes de rodar; §§6–8 depois.

## Ancorar tolerâncias

Uma tolerância não pode sair do resultado observado. Ela sai da **magnitude que as escolhas subdeterminadas conseguem explicar** — que é estimável antes de rodar e verificável depois, medindo cada uma.

Se, medidas, elas explicam menos do que o resíduo observado, a conclusão honesta é *"o resíduo não é atribuível à ambiguidade documentada"*. **Alargar a tolerância não é uma opção**: um critério que se ajusta ao resultado não é critério.

Prefira invariantes que **não precisam de tolerância**. Contagens inteiras (veículos, rotas, instâncias viáveis) valem mais que percentuais contínuos, e médias publicadas com arredondamento a 1 casa frequentemente reconstroem o inteiro subjacente sem ambiguidade.

## Ramo de falha

Um conjunto fora do critério dispara, nesta ordem: (1) rodar as sensibilidades já implementadas; (2) formular e testar hipóteses específicas; (3) se nenhuma explicar, é bug — depurar contra o teste de força bruta correspondente. Teto: 2 dias por conjunto. Persistindo, o veredito é *"não reproduzimos X"* na §7.

## Armadilhas que já custaram caro

- **Métrica inflada por constante.** Medir desvio numa grandeza dominada por um termo fixo (ex.: schedule time, 89% serviço nas famílias C) esconde desvios de uma ordem de grandeza.
- **Cherry-picking de convenção.** Havendo variantes, escolher por conjunto a que melhor encaixa é fraude. A escolha tem que vir de evidência externa ou de degradação uniforme.
- **Binário desatualizado.** Se o build de um app falha, os testes ainda compilam (linkam só a biblioteca) e uma varredura roda com o binário antigo, ignorando a flag nova em silêncio. **Toda flag nova exige um teste "isto muda alguma coisa?" antes de qualquer varredura.**
- **Premissa herdada não conferida.** Uma afirmação de levantamento ("dezenas de clientes empatam no prazo") pode estar errada e desviar horas de investigação. Confira antes de planejar em cima.
