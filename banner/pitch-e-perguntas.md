# Pitch e banco de perguntas da banca

XXXVI Jornada de Iniciação Científica e Tecnológica da Ufes
Quinta-feira, 12/11/2026, 9h às 12h (credenciamento 8h30)
Campus de Goiabeiras, Quadras do CEFD, sessão de Engenharias e Ciências Exatas e da Terra
Protocolo de inscrição **202526313**

Regras da sessão que mudam o modo de falar: não há projeção, você fica as 3 h ao
lado do pôster, 1 ou 2 avaliadores chegam e perguntam, e o relatório final está
na mão deles. Então o roteiro aqui não é uma apresentação: é uma abertura curta,
um pitch de 3 min e um banco de respostas.

Toda resposta abaixo cita onde o número está, para você poder abrir a página se
o avaliador insistir. "Relatório" é `banner/document(35).pdf`.

---

## Abertura de 30 segundos (para quem só passa olhando)

> "O caminhão de lixo hoje passa nos mesmos pontos, nos mesmos dias, não importa
> se a lixeira está cheia ou vazia. Eu comparei cinco algoritmos clássicos de
> roteamento para descobrir qual planeja melhor e depois coloquei o vencedor
> para rodar num simulador da coleta seletiva de Vitória, com os 38 pontos de
> entrega voluntária reais. A coleta guiada por sensor faz 46 % menos coletas,
> mas tem um preço, e o preço está nesta figura aqui."

Aponte para a tabela do Gêmeo digital. Se a pessoa continuar olhando, siga para o pitch.

---

## Pitch de 3 minutos

**(1) Problema, 25 s.** Aponte a caixa O problema.
"Coleta por rota e frequência fixas gera dois desperdícios: visita a lixeira
quase vazia e transbordo em lixeira que encheu antes da visita. Um sensor de
nível em cada lixeira, ligado por LoRaWAN, diz o enchimento real. A pergunta é
como transformar essa informação em rotas boas e viáveis."

**(2) O problema matemático, 25 s.** Aponte a caixa O VRPTW.
"Isso é um VRPTW: frota de capacidade fixa, cada cliente visitado uma vez,
respeitando janela de tempo e tempo de serviço. Eu minimizo distância total,
com a convenção do desafio DIMACS, que é truncada e por isso verificável: eu
reproduzo exatamente os custos das soluções de referência do CVRPLIB."

**(3) O que eu fiz de fato, 40 s.** Aponte Os cinco métodos e a Metodologia (Algoritmo 1).
"Implementei cinco métodos sobre um núcleo de código único em C++. Isso é o
ponto metodológico: se cada um tivesse seu próprio leitor de instância ou sua
própria matriz de distância, a comparação misturaria estratégia de busca com
detalhe de implementação. Dividi as 56 instâncias de Solomon ao meio: 28 para
calibrar com o irace e 28 para comparar. E declarei antes da calibração o
critério de aceitação: o parâmetro calibrado só entra se vencer no conjunto de
teste."

**(4) Resultado do benchmark, 40 s.** Aponte Resultados nas instâncias de Solomon (Figuras 1 e 2).
"Cada camada contribui: a I1 pura dá 36 % de gap, a busca local leva para 8 %,
e as meta-heurísticas para menos de 2 %. A maior contribuição individual é a
busca local. Estatisticamente, GRASP e GRASP reativo empatam entre si e ficam
à frente da Busca Tabu, do VND e da I1. Em 3.528 execuções, o verificador
independente não encontrou uma única solução inviável."

**(5) Gêmeo digital, 50 s.** Aponte o Gêmeo digital (mapa e Tabela 1).
"Peguei o GRASP calibrado e coloquei num simulador da coleta seletiva de
Vitória, com os 38 PEVs reais e malha viária real. Comparei dois regimes:
dinâmico, que coleta sob demanda quem passou de 70 % de enchimento, e estático,
que coleta todo mundo a cada 3 ciclos. O dinâmico faz 46 % menos coletas. Mas
não roda menos: ele despacha caminhão em 15 dos 16 ciclos, com rotas mais
curtas, e a distância acaba comparável. E, no limiar padrão, ele transborda
mais."

