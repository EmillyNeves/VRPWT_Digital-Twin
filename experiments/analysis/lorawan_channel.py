"""Efeito do canal LoRaWAN no servico (Secao 5.1 do relatorio) -- com artefato.

Reexecuta o experimento citado na prosa (mapa R101, 12 ciclos, VND como
roteador): canal PERFEITO (pdr=1.0, transmissao a cada ciclo) contra canal
DEGRADADO (pdr=0.9, transmissao a cada 2 ciclos), mesma realizacao de
enchimento. Grava results/digital_twin/lorawan_channel.csv -- nenhum numero
copiado a mao para o texto (regra de ouro do PLANO-RELATORIO-FINAL).

Transbordos contados por EPISODIO (sensors.py), a definicao do relatorio.
"""
import csv
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "digital_twin"))
os.environ.setdefault("VRPTW_SOLVER", os.path.join(ROOT, "solver", "build", "solve"))

from twin import simulate, kpis, load_map             # noqa: E402

OUT = os.path.join(ROOT, "results", "digital_twin")
CYCLES = 12
ALGO = "vnd"
CENARIOS = [("perfeito", 1.0, 1), ("degradado", 0.9, 2)]


def main():
    cmap = load_map("solomon", "R101")
    linhas = []
    for nome, pdr, duty in CENARIOS:
        hist = simulate(cmap, cycles=CYCLES, algo=ALGO, seed=0, pdr=pdr, duty_interval=duty)
        k = kpis(hist)
        lw = k.get("lorawan", {})
        linhas.append({"cenario": nome, "pdr": pdr, "duty_interval": duty,
                       "transbordos": k["transbordos"], "coletas": k["coletas"],
                       "distancia": k["distancia_total"],
                       "defasagem_media_ciclos": lw.get("defasagem_media_ciclos", 0.0),
                       "pdr_observado": lw.get("pdr_observado", 1.0)})

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "lorawan_channel.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    print("-> results/digital_twin/lorawan_channel.csv")
    for r in linhas:
        print(f"  {r['cenario']:10s} pdr={r['pdr']} duty={r['duty_interval']}: "
              f"{r['transbordos']} transbordos, defasagem {r['defasagem_media_ciclos']} ciclos")


if __name__ == "__main__":
    sys.exit(main())
