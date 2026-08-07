#!/usr/bin/env python3
"""Interactive Digital Twin dashboard (Streamlit + Plotly).

Run with:  experiments/.venv/bin/streamlit run digital_twin/dashboard.py
"""
import os
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from twin import simulate, load_map, compare_algorithms, route_schedules, plan_routes

_SENS_FIG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "results", "digital_twin", "sensitivity.png")

HORIZON, SERVICE = 5000, 5          # must match twin.simulate defaults
CYCLES_PER_DAY = 8                  # must match sensors.FillSimulator default
HOURS_PER_CYCLE = 24 // CYCLES_PER_DAY
PERIOD_NAME = {"pico": "horário de pico", "fora": "fora de pico"}
PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b",
           "#e377c2", "#17becf", "#bcbd22", "#7f7f7f"]

st.set_page_config(layout="wide", page_title="Digital Twin — Coleta de Resíduos")
st.markdown(
    '<div style="background:#5a9367;border-radius:38px;padding:12px 30px;margin:0 0 10px 0;">'
    '<h1 style="color:white;text-align:center;margin:0;font-size:2rem;">'
    'Digital Twin — Coleta Inteligente de Resíduos</h1></div>',
    unsafe_allow_html=True)
st.markdown(
    "Simulação da coleta **dinâmica**: sensores medem o enchimento das lixeiras e, a cada rodada de "
    "monitoramento, o otimizador **replaneja as rotas** dos caminhões para atender apenas as que "
    "precisam, dentro do prazo — reduzindo deslocamento e evitando transbordo."
)
with st.expander("Como funciona a simulação", expanded=False):
    st.graphviz_chart(
        'digraph { rankdir=LR; bgcolor="transparent"; '
        'node [shape=box style="rounded,filled" fillcolor="#eaf3ec" color="#5a9367" fontname="Arial" fontsize="11"]; '
        'edge [color="#5a9367" fontname="Arial" fontsize="9"]; '
        '"Sensores IoT\\n(enchimento em\\ntempo real)" -> "Lixeiras críticas\\n(acima do limiar +\\njanela por urgência)" '
        '-> "Otimizador VRPTW\\n(GRASP/Tabu/...)" -> "Rotas dos\\ncaminhões" -> "Coleta\\n(lixeiras esvaziam)"; '
        '"Coleta\\n(lixeiras esvaziam)" -> "Sensores IoT\\n(enchimento em\\ntempo real)" '
        '[label="próximo ciclo" style=dashed]; }')
    st.markdown(
        f"Cada **ciclo** ≈ **{HOURS_PER_CYCLE} h** ({CYCLES_PER_DAY} ciclos = 1 dia), com períodos de "
        "**pico** (enchimento mais rápido, modelado por um processo de Poisson não homogêneo). "
        "Lixeiras mais cheias recebem **prazo menor** (a técnica *Push Forward* prioriza as críticas). "
        "Lixeiras que passam do limite antes da coleta **transbordam** — o indicador de qualidade do serviço."
    )

st.info(
    "ℹ️ **Prova de conceito.** As **localizações** das lixeiras são reais (38 pontos de coleta seletiva "
    "de Vitória/ES); o **enchimento é simulado** por um processo de Poisson não homogêneo calibrado pela "
    "literatura — medir o enchimento real exigiria meses de sensores. A comunicação LoRaWAN é "
    "representada pelos ciclos de monitoramento, sem validação energética. Os parâmetros do cenário são "
    "**escolhas de modelagem**: veja o efeito de cada um na seção *Sensibilidade*."
)

