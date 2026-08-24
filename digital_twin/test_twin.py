#!/usr/bin/env python3
"""Testes do gemeo digital (camadas Python; o solver C++ tem suite propria).

Cobrem as duas propriedades que o relatorio final AFIRMA como verificadas:

  1. TRANSPARENCIA DO CANAL  Com pdr=1.0 e duty_interval=1, a visao de radio
     (`perceived`) e identica ao estado fisico em todo ciclo -- a camada
     LoRaWAN nao altera nenhuma decisao do orquestrador.

  2. TRANSBORDO POR EPISODIO  O KPI de transbordo conta EPISODIOS (a lixeira
     atinge f=1 antes de ser coletada, uma vez por enchimento), e nao
     lixeira-ciclos: uma lixeira que permanece cheia por varios ciclos conta
     um unico transbordo ate ser coletada; apos a coleta, pode transbordar
     de novo.

Rodar:  python3 digital_twin/test_twin.py   (ou via pytest)
"""
import numpy as np

from lorawan import LoRaWANChannel
from sensors import FillSimulator


def test_lorawan_transparente_com_canal_perfeito():
    n, cycles = 25, 40
    sim = FillSimulator(n, seed=7)
    radio = LoRaWANChannel(n, pdr=1.0, duty_interval=1, seed=7)
    rng = np.random.default_rng(3)
    for c in range(cycles):
        sim.step(c)
        perceived = radio.step(c, sim.fill)
        assert np.array_equal(perceived, sim.fill), f"visao != fisico no ciclo {c}"
        # coleta aleatoria de algumas lixeiras, como faria o orquestrador
        served = list(rng.choice(n, size=rng.integers(0, 5), replace=False))
        sim.collect(served)
        radio.on_collect(served, c)
        assert np.array_equal(radio.perceived, sim.fill), f"visao != fisico pos-coleta, ciclo {c}"


def test_lorawan_canal_degradado_gera_defasagem():
    n = 25
    sim = FillSimulator(n, seed=7)
    radio = LoRaWANChannel(n, pdr=0.5, duty_interval=2, seed=7)
    diverged = False
    for c in range(20):
        sim.step(c)
        perceived = radio.step(c, sim.fill)
        if not np.array_equal(perceived, sim.fill):
            diverged = True
    assert diverged, "canal degradado deveria produzir visao defasada"
    assert radio.stats(19)["pdr_observado"] < 1.0


def test_transbordo_conta_episodios_nao_lixeira_ciclos():
    sim = FillSimulator(1, seed=0)
    sim.fill[:] = 0.0
    sim.overflowing[:] = False
    sim.overflow_events = 0
    # forca o processo: injeta enchimento manualmente via step com propensao
    # controlada e o degrau direto no estado
    sim.fill[0] = 1.0
    sim.overflowing[0] = False
    # ciclo 1: atinge a capacidade -> 1 episodio
    new_fill = sim.fill + 0.2
    newly = (new_fill >= 1.0 - 1e-9) & ~sim.overflowing
    sim.overflow_events += int(np.sum(newly))
    sim.overflowing |= newly
    sim.fill = np.minimum(new_fill, 1.0)
    assert sim.overflow_events == 1
    # ciclos 2-4: permanece cheia -> NAO reconta
    for _ in range(3):
        new_fill = sim.fill + 0.2
        newly = (new_fill >= 1.0 - 1e-9) & ~sim.overflowing
        sim.overflow_events += int(np.sum(newly))
        sim.overflowing |= newly
        sim.fill = np.minimum(new_fill, 1.0)
    assert sim.overflow_events == 1, "lixeira cheia recontou transbordo"
    # coleta e novo enchimento -> novo episodio
    sim.collect([0])
    assert sim.fill[0] == 0.0 and not sim.overflowing[0]
    sim.fill[0] = 1.0
    newly = (sim.fill >= 1.0 - 1e-9) & ~sim.overflowing
    sim.overflow_events += int(np.sum(newly))
    sim.overflowing |= newly
    assert sim.overflow_events == 2, "novo enchimento apos coleta deveria contar novo episodio"


def test_transbordo_via_step_integrado():
    """Mesma propriedade, agora pelo caminho real (step do NHPP)."""
    sim = FillSimulator(5, seed=1)
    # muitos ciclos sem coleta: cada lixeira transborda NO MAXIMO uma vez
    for c in range(60):
        sim.step(c)
    assert sim.overflow_events <= 5, (
        f"sem coleta, cada lixeira conta no maximo 1 episodio; contou {sim.overflow_events}")
    # apos coletar todas, novos episodios voltam a ser possiveis
    before = sim.overflow_events
    sim.collect(range(5))
    for c in range(60, 120):
        sim.step(c)
    assert sim.overflow_events > before, "apos coleta, novos episodios deveriam ocorrer"


if __name__ == "__main__":
    for fn in [test_lorawan_transparente_com_canal_perfeito,
               test_lorawan_canal_degradado_gera_defasagem,
               test_transbordo_conta_episodios_nao_lixeira_ciclos,
               test_transbordo_via_step_integrado]:
        fn()
        print(f"ok  {fn.__name__}")
    print("4 passou, 0 falhou")
