# Parágrafos revisados (aplicados ao main.tex em 2026-09-10)

Texto final, já compilado em 15 páginas. Cada bloco abaixo é a versão que está no `main.tex`;
serve como registro e para colar em outro editor. Regras aplicadas: sem travessões, vocabulário
direto, pseudocódigos em estilo livro-texto.

## O que foi cortado para caber

- Introdução: o parágrafo das três camadas virou uma frase; os objetivos já as listam.
- Objetivos: parágrafo final "Esses objetivos respondem a duas necessidades" (dito na Metodologia e nos Resultados).
- Metodologia: frase do hash da semente; descrição do fluxo de cada execução (o pipeline já a resume); glosa de gap e frase O(n^3) nas vizinhanças; frase duplicada de alpha=0; papel do tenure (fica nos Resultados); explicação dupla de c11/c12 antes e depois da equação; citações repetidas de Feo e Resende e de Prais e Ribeiro; frase "tempo e iterações são reportados" (está na legenda da Tabela 3); "pois a coleta de séries reais exigiria meses"; justificativa longa da herança de parâmetros.
- Pseudocódigos: I1 de 17 para 10 linhas, VND de 10 para 7, GRASP de 12 para 9 (com o reativo dentro), Tabu de 17 para 11; leituras "Na linha" reescritas e mais curtas; algoritmos e legendas de figura em espaço simples, como as tabelas do modelo.
- Equações: D(S)/K(S), gap, RCL e CD passaram para o texto corrido (continuam definidas; só perderam o número).
- Resultados: análise da integral primal reduzida a uma frase; explicação do Cross-exchange na ablação encurtada; leitura da Figura 5 encurtada; "tipicamente 10--20 lixeiras" trocado pelo intervalo medido (1 a 16).
- Conclusões: recapitulação do método e contribuições fundidas num parágrafo; dois itens de continuidade fundidos.
- Referências: saem Or (1976), Potvin e Rousseau (1995), Taillard et al. (1997) (cobertos por Bräysy e Gendreau, 2005), Resende e Ribeiro (2003) e Pardini et al. (2020); entram Bräysy e Gendreau (2005) e Pillac et al. (2013).
- Legendas das Tabelas 2, 3 e 5 encurtadas (a 5 ganhou mapa e capacidade); negrito da Tabela 3 removido no gerador.
- Figuras 2 e 3 lado a lado; Figura 4 (rotas) ao lado do parágrafo do gêmeo digital, a 0,40 da largura.

Observação: os "---" que restam nos arquivos de tabela são marcadores de célula vazia gerados pelos scripts (não é prosa).

## Resumo (só a oração final mudou)

```latex
\section*{Resumo}
%---------------------------------------------------------------------
A coleta de resíduos sólidos urbanos baseada em rotas e frequências fixas responde mal ao enchimento real dos recipientes, gerando deslocamentos desnecessários e transbordos. Este subprojeto comparou, sob condições controladas e reprodutíveis, cinco heurísticas clássicas para o Problema de Roteamento de Veículos com Janelas de Tempo (VRPTW): a inserção I1 de Solomon, a Descida em Vizinhança Variável (VND), o GRASP nas formas fixa e reativa e a Busca Tabu. Todos os métodos compartilham o mesmo núcleo de código, de modo que as diferenças observadas decorram exclusivamente da estratégia de busca. Foram avaliadas as 56 instâncias de Solomon com 100 clientes, com calibração de parâmetros pelo pacote irace sob divisão treino/teste, parada por iterações sem melhora e comparação estatística por Friedman, Nemenyi e Wilcoxon. As variantes de GRASP obtiveram os menores desvios de distância, abaixo de 2\% do melhor conhecido, seguidas da Busca Tabu, do VND e da I1; nenhuma das 3.528 execuções produziu solução inviável. Por fim, um gêmeo digital aplicou os algoritmos calibrados à coleta seletiva de Vitória/ES, com malha viária real e comunicação LoRaWAN simulada: a coleta dinâmica guiada por sensores reduziu as coletas em 46\% a distância comparável, com o nível de serviço governado pelo limiar de acionamento.
```

## Seção 1, Introdução, parágrafo 3 (condensado)

```latex
A contribuição é metodológica e experimental: um \textit{benchmark} estático sobre as instâncias de Solomon calibra e compara os cinco métodos, e um gêmeo digital os transfere, com os mesmos operadores e parâmetros, a um cenário de coleta com dados reais de Vitória/ES.
```

## Seção 3, Convenção de distância e objetivo (gap definido aqui, em linha)

```latex
\textbf{Convenção de distância e objetivo.} Adota-se a convenção do 12\textsuperscript{o} Desafio de Implementação DIMACS para o VRPTW (DIMACS, 2022): a distância de cada arco é a euclidiana truncada a uma casa decimal, $d_{ij}=\lfloor 10\,e_{ij}\rfloor/10$, e o tempo de viagem é igual à distância. O objetivo otimizado é $\min D(S)$ sobre as soluções viáveis, com $K(S)$ reportado como medida secundária, diferentemente da hierarquia lexicográfica clássica de Solomon (1987), que minimiza primeiro o número de veículos. A convenção foi escolhida por ser o padrão internacional moderno e por ser verificável: ela reproduz exatamente os custos das soluções de referência de mínima distância do repositório CVRPLIB (2026), adotadas neste trabalho como base de comparação; o repositório SINTEF (2026) publica as referências da hierarquia de mínima frota, incomparáveis com as primeiras sem reconversão. O desempenho de uma solução é medido pelo \emph{gap} percentual de distância a essa referência, $\mathrm{gap}=100\,(d-d^{\mathrm{bk}})/d^{\mathrm{bk}}$, em que $d$ é a distância obtida e $d^{\mathrm{bk}}$ a da solução de referência, recomputada sob a mesma convenção truncada; o gap normaliza as escalas entre instâncias.
```

## Seção 3, Coleta inteligente, roteamento dinâmico e gêmeo digital