with st.expander("O que está por trás — a metodologia (o que estudamos)", expanded=False):
    st.markdown(
        "Este painel aplica, a um cenário de coleta, os algoritmos validados num **benchmark científico** "
        "sobre as 56 instâncias clássicas de Solomon. Em resumo:\n\n"
        "- **Problema (VRPTW).** Roteirizar veículos a partir de um depósito para atender lixeiras dentro "
        "de **janelas de tempo**, sem exceder a **capacidade**, visitando **cada uma uma vez** e voltando "
        "ao depósito dentro do horizonte.\n"
        "- **Objetivo = distância total** (convenção DIMACS, euclidiana truncada a 1 casa). O **número de "
        "veículos** é uma *consequência*, reportada à parte: só diminui quando um movimento entre rotas "
        "**esvazia** uma rota inteira.\n"
        "- **Viabilidade garantida.** Toda rota — na construção **e** na melhoria — respeita janela, "
        "capacidade, cobertura e retorno; cada movimento é validado **antes** de ser aceito, e a solução "
        "final é reverificada de forma independente (nas execuções do estudo, **0 inviáveis**).\n"
        "- **Cinco métodos** sobre o **mesmo núcleo** (para uma comparação justa): *Solomon I1* "
        "(construção), *VND* (busca local), *GRASP* e *GRASP reativo* (construção gulosa-aleatorizada + "
        "busca local) e *Busca Tabu*. No estudo, **GRASP/reativo** foram os melhores, seguidos da Tabu.\n"
        "- **Parada por iterações sem melhoria** (reprodutível, não depende da máquina); o tempo é "
        "reportado à parte.\n"
        "- **Calibração** por *irace* (divisão treino/teste) e comparação estatística por "
        "**Friedman + Nemenyi**."
    )

with st.expander("O que faz aumentar o número de caminhões e esvaziar rotas", expanded=False):
    st.markdown(
        "- **Limiar de coleta menor** → mais lixeiras por ciclo → mais carga → **mais caminhões**.\n"
        "- **Capacidade do veículo** frente à **demanda** de cada lixeira (a demanda cresce com o "
        "enchimento, como *prioridade*, não peso): quanto menor a razão capacidade/demanda, **mais rotas**.\n"
        "- **Janelas mais apertadas** (coef. de urgência alto) dificultam agrupar lixeiras numa mesma "
        "rota → tende a **mais caminhões**, porém **menos transbordos**.\n"
        "- Uma rota **esvazia** (libera um caminhão) quando a busca consegue redistribuir todos os seus "
        "clientes em outras rotas **sem violar a viabilidade**."
    )

with st.expander("Sensibilidade dos parâmetros (compromisso distância × transbordos)", expanded=False):
    if os.path.isfile(_SENS_FIG):
        st.image(_SENS_FIG, use_container_width=True)
        st.caption("Cada parâmetro de modelagem (limiar, capacidade, urgência) varia isoladamente; mostra-se "
                   "o compromisso entre distância total (verde) e transbordos (vermelho). "
                   "Em vez de fixar valores arbitrários, justificamos as escolhas por este compromisso.")
    else:
        st.caption("Para gerar a figura de sensibilidade, rode: "
                   "`.venv/bin/python digital_twin/sensitivity.py` "
                   "(varia limiar, capacidade e coeficiente de urgência e mede distância × transbordos).")


def cycle_label(c):
    day = c // CYCLES_PER_DAY + 1
    hour = (c % CYCLES_PER_DAY) * HOURS_PER_CYCLE
    return f"Dia {day}, {hour:02d}h"


