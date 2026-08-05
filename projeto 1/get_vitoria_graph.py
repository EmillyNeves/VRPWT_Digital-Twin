#!/usr/bin/env python3
"""
get_vitoria_graph.py
Baixa a rede viária de Vitória/ES via OSMnx e os Pontos de Entrega Voluntária
(PEVs) da Coleta Seletiva direto do GIS oficial da PMV (ArcGIS REST), e gera
um grafo de roteamento sobre esses pontos.

Fonte oficial dos pontos:
  https://gis.vitoria.es.gov.br/arcgis/rest/services/Opendata/HubGeoweb/MapServer/14
  (camada "Coleta seletiva de lixo" do mapa público da Prefeitura de Vitória)

Saídas:
  - vitoria.graphml      : grafo viário (NetworkX/OSMnx) em GraphML
  - vitoria.png          : malha viária + PEVs destacados em vermelho
  - pontos_coleta.csv    : tabela com nome, endereço, bairro, lat/lon e id do nó snap
  - roteamento.graphml   : grafo completo entre PEVs com distâncias em metros (Dijkstra)

Dependências: pip install osmnx matplotlib networkx requests
"""

import csv
import os
import time

import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

CITY = "Vitória, Espírito Santo, Brasil"

# Bounding box aproximado de Vitória/ES (oeste, sul, leste, norte)
NORTH, SOUTH, EAST, WEST = -20.24, -20.34, -40.27, -40.37
BBOX = (WEST, SOUTH, EAST, NORTH)

# Endpoint oficial: layer 14 = "Coleta seletiva de lixo"
PMV_URL = (
    "https://gis.vitoria.es.gov.br/arcgis/rest/services/"
    "Opendata/HubGeoweb/MapServer/14/query"
)

ox.settings.requests_timeout = 600
ox.settings.log_console = True


def http_session(total_retries: int = 5) -> requests.Session:
    """Sessão requests com retry exponencial para falhas de rede transitórias."""
    s = requests.Session()
    retry = Retry(
        total=total_retries, connect=total_retries, read=total_retries,
        backoff_factor=2.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


# 1) Rede viária (reaproveita vitoria.graphml se existir) ----------------
GRAPHML = "vitoria.graphml"
if os.path.exists(GRAPHML):
    print(f"[osmnx] reaproveitando {GRAPHML} existente...")
    G = ox.load_graphml(GRAPHML)
else:
    last_err = None
    for tentativa in range(1, 4):
        try:
            print(f"[osmnx] baixando rede 'drive' de '{CITY}' (tentativa {tentativa})...")
            G = ox.graph_from_bbox(bbox=BBOX, network_type="drive")
            ox.save_graphml(G, GRAPHML)
            break
        except Exception as e:
            last_err = e
            print(f"[osmnx] falha: {e}; aguardando {30 * tentativa}s...")
            time.sleep(30 * tentativa)
    else:
        raise SystemExit(f"OSMnx falhou após retries: {last_err}")
print(f"[osmnx] grafo: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")


# 2) PEVs oficiais da PMV ------------------------------------------------
print("[pmv] consultando PEVs da Coleta Seletiva (ArcGIS REST)...")
params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "true",
    "f": "geojson",
}
sess = http_session()
headers = {"User-Agent": "Mozilla/5.0 (compatible; coleta-vitoria/1.0)"}
r = sess.get(PMV_URL, params=params, timeout=60, headers=headers)
r.raise_for_status()
geo = r.json()
features = geo.get("features", [])
print(f"[pmv] PEVs recebidos: {len(features)}")
if not features:
    raise SystemExit("Nenhum PEV retornado pelo serviço da PMV.")

# Conexão para a maior componente fortemente conexa (o grafo direcionado das ruas
# pode não ser fortemente conexo na borda do bbox — PEVs nessas regiões podem
# ficar isolados na matriz de distâncias).
Gc = ox.routing.utils_graph if False else None  # placeholder para legibilidade
largest_scc = max(nx.strongly_connected_components(G), key=len)
G_strong = G.subgraph(largest_scc).copy()
print(f"[osmnx] componente fortemente conexa: {G_strong.number_of_nodes()} nós")