**(6) O fecho, 20 s.** Aponte o último parágrafo do Gêmeo digital e as Conclusões.
"Não existe regime dominante, existe um compromisso, e o limiar é a alavanca.
Baixando o limiar de 0,7 para 0,5, os transbordos caem de 27 para 5 e ainda
assim são 167 coletas contra 228 do estático. Ou seja: o serviço é recuperado
sem abrir mão da economia."

---

## Banco de perguntas

### A. Problema e modelagem

**Por que VRPTW e não o roteamento simples (CVRP)?**
Porque a coleta tem prazo. Uma lixeira perto do transbordo precisa ser atendida
antes das outras, e isso é exatamente uma janela de tempo. Sem janela, o modelo
não consegue representar urgência. (Relatório, seção 3.)

**O que é um PEV?**
Ponto de entrega voluntária: o contêiner de coleta seletiva onde o morador
deposita o reciclável. Vitória tem 38 deles, e eu uso as localizações reais do
portal de dados geográficos abertos do município. (Seção 4.)

**As lixeiras são reais ou inventadas?**
As **localizações** são reais, e a malha viária também. O **enchimento** é
simulado, porque coletar séries reais exigiria meses de monitoramento com
sensores físicos, que não existem nesta fase. Isso está declarado como
limitação. (Seção 4 e Conclusões.)

**Como você simula o enchimento?**
Processo de Poisson não homogêneo discretizado em ciclos de cerca de 3 h, 8
ciclos por dia, com intensidade entre 0,8 e 4,0 em dois picos diários e
propensão própria de cada lixeira, sorteada uniformemente entre 0,5 e 1,5. Cada
chegada acrescenta 1/12 do volume. (Seção 4.)

**O que é "demanda" no seu modelo? É peso?**
Não é peso. É `demanda = round(9·f) + 1`, entre 1 e 10, derivada do enchimento
`f`. É ao mesmo tempo medida de volume a recolher e de prioridade. A capacidade
do veículo é 30 dessas unidades. (Seção 4.)

**O que exatamente conta como transbordo?**
A lixeira atinge enchimento 1 antes de ser coletada. É contado **por episódio**:
cada enchimento completo conta um transbordo, e a lixeira só volta a poder
transbordar depois de ser coletada. Não é "lixeira-dia" nem "lixeira cheia".
(Seção 4.)

**Onde está o "dinâmico" do título?**
Em dois mecanismos. Primeiro, a instância de cada ciclo é formada só pelas
lixeiras acima do limiar, então o conjunto de clientes muda a cada ciclo, de 0 a
16, contra as 38 fixas do estático. Segundo, o prazo de cada lixeira encolhe com
a urgência: `due = H·(1 − κ·crit)`, com κ = 0,6, de modo que a lixeira cheia
recebe 40 % do horizonte. O critério Push Forward de Solomon só aceita inserção
que respeite prazo, então as críticas sobem na ordem da rota. (Seção 4, eq. 7.)

### B. Métodos

**Por que esses cinco métodos?**
Porque formam uma cadeia que isola o efeito de cada camada: construção pura
(I1), construção mais busca local (VND), e três meta-heurísticas que usam o
mesmo VND por dentro mas o exploram de formas diferentes, multipartida
aleatorizada (GRASP), multipartida com aprendizado (reativo) e trajetória única
com memória (Tabu). (Seção 3.)

**O que o GRASP reativo aprende?**
O grau de aleatorização α. Ele mantém uma grade de 10 valores de 0,05 a 0,50,
começa com todos igualmente prováveis, testa cada um uma vez no aquecimento e,
a cada bloco de iterações, repondera: α que produz soluções mais perto do
incumbente ganha peso, com expoente δ controlando a agressividade. (Seção 4,
eq. 5.)

