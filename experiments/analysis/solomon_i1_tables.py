#!/usr/bin/env python3
"""Verificação de fidelidade da I1 contra Solomon (1987), Tabelas I-VI.

Roda as OITO configurações que Solomon publica (p.259) em cada instância e em
cada convenção numérica, agrega pelo critério lexicográfico do próprio artigo
(veículos -> schedule -> distância -> espera) e confronta com as médias por
conjunto de problemas das Tabelas I-VI.

    (mu, lambda, alpha1, alpha2) in {(1,1,1,0), (1,2,1,0), (1,1,0,1), (1,2,0,1)}
      x  semente in {mais distante do depósito, prazo mais cedo}

Saídas (versionadas, é delas que sai toda tabela do relatório):
  results/solomon-i1/i1_configs.csv   uma linha por (instância, config, convenção)
  results/solomon-i1/tables_I_VI.csv  o confronto por conjunto de problemas

Uso:
  python3 experiments/analysis/solomon_i1_tables.py [--sensitivity FLAG ...]

Sensibilidades disponíveis (ver docs/verificacao/01-solomon-i1.md):
  --i1-tiebreak-c11        S1  desempate de c1 por c11
  --i1-c12-zero-at-end     S5  c12 = 0 na última posição da rota
  --i1-seed-tie-farthest   S3  empate no prazo resolvido pelo mais distante
"""
import argparse
import csv
import os
import subprocess
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
SOLVER = os.path.join(_ROOT, "solver", "build", "solve")
INPUT = os.path.join(_ROOT, "data", "instances", "solomon")
OUTDIR = os.path.join(_ROOT, "results", "solomon-i1")

COLS = ["instance", "set", "dist_mode", "mu", "lambda", "alpha1", "alpha2", "seed_rule",
        "tiebreak", "vehicles", "schedule_time", "distance", "waiting_time",
        "service_time", "cpu_ms", "feasible"]

# As oito configurações do artigo (p.259).
CONFIGS = [(1, lam, a1, 1 - a1, seed)
           for a1 in (1, 0) for lam in (1, 2) for seed in ("far", "deadline")]

# Tabelas I-VI: (veículos médios, distância média, espera média).
SOLOMON = {"R1": (13.6, 1436.7, 258.8), "C1": (10.0, 951.9, 152.3),
           "RC1": (13.5, 1596.5, 178.5), "R2": (3.3, 1402.4, 175.6),
           "C2": (3.1, 692.7, 228.6), "RC2": (3.9, 1682.1, 273.2)}
# Nº de instâncias por conjunto. Como a média publicada é arredondada a 1 casa e
# n é inteiro, o TOTAL de veículos de Solomon é reconstruível sem ambiguidade.
NINST = {"R1": 12, "C1": 9, "RC1": 8, "R2": 11, "C2": 8, "RC2": 8}


def solomon_vehicle_total(pset):
    """Único inteiro compatível com a média publicada arredondada a 1 casa."""
    mean, n = SOLOMON[pset][0], NINST[pset]
    cands = [t for t in range(n, 30 * n) if abs(t / n - mean) <= 0.05 + 1e-12]
    if len(cands) != 1:
        raise RuntimeError(f"{pset}: total de veículos ambíguo {cands}")
    return cands[0]


def run_all(extra_flags):
    """Executa 56 x 8 x 2 e devolve as linhas do CSV."""
    names = sorted(os.path.splitext(f)[0] for f in os.listdir(INPUT) if f.endswith(".txt"))
    rows = []
    for name in names:
        for mode in ("trunc", "double"):
            for mu, lam, a1, a2, seed in CONFIGS:
                cmd = [SOLVER, "--algo", "i1",
                       "--instance", os.path.join(INPUT, name + ".txt"),
                       "--dist-mode", mode,
                       "--i1-mu", str(mu), "--i1-lambda", str(lam),
                       "--i1-alpha1", str(a1), "--i1-alpha2", str(a2),
                       "--i1-seed", seed, "--csv-solomon"] + extra_flags
                out = subprocess.run(cmd, capture_output=True, text=True)
                line = out.stdout.strip()
                if not line:
                    sys.stderr.write(f"[ERRO] sem saida: {name} {mode} {cmd}\n{out.stderr}\n")
                    continue
                rows.append(line.split(","))
        print(f"  {name}", end="\r", flush=True)
    print(" " * 20, end="\r")
    return rows