# 3) Snap dos PEVs ao nó mais próximo da rede ---------------------------
xs, ys, attrs = [], [], []
for feat in features:
    lon, lat = feat["geometry"]["coordinates"]
    xs.append(lon)
    ys.append(lat)
    p = feat["properties"]
    attrs.append({
        "objectid": p.get("objectid"),
        "nome": p.get("nome", ""),
        "logradouro": p.get("logradouro", ""),
        "numero": p.get("numero", ""),
        "bairro": p.get("bairro", ""),
        "ponto_referencia": p.get("pontoReferencia", ""),
        "lat": lat,
        "lon": lon,
    })

try:
    nearest_nodes = ox.distance.nearest_nodes(G_strong, X=xs, Y=ys)
except ImportError:
    # Fallback brute-force (sem scipy/sklearn): grande círculo nó-a-nó.
    print("[snap] scipy/sklearn não disponíveis; usando busca brute-force...")
    import math
    node_ids = list(G_strong.nodes)
    node_x = [G_strong.nodes[n]["x"] for n in node_ids]
    node_y = [G_strong.nodes[n]["y"] for n in node_ids]

    def haversine(lon1, lat1, lon2, lat2):
        R = 6371000.0
        rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))

    nearest_nodes = []
    for px, py in zip(xs, ys):
        best_i, best_d = 0, float("inf")
        for i, (nx_, ny_) in enumerate(zip(node_x, node_y)):
            d = haversine(px, py, nx_, ny_)
            if d < best_d:
                best_i, best_d = i, d
        nearest_nodes.append(node_ids[best_i])


# 4) CSV dos PEVs --------------------------------------------------------
with open("pontos_coleta.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "idx", "objectid", "nome", "bairro", "logradouro", "numero",
        "ponto_referencia", "lat", "lon", "node_id",
    ])
    for i, a in enumerate(attrs):
        w.writerow([
            i, a["objectid"], a["nome"], a["bairro"], a["logradouro"],
            a["numero"] or "", a["ponto_referencia"], a["lat"], a["lon"],
            nearest_nodes[i],
        ])
print(f"[out] pontos_coleta.csv ({len(attrs)} PEVs)")


# 5) Grafo de roteamento (clique) ---------------------------------------
print("[net] calculando matriz de distâncias por menor caminho (Dijkstra)...")
H = nx.complete_graph(len(nearest_nodes))
H = nx.relabel_nodes(H, {i: f"P{i}" for i in range(len(nearest_nodes))})
for i, n in enumerate(nearest_nodes):
    H.nodes[f"P{i}"].update({
        "x": float(G_strong.nodes[n]["x"]),
        "y": float(G_strong.nodes[n]["y"]),
        "road_node": int(n),
        "nome": attrs[i]["nome"],
        "bairro": attrs[i]["bairro"],
    })

n_pts = len(nearest_nodes)
desconectados = 0
for i in range(n_pts):
    src = nearest_nodes[i]
    lengths = nx.single_source_dijkstra_path_length(G_strong, src, weight="length")
    for j in range(i + 1, n_pts):
        dst = nearest_nodes[j]
        d = lengths.get(dst)
        if d is None:
            H.remove_edge(f"P{i}", f"P{j}")
            desconectados += 1
        else:
            H[f"P{i}"][f"P{j}"]["length_m"] = float(d)

nx.write_graphml(H, "roteamento.graphml")
print(
    f"[out] roteamento.graphml ({H.number_of_nodes()} nós, "
    f"{H.number_of_edges()} arestas; pares desconectados removidos: {desconectados})"
)


# 6) Plot com PEVs destacados -------------------------------------------
print("[plot] gerando vitoria.png...")
fig, ax = ox.plot_graph(
    G, show=False, close=False,
    node_size=0, edge_color="#888", edge_linewidth=0.4, bgcolor="white",
)
ax.scatter(
    xs, ys, s=45, c="red", marker="o", edgecolors="black",
    linewidths=0.6, zorder=5, label=f"PEVs Coleta Seletiva ({len(attrs)})",
)
ax.legend(loc="lower right", fontsize=9)
fig.savefig("vitoria.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("[out] vitoria.png")
