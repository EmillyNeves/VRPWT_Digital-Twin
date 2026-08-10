#!/usr/bin/env python3
"""Comparacao pareada por Wilcoxon + correcao de Holm (substitui o pos-teste de Nemenyi).

MOTIVO. O pos-teste de Nemenyi sobre ranks medios tem uma propriedade indesejada
(Benavoli, Corani & Mangili, 2016): a decisao sobre UM par depende de QUAIS outros
algoritmos estao no conjunto, porque a diferenca critica CD = q_alpha*sqrt(k(k+1)/6N)
cresce com k. Neste estudo isso e decisivo: a I1 tem rank medio exatamente 5,00 (e
dominada em todas as instancias, o que e estrutural, pois o VND parte dela e so
aplica movimentos melhorantes). Retira-la nao altera nenhum rank dos demais, mas
leva CD de 0,815 (k=5) para 0,627 (k=4) — e a diferenca GRASP x Tabu (0,66) muda
de "nao significativa" para "significativa".

O teste de Wilcoxon pareado com correcao de Holm decide cada par sem olhar para os
demais metodos, e por isso nao sofre desse problema.

ENTRADA. Le docs/relatorio-final/tabela_por_instancia.tex — artefato versionado —
de modo que os numeros sao auditaveis a partir do repositorio, sem reexecutar o
solver. Sem dependencias externas (biblioteca padrao apenas).

SAIDA. Friedman (com e sem a I1), ranks medios, CD, matriz de p-valores de Wilcoxon
com Holm, contagem vitoria/derrota/empate e gap medio treino x teste.

Uso:
    python3 experiments/analysis/stats_paired.py
"""
import math
import os
import re
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
TABELA = os.path.join(ROOT, "docs", "relatorio-final", "tabela_por_instancia.tex")
TRAIN = os.path.join(ROOT, "experiments", "config", "train.txt")
TEST = os.path.join(ROOT, "experiments", "config", "test.txt")

ALG = ["I1", "VND", "GRASP", "GRASP-R", "Tabu"]
GAP = 2   # indice da coluna de gap em [veic, custo, gap, iter, tempo]

# q_alpha de Demsar (2006, Tabela 5), alpha=0,05, ja divididos por sqrt(2).
QALPHA = {2: 1.960, 3: 2.343, 4: 2.569, 5: 2.728}


def carregar():
    """tabela_por_instancia.tex -> {instancia: {algoritmo: [veic, custo, gap, iter, tempo]}}"""
    data, cur = defaultdict(dict), None
    for line in open(TABELA, encoding="utf-8"):
        s = line.strip()
        m = re.match(r"\\multirow\{5\}\{\*\}\{([A-Za-z0-9]+)\}", s)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"&\s*(?:\\textbf\{)?([A-Za-z0-9\-]+)\}?\s*&(.*?)\\\\", s)
        if not (m and cur):
            continue
        algo = m.group(1)
        if algo not in ALG:
            continue
        vals = []
        for c in m.group(2).split("&"):
            c = re.sub(r"\\textbf\{|\}", "", c).strip().replace(".", "").replace(",", ".")
            try:
                vals.append(float(c))
            except ValueError:
                vals.append(None)
        if len(vals) >= 5:
            data[cur][algo] = vals
    return data


def _ranks_por_instancia(data, names, algos):
    """Rank por instancia (menor gap = rank 1), media em empates."""
    R = {a: [] for a in algos}
    for n in names:
        order = sorted((data[n][a][GAP], a) for a in algos)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and abs(order[j + 1][0] - order[i][0]) < 1e-9:
                j += 1
            avg = (i + 1 + j + 1) / 2
            for k in range(i, j + 1):
                R[order[k][1]].append(avg)
            i = j + 1
    return R


def friedman(data, names, algos):
    """Estatistica de Friedman com correcao de empates (mesma formula do scipy)."""
    R = _ranks_por_instancia(data, names, algos)
    N, k = len(names), len(algos)
    chi = 12.0 / (k * N * (k + 1)) * sum(sum(R[a]) ** 2 for a in algos) - 3 * N * (k + 1)
    ties = 0
    for i in range(N):
        row = sorted(R[a][i] for a in algos)
        j = 0
        while j < k:
            m = j
            while m + 1 < k and row[m + 1] == row[j]:
                m += 1
            t = m - j + 1
            if t > 1:
                ties += t ** 3 - t
            j = m + 1
    C = 1 - ties / (N * (k ** 3 - k)) if ties else 1.0
    ranks = {a: sum(R[a]) / N for a in algos}
    return chi / C, chi, C, ranks


def cd(k, N):
    """Diferenca critica do pos-teste de Nemenyi."""
    return QALPHA[k] * math.sqrt(k * (k + 1) / (6.0 * N))


