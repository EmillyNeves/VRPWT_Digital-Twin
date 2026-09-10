# Roteiro da apresentação final (PIIC 2025/2026)

Otimização Dinâmica de Rotas para Coleta de Resíduos Sólidos: Adaptação do Algoritmo de Solomon com Integração IoT.
Regras seguidas: máximo de 4 tópicos por slide, máximo de 12 palavras por tópico, sem travessões.
Figuras citadas estão em `relatorio-final-2026/figuras/`. Números conferidos com o relatório final de 2026-09-10.

---

Slide 1: Otimização Dinâmica de Rotas para Coleta de Resíduos Sólidos

Texto:
- Adaptação do Algoritmo de Solomon com Integração IoT
- Emilly Lopes das Neves, orientadora Maria Claudia Silva Boeres
- Programa Institucional de Iniciação Científica, UFES
- Edital PIIC 2025/2026, Ciência da Computação

Fala: Bom dia. Vou apresentar o subprojeto de iniciação científica sobre roteamento de caminhões de coleta guiado por sensores de enchimento. A ideia central é usar heurísticas clássicas do problema de roteamento com janelas de tempo, comparadas de forma controlada, e depois aplicá-las em um gêmeo digital da coleta seletiva de Vitória.

Visual: mapa `vitoria_road_routes.png` ao fundo, com transparência, e o título por cima.

---

Slide 2: O problema

Texto:
- Coleta convencional: rotas fixas e frequência fixa
- Lixeira vazia recebe visita, lixeira cheia transborda
- Sensores de nível via LoRaWAN mostram o enchimento real
- Pergunta: como rotear com essa informação sem violar janelas de tempo?

Fala: Hoje o caminhão passa nos mesmos pontos, nos mesmos dias, independente do que há na lixeira. Isso gera dois desperdícios: visitas a lixeiras vazias e transbordos em lixeiras que encheram antes da visita. Com um sensor de nível em cada lixeira, ligado por uma rede de baixo consumo como LoRaWAN, o planejador sabe o enchimento real. A pergunta do trabalho é como transformar essa informação em rotas boas e viáveis, respeitando capacidade e prazos.

Visual: dois quadros lado a lado. Esquerda: caminhão em rota fixa passando por lixeiras vazias. Direita: lixeira transbordando. Ícones simples, uma frase em cada.

---

Slide 3: Objetivos e estrutura do trabalho

Texto:
- Comparar cinco heurísticas clássicas do VRPTW de forma controlada
- Calibrar parâmetros e comparar com testes estatísticos pareados
- Transferir os métodos calibrados a um gêmeo digital de Vitória/ES
- Medir o compromisso entre coletas e transbordos

Fala: O trabalho tem três camadas. Primeiro um benchmark estático nas instâncias clássicas de Solomon, que serve para calibrar e comparar os algoritmos. Segundo, a análise estatística dessa comparação. Terceiro, a aplicação dinâmica: os mesmos algoritmos, com os mesmos parâmetros, rodando dentro de um simulador da coleta seletiva de Vitória.

Visual: três blocos em sequência com setas: Benchmark, Estatística, Gêmeo digital.

---

Slide 4: Metodologia: um núcleo compartilhado

Texto:
- Cinco algoritmos: Solomon I1, VND, Busca Tabu, GRASP, GRASP Reativo
- Mesmo núcleo em C++: leitor, distâncias, rotas, vizinhanças, semente
- Verificador independente recalcula toda solução do zero
- Pseudocódigos em estilo livro-texto, com chamadas de sub-rotinas

Fala: Os cinco métodos foram implementados sobre um único núcleo de código. Isso importa porque, se cada um tivesse seu próprio leitor de instância ou sua própria matriz de distâncias, a comparação misturaria estratégia de busca com detalhe de implementação. Toda solução final passa por um verificador que só recebe a sequência de clientes e recalcula tudo do zero; qualquer violação derruba o experimento. Nas 3.528 execuções do estudo, nenhuma solução inviável apareceu. No relatório, os algoritmos estão em pseudocódigo compacto, com sub-rotinas como melhor_movimento e enfileira, e uma leitura linha a linha no texto.

Visual: diagrama com o núcleo no centro e os cinco métodos em volta; abaixo, o verificador como um portão. Ao lado, o Algoritmo 4 (Busca Tabu) recortado do PDF do relatório.

---

Slide 5: Do construtivo às meta-heurísticas

Texto:
- I1 de Solomon constrói a solução inicial de todos os métodos
- VND: seis operadores em ordem de custo, melhor melhora
- GRASP: reconstrói do zero a cada iteração e refina com VND
- Busca Tabu: aceita pioras, fila tabu, aspiração por objetivo