```latex
\textbf{Coleta inteligente, roteamento dinâmico e gêmeo digital.} Sensores de nível em lixeiras, conectados por redes de longo alcance e baixo consumo como o LoRaWAN (Adelantado et al., 2017; Ramson et al., 2022), permitem acionar a coleta pelo enchimento real. Isso muda a natureza do problema de roteamento. No VRPTW estático, o conjunto de clientes, as demandas e as janelas de tempo são conhecidos antes do planejamento; na coleta guiada por sensores, os três são \emph{estado} que muda ao longo do dia: quais lixeiras precisam de coleta, quanto há para recolher e com que urgência só se sabe na leitura mais recente. O problema torna-se dinâmico no sentido de re-otimização periódica (Pillac et al., 2013): a cada ciclo de monitoramento resolve-se uma nova instância VRPTW, formada apenas pelas lixeiras que cruzaram o limiar de acionamento, com janelas de tempo que encolhem com a criticidade de cada uma; o re-roteamento de veículos já em rota, a outra face do roteamento dinâmico, fica fora do escopo. Um \emph{gêmeo digital} é uma representação virtual de um sistema físico, mantida atualizada por leituras de sensores, na qual decisões de operação podem ser ensaiadas e medidas antes de ir às ruas (Barth et al., 2023).
```

## Seção 4, Construção (I1): notação, Algoritmo 1 e leitura

```latex
\textbf{Construção (heurística I1 de Solomon).} A construção segue a heurística sequencial I1 de Solomon (1987) na variante baseada em distância. Cada rota nasce de uma \emph{semente} (o cliente não roteado mais distante do depósito) e cresce por inserções guiadas por dois critérios, definidos na equação~\eqref{eq:i1}:
\begin{equation}
\begin{aligned}
c_{11}(i,u,j) &= d_{iu}+d_{uj}-\mu\,d_{ij}, &\qquad c_{12}(i,u,j) &= b_{j_u}-b_{j},\\
c_{1}(i,u,j) &= \alpha_1\,c_{11}(i,u,j)+\alpha_2\,c_{12}(i,u,j), &\qquad c_{2}(u) &= \lambda\,d_{0u}-c_1^{\min}(u),
\end{aligned}
\label{eq:i1}
\end{equation}
em que $c_{11}$ é o acréscimo de distância de inserir $u$ entre $(i,j)$, $c_{12}$ é o deslocamento temporal que $u$ provoca no sucessor $j$ ($b_j$ e $b_{j_u}$ são os inícios de serviço antes e depois da inserção), $c_1^{\min}(u)$ é o custo da melhor posição \emph{viável} de $u$ na rota corrente e $c_2$ mede a economia de aproveitá-lo agora em vez de servi-lo depois em viagem dedicada. Usa-se a configuração canônica $\mu=1$, $\lambda=2$, $\alpha_1=1$ e $\alpha_2=0$, fixa para todos os métodos: com $\alpha_2=0$, o critério reduz-se ao acréscimo de distância, coerente com o objetivo adotado. Nos algoritmos, $D(S)$ é a distância total definida na Seção~3; $S\oplus m$ é a solução obtida aplicando o movimento $m$ a $S$; $\mathrm{attr}(m)$ é o conjunto dos clientes-atributo de $m$ (o primeiro cliente de cada segmento movido); \textsc{nulo} denota ausência de movimento; $\mathcal{F}(r,U)=\{u\in U:\ u\ \text{admite inserção viável em}\ r\}$; e \texttt{insere}$(u,r)$ coloca $u$ na posição de $r$ de custo $c_1^{\min}(u)$. O Algoritmo~\ref{alg:i1} formaliza o procedimento.

\begin{algorithm}[H]\singlespacing
\caption{\textsc{I1-Solomon}: construção por inserção sequencial}\label{alg:i1}
\begin{algorithmic}[1]
\REQUIRE{clientes $C$; parâmetros $\mu$, $\lambda$, $\alpha_1$, $\alpha_2$}
\ENSURE{solução viável $S$ cobrindo $C$}
\STATE{$S \gets \emptyset$;\quad $U \gets C$}\label{i1:init}
\WHILE{$U \neq \emptyset$}
  \STATE{$u^{\star} \gets \arg\max_{u\in U} d_{0u}$;\quad $r \gets \langle 0,u^{\star},0\rangle$;\quad $U \gets U\setminus\{u^{\star}\}$}\label{i1:seed}
  \WHILE{$\mathcal{F}(r,U) \neq \emptyset$}\label{i1:loop}
    \STATE{$u^{\star} \gets \arg\max_{u\in\mathcal{F}(r,U)} c_2(u)$;\quad \texttt{insere}$(u^{\star},\,r)$;\quad $U \gets U\setminus\{u^{\star}\}$}\label{i1:insert}
  \ENDWHILE
  \STATE{$S \gets S\cup\{r\}$}\label{i1:close}
\ENDWHILE
\RETURN{$S$}
\end{algorithmic}
\end{algorithm}

Na linha~\ref{i1:init}, a solução começa vazia e $U$ recebe todos os clientes. Na linha~\ref{i1:seed}, cada rota nasce da semente mais distante do depósito, escolha que ancora a rota em uma região periférica e tende a reduzir o número de veículos. O laço da linha~\ref{i1:loop} faz a rota crescer enquanto houver cliente com inserção viável: a linha~\ref{i1:insert} escolhe o de maior economia $c_2$ e o insere na sua melhor posição, cada posição testada em $O(1)$ pela folga \textit{Push Forward}; a rota fecha na linha~\ref{i1:close} e outra é aberta. A cobertura é garantida pelo laço externo, que só termina com $U=\emptyset$ e roteia ao menos a semente por rota; a viabilidade, pela restrição a $\mathcal{F}(r,U)$. Restam rotas densas, mas sem reotimização entre si, a lacuna que a busca local explora.
```

## Seção 4, Conjunto de vizinhanças

