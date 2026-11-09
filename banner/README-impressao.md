# Banner da XXXVI Jornada de IC da Ufes: impressão e conferência

## O evento

- **Quinta-feira, 12/11/2026, 9h às 12h** (credenciamento às 8h30)
- Campus de Goiabeiras, **Quadras do CEFD**, sessão de Engenharias e Ciências Exatas e da Terra
- Protocolo de inscrição: **202526313** (está impresso no cabeçalho do banner)
- Só a estudante responsável pelo relatório apresenta, e deve ficar as 3 h de exposição.
- Se não puder comparecer: justificativa com comprovante para pesquisa.prppg@ufes.br,
  assunto "Jornada 2026 - justificativa de ausência".

## Para a gráfica

| Item | Valor |
|---|---|
| Arquivo | `banner.pdf` (1 página, vetorial, fontes embutidas) |
| Tamanho | **A0, 84,1 cm × 118,9 cm**, retrato (dentro do máximo de 90 × 120 cm do edital), mesmo formato do modelo do LABOTIM |
| Material | lona ou papel fotográfico fosco; lona com bastão e cordão é o padrão das Jornadas |
| Acabamento | bastão superior e inferior, cordão para pendurar (as quadras usam varal/painel) |
| Sangria | não precisa, o conteúdo já tem margem |
| Cor | RGB; peça para a gráfica converter, não converta você |
| Resolução das figuras | o mapa está em 2768 px de largura para ~22 cm impressos (≈ 320 dpi); as demais em 300 dpi |

Leve o PDF em pendrive e também por e-mail. Peça uma prova em tela antes de imprimir
e confira que vai sair em A0 a 100 %, sem "ajustar à página".

## Checklist do edital (conferido no PDF)

- [x] Dimensões dentro do máximo de 90 × 120 cm (A0)
- [x] Número de protocolo visível (cabeçalho)
- [x] Logomarca da fonte de fomento (Ufes, bolsa Piic) e do projeto Fapes 2026-6NX7B
- [x] Métodos e resultados claramente apresentados
- [x] Nome da estudante e da orientadora

## Como recompilar

```bash
# Tectonic 0.17 em ~/.local/bin (instalado em 09/11/2026)
cd "/home/emilly/Área de trabalho/IC/banner"
tectonic banner.tex          # gera banner.pdf
pdfinfo banner.pdf           # deve dizer: Pages 1, Page size 2383.94 x 3370.39 pts (A0)
```

Para regenerar as figuras a partir dos CSVs de `results/` (sem reexecutar algoritmo
nenhum, os números são os do relatório):

```bash
cd "/home/emilly/Área de trabalho/IC"
.venv/bin/python banner/figuras/gerar_figuras.py
```

Os avisos `Missing character ... nullfont` na compilação são da medição interna
do `baposter` e não afetam o PDF.

## Decisões de layout que não são óbvias

- Modelo: `poster_dmbv_Marcos_Vinicius/poster-jornada-2024.tex` (LABOTIM, Jornada 2024).
  Mesma classe `baposter.cls` (copiada para esta pasta), A0, `fontscale=0.285`,
  Palatino, bordas `roundedleft`, títulos `roundedright` em versalete, Resumo em largura
  total, coluna 1 com problema/métodos/conclusão, colunas 2 e 3 com Metodologia e
  Resultados, Agradecimentos e Referências em caixas separadas no rodapé.
- O Tectonic não renderiza o degradê nativo do `baposter`: as barras são desenhadas
  com 60 faixas sólidas, encaixadas em `\baposter@box@headershade@plain`.
- Cores iguais às do modelo: barra em degradê linear de preto a ciano (#25AAFF, a
  `lightblue` do modelo) e borda #3189D1, medidas no PDF do lab (CNMAC-2019).
- A classe carrega o `xcolor` em CMYK; o preâmbulo força `\selectcolormodel{rgb}`.
- No `baposter`, uma caixa com `above=` precisa vir depois da caixa citada: por isso o
  rodapé é declarado antes das colunas.
- Nas referências, não use `\\` antes de `[2]`: o LaTeX lê `\\[2]` como espaçamento.
  Use `\par`.
- Logos: `logos/labotim-ufes.png` e `logos/fapes-cor.png` vêm do modelo (coloridos).
- Versão anterior (13 seções, 90 × 120 cm) arquivada em
  `_arquivo_morto/banner-v1-xebaposter/`.

## Arquivos

```
banner.tex              fonte do pôster
banner.pdf              arquivo para a gráfica
banner-preview.png      prévia em baixa resolução para conferir no celular
pitch-e-perguntas.md    fala de 3 min e banco de perguntas da banca
figuras/gerar_figuras.py   regenera as figuras a partir de results/
figuras/*.png           figuras em 300 dpi
logos/                  Ufes (vetor, manual de marca), Fapes, LABOTIM
document(35).pdf        relatório final entregue (fonte de todos os números)
```