Fala: A inserção I1 de Solomon é a partida comum. O VND percorre seis operadores de vizinhança, do mais barato ao mais caro, e reinicia do primeiro a cada melhora. Fizemos uma ablação retirando um operador de cada vez; remover qualquer um piora o gap médio, com o Relocate como o mais importante, então o kit completo ficou. O GRASP repete construção aleatorizada e VND, guardando a melhor solução. A Busca Tabu segue uma trajetória única, aceita piorar para escapar de ótimos locais e usa uma fila de movimentos proibidos.

Visual: figura `operadores.png` com os seis operadores antes e depois.

---

Slide 6: Protocolo experimental

Texto:
- 56 instâncias de Solomon, 100 clientes, famílias C, R e RC
- Metade treino para o irace, metade teste para o resultado
- Parada por 800 iterações sem melhora, igual para todos
- Friedman e Nemenyi, depois Wilcoxon pareado com Holm

Fala: Usamos a convenção do desafio DIMACS: distância euclidiana truncada a uma casa decimal e objetivo de distância total. Validamos a implementação reproduzindo o custo das 56 soluções de referência. As instâncias foram divididas em 28 de treino, usadas pelo irace, e 28 de teste, que a calibração nunca viu. O critério de parada foi declarado, não calibrado, porque mais iterações nunca pioram e o irace levaria o valor ao teto. Testamos de 50 a 3200 iterações e a ordem dos métodos não muda. Um valor calibrado só substitui o clássico se vencer no conjunto de teste.

Visual: tabela de três colunas: parâmetros fixos, calibrados e declarados, com um exemplo em cada.

---

Slide 7: Calibração do GRASP Reativo

Texto:
- Grade de alfa de 0,05 a 0,50, probabilidades iniciais uniformes
- A cada bloco, reponderação pelo custo médio de cada alfa
- irace: expoente 1,85 e fração de bloco 0,0275
- Tabu: tenure calibrado 49; GRASP fixo mantém alfa 0,30

Fala: O GRASP Reativo não usa um alfa fixo. Ele tem uma grade de dez valores, de 0,05 a 0,50, todos com a mesma probabilidade no início. Cada alfa é testado uma vez nas dez primeiras iterações. Depois, a cada bloco de iterações, as probabilidades são recalculadas: alfas que produzem soluções mais perto do incumbente ganham peso, e o expoente controla a força desse ajuste. O irace calibrou o expoente em 1,85 e a fração de bloco em 0,0275, ou seja, 22 iterações com o orçamento de 800. Esse calibrado ficou 0,03 ponto percentual melhor que o clássico, com p igual a 0,0496, então foi mantido como não pior. Na Busca Tabu, o tenure calibrado de 49 rendeu 1,26 ponto sobre o clássico 15. No GRASP fixo, o alfa calibrado 0,22 não venceu o 0,30 clássico, e o clássico ficou.

Visual: a fórmula da reponderação, q_i = (Z*/Z̄_i)^δ, e a Tabela 2 do relatório (clássico contra calibrado) recortada.

---

Slide 8: Resultados no benchmark

Texto:
- Gap médio: I1 36,0%, VND 8,4%, Tabu 4,0%, GRASP 2,0%
- Hierarquia: GRASP e Reativo, depois Tabu, VND, I1
- Friedman rejeita igualdade; Wilcoxon com Holm separa todos os pares
- Exceção: GRASP fixo e Reativo não diferem

Fala: Cada camada contribui: a busca local tira o gap de 36% para 8%, e as meta-heurísticas levam para perto de 2%. O teste de Friedman rejeita a igualdade dos cinco métodos. Nas comparações par a par com Wilcoxon e correção de Holm, todos os pares diferem, com uma exceção que vou detalhar no próximo slide. Uma observação honesta: o pós-teste de Nemenyi, que é mais conservador, separa o GRASP fixo da Tabu por pouco e não separa o Reativo da Tabu; por isso a hierarquia se apoia no Wilcoxon. Em tempo, o GRASP gasta cerca de 57 segundos por execução e a Tabu 7,6.

Visual: `cd_diagram_full.png` em cima e `boxplot_gap.png` ao lado.

---

Slide 9: O empate entre GRASP fixo e GRASP Reativo

Texto:
- Wilcoxon: p = 0,95 no teste, 11 vitórias contra 9
- Gap 1,96% contra 1,88%: diferença dentro do ruído
- Calibração já mostrava: GRASP insensível a alfa entre 0,2 e 0,3
- Escolha: a versão mais simples, alfa fixo em 0,30

Fala: Entre o GRASP fixo e o Reativo não há evidência de diferença: p igual a 0,95 no teste, 11 vitórias contra 9 e 8 empates. O sentido da diferença muda conforme a estatística: o Reativo tem o menor gap médio, mas o fixo tem o melhor gap por instância e o melhor posto médio. A explicação está na calibração: o GRASP é insensível ao alfa nessa faixa, e o alfa fixo de 0,30 já pertence à grade que o Reativo aprende. O mecanismo reativo só rende quando o melhor alfa varia entre instâncias, o que não acontece aqui. Com o mesmo tempo e o mesmo resultado, a decisão é ficar com a versão mais simples.