```latex
\textbf{Conjunto de vizinhanças.} Os métodos de melhoria compartilham um \emph{kit} de seis operadores clássicos do VRPTW (Br\"aysy; Gendreau, 2005), listado na ordem de exploração:
\begin{itemize}
\item \textbf{2-opt} (intrarrota): inverte um subtrecho de uma rota;
\item \textbf{Swap} (intrarrota e entre rotas): troca dois clientes de posição;
\item \textbf{2-opt*} (entre rotas): troca as caudas de duas rotas;
\item \textbf{Relocate} (intrarrota e entre rotas): remove um cliente e o reinsere em outra posição;
\item \textbf{Or-opt} (intrarrota e entre rotas): move uma cadeia de 2--3 clientes, eventualmente invertida;
\item \textbf{Cross-exchange} (entre rotas): troca subtrechos de até 3 clientes entre duas rotas.
\end{itemize}
Os seis operadores cobrem os oito movimentos avaliados no relatório parcial: Relocate, Swap e Or-opt implementam as variantes intrarrota e entre rotas em varredura única, e o ``2-opt entre rotas'' do parcial corresponde ao 2-opt*. Conforme ali previsto, o conjunto foi submetido a seleção por ablação nas instâncias de treino, e a ablação da Seção~5 manteve o kit completo. A ordem de exploração é a de custo \emph{medido} de uma varredura completa, conferida por teste automatizado (as seis têm a mesma ordem assintótica; diferem nas constantes).
```

## Seção 4, VND: parágrafo, Algoritmo 2 e leitura

```latex
\textbf{Descida em Vizinhança Variável (VND).} O VND (Hansen; Mladenovi\'c, 2001) percorre as vizinhanças em ordem fixa, da varredura mais barata à mais cara, com estratégia de \emph{melhor melhora}: a cada passo aplica o movimento viável de maior redução de $D(S)$ e reinicia da primeira vizinhança; quando nenhuma vizinhança melhora, para em um ótimo local em relação a todas elas (Algoritmo~\ref{alg:vnd}).

\begin{algorithm}[H]\singlespacing
\caption{\textsc{VND}: Descida em Vizinhança Variável}\label{alg:vnd}
\begin{algorithmic}[1]
\REQUIRE{solução viável $S$; vizinhanças ordenadas $N_1,\dots,N_p$}
\ENSURE{ótimo local $S$ em relação a $N_1,\dots,N_p$}
\STATE{$\ell \gets 1$}\label{vnd:init}
\WHILE{$\ell \le p$}
  \STATE{$m \gets \texttt{melhor\_movimento}(N_{\ell},\,S)$}\label{vnd:find}
  \STATE{\textbf{se} $m \neq \textsc{nulo}$ \textbf{então} $S \gets S\oplus m$;\ $\ell \gets 1$ \textbf{senão} $\ell \gets \ell+1$}\label{vnd:step}
\ENDWHILE
\RETURN{$S$}
\end{algorithmic}
\end{algorithm}

Na linha~\ref{vnd:find}, a vizinhança ativa é varrida por completo e \texttt{melhor\_movimento} devolve o movimento viável de maior redução de $D(S)$, ou \textsc{nulo}; a escolha do melhor movimento, e não do primeiro, torna o resultado determinístico dado o ponto de partida. Na linha~\ref{vnd:step}, havendo ganho, o movimento é aplicado e a busca \emph{reinicia} da primeira vizinhança (é o que caracteriza o VND e faz os operadores baratos absorverem a maior parte dos movimentos); sem ganho, avança-se para a seguinte, e o laço encerra quando nenhuma das $p$ melhora $S$. O método para no primeiro ótimo local, limitação da qual partem as meta-heurísticas.
```

## Seção 4, GRASP e reativo: parágrafo, Algoritmo 3, leitura e variante reativa

```latex
\textbf{GRASP.} O GRASP (Feo; Resende, 1995) repete o ciclo construção aleatorizada $\rightarrow$ busca local e guarda a melhor solução encontrada. A construção reusa a I1, substituindo a escolha gulosa por um sorteio uniforme dentro da Lista Restrita de Candidatos, $\mathrm{RCL}=\{u : c_2(u)\ge c^{\max}-\alpha\,(c^{\max}-c^{\min})\}$, com $\alpha\in[0,1]$ e $c^{\max}$, $c^{\min}$ o maior e o menor valor de $c_2$ entre os candidatos, de modo que $\alpha=0$ recupera a construção gulosa (propriedade conferida por teste automatizado nas 56 instâncias) e $\alpha=1$, a totalmente aleatória. A busca local é o próprio VND, e $K$ é o número máximo de iterações consecutivas sem melhora (Algoritmo~\ref{alg:grasp}).

\begin{algorithm}[H]\singlespacing
\caption{\textsc{GRASP} e variante reativa}\label{alg:grasp}
\begin{algorithmic}[1]
\REQUIRE{instância; $\alpha$ fixo, ou grade $A=\{\alpha_1,\dots,\alpha_g\}$ e bloco $\beta$ (reativo); orçamento $K$}
\ENSURE{melhor solução $S^{\star}$}
\STATE{$S^{\star} \gets \textsc{I1-Solomon}$;\quad $k \gets 0$;\quad $i \gets 0$;\quad $p \gets (1/g,\dots,1/g)$}\label{g:init}
\WHILE{$k < K$}
  \STATE{\textbf{se} reativo \textbf{então} $\alpha \gets \alpha_{i+1}$ \textbf{se} $i<g$ \textbf{senão} $\alpha \gets \texttt{sorteia}(A,\,p)$}\label{g:alpha}
  \STATE{$S \gets \textsc{VND}(\textsc{Constru\c{c}\~ao-Aleatorizada}(\alpha))$;\quad acumula $D(S)$ em $\bar{Z}_{\alpha}$}\label{g:build}
  \STATE{\textbf{se} $D(S) < D(S^{\star})$ \textbf{então} $S^{\star} \gets S$;\ $k \gets 0$ \textbf{senão} $k \gets k+1$}\label{g:accept}
  \STATE{$i \gets i+1$;\quad \textbf{se} reativo \textbf{e} $\beta \mid i$ \textbf{então} atualiza $p$ pela equação~\eqref{eq:reativo}}\label{g:update}
\ENDWHILE
\RETURN{$S^{\star}$}
\end{algorithmic}
\end{algorithm}

Na linha~\ref{g:init}, o incumbente é a solução da I1 pura (a mesma partida entregue ao VND e à Busca Tabu), o que garante que o GRASP nunca termine pior que a I1. Cada iteração constrói uma solução nova com aleatorização controlada por $\alpha$ e a conduz a um ótimo local (linha~\ref{g:build}); a linha~\ref{g:accept} retém o melhor já visto e controla a estagnação. O acréscimo sobre o VND é a diversificação: reconstruindo as rotas do zero a cada iteração, o método rompe a dependência da semente única da I1, e o resultado é o melhor entre centenas de ótimos locais independentes. As linhas~\ref{g:alpha} e~\ref{g:update} só atuam na variante reativa.

\vspace{\baselineskip}
\textbf{GRASP reativo.} A variante reativa (Prais; Ribeiro, 2000) difere do GRASP apenas na escolha de $\alpha$: em vez de um valor fixo, mantém a grade $A=\{0{,}05, 0{,}10, \dots, 0{,}50\}$ ($g=10$) com probabilidades de seleção $p$, inicialmente uniformes. Na linha~\ref{g:alpha}, cada $\alpha_i$ é experimentado uma vez nas $g$ primeiras iterações (aquecimento) e depois sorteado segundo $p$; na linha~\ref{g:update}, a cada $\beta$ iterações, $p$ é reponderado pela equação~\eqref{eq:reativo},
\begin{equation}
q_i=\left(\frac{Z^{\star}}{\bar{Z}_i}\right)^{\!\delta},\qquad p_i=\frac{q_i}{\sum_{j} q_j},
\label{eq:reativo}
\end{equation}
em que $Z^{\star}=D(S^{\star})$, $\bar{Z}_i$ é o custo médio das soluções obtidas com $\alpha_i$ e $\delta$ regula a agressividade do aprendizado. O bloco é derivado do orçamento, $\beta=\mathit{block\_frac}\cdot K$, para que o número de reponderações independa de $K$; como $\beta\ge 16>g$ em toda a faixa calibrada, a primeira reponderação só ocorre com todos os $\alpha_i$ já experimentados. O efeito é ajustar o equilíbrio guloso-aleatório ao perfil de cada instância, desde que o $\alpha$ mais produtivo varie entre instâncias, condição que a Seção~5 examina.
```