def map_figure(cmap, snap, scheds):
    fig = go.Figure()
    is_geo = cmap.display_is_lonlat
    Marker = go.Scattermapbox if is_geo else go.Scatter
    xy = (lambda ns: dict(lon=[n.dx for n in ns], lat=[n.dy for n in ns])) if is_geo \
        else (lambda ns: dict(x=[n.dx for n in ns], y=[n.dy for n in ns]))

    if snap["active"]:
        fig.add_trace(Marker(**xy([cmap.bins[i] for i in snap["active"]]), mode="markers",
                             marker=dict(size=22 if is_geo else 20, color="red", opacity=0.20),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(Marker(**xy(cmap.bins), mode="markers",
                         marker=dict(size=11 if is_geo else 9, color=snap["fills"],
                                     colorscale="YlOrRd", cmin=0, cmax=1, showscale=True,
                                     colorbar=dict(title="enchimento")),
                         text=[f"{b.label}<br>enchimento {snap['fills'][k]*100:.0f}%"
                               for k, b in enumerate(cmap.bins)],
                         hoverinfo="text", name="lixeiras"))
    for k, (route, sch) in enumerate(zip(snap["routes"], scheds)):
        nodes = [cmap.depot] + [cmap.bins[i] for i in route] + [cmap.depot]
        color = PALETTE[k % len(PALETTE)]
        fig.add_trace(Marker(**xy(nodes), mode="lines", line=dict(width=2.5, color=color),
                             hoverinfo="skip", name=f"Caminhão {k+1} ({len(route)} paradas)"))
        hover = [f"{s['label']}<br>parada {j+1} de {len(sch['stops'])}<br>chegada {s['arrival']:.0f}"
                 f"<br>prazo {s['due']}" for j, s in enumerate(sch["stops"])]
        fig.add_trace(Marker(**xy([cmap.bins[i] for i in route]), mode="markers+text",
                             marker=dict(size=15 if is_geo else 13, color=color),
                             text=[str(j + 1) for j in range(len(route))],
                             textfont=dict(color="white", size=9), textposition="middle center",
                             hovertext=hover, hoverinfo="text", showlegend=False))
    full = snap.get("full", [])
    if full:
        fmark = dict(size=13, color="black") if is_geo else dict(size=15, color="black", symbol="x")
        fig.add_trace(Marker(**xy([cmap.bins[i] for i in full]), mode="markers", marker=fmark,
                             text=[f"{cmap.bins[i].label}<br>TRANSBORDOU (100%)" for i in full],
                             hoverinfo="text", name="transbordando (100%)"))
    fig.add_trace(Marker(**xy([cmap.depot]), mode="markers",
                         marker=dict(size=17, color="#1f4e79"),
                         text=[cmap.depot.label], hoverinfo="text", name="depósito / garagem"))
    if is_geo:
        fig.update_layout(mapbox_style="open-street-map", mapbox_zoom=12,
                          mapbox_center=dict(lon=cmap.depot.dx, lat=cmap.depot.dy))
    else:
        fig.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1))
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=0, b=0),
                      legend=dict(orientation="h", y=-0.03))
    return fig