**Por que a grade do reativo para em 0,5 e não vai até 1?**
Para coincidir com o intervalo em que o α do GRASP fixo é calibrado, (0; 0,5), e
manter as duas variantes comparáveis. Testei valores acima: o gap médio cai de
3,42 % em α = 0,3 para 2,80 % em α = 0,9, mas puxado por poucas instâncias,
α = 0,9 ganha em apenas 10 das 28 instâncias na média das sementes, e cada
iteração custa até 1,6 vez mais. Estender a grade está registrado como
continuidade. (Seção 4.)

**Por que a Busca Tabu ficou na forma mais simples?**
Decisão declarada: memória de curto prazo apenas, sem memória de longo prazo nem
religação de caminhos, para que a comparação fosse contra a formulação clássica
de Glover. Está listado como limitação e como continuidade. (Seções 4 e 6.)
Se o avaliador disser "então a Tabu foi prejudicada", a resposta honesta é:
sim, uma Tabu mais rica poderia mudar o resultado, e eu digo isso no relatório.

**Melhor melhora ou primeira melhora?**
Melhor melhora. A vizinhança ativa é varrida por completo e aplica-se o
movimento de maior redução. Isso torna o VND determinístico dado o ponto de
partida, o que é necessário para que a I1 e o VND rodem uma vez só. (Seção 4,
Algoritmo 2.)

**Como você garante que nenhuma solução é inviável?**
Três mecanismos redundantes. Cada operador simula a rota afetada e descarta
movimento inviável antes de comparar custo; a inserção é testada em O(1) pelo
Push Forward; e um verificador independente recalcula toda solução final do
zero, só a partir da sequência de clientes. A independência é o ponto: a busca
confia nos próprios caches, e um erro neles passaria despercebido; o verificador
não usa nenhuma estrutura da busca, então o erro apareceria como divergência.
Qualquer violação é erro fatal e derruba o estudo. (Seção 4.)

### C. Protocolo e estatística

**Por que dividir 28 e 28?**
Para que a comparação final não rode nas mesmas instâncias que a calibração viu.
A divisão é estratificada por família e tipo. O superajuste medido é pequeno: a
diferença de gap entre treino e teste fica entre 0,10 e 0,24 pp nos três métodos
calibrados. (Seções 4 e 5.)

**Por que o critério de parada não foi calibrado?**
Porque mais iterações sem melhora nunca pioram o resultado. Se eu calibrasse K
pelo gap, o irace o levaria sempre ao teto do intervalo, confundindo orçamento
com qualidade. Declarar o orçamento é a prática consolidada na literatura de
GRASP. Usei K = 800 para todos. E testei de 50 a 3200, variação de 64 vezes:
nem a ordem dos métodos nem o resultado dos testes par a par mudam. (Seção 4.)

**Wilcoxon e Nemenyi discordam. Qual vale?**
Os dois, cada um no seu papel, e eu digo onde discordam. O Nemenyi é a leitura
global conservadora; o Wilcoxon pareado com Holm tem mais poder para pares e é o
que sustenta as afirmações par a par. Nas 56 instâncias o Nemenyi separa GRASP
de Tabu (diferença de postos 0,830 contra CD = 0,815) mas não separa o reativo
da Tabu (0,804). No conjunto de teste, com só 28 instâncias, o CD sobe para
1,153 e o Nemenyi não separa nenhuma das duas variantes da Tabu. O Wilcoxon, no
mesmo conjunto, dá p de Holm = 6,9×10⁻⁴. (Seção 5 e `results/stats_paired.txt`.)

**Por que 30 sementes?**
Porque GRASP e reativo são estocásticos e uma execução só não mede o método, mede
um sorteio. I1, VND e Tabu são determinísticos dado o ponto de partida e rodam
uma vez. A semente vem do número da execução e do nome da instância, nunca do
relógio, então qualquer computador reproduz o mesmo resultado. (Seção 4.)