def chi2_sf(x, df):
    """P(X > x) para qui-quadrado com df PAR (serie fechada)."""
    if df % 2:
        raise ValueError("apenas df par")
    s, t = 0.0, math.exp(-x / 2)
    for i in range(df // 2):
        if i:
            t *= (x / 2) / i
        s += t
    return s


def wilcoxon(data, names, A, B):
    """Wilcoxon pareado bilateral (aprox. normal, correcoes de empate e continuidade).

    Devolve (p, A_melhor, B_melhor, empates, n_efetivo). Gap menor = melhor.
    """
    diffs = [data[n][A][GAP] - data[n][B][GAP] for n in names]
    nz = [d for d in diffs if abs(d) > 1e-9]
    n = len(nz)
    a_melhor = sum(1 for d in diffs if d < -1e-9)
    b_melhor = sum(1 for d in diffs if d > 1e-9)
    empates = len(diffs) - a_melhor - b_melhor
    if n < 1:
        return None, a_melhor, b_melhor, empates, 0
    order = sorted(range(n), key=lambda i: abs(nz[i]))
    ranks, ties, i = [0.0] * n, 0, 0
    while i < n:
        j = i
        while j + 1 < n and abs(abs(nz[order[j + 1]]) - abs(nz[order[i]])) < 1e-9:
            j += 1
        avg, t = (i + 1 + j + 1) / 2, j - i + 1
        if t > 1:
            ties += t ** 3 - t
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    Wp = sum(ranks[i] for i in range(n) if nz[i] > 0)
    mu = n * (n + 1) / 4.0
    var = n * (n + 1) * (2 * n + 1) / 24.0 - ties / 48.0
    if var <= 0:
        return None, a_melhor, b_melhor, empates, n
    z = (abs(Wp - mu) - 0.5) / math.sqrt(var)
    return math.erfc(z / math.sqrt(2)), a_melhor, b_melhor, empates, n


def holm(pares):
    """Correcao de Holm (step-down) sobre [(rotulo, p)] -> {rotulo: p_ajustado}."""
    s = sorted(pares, key=lambda x: x[1])
    m, out, prev = len(s), {}, 0.0
    for i, (lab, p) in enumerate(s):
        prev = out[lab] = min(1.0, max(prev, (m - i) * p))
    return out


def bloco_pareado(data, names, titulo):
    print("=" * 84)
    print(titulo)
    print("=" * 84)
    pares, det = [], {}
    for i in range(len(ALG)):
        for j in range(i + 1, len(ALG)):
            A, B = ALG[i], ALG[j]
            p, w, l, t, n = wilcoxon(data, names, A, B)
            lab = f"{A} x {B}"
            pares.append((lab, 1.0 if p is None else p))
            det[lab] = (w, l, t, n, p)
    adj = holm(pares)
    print(f"{'par':18s} {'A melhor':>9s} {'B melhor':>9s} {'empate':>7s} "
          f"{'p bruto':>10s} {'p Holm':>10s}  decisao")
    for lab, _ in sorted(pares, key=lambda x: x[1]):
        w, l, t, n, p = det[lab]
        pa = adj[lab]
        if pa >= 0.05:
            dec = "sem evidencia de diferenca"
        else:
            dec = f"{lab.split(' x ')[0 if w > l else 2]} melhor (signif.)"
        print(f"{lab:18s} {w:9d} {l:9d} {t:7d} {p:10.2e} {pa:10.2e}  {dec}")
    print()


def main():
    data = carregar()
    insts = sorted(data)
    faltando = [i for i in insts if len(data[i]) != len(ALG)]
    if faltando:
        raise SystemExit(f"linhas incompletas em: {faltando}")
    train = sorted(l.strip() for l in open(TRAIN) if l.strip())
    test = sorted(l.strip() for l in open(TEST) if l.strip())
    print(f"instancias lidas: {len(insts)}  (treino {len(train)} / teste {len(test)})\n")

    for titulo, names in (("FRIEDMAN — conjunto de TESTE (28), resultado primario", test),
                          ("FRIEDMAN — todas as 56 (inclui as 28 vistas pelo irace)", insts)):
        chi, bruto, C, ranks = friedman(data, names, ALG)
        print("=" * 84)
        print(titulo)
        print("=" * 84)
        print(f"chi2 = {chi:.2f} (sem correcao de empates {bruto:.1f}; C = {C:.4f})  "
              f"p = {chi2_sf(chi, 4):.3g}  CD(k=5) = {cd(5, len(names)):.4f}")
        print("ranks medios:", {a: round(v, 3) for a, v in sorted(ranks.items(), key=lambda x: x[1])})
        print()

    # Sensibilidade da conclusao ao conjunto de algoritmos incluido.
    print("=" * 84)
    print("SENSIBILIDADE DO NEMENYI AO POOL (Benavoli et al., 2016)")
    print("=" * 84)
    _, _, _, r5 = friedman(data, insts, ALG)
    _, _, _, r4 = friedman(data, insts, [a for a in ALG if a != "I1"])
    d = abs(r4["GRASP"] - r4["Tabu"])
    print(f"56 instancias, |rank(GRASP) - rank(Tabu)| = {d:.4f}")
    print(f"  k=5 (com I1):  CD = {cd(5, 56):.4f}  ->  "
          f"{'significativo' if d > cd(5, 56) else 'NAO significativo'}")
    print(f"  k=4 (sem I1):  CD = {cd(4, 56):.4f}  ->  "
          f"{'SIGNIFICATIVO' if d > cd(4, 56) else 'nao significativo'}")
    print("  (os ranks dos demais metodos nao mudam: a I1 e dominada em todas as instancias)\n")

    bloco_pareado(data, test, "WILCOXON + HOLM — conjunto de TESTE (28), resultado PRIMARIO")
    bloco_pareado(data, insts, "WILCOXON + HOLM — todas as 56")

    print("=" * 84)
    print("GAP MEDIO TREINO x TESTE (medida direta de superajuste da calibragem)")
    print("=" * 84)
    print(f"{'algoritmo':10s} {'treino(28)':>11s} {'teste(28)':>10s} {'diferenca':>10s}")
    for a in ALG:
        gtr = sum(data[n][a][GAP] for n in train) / len(train)
        gte = sum(data[n][a][GAP] for n in test) / len(test)
        print(f"{a:10s} {gtr:11.3f} {gte:10.3f} {gte - gtr:+10.3f}")


if __name__ == "__main__":
    main()