## Seção 4, Busca Tabu: parágrafo, Algoritmo 4 e leitura

```latex
\textbf{Busca Tabu.} Adota-se a forma clássica (Glover, 1989): a cada iteração, move-se para o melhor vizinho \emph{admissível} do kit de vizinhanças, mesmo que piore a solução corrente (é assim que a busca escapa de ótimos locais), e o incumbente $S^{\star}$ retém o menor custo visitado. A memória de curto prazo é a fila $L$ dos atributos dos últimos $t$ movimentos ($t$ = \textit{tenure}): um movimento $m$ é \emph{admissível} se é viável e $\mathrm{attr}(m)\cap L=\emptyset$, ou se $D(S\oplus m)<D(S^{\star})$ (aspiração por objetivo); \texttt{melhor\_admiss\'ivel} devolve o admissível de menor $D(S\oplus m)$, ou \textsc{nulo}. Se nenhum movimento é admissível, adota-se a aspiração por omissão (Glover; Laguna, 1997): libera-se o grupo de proibições mais antigo e refaz-se a varredura, em vez de encerrar a busca.

\begin{algorithm}[H]\singlespacing
\caption{\textsc{Busca-Tabu}: forma clássica}\label{alg:tabu}
\begin{algorithmic}[1]
\REQUIRE{solução inicial $S$ (da I1); \textit{tenure} $t$; orçamento $K$}
\ENSURE{melhor solução $S^{\star}$}
\STATE{$S^{\star} \gets S$;\quad $k \gets 0$;\quad $L \gets \langle\,\rangle$}\label{t:init}
\WHILE{$k < K$}
  \STATE{$m \gets \texttt{melhor\_admiss\'ivel}(N,\,S,\,L,\,S^{\star})$}\label{t:find}
  \WHILE{$m = \textsc{nulo}$ \textbf{e} $L \neq \langle\,\rangle$}\label{t:revoke}
    \STATE{\texttt{desenfileira}$(L)$;\quad $m \gets \texttt{melhor\_admiss\'ivel}(N,\,S,\,L,\,S^{\star})$}\label{t:default}
  \ENDWHILE
  \STATE{\textbf{se} $m = \textsc{nulo}$ \textbf{então retorne} $S^{\star}$}\label{t:exhaust}
  \STATE{$S \gets S\oplus m$;\quad \texttt{enfileira}$(L,\,\mathrm{attr}(m),\,t)$}\label{t:apply}
  \STATE{\textbf{se} $D(S) < D(S^{\star})$ \textbf{então} $S^{\star} \gets S$;\ $k \gets 0$ \textbf{senão} $k \gets k+1$}\label{t:accept}
\ENDWHILE
\RETURN{$S^{\star}$}
\end{algorithmic}
\end{algorithm}

Na linha~\ref{t:find}, todo o kit é varrido em busca do melhor movimento admissível; diferentemente do VND, a linha~\ref{t:apply} pode aplicar uma piora controlada, e a fila $L$, alimentada na mesma linha (\texttt{enfileira} descarta o grupo mais antigo quando $|L|=t$), impede a busca de reverter movimentos recentes e ciclar. O laço das linhas~\ref{t:revoke}--\ref{t:default} implementa a aspiração por omissão sem consumir iteração; o retorno da linha~\ref{t:exhaust} só ocorre se não existe movimento viável algum, tabu ou não. A Tabu refina a estrutura herdada da I1 em trajetória única e contínua; o GRASP, ao contrário, explora múltiplas estruturas independentes.
```

## Seção 4, Parametrização (frase das citações repetidas e do critério de parada)