**O que é a integral primal e por que ela não é a comparação principal?**
É o gap médio da melhor solução corrente ao longo de um orçamento de tempo fixo:
premia quem chega cedo a boas soluções, não só quem termina bem. Com T = 20 s
ela ordena GRASP 3,08, reativo 3,10, Tabu 4,25 e VND 8,61, a mesma leitura da
comparação primária. Não serve de base porque depende do tempo de relógio, logo
do computador, e não é reproduzível em outra máquina. Entra como leitura
complementar. (Seção 5.)

**Em que máquina rodou?**
Uma só, para que os tempos sejam comparáveis entre si: Intel Core Ultra 9 285K,
Ubuntu 24.04, g++ 13.3. Há ainda 34 testes unitários cobrindo o núcleo e a
fidelidade dos algoritmos à literatura. (Seção 4.)

### D. As perguntas incômodas

**Na Figura 2 a barra une o reativo à Tabu, mas o texto diz que o Wilcoxon separa
os dois. Qual vale?**
A barra é do Nemenyi nas 56 instâncias, teste global e conservador; o texto é do
Wilcoxon pareado com Holm nas 28 de teste, que tem mais poder para comparar pares
(p de Holm = 6,9×10⁻⁴). As afirmações par a par do banner se apoiam no Wilcoxon,
e a legenda da figura diz que a barra é do Nemenyi. (Seção 5.)

**Qual a unidade da distância na Tabela 1?**
Unidade do grafo euclidiano normalizado dos 38 pontos, adimensional. Por isso não
se compara com os 83,8 km do mapa. (Seção 4.)


**Se o dinâmico é melhor, por que ele transborda mais?**
Porque o gatilho é tarde. Esperar a lixeira chegar a 70 % para agendá-la deixa
pouca margem. Entre o limiar 0,7 e a capacidade cabem 3,6 chegadas, já que cada
chegada vale 1/12 do volume; num ciclo de pico, com intensidade 4,0, a
probabilidade de 4 ou mais chegadas é cerca de 0,57. Ou seja, a lixeira cruza o
limiar e enche dentro do mesmo ciclo, antes de o planejador poder agir.
*(Esta conta é derivação minha a partir dos parâmetros da Seção 4; o relatório
registra o fato, não a conta. Se perguntarem a fonte, diga isso.)*
A saída está medida: com τ = 0,5, a mesma realização cai para 5 transbordos e
ainda faz 167 coletas contra 228 do estático. (Tabela 6.)

**Se faz 46 % menos coletas, por que a distância não caiu?**
Porque a economia está nos esvaziamentos evitados, não na quilometragem. O
dinâmico despacha caminhões em 15 dos 16 ciclos e o estático em 6; o dinâmico
faz muitas rotas curtas e o estático poucas rotas longas. O total acaba 2,4 %
maior (p = 0,0016), o que eu chamo de comparável, não de melhor. (Tabela 5.)

**Você usou 8,3 veículos em média. Solomon minimiza frota primeiro. Isso não
está errado?**
Não, é consequência declarada da escolha de objetivo. Eu minimizo distância, sob
a convenção DIMACS, e reporto o número de veículos como medida secundária. As
soluções de referência de mínima distância do CVRPLIB nunca usam menos veículos
que as de mínima frota: usam mais em 37 das 56 instâncias e o mesmo número em
19, e têm distância menor ou igual em todas as 56. Minha média fica entre as
duas referências, que é a assinatura esperada. Avaliar sob o critério
lexicográfico veículos antes de distância está listado como continuidade.
(Seção 5 e Conclusões.)

**Você calibrou com o irace e depois descartou o resultado do GRASP. Por quê?**
Porque o portão de aceitação foi declarado **antes** da calibração: o calibrado
só entra se vencer nas 28 instâncias de teste. O α calibrado foi 0,22 e não
superou o clássico 0,30 (p = 0,63), então o estudo final usa 0,30. Esse
resultado negativo é informativo, e não um fracasso: ele diz que o GRASP é
insensível a α na faixa de 0,2 a 0,3 nestas instâncias. Na Tabu o calibrado
venceu (tenure 49 contra 15, +1,26 pp, p = 0,043) e foi adotado. (Tabela 2.)