def lexkey(r):
    """Ordem lexicográfica de Solomon (p.259), com os contínuos a 2 casas."""
    return (int(r["vehicles"]), round(float(r["schedule_time"]), 2),
            round(float(r["distance"]), 2), round(float(r["waiting_time"]), 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sensitivity", action="append", default=[],
                    help="flag de sensibilidade repassada ao solver (pode repetir)")
    args = ap.parse_args()

    if not os.access(SOLVER, os.X_OK):
        sys.exit(f"solver nao compilado: {SOLVER}\nrode: make -C solver")
    os.makedirs(OUTDIR, exist_ok=True)

    print(f"executando 56 instancias x {len(CONFIGS)} configs x 2 convencoes"
          + (f"  [{' '.join(args.sensitivity)}]" if args.sensitivity else ""))
    rows = run_all(args.sensitivity)

    cfg_path = os.path.join(OUTDIR, "i1_configs.csv")
    with open(cfg_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(rows)
    print(f"{len(rows)} execucoes -> {cfg_path}")

    recs = [dict(zip(COLS, r)) for r in rows]
    if any(r["feasible"] != "1" for r in recs):
        sys.exit("ERRO: ha solucoes inviaveis; a verificacao nao pode prosseguir")

    # duas agregações do MESMO CSV, deliberadamente separadas:
    #   I1-Solomon  seleção lexicográfica (o critério dele) -> confronto Tabelas I-VI
    #   I1-DIMACS   seleção por menor distância (o nosso)   -> baseline do estudo
    out_rows = []
    for mode in ("trunc", "double"):
        by_inst = defaultdict(list)
        for r in recs:
            if r["dist_mode"] == mode:
                by_inst[r["instance"]].append(r)
        best_lex = {i: min(v, key=lexkey) for i, v in by_inst.items()}
        best_dist = {i: min(v, key=lambda r: float(r["distance"])) for i, v in by_inst.items()}

        for pset in ("R1", "C1", "RC1", "R2", "C2", "RC2"):
            lex_v = [r for r in best_lex.values() if r["set"] == pset]
            dis_v = [r for r in best_dist.values() if r["set"] == pset]
            n = len(lex_v)
            assert n == NINST[pset], f"{pset}: {n} instancias, esperado {NINST[pset]}"

            def mean(v, f):
                return sum(f(r) for r in v) / len(v)

            k_ours = sum(int(r["vehicles"]) for r in lex_v)
            k_sol = solomon_vehicle_total(pset)
            d_ours = mean(lex_v, lambda r: float(r["distance"]))
            w_ours = mean(lex_v, lambda r: float(r["waiting_time"]))
            _, d_sol, w_sol = SOLOMON[pset]
            var_ours, var_sol = d_ours + w_ours, d_sol + w_sol

            out_rows.append({
                "dist_mode": mode, "set": pset, "n": n,
                "vehicles_total_ours": k_ours, "vehicles_total_solomon": k_sol,
                "vehicles_diff": k_ours - k_sol,
                "distance_ours": round(d_ours, 2), "distance_solomon": d_sol,
                "waiting_ours": round(w_ours, 2), "waiting_solomon": w_sol,
                "variable_ours": round(var_ours, 2), "variable_solomon": round(var_sol, 2),
                "variable_dev_pct": round((var_ours - var_sol) / var_sol * 100, 2),
                # a agregação alternativa, para o estudo (não entra no confronto)
                "dimacs_distance_ours": round(mean(dis_v, lambda r: float(r["distance"])), 2),
                "dimacs_vehicles_total": sum(int(r["vehicles"]) for r in dis_v),
            })

    tab_path = os.path.join(OUTDIR, "tables_I_VI.csv")
    with open(tab_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)
    print(f"confronto -> {tab_path}\n")

    # ---- relato -------------------------------------------------------------
    # O critério PRIMÁRIO é o total INTEIRO de veículos: é a primeira chave
    # lexicográfica de Solomon e não precisa de tolerância. A parte variável
    # (distância + espera) é descritiva e vem confundida pela diferença de
    # veículos, por isso não é usada como aprovação/reprovação.
    for mode in ("trunc", "double"):
        sel = [r for r in out_rows if r["dist_mode"] == mode]
        tot_o = sum(r["vehicles_total_ours"] for r in sel)
        tot_s = sum(r["vehicles_total_solomon"] for r in sel)
        print(f"--- convencao {mode} ---")
        print(f"{'conj':5} {'veiculos':>16} {'dist+espera':>22} {'desvio':>8}")
        for r in sel:
            vk = f"{r['vehicles_total_ours']} vs {r['vehicles_total_solomon']}"
            vv = f"{r['variable_ours']:.1f} vs {r['variable_solomon']:.1f}"
            print(f"{r['set']:5} {vk:>16} {vv:>22} {r['variable_dev_pct']:+7.2f}%")
        print(f"{'TOTAL':5} {f'{tot_o} vs {tot_s}':>16}"
              f"   ({tot_o - tot_s:+d} veiculos em {sum(NINST.values())} instancias)\n")


if __name__ == "__main__":
    main()