```latex
\textbf{Parametrização, critério de parada e calibração.} Cada parâmetro pertence a uma de três categorias. Os \emph{fixos} definem o terreno comum da comparação e por isso não podem ser ajustados por método: os coeficientes canônicos da I1, o kit e a ordem das vizinhanças e a convenção de distância. Os \emph{calibrados} são os de qualidade intrínsecos a cada meta-heurística, ajustados pelo \textit{irace} (L\'opez-Ib\'a\~nez et al., 2016) sobre 28 instâncias de treino (metade das 56, estratificadas por família e tipo), com o gap ao melhor conhecido como função-objetivo: a largura da RCL $\alpha\in(0;\,0{,}5)$ no GRASP; o expoente $\delta\in(0{,}5;\,3{,}0)$ e a fração $\mathit{block\_frac}\in(0{,}02;\,0{,}40)$ no reativo; e $\mathit{tenure}\in(5;\,80)$ na Tabu. Os \emph{declarados} são orçamentos computacionais, para os quais não existe valor ótimo a descobrir: como mais iterações sem melhora nunca pioram o resultado, calibrar o critério de parada $K$ pelo gap o levaria sempre ao teto do intervalo, confundindo orçamento com qualidade; declará-lo é a prática consolidada na literatura de GRASP, básico e reativo. Adotou-se $K=800$ iterações sem melhora, uniforme entre os métodos, com teto de segurança de 600~s; na faixa medida de $K=50$ a $K=3200$, nem o ordenamento dos métodos nem o resultado dos testes par a par se alteram, de modo que nenhuma conclusão depende dessa escolha. A parada por iterações, e não por tempo, favorece a reprodutibilidade. Por fim, o protocolo de aceitação da calibração foi declarado \emph{antes} da corrida do \textit{irace}: o valor calibrado só substitui o clássico da literatura se o superar nas 28 instâncias de teste com Wilcoxon pareado a 5\%; caso contrário, adota-se o clássico.
```

## Seção 4, Protocolo estatístico (regra Nemenyi/Wilcoxon)

```latex
\textbf{Protocolo estatístico.} Cada método estocástico executa 30 vezes por instância com sementes independentes; os determinísticos (I1, VND, Tabu), uma vez. A comparação global usa o teste de Friedman sobre os postos por instância, com correção para empates (frequentes na família C), seguido do pós-teste de Nemenyi (Dem\v{s}ar, 2006): dois métodos diferem se seus postos médios distam mais que a diferença crítica $CD=q_{\alpha}\sqrt{k(k+1)/(6N)}$, com $k$ algoritmos, $N$ instâncias e $q_{\alpha}$ o valor crítico do \textit{range} estudentizado; para $k=5$, $\alpha=0{,}05$ e $N=56$, $CD=0{,}815$. Cada par de interesse é também examinado por Wilcoxon pareado sobre os gaps por instância, com correção de Holm (Garc\'ia; Herrera, 2008); o Nemenyi é a leitura global conservadora, e o Wilcoxon com Holm, de maior poder para pares (Garc\'ia; Herrera, 2008), é o teste que sustenta as afirmações par a par; onde os dois discordam, o texto diz. Os experimentos foram conduzidos em uma única máquina (Intel Core Ultra~9 285K, Ubuntu~24.04, \texttt{g++}~13.3).
```

## Seção 4, Gêmeo digital (quatro parágrafos e Figura 1)