**Por que o tenure calibrado ficou tão alto, 49?**
Porque o kit tem seis vizinhanças e a vizinhança conjunta é grande. Com tantas
alternativas por iteração, proibições curtas não impedem a busca de voltar para
a mesma região, então são necessárias proibições mais longas para forçar
exploração. (Seção 5.)

**O coeficiente de urgência κ não muda nada. Isso não é um bug?**
Não. No cenário do gêmeo digital o horizonte é folgado, então as janelas
dinâmicas quase nunca tornam uma inserção inviável: elas atuam só na priorização
interna ao plano, mudando a ordem dentro da rota sem mudar quem é atendido nem
quanto se roda. Por isso os indicadores agregados (distância, coletas,
transbordos) não se movem. Em um cenário apertado, κ voltaria a importar.
(Tabela 6.)

**A capacidade muda a distância mas não os transbordos. Por quê?**
Porque a capacidade decide quantos veículos e quanto se roda, não **quais**
lixeiras entram no plano daquele ciclo. Quem entra é decidido pelo limiar. Então
a distância cai de 6.526 para 3.049 ao passar de 15 para 40 unidades, e os
transbordos ficam em 27. (Tabela 6.)

**Os 83,8 km do mapa batem com a tabela dos regimes?**
Não batem porque são coisas diferentes; a legenda da Tabela 1 avisa que a distância está em unidades do grafo, não em km. O mapa é uma
demonstração viária: uma única roteirização dos 38 PEVs, com distância em metros
e tempo de direção em segundos vindos do OSRM, horizonte de 6 h e serviço de
120 s. A comparação entre regimes corre sobre o grafo euclidiano normalizado dos
mesmos 38 pontos, em escala adimensional, ao longo de 16 ciclos e 30
realizações. O fator de circuito médio entre os dois mapas é 1,53, chegando a
6,9 em pares separados por água. (Seção 4 e Figura 3.)

**Por que não recalibrou os parâmetros para o cenário viário?**
Porque exigiria treinar sobre o próprio simulador. Os parâmetros herdados são
defensáveis porque a calibração ajusta só a estratégia de busca (largura da RCL,
memória de proibição, cadência do aprendizado), nada que dependa da geometria da
instância. Mesmo assim, a ausência de recalibração está registrada como
limitação. (Seção 4.)

**A análise de sensibilidade usa uma realização só. Isso não é frágil?**
É, e está declarado. A **comparação entre regimes**, que é a afirmação central,
usa 30 realizações pareadas com teste de Wilcoxon. A sensibilidade, que varia um
parâmetro por vez, usa uma realização para isolar o efeito do parâmetro do ruído
entre realizações. Ampliar isso é continuidade direta. (Seções 4 e 6.)

### E. Balanço dos objetivos do subprojeto

O avaliador pode cobrar o que foi prometido no projeto submetido ao edital. São
sete objetivos específicos, e o relatório faz o balanço de cada um (Conclusões).
Decore esta tabela.

| | Objetivo | Situação | Por quê |
|---|---|---|---|
| a | Modelar o enchimento com distribuições estatísticas | **cumprido** | Poisson não homogêneo, dois picos, propensão por lixeira |
| b | Adaptar Solomon com Push Forward para priorizar lixeiras críticas | **cumprido** | I1 é a construção dos cinco métodos, janelas dinâmicas antecipam as críticas, nenhuma execução inviável |
| c | Simular LoRaWAN avaliando desempenho em baixo consumo | **parcial** | perda de pacote, ciclo de trabalho e idade da leitura simulados e medidos; **consumo de energia não foi avaliado** |
| d | Interface geoespacial em tempo real | **parcial** | painel interativo e animação por ciclo existem como protótipos; tempo real depende de sensores físicos |
| e | Implementar um Digital Twin | **cumprido** | 30 realizações comparadas, mais limiar, capacidade, urgência e canal |
| f | Validar com dados reais comparando rotas estáticas e dinâmicas | **parcial** | localizações e malha são reais, **o enchimento é simulado** |
| g | Quantificar benefícios econômicos, ambientais e sociais | **não cumprido de forma direta** | os indicadores operacionais medidos são a base, mas não foram convertidos em custo nem em emissões |

