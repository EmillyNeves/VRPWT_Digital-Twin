#!/usr/bin/env python3
"""IoT bin-fill simulation (sensor layer of the Digital Twin).

Following the subproject proposal, bin filling is modeled as a NON-HOMOGENEOUS
POISSON PROCESS: at each monitoring cycle, the number of "garbage arrivals" at a
bin is Poisson-distributed with a rate lambda(t) that varies over the day (two
daily peaks) and scales by a per-bin propensity. The fill level rises with the
arrivals (each contributes a fraction of the bin capacity); a bin overflows if it
reaches 1.0 before being collected (a tracked KPI). Collecting resets it to 0.
"""
import math
import numpy as np


class FillSimulator:
    def __init__(self, n_bins, threshold=0.7, cycles_per_day=8,
                 lam_peak=4.0, lam_off=0.8, capacity_arrivals=12, seed=0):
        self.threshold = threshold
        self.cycles_per_day = cycles_per_day
        self.lam_peak = lam_peak
        self.lam_off = lam_off
        self.cap = capacity_arrivals
        self.rng = np.random.default_rng(seed)
        self.fill = self.rng.uniform(0.0, 0.30, n_bins)
        self.propensity = self.rng.uniform(0.5, 1.5, n_bins)   # heterogeneous bins
        self.overflow_events = 0
        # Estado de transbordo por lixeira: um EPISODIO conta uma unica vez,
        # quando f atinge 1 antes da coleta (definicao do relatorio); a lixeira
        # so volta a poder transbordar depois de coletada.
        self.overflowing = np.zeros(n_bins, dtype=bool)

    def rate(self, cycle):
        """Non-homogeneous Poisson intensity lambda(t): two Gaussian peaks per day."""
        h = cycle % self.cycles_per_day
        peaks = math.exp(-((h - 1.5) / 1.0) ** 2) + math.exp(-((h - 5.5) / 1.0) ** 2)
        return self.lam_off + (self.lam_peak - self.lam_off) * min(1.0, peaks)

    def is_peak(self, cycle):
        return self.rate(cycle) >= (self.lam_off + self.lam_peak) / 2.0

    def period_label(self, cycle):
        return "pico" if self.is_peak(cycle) else "fora"

    def step(self, cycle):
        lam = self.rate(cycle)
        arrivals = self.rng.poisson(lam * self.propensity)      # NHPP arrivals per bin
        new_fill = self.fill + arrivals / self.cap
        # Episodio de transbordo: a lixeira ATINGE a capacidade agora e ainda
        # nao estava transbordando (nao recontar a mesma lixeira cheia a cada
        # ciclo; ela so reconta apos ser coletada).
        newly_full = (new_fill >= 1.0 - 1e-9) & ~self.overflowing
        self.overflow_events += int(np.sum(newly_full))
        self.overflowing |= newly_full
        self.fill = np.minimum(new_fill, 1.0)

    def active(self):
        return [i for i in range(len(self.fill)) if self.fill[i] >= self.threshold]

    def full_bins(self):
        """Bins at (or above) capacity right now = overflowing (transbordando)."""
        return [i for i in range(len(self.fill)) if self.fill[i] >= 1.0 - 1e-9]

    def collect(self, idxs):
        for i in idxs:
            self.fill[i] = 0.0
            self.overflowing[i] = False