```latex
\textbf{Gêmeo digital da coleta seletiva de Vitória/ES.} A terceira camada aplica os algoritmos calibrados a um cenário com localizações reais: os 38 pontos de entrega voluntária (PEVs) de coleta seletiva de Vitória/ES, dos dados abertos do município, com depósito na associação de triagem AMARIV. Cada PEV é uma lixeira monitorada, o ``cliente'' do VRPTW. É uma \emph{prova de conceito}: as localizações são reais, mas o enchimento é sintético, calibrado pela literatura de resíduos urbanos (Lozano et al., 2018; Barth et al., 2023). O nível de enchimento $f\in[0,1]$ de cada lixeira evolui por um processo de Poisson não homogêneo discretizado em ciclos (8 ciclos/dia, cerca de 3~h cada), com intensidade entre $\lambda_{\mathrm{off}}=0{,}8$ e $\lambda_{\mathrm{pico}}=4{,}0$ chegadas por ciclo em dois picos diários (média diária de $2{,}2$), propensão heterogênea por lixeira ($p_i\sim\mathcal{U}(0{,}5;\,1{,}5)$) e incremento $\Delta f=\text{chegadas}/12$: a lixeira média enche em cerca de $5{,}4$ ciclos. Uma lixeira \emph{transborda} se $f$ atinge 1 antes de ser coletada; é o indicador de falha de serviço, contado por \emph{episódio}: cada enchimento completo conta um único transbordo, e a lixeira só volta a poder transbordar depois de coletada. A demanda de coleta deriva do enchimento por $\mathrm{demanda}=\operatorname{round}(9f)+1$, entre 1 e 10 (medida de prioridade e volume a recolher, não peso físico), e a capacidade do veículo é de 30 unidades de demanda.

\vspace{\baselineskip}
\textbf{O que torna o roteamento dinâmico.} Dois mecanismos fazem do planejamento um problema dinâmico, e ambos atuam dentro da ordem que cada ciclo segue: enchimento $\rightarrow$ leitura dos sensores $\rightarrow$ planejamento e execução das rotas $\rightarrow$ esvaziamento das lixeiras roteadas. O primeiro é o \emph{roteamento sob demanda a cada ciclo}: só as lixeiras cujo nível \emph{percebido} (a leitura mais recente entregue pela camada de rádio, descrita adiante) está acima do limiar de acionamento $\tau$ (padrão $0{,}7$) entram na instância VRPTW do ciclo; o conjunto de clientes não é conhecido de antemão e muda de ciclo para ciclo. O segundo é a \emph{janela de tempo que encolhe com a criticidade}: com $\mathrm{crit}=\max(0,\,(f-\tau)/(1-\tau))\in[0,1]$, o prazo de coleta é dado pela equação~\eqref{eq:due},
\begin{equation}
\mathit{due}=H\,\big(1-\kappa\cdot\mathrm{crit}\big),
\label{eq:due}
\end{equation}
em que $H$ é o horizonte de planejamento e $\kappa$ (padrão $0{,}6$) o coeficiente de urgência: uma lixeira no limiar recebe a janela inteira $[0,H]$; uma lixeira cheia, $[0,\,(1-\kappa)H]$. Como o critério \textit{Push Forward} só aceita inserções que respeitam os prazos, quanto mais crítica a lixeira, mais cedo ela precisa ser visitada dentro da rota. O plano de cada ciclo é \emph{atômico} (as rotas são executadas por inteiro dentro do próprio ciclo), de modo que as janelas dinâmicas atuam como priorização dentro do plano, não como calendário entre ciclos. Juntos, os dois mecanismos são a adaptação do algoritmo de Solomon anunciada no título: o mesmo solver do \textit{benchmark} (mesmo binário, parâmetros aprovados e critério de parada), alimentado a cada ciclo por uma instância gerada pelo estado dos sensores, com a matriz de distâncias e tempos do cenário. Os parâmetros herdados são defensáveis porque a calibração ajusta apenas a estratégia de busca, nada que dependa da geometria da instância; a ausência de recalibração no cenário fica registrada como limitação.

\begin{figure}[H]
  \centering\singlespacing
  \begin{minipage}{\textwidth}
    \caption{Gêmeo digital em uma realização de enchimento (semente 0, $\tau=0{,}7$): (a) tamanho da instância VRPTW de cada ciclo nos dois regimes, ciclos de pico sombreados; (b) transbordos acumulados por episódio; (c) prazo relativo $\mathit{due}/H$ em função do enchimento, equação~\eqref{eq:due}, para três valores de $\kappa$}
    \label{fig:cycles}
    \centering
    \includegraphics[width=\linewidth]{cycles_seed0.png}
    \fonte{Produção da própria autora.}
  \end{minipage}
\end{figure}

A Figura~\ref{fig:cycles} torna os dois mecanismos visíveis em uma realização. No painel (a), o regime estático resolve sempre a mesma instância de 38 lixeiras, a cada 3 ciclos; o dinâmico resolve, a cada ciclo, uma instância diferente, de 1 a 16 lixeiras, maior nos ciclos de pico; o conjunto de clientes é revelado pelos sensores, não conhecido de antemão. No painel (b), os transbordos do regime dinâmico sobem em degraus nos ciclos de pico (de 1 para 9 no ciclo 2; de 12 para 18 no ciclo 6), exatamente onde uma lixeira pode cruzar o limiar e encher dentro do mesmo ciclo; o estático os acumula entre visitas. O painel (c) é a equação~\eqref{eq:due}: abaixo do limiar a lixeira não entra na instância; acima dele, o prazo cai linearmente com o enchimento até $(1-\kappa)H$, e $\kappa$ regula a inclinação.

\vspace{\baselineskip}
Entre os sensores e o planejador há uma camada que simula os efeitos relevantes de uma rede LoRaWAN classe A com \textit{uplinks} não confirmados (Adelantado et al., 2017; Ramson et al., 2022): perda de pacote (entrega com probabilidade $\mathit{pdr}$, padrão $0{,}98$, sem retransmissão), ciclo de trabalho (cada sensor transmite a cada $\mathit{duty}$ ciclos, com fases sorteadas) e idade da leitura (entre transmissões, ou após uma perda, o planejador segue com a última leitura recebida). O planejador decide, portanto, sobre a \emph{visão de rádio} do sistema, enquanto o transbordo é contado no estado físico: um transbordo ocorrido com a lixeira invisível ao rádio é atribuível à comunicação, não ao roteamento. Dois mapas são usados. A comparação entre regimes e a análise de sensibilidade correm sobre o grafo euclidiano das coordenadas projetadas dos PEVs, normalizadas para a escala do \textit{benchmark} (distâncias adimensionais, $H=5\,000$, serviço 5); a demonstração viária da Figura~\ref{fig:road} usa matrizes de distância (metros) e tempo de direção (segundos) da malha do OpenStreetMap via OSRM (Luxen; Vetter, 2011), com $H=6$~h e serviço de 120~s; o fator de circuito médio (distância rodoviária sobre linha reta) foi de $1{,}53$, chegando a $6{,}9$ em pares separados por água.

\vspace{\baselineskip}
A validação compara dois regimes: o \emph{dinâmico} (coleta sob demanda das lixeiras acima do limiar, a cada ciclo) e o \emph{estático} (coleta de todas as lixeiras a cada 3 ciclos, independentemente do enchimento; nesse intervalo a lixeira média atinge $55\%$ da capacidade, mas as de maior propensão, que enchem em $3{,}6$ ciclos, já podem transbordar). A comparação é pareada sobre 30 realizações independentes de enchimento (em cada semente, os dois regimes veem a mesma sequência de chegadas), com teste de Wilcoxon pareado; para os empates, frequentes em indicadores inteiros, usa-se o tratamento \textit{zsplit} (empates divididos igualmente entre os postos positivos e negativos, em vez de descartados). Como limiar, capacidade e coeficiente de urgência são escolhas de modelagem, reporta-se também uma análise de sensibilidade variando um parâmetro por vez sobre uma mesma realização de enchimento.
```

## Seção 5, abertura (portão de validação)

```latex
Antes de qualquer comparação, a implementação foi validada reproduzindo o custo declarado das 56 soluções de referência (diferença absoluta $\le 0{,}05$ em todas), um portão: nenhum resultado foi considerado antes de ele passar. Em todas as 3.528 execuções do estudo, o verificador independente não acusou nenhuma solução inviável e nenhum gap negativo ocorreu, o que confirma empiricamente o invariante de viabilidade da Seção~4.
```

## Seção 5, Comparação, empate técnico, Figuras 2 e 3