**Então o objetivo geral foi atingido?**
Como prova de conceito, sim: os componentes existem e operam integrados em
simulação. Diga isso exatamente assim, "prova de conceito", que é o termo do
relatório.

**A comparação de heurísticas não estava no projeto original. Por que você a fez?**
Porque ela é a fundação metodológica de todo o resto: ela é o que garante que o
otimizador transferido ao gêmeo digital é o melhor entre os avaliados. Isso está
declarado nas Conclusões, não escondido.

### F. Gerais

**O que é seu e o que é do grupo?**
O subprojeto está vinculado ao projeto de pesquisa "Pesquisa Operacional e
Inovação em Logística Regional", no qual constitui a frente de otimização de
rotas e simulação orientada a sensores. A implementação, a calibração, a
experimentação e a análise foram feitas por mim.

**Usou inteligência artificial?**
Sim, e está declarado no relatório, em seção própria: o modelo Claude, pela
ferramenta Claude Code, como apoio na depuração e estruturação do código C++20,
nos testes unitários, no pipeline em Python, nos scripts de estatística e na
revisão ortográfica. Todo código sugerido foi inspecionado e validado, e eu
assumo a responsabilidade pela coerência metodológica, pela integridade dos
dados e pela redação final.

**É reproduzível?**
Sim. Todo o experimento roda por um único comando, as sementes não dependem da
máquina nem do relógio, e o pipeline agrega resultados e gera tabelas e figuras
sozinho.

**O que você faria diferente?**
Começaria o gêmeo digital com séries reais de enchimento, ou ao menos com uma
campanha curta de sensores, porque é a única limitação que atinge a conclusão
aplicada. E avaliaria desde o início os dois critérios de objetivo, distância e
frota, em vez de só distância.

**Qual é o próximo passo?**
Piloto com sensores físicos em Vitória, avaliação sob o critério lexicográfico,
variantes mais ricas da Tabu, planos que atravessam ciclos com replanejamento de
veículos já em rota, e a conversão dos indicadores operacionais em custo e
emissões.

---

## Mapa do banner (para apontar sem procurar)

| Coluna 1 | Colunas 2 e 3 |
|---|---|
| Resumo (faixa inteira no topo) | |
| O problema | Metodologia + Algoritmo 1 (GRASP com VND) |
| O VRPTW (gap definido aqui) | Resultados: Figura 1 (gap) e Figura 2 (postos) |
| Os cinco métodos | Gêmeo digital: Figura 3 (mapa), Tabela 1, limiar |
| Conclusões | |
| Agradecimentos (rodapé, colunas 1 e 2) | Referências (rodapé, coluna 3) |

O que saiu do banner e agora é só falado (está no banco acima): ablação das
vizinhanças, portão do irace em detalhe, Nemenyi contra Wilcoxon, ciclo do gêmeo
digital (antigo Algoritmo 2), capacidade e κ na sensibilidade, aviso "dois mapas".

## Três frases para não errar

1. "Não há dominância de um regime sobre o outro, e sim um compromisso entre
   esforço de coleta e nível de serviço, governado pelo limiar de acionamento."
2. "A hierarquia par a par apoia-se no Wilcoxon pareado; o Nemenyi, mais
   conservador, não separa o reativo da Tabu, e eu digo isso."
3. "As localizações e a malha viária são reais; o enchimento é simulado."