def routes_map(cmap, fills, active, routes, title):
    fig = go.Figure()
    is_geo = cmap.display_is_lonlat
    Marker = go.Scattermapbox if is_geo else go.Scatter
    xy = (lambda ns: dict(lon=[n.dx for n in ns], lat=[n.dy for n in ns])) if is_geo \
        else (lambda ns: dict(x=[n.dx for n in ns], y=[n.dy for n in ns]))
    if active:
        fig.add_trace(Marker(**xy([cmap.bins[i] for i in active]), mode="markers",
                             marker=dict(size=18 if is_geo else 15, color="red", opacity=0.18),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(Marker(**xy(cmap.bins), mode="markers",
                         marker=dict(size=8, color=fills, colorscale="YlOrRd", cmin=0, cmax=1),
                         hoverinfo="skip", showlegend=False))
    for k, route in enumerate(routes):
        nodes = [cmap.depot] + [cmap.bins[i] for i in route] + [cmap.depot]
        fig.add_trace(Marker(**xy(nodes), mode="lines",
                             line=dict(width=1.6, color=PALETTE[k % len(PALETTE)]),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(Marker(**xy([cmap.depot]), mode="markers",
                         marker=dict(size=13, color="black"), hoverinfo="skip", showlegend=False))
    if is_geo:
        fig.update_layout(mapbox_style="open-street-map", mapbox_zoom=11.5,
                          mapbox_center=dict(lon=cmap.depot.dx, lat=cmap.depot.dy))
    else:
        fig.update_layout(yaxis=dict(scaleanchor="x", scaleratio=1))
    fig.update_layout(height=430, margin=dict(l=0, r=0, t=32, b=0),
                      title=dict(text=title, x=0.5, font=dict(size=13)))
    return fig


def schedule_figure(scheds):
    fig = go.Figure()
    if not scheds:
        return fig
    for k, sch in enumerate(scheds):
        color = PALETTE[k % len(PALETTE)]
        y = f"Caminhão {k+1}"
        for s in sch["stops"]:
            fig.add_trace(go.Bar(
                base=[s["start"]], x=[max(SERVICE, s["departure"] - s["start"])], y=[y],
                orientation="h", marker_color=color, showlegend=False,
                hovertext=f"{s['label']}<br>chegada {s['arrival']:.0f} · espera {s['wait']:.0f}"
                          f"<br>atende {s['start']:.0f}–{s['departure']:.0f} · prazo {s['due']}",
                hoverinfo="text"))
        dues = [s["due"] for s in sch["stops"]]
        fig.add_trace(go.Scatter(x=dues, y=[y] * len(dues), mode="markers",
                                 marker=dict(symbol="line-ns-open", size=13, color="crimson"),
                                 name="prazo de cada lixeira", showlegend=(k == 0), hoverinfo="skip"))
    fig.update_layout(barmode="overlay", height=max(220, 58 * len(scheds)),
                      xaxis_title="tempo do turno (unidades proporcionais à distância)",
                      margin=dict(t=10, b=0), legend=dict(orientation="h"))
    return fig


def evolution_figure(history, current):
    cycles = [h["cycle"] + 1 for h in history]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=cycles, y=[len(h["active"]) for h in history], name="lixeiras coletadas",
                         marker_color="orange", opacity=0.6), secondary_y=False)
    fig.add_trace(go.Scatter(x=cycles, y=[h["overflow"] for h in history], name="transbordos (acumulado)",
                             line=dict(color="crimson")), secondary_y=True)
    fig.add_vline(x=current + 1, line_dash="dash", line_color="gray")
    fig.update_xaxes(title_text="ciclo")
    fig.update_yaxes(title_text="lixeiras coletadas", secondary_y=False)
    fig.update_yaxes(title_text="transbordos", secondary_y=True)
    fig.update_layout(height=280, margin=dict(t=10, b=0), legend=dict(orientation="h"))
    return fig


with st.sidebar:
    st.header("1 · Cenário")
    source = st.selectbox("Mapa", ["vitoria", "solomon", "wcvrptw"],
                          format_func=lambda s: {"vitoria": "Vitória/ES (pontos reais)",
                                                 "solomon": "Solomon (benchmark)",
                                                 "wcvrptw": "WCVRPTW (coleta, benchmark)"}[s])
    arg = st.text_input("Instância", "R101") if source != "vitoria" else None

    st.header("2 · Enchimento das lixeiras")
    threshold = st.slider("Limiar de coleta", 30, 95, 70, 5,
                          format="%d%%", help="a lixeira entra na rota quando passa deste enchimento") / 100.0
    urgency_coef = st.slider("Urgência da janela", 0.0, 0.9, 0.6, 0.1,
                             help="0 = todas as janelas iguais; maior = lixeiras mais cheias recebem "
                                  "prazo bem mais curto (intensidade do Push Forward)")
    days = st.slider("Dias simulados", 1, 6, 2, help=f"cada dia tem {CYCLES_PER_DAY} ciclos de ~{HOURS_PER_CYCLE} h")
    cycles = days * CYCLES_PER_DAY
    seed = int(st.number_input("Semente (reprodutibilidade)", 0, 9999, 0))

    st.header("3 · Otimização das rotas")
    capacity = st.slider("Capacidade do caminhão", 10, 100, 25, 5,
                         help="carga máxima antes de fechar a rota e voltar ao depósito")
    algo = st.selectbox("Algoritmo de roteamento", ["grasp", "rgrasp", "tabu", "vnd", "i1"], index=0,
                        format_func=lambda a: {"grasp": "GRASP (melhor no estudo)", "rgrasp": "GRASP reativo",
                                               "tabu": "Busca Tabu", "vnd": "VND", "i1": "Solomon I1 (base)"}[a])
    budget = st.slider("Tempo de cálculo por ciclo", 100, 3000, 600, 100, format="%d ms")

    compare_mode = st.checkbox("Comparar todos os algoritmos",
                               help="aplica os 5 algoritmos na mesma simulação e compara a distância total")
    run = st.button("Simular", type="primary", use_container_width=True)

if run:
    cmap = load_map(source, arg)
    if compare_mode:
        with st.spinner("Aplicando todos os algoritmos na mesma simulação..."):
            comp = compare_algorithms(cmap, cycles=cycles, threshold=threshold,
                                      budget_ms=budget, capacity=capacity, seed=seed,
                                      urgency_coef=urgency_coef)
        st.session_state.update(cmap=cmap, comp=comp, mode="compare")
    else:
        with st.spinner("Simulando ciclos e replanejando rotas..."):
            hist = simulate(cmap, cycles=cycles, threshold=threshold, algo=algo, budget_ms=budget,
                            capacity=capacity, horizon=HORIZON, service=SERVICE, seed=seed,
                            urgency_coef=urgency_coef)
        st.session_state.update(cmap=cmap, hist=hist, mode="single", threshold=threshold,
                                capacity=capacity, budget=budget, algo=algo, urgency_coef=urgency_coef)

if st.session_state.get("mode") == "compare":
    cmap, comp = st.session_state["cmap"], st.session_state["comp"]
    st.subheader(f"Qual algoritmo coleta com menos deslocamento — {cmap.name}")
    st.caption("Todos enfrentam exatamente o mesmo enchimento; muda só a qualidade do roteamento. "
               "Menor distância total é melhor.")
    algos = list(comp.keys())
    bar = go.Figure(go.Bar(x=algos, y=[comp[a]["kpis"]["distancia_total"] for a in algos],
                           marker_color="seagreen",
                           text=[f"{comp[a]['kpis']['distancia_total']:.0f}" for a in algos],
                           textposition="outside"))
    bar.update_layout(height=340, yaxis_title="distância total (todos os ciclos)", margin=dict(t=10))
    line = go.Figure()
    for a in algos:
        line.add_trace(go.Scatter(y=comp[a]["per_cycle"], mode="lines+markers", name=a))
    line.update_layout(height=340, xaxis_title="ciclo", yaxis_title="distância do ciclo",
                       margin=dict(t=10), legend=dict(orientation="h"))
    c1, c2 = st.columns(2)
    c1.plotly_chart(bar, use_container_width=True)
    c2.plotly_chart(line, use_container_width=True)
    st.dataframe({"algoritmo": algos,
                  "distância total": [comp[a]["kpis"]["distancia_total"] for a in algos],
                  "lixeiras coletadas": [comp[a]["kpis"]["coletas"] for a in algos],
                  "transbordos": [comp[a]["kpis"]["transbordos"] for a in algos]},
                 use_container_width=True)

elif st.session_state.get("mode") == "single":
    cmap, hist = st.session_state["cmap"], st.session_state["hist"]
    thr = st.session_state.get("threshold", 0.7)
    uc = st.session_state.get("urgency_coef", 0.6)
    c = st.slider("Avance no tempo (ciclos)", 0, len(hist) - 1, 0)
    snap = hist[c]
    scheds = route_schedules(cmap, snap["routes"], snap["fills"], threshold=thr,
                             horizon=HORIZON, service=SERVICE, urgency_coef=uc)

    st.subheader(f"Ciclo {c+1} de {len(hist)} — {cycle_label(c)} · {PERIOD_NAME.get(snap['period'], snap['period'])}")
    full_now = len(snap.get("full", []))
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Lixeiras a coletar", len(snap["active"]), help="acima do limiar neste ciclo")
    k2.metric("Caminhões usados", snap["vehicles"])
    k3.metric("Distância do ciclo", f"{snap['distance']:.0f}")
    k4.metric("Transbordando agora", full_now,
              delta=("em dia" if full_now == 0 else "atenção"),
              delta_color=("normal" if full_now == 0 else "inverse"),
              help="lixeiras que atingiram 100% (transbordaram) neste ciclo")
    k5.metric("Transbordos acumulados", snap["overflow"])
    if full_now == 0:
        st.success("Atendimento em dia: nenhuma lixeira transbordando neste ciclo.")
    else:
        st.warning(f"{full_now} lixeira(s) transbordando (100%) neste ciclo — coletadas com atraso. "
                   "Reduza o limiar ou aumente a capacidade/frequência para evitar.")

    tab_map, tab_sched, tab_ba, tab_det = st.tabs(
        ["Mapa das rotas", "Cronograma (horários)", "Otimização (antes/depois)", "Detalhe das rotas"])
    with tab_map:
        st.caption("Cada cor é um caminhão; números = ordem de visita. Cor da lixeira = nível de "
                   "enchimento; anel vermelho = será coletada agora; **preto = transbordou (100%)**; "
                   "marcador azul-escuro = depósito.")
        st.plotly_chart(map_figure(cmap, snap, scheds), use_container_width=True)
    with tab_sched:
        st.caption("Quando cada caminhão atende cada lixeira ao longo do turno. "
                   "A barra é o tempo de serviço; o traço vermelho marca o prazo (janela de tempo) da lixeira.")
        st.plotly_chart(schedule_figure(scheds), use_container_width=True)
        st.markdown("**Evolução ao longo dos ciclos**")
        st.plotly_chart(evolution_figure(hist, c), use_container_width=True)
    with tab_ba:
        if not snap["active"]:
            st.info("Nenhuma coleta neste ciclo.")
        else:
            algo_sel = st.session_state.get("algo", "grasp")
            cap = st.session_state.get("capacity", 25)
            bud = st.session_state.get("budget", 600)
            rb, db = plan_routes(cmap, snap["active"], snap["fills"], "i1", bud, cap,
                                 HORIZON, SERVICE, True, thr, urgency_coef=uc)
            ra, da = snap["routes"], snap["distance"]
            ganho = (db - da) / db * 100.0 if db > 0 else 0.0
            st.caption("Mesma demanda do ciclo, dois roteadores: **I1** (construção simples) vs "
                       f"**{algo_sel}** (escolhido). A otimização reduz o deslocamento total.")
            g1, g2, g3 = st.columns(3)
            g1.metric("Antes — I1", f"{db:.0f}")
            g2.metric(f"Depois — {algo_sel}", f"{da:.0f}")
            g3.metric("Ganho", f"{ganho:.1f}%", delta=f"-{db - da:.0f}")
            cb, ca = st.columns(2)
            cb.plotly_chart(routes_map(cmap, snap["fills"], snap["active"], rb,
                                       f"Antes — I1 ({len(rb)} rotas, dist {db:.0f})"),
                            use_container_width=True)
            ca.plotly_chart(routes_map(cmap, snap["fills"], snap["active"], ra,
                                       f"Depois — {algo_sel} ({len(ra)} rotas, dist {da:.0f})"),
                            use_container_width=True)
    with tab_det:
        if not scheds:
            st.info("Nenhuma coleta neste ciclo — as lixeiras ainda estão abaixo do limiar.")
        for k, sch in enumerate(scheds):
            with st.expander(f"Caminhão {k+1} — {len(sch['stops'])} paradas · "
                             f"distância {sch['distance']:.0f} · carga {sch['load']}"):
                st.dataframe({"ordem": list(range(1, len(sch["stops"]) + 1)),
                              "lixeira": [s["label"] for s in sch["stops"]],
                              "chegada": [round(s["arrival"]) for s in sch["stops"]],
                              "prazo": [s["due"] for s in sch["stops"]],
                              "espera": [round(s["wait"]) for s in sch["stops"]],
                              "demanda": [s["demand"] for s in sch["stops"]]},
                             use_container_width=True)
else:
    st.info("Defina o cenário na barra lateral e clique em **Simular**.")
