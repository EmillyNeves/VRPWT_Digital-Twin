#!/usr/bin/env python3
"""Camada de comunicacao LoRaWAN (simulada) entre os sensores e o orquestrador.

O Quadro 1 do relatorio parcial preve comunicacao LoRaWAN no gemeo digital. O
essencial dessa tecnologia, na granularidade de um ciclo de monitoramento, sao
tres efeitos, e sao eles que este modulo modela:

  PERDA DE PACOTE   Um uplink LoRaWAN nao confirmado pode se perder (colisao,
                    alcance, interferencia). Modelada como Bernoulli por uplink
                    com taxa de entrega `pdr` (packet delivery ratio). Um pacote
                    perdido NAO e retransmitido -- classe A sem confirmacao, o
                    modo tipico de sensores de lixeira alimentados por bateria.

  CICLO DE DUTY     A banda ISM de 868/915 MHz limita o tempo de ar de cada
                    dispositivo (~1% na regiao EU868). Na pratica isso limita a
                    FREQUENCIA de transmissao: o sensor so transmite a cada
                    `duty_interval` ciclos (1 = todo ciclo). Entre transmissoes
                    o controlador fica com a ultima leitura recebida.

  LATENCIA          O atraso fim-a-fim de um uplink (segundos) e desprezivel
                    frente a um ciclo de monitoramento (horas). O efeito real de
                    latencia nessa escala e a DEFASAGEM: a leitura usada pelo
                    controlador tem a idade de quando foi transmitida, nao de
                    agora. O modulo mede essa idade (staleness) por lixeira.

Consequencia observavel: o controlador decide com a "visao de radio" do estado
das lixeiras -- `perceived` -- que pode estar defasada. Uma lixeira que cruzou o
limiar mas teve o uplink perdido so entra na rota quando um uplink futuro chegar,
e o transbordo que ocorrer nesse intervalo e atribuivel a comunicacao. Com
pdr=1.0 e duty_interval=1 o canal e transparente e o gemeo se comporta exatamente
como sem esta camada (propriedade verificada em teste).
"""
import numpy as np


class LoRaWANChannel:
    def __init__(self, n_bins, pdr=0.98, duty_interval=1, seed=0):
        if not (0.0 <= pdr <= 1.0):
            raise ValueError("pdr deve estar em [0,1]")
        if duty_interval < 1:
            raise ValueError("duty_interval minimo e 1 (transmite todo ciclo)")
        self.pdr = float(pdr)
        self.duty = int(duty_interval)
        self.rng = np.random.default_rng(seed)
        # visao do controlador: ultima leitura RECEBIDA e o ciclo em que ela foi gerada
        self.perceived = np.zeros(n_bins)
        self.last_rx_cycle = np.full(n_bins, -1)
        # desloca a janela de duty de cada sensor para nao sincronizar a rede toda
        self.phase = self.rng.integers(0, self.duty, n_bins)
        self.sent = 0
        self.delivered = 0

    def step(self, cycle, true_fill):
        """Transmite as leituras do ciclo e devolve a visao do controlador."""
        for i in range(len(true_fill)):
            if (cycle + self.phase[i]) % self.duty != 0:
                continue                              # janela de duty fechada
            self.sent += 1
            if self.rng.random() < self.pdr:
                self.delivered += 1
                self.perceived[i] = true_fill[i]
                self.last_rx_cycle[i] = cycle
        return self.perceived

    def on_collect(self, idxs, cycle):
        """A coleta e observada em campo pelo proprio caminhao: o controlador
        sabe que esvaziou, independentemente de radio."""
        for i in idxs:
            self.perceived[i] = 0.0
            self.last_rx_cycle[i] = cycle

    def staleness(self, cycle):
        """Idade media, em ciclos, da leitura que o controlador esta usando."""
        seen = self.last_rx_cycle >= 0
        if not np.any(seen):
            return float(cycle + 1)
        return float(np.mean(cycle - self.last_rx_cycle[seen]))

    def stats(self, cycle):
        return {"uplinks_enviados": self.sent,
                "uplinks_entregues": self.delivered,
                "pdr_observado": round(self.delivered / self.sent, 4) if self.sent else 1.0,
                "defasagem_media_ciclos": round(self.staleness(cycle), 3)}