```latex
O resultado primário usa o conjunto de teste, que a calibração nunca viu. O teste de Friedman rejeita a igualdade entre os cinco métodos ($\chi^2_F=94{,}15$, $p=1{,}7\times10^{-19}$), com postos médios GRASP $1{,}77$, reativo $1{,}84$, Tabu $2{,}63$, VND $3{,}77$ e I1 $5{,}00$; nas 56 instâncias o quadro é o mesmo ($\chi^2_F=185{,}36$, $p=5{,}3\times10^{-39}$). As comparações par a par por Wilcoxon com Holm dão o quadro final: todos os pares diferem, \emph{exceto} GRASP $\times$ reativo; em particular, as duas variantes de GRASP superam a Busca Tabu ($p_{\mathrm{Holm}}=6{,}9\times10^{-4}$ no teste, com o GRASP melhor em 18 das 28 instâncias e pior em 3; $4{,}8\times10^{-7}$ nas 56). O pós-teste de Nemenyi, mais conservador, confirma a separação GRASP--Tabu nas 56 instâncias por margem estreita (diferença de postos $0{,}830$ contra $CD=0{,}815$; $0{,}627$ sem a I1) e não separa o reativo da Tabu ($0{,}804$), o que aparece como a barra que une os dois na Figura~\ref{fig:cd}; no conjunto de teste ($N=28$, $CD=1{,}15$), não separa nenhum dos dois. A hierarquia afirmada, GRASP $\approx$ reativo $\succ$ Tabu $\succ$ VND $\succ$ I1, apoia-se assim no Wilcoxon--Holm, e o Nemenyi a sustenta integralmente apenas para o GRASP fixo. Sob orçamento de tempo fixo ($T=20$~s), a integral primal $\mathit{PI}$ do desafio (DIMACS, 2022), métrica dependente da máquina e reportada só como complemento, dá a mesma ordem. \input{tabelas/pi_frase}

\vspace{\baselineskip}
\textbf{GRASP fixo e reativo: empate técnico.} A equivalência entre as duas variantes não é ausência de resultado, e sim um resultado com explicação. Os dois conjuntos concordam: Wilcoxon $p=0{,}95$ no teste (11 vitórias do GRASP, 9 do reativo, 8 empates) e $p=0{,}37$ nas 56 instâncias (22/20/14). O sentido da diferença nominal muda com a estatística escolhida (o reativo tem o menor gap médio, $1{,}88$ contra $1{,}96$, mas o GRASP tem o melhor gap por instância, $0{,}99$ contra $1{,}02$, e o menor posto médio, $1{,}77$ contra $1{,}84$) e muda com a família (Tabela~\ref{tab:familia}), assinatura de diferenças dentro do ruído. A explicação está na Tabela~\ref{tab:gain}: o GRASP é insensível a $\alpha$ na faixa $0{,}2$--$0{,}3$ ($p=0{,}63$), e o valor fixo $\alpha=0{,}30$ já pertence à grade que o reativo aprende. O mecanismo reativo só rende quando o $\alpha$ mais produtivo varia entre instâncias (Prais; Ribeiro, 2000); nestas, não varia, e a exploração dos valores piores da grade ($0{,}05$, $0{,}50$) durante o aprendizado não custou nada mensurável: mesmas iterações ($1\,249$) e mesmo tempo ($\approx 57$~s). Pelo mesmo motivo, o ganho limítrofe da calibração do reativo ($+0{,}03$~pp, $p=0{,}0496$, $1{,}5\%$ do gap) é irrelevante para as conclusões: com parâmetros clássicos ou calibrados, o reativo empata com o GRASP.

\begin{figure}[H]
  \centering\singlespacing
  \begin{minipage}[t]{0.57\textwidth}
    \caption{Diagrama de diferença crítica (Friedman/Nemenyi, 56 instâncias): cada método na posição do seu posto médio (esquerda = melhor); uma barra une métodos indistinguíveis a 5\%}
    \label{fig:cd}
    \centering
    \includegraphics[width=\linewidth]{cd_diagram_full.png}
    \fonte{Produção da própria autora.}
  \end{minipage}\hfill
  \begin{minipage}[t]{0.40\textwidth}
    \caption{Distribuição do gap por método nas 56 instâncias (todas as execuções); traço = mediana, triângulo = média}
    \label{fig:box}
    \centering
    \includegraphics[width=\linewidth]{boxplot_gap.png}
    \fonte{Produção da própria autora.}
  \end{minipage}
\end{figure}

A Figura~\ref{fig:box} mostra o que as médias da Tabela~\ref{tab:overall} resumem. As caixas do GRASP e do reativo coincidem em posição e largura (a imagem do empate); a da Busca Tabu é mais alta e mais longa, com cauda até $14\%$: a Tabu é pior em média e mais irregular entre instâncias. VND e I1 dão a escala do que cada camada de refinamento remove.
```

## Seção 5, Gêmeo digital (parágrafo ao lado da Figura 4, Tabela 5, sensibilidade e Figura 5)