Visual: tabela pequena com duas linhas (GRASP e GRASP Reativo) e colunas gap médio, gap melhor, posto médio, tempo. Ao lado, as duas caixas do boxplot recortadas.

---

Slide 10: Gêmeo digital: onde está o "dinâmico"

Texto:
- 38 PEVs reais de Vitória/ES, enchimento simulado por Poisson
- Mecanismo 1: instância nova a cada ciclo, só lixeiras acima do limiar
- Mecanismo 2: prazo de coleta encolhe conforme a lixeira enche
- Lixeira cheia recebe só 40% do horizonte para ser atendida

Fala: Este slide justifica o título. Os 38 pontos de entrega voluntária são reais, com depósito na AMARIV; o enchimento é simulado por um processo de Poisson com dois picos por dia. A cada ciclo de cerca de três horas, o enchimento avança, as leituras chegam pela camada LoRaWAN simulada e só as lixeiras acima do limiar de 70% entram na instância daquele ciclo. Ou seja, o conjunto de clientes não é conhecido de antemão. Segundo mecanismo: o prazo de cada lixeira é H vezes um menos kappa vezes a criticidade, com kappa 0,6. Uma lixeira no limiar tem a janela inteira; uma lixeira cheia tem 40% do horizonte. Como o critério Push Forward só aceita inserções que respeitam prazos, as lixeiras críticas são atendidas mais cedo dentro da rota. É a adaptação do algoritmo de Solomon anunciada no título: o mesmo solver, alimentado por instâncias geradas pelo estado dos sensores.

Visual: figura `cycles_seed0.png` (painéis a e c) e, ao lado, um esquema do ciclo com quatro setas: enchimento, leitura, planejamento, coleta. A fórmula due = H(1 − κ·crit) em destaque.

---

Slide 11: Resultados do gêmeo digital

Texto:
- Coletas: 124 contra 228, redução de 46%
- Distância comparável (+2,4%): mais despachos, rotas mais curtas
- Transbordos: 27 contra 19 no limiar 0,7
- Limiar controla o compromisso: com 0,5, transbordos caem para 5

Fala: Comparamos o regime dinâmico com um estático que coleta todas as lixeiras a cada três ciclos, em 30 realizações pareadas de enchimento. O dinâmico faz 46% menos coletas, mas não roda menos: despacha caminhões em 15 dos 16 ciclos, com cerca de 8 lixeiras por saída, e a distância fica comparável. A economia está nos esvaziamentos evitados, não na quilometragem. Em troca, no limiar de 70%, tem mais transbordos, e o motivo está no modelo: entre o limiar e a capacidade cabem 3,6 chegadas, e no pico uma lixeira recebe quatro ou mais chegadas num ciclo com probabilidade 0,57; ela cruza o limiar e transborda antes de ser vista. Baixar o limiar para 0,5 leva os transbordos para 5 na realização analisada, ainda com 167 coletas contra 228. A capacidade do caminhão só muda a distância. A qualidade do rádio também limita o serviço: com perdas e transmissão a cada dois ciclos, os transbordos de um cenário de teste foram de 51 para 96. Na malha viária real, rotear os 38 pontos deu 6 caminhões, 83,7 km e 3,7 horas.

Visual: `sensitivity.png` com o painel do limiar em destaque e, ao lado, a Tabela 5 do relatório recortada (dinâmico contra estático).

---

Slide 12: Conclusões e próximos passos

Texto:
- GRASP e Reativo empatam e superam Tabu, VND e I1
- Coleta guiada por sensores: 46% menos coletas, serviço depende do limiar
- Limitações: enchimento simulado, grafo euclidiano, sensibilidade com uma realização
- Próximos: piloto com sensores reais, replanejamento em rota, malha viária

Fala: Duas contribuições. Na parte acadêmica, um protocolo reprodutível de comparação de meta-heurísticas, com partida comum, ablação, calibração com portão de aceitação e testes pareados, e a evidência de que o GRASP domina a Busca Tabu clássica nas instâncias de Solomon sob objetivo de distância. Na parte aplicada, a quantificação do compromisso entre coletas e transbordos, com o limiar de acionamento como a alavanca de operação. As limitações são claras: o enchimento é simulado, a comparação entre regimes roda no grafo euclidiano dos pontos, e a sensibilidade usa uma realização. Os próximos passos são um piloto com sensores reais em Vitória, a comparação sobre a malha viária em vários limiares e planos que atravessam ciclos com replanejamento de caminhões em rota. Obrigada.

Visual: `vitoria_road_routes.png` grande, com as três frases de contribuição ao lado e o agradecimento à UFES e ao PIIC no rodapé.