```latex
\noindent\begin{minipage}[t]{0.57\textwidth}
\textbf{Gêmeo digital.} A Tabela~\ref{tab:twin} apresenta a comparação pareada entre os regimes sobre 30 realizações de enchimento. O quadro é de \emph{compromisso}, não de dominância. O regime dinâmico realiza pouco mais da metade das coletas do estático ($123{,}9$ contra $228{,}0$; redução de $46\%$), mas não percorre menos distância: como despacha veículos em 15 dos 16 ciclos (o estático, em 6), suas rotas são mais numerosas e mais curtas (cerca de 8 lixeiras por despacho contra 38), e a distância total resulta comparável, ligeiramente maior ($+2{,}4\%$, $p=0{,}0016$). A economia da coleta guiada por sensores está, portanto, nos esvaziamentos evitados (104 a menos em 16 ciclos), não na quilometragem. Em contrapartida, no limiar padrão $\tau=0{,}7$, o dinâmico incorre em \emph{mais} transbordos ($27{,}0$ contra $19{,}1$ episódios, $p<0{,}001$). A causa está no próprio modelo de enchimento: entre o limiar e a capacidade cabem $3{,}6$ chegadas, e no pico ($\lambda=4$) uma lixeira recebe 4 ou mais chegadas em um único ciclo com probabilidade $0{,}57$ ($0{,}85$ para as de propensão $1{,}5$); ela pode cruzar o limiar e transbordar dentro do mesmo ciclo, antes de ser vista pelo planejador. Baixar o limiar alarga essa faixa: com $\tau=0{,}5$ (6 chegadas), a realização analisada na sensibilidade registra 5 transbordos e 167 coletas, ainda bem abaixo das 228 do estático.
\end{minipage}\hfill
\begin{minipage}[t]{0.40\textwidth}
  \singlespacing
  \captionof{figure}{Rotas do gêmeo digital sobre a malha viária real de Vitória/ES: cada cor é um caminhão; a estrela é o depósito (AMARIV)}
  \label{fig:road}
  \centering
  \includegraphics[width=\linewidth]{vitoria_road_routes.png}
  \fonte{Produção da própria autora, com malha viária do OpenStreetMap via OSRM.}
\end{minipage}
\par

\input{tabelas/twin_compare}

A análise de sensibilidade, sobre uma única realização (Figura~\ref{fig:sens}), delimita o papel de cada parâmetro: o limiar $\tau$ domina o compromisso serviço--custo (de 5 a 61 transbordos ao variar $\tau$ de $0{,}5$ a $0{,}9$); a capacidade do veículo reduz fortemente a distância (de $6\,527$ a $3\,049$ ao variar de 15 a 40) sem afetar transbordos; e o coeficiente de urgência $\kappa$ não altera nenhum dos três indicadores agregados. Este último resultado pede leitura cuidadosa: no horizonte folgado do cenário, as janelas dinâmicas raramente restringem a viabilidade, e o seu efeito (antecipar as lixeiras críticas dentro de cada rota) está na ordem de visita, que distância, coletas e transbordos não medem; o tempo entre o cruzamento do limiar e a coleta de cada lixeira crítica é a métrica que faltou, registrada como continuidade. O efeito do canal é mensurável: no mapa da instância R101, com 12 ciclos e o VND como roteador, degradar o canal perfeito para $\mathit{pdr}=0{,}9$ com transmissão a cada 2 ciclos elevou os transbordos de 51 para 96 episódios, com defasagem média de $0{,}52$ ciclo; além do roteamento, a qualidade da comunicação limita o serviço. Nas instâncias pequenas de cada ciclo (1 a 16 lixeiras na Figura~\ref{fig:cycles}), os métodos de melhoria convergem a rotas de custo muito próximo; as distinções do \textit{benchmark} aparecem em problemas maiores. Por fim, a Figura~\ref{fig:road} mostra as rotas sobre a malha viária real: rotear os 38 PEVs produziu 6 veículos, $83{,}7$~km e $3{,}7$~h de operação.

\begin{figure}[H]
  \centering\singlespacing
  \begin{minipage}{\textwidth}
    \caption{Sensibilidade do gêmeo digital, um parâmetro por vez sobre uma mesma realização: distância total (eixo esquerdo) e transbordos (eixo direito) em função do limiar, da capacidade do veículo e do coeficiente de urgência}
    \label{fig:sens}
    \centering
    \includegraphics[width=\linewidth]{sensitivity.png}
    \fonte{Produção da própria autora.}
  \end{minipage}
\end{figure}

Na Figura~\ref{fig:sens}, a distância está no eixo esquerdo e os transbordos no direito. No primeiro painel as curvas se cruzam: subir o limiar reduz a distância e multiplica os transbordos, e esse cruzamento faz do limiar a alavanca operacional. No segundo, a capacidade só move a distância (transbordos fixos em 27). No terceiro, as duas retas horizontais mostram que o coeficiente de urgência não altera nenhum agregado.
```

## Seção 6, Conclusões

```latex
Este subprojeto construiu uma comparação controlada de cinco heurísticas clássicas para o VRPTW (núcleo de código compartilhado, viabilidade garantida por construção e conferida por verificador independente, calibração com portão de aceitação pré-declarado e testes pareados) e transferiu os métodos calibrados a um gêmeo digital da coleta seletiva de Vitória/ES. Quanto à pergunta de pesquisa: a comparação estabeleceu, com significância estatística, a hierarquia entre as estratégias de busca (GRASP e sua variante reativa, indistinguíveis entre si, à frente da Busca Tabu, do VND e da I1), e a transferência ao cenário dinâmico mostrou que a coleta guiada por sensores preserva a factibilidade temporal das rotas e reduz as coletas em $46\%$ a distância comparável, com o nível de serviço governado pelo limiar de acionamento: no limiar padrão, os transbordos superam os do regime fixo; na realização analisada, um limiar mais baixo recuperou o serviço mantendo a economia de coletas. São estas as contribuições: no âmbito acadêmico, o protocolo reprodutível de comparação e a evidência de que, sob objetivo de distância, o GRASP domina a Busca Tabu clássica nas instâncias de Solomon; no âmbito profissional e social, a quantificação do compromisso entre esforço de coleta e transbordos, com o limiar de acionamento como a alavanca operacional decisiva.

\vspace{\baselineskip}
As principais limitações delimitam o alcance das conclusões: o objetivo otimizado é apenas a distância (a hierarquia lexicográfica veículos $\rightarrow$ distância não foi avaliada como objetivo); a Busca Tabu foi mantida na forma mais simples, sem memória de longo prazo; no gêmeo digital, o enchimento é simulado e não medido, a camada LoRaWAN é representada e não validada energeticamente, a comparação entre regimes corre sobre o grafo euclidiano dos PEVs e não sobre a malha viária, os hiperparâmetros são herdados do \textit{benchmark} sem recalibração, o efeito das janelas dinâmicas na ordem das visitas não foi medido, e a análise de sensibilidade usa uma única realização de enchimento (a comparação entre regimes usa 30). A principal dificuldade metodológica foi evitar que escolhas de configuração enviesassem a comparação, respondida com o desenho de parâmetros fixos, calibrados e declarados e com a verificação de que as conclusões independem do orçamento de parada.

\vspace{\baselineskip}
Como continuidade, sugerem-se: validação com dados reais de enchimento em Vitória (piloto com sensores); comparação pareada sobre a malha viária e em vários limiares; medição do tempo entre o cruzamento do limiar e a coleta das lixeiras críticas; avaliação sob o critério lexicográfico; Tabu com memória de longo prazo; planos que atravessam ciclos, com replanejamento de veículos em rota; e quantificação de benefícios econômicos e ambientais.
```

## Referências acrescentadas

```latex
\referencia BR\"AYSY, O.; GENDREAU, M. Vehicle routing problem with time windows, part I: route construction and local search algorithms. \textbf{Transportation Science}, [\textit{s.~l.}], v. 39, n. 1, p. 104-118, 2005.
\referencia PILLAC, V.; GENDREAU, M.; GU\'ERET, C.; MEDAGLIA, A. L. A review of dynamic vehicle routing problems. \textbf{European Journal of Operational Research}, [\textit{s.~l.}], v. 225, n. 1, p. 1-11, 2013.
```
