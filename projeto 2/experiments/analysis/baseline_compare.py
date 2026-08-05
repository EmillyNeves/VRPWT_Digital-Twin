#!/usr/bin/env python3
"""Caracteriza e compara as DUAS referências de baseline das instâncias Solomon-100.

  - ``solution (Dinamics)/``  : referência de **mínima distância** (critério DIMACS,
    o mesmo que o solver otimiza). Cada .sol traz "Route #k: ..." e uma linha "Cost".
  - ``sintef_solutions_100/`` : melhor-conhecido **lexicográfico** de Solomon
    (veículos -> distância). Cada .txt traz "Route k : ..." e NÃO traz custo.

Para cada instância, recomputamos distância e número de veículos das DUAS referências
com a mesma convenção do solver (euclidiana **truncada** a 1 casa por aresta; tempo de
viagem = distância; espera até abrir a janela; serviço soma; janela e capacidade
verificadas; retorno ao depósito dentro do horizonte). O objetivo é documentar, de forma
auditável, que:
  * Dinamics minimiza DISTÂNCIA (menor dist, geralmente MAIS veículos);
  * SINTEF minimiza VEÍCULOS (menos veículos, geralmente MAIOR dist),
o que justifica usar Dinamics como baseline do gap de distância (DIMACS) e reportar
SINTEF na visão lexicográfica complementar (veículos -> distância).

Saída: results/baseline_compare.csv + um resumo no stdout.
"""
import csv
import math
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
INPUT_DIR = os.path.join(ROOT, "input")
DINAMICS_DIR = os.path.join(ROOT, "solution (Dinamics)")
SINTEF_DIR = os.path.join(ROOT, "sintef_solutions_100")
OUT_CSV = os.path.join(ROOT, "results", "baseline_compare.csv")

EPS = 1e-6


def trunc1(v):
    return math.trunc(v * 10.0) / 10.0


def parse_instance(path):
    """Lê uma instância Solomon. Retorna (nodes, capacity) onde nodes[i] =
    (x, y, demand, ready, due, service); nodes[0] é o depósito."""
    nodes, capacity, section = {}, None, None
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            t = line.split()
            if not t:
                continue
            head = t[0].upper()
            if head == "VEHICLE":
                section = "veh"; continue
            if head == "CUSTOMER":
                section = "cust"; continue
            if section == "veh" and len(t) >= 2 and t[0].isdigit():
                capacity = float(t[1])              # "NUMBER  CAPACITY"
                section = None
            elif section == "cust" and t[0].lstrip("-").isdigit() and len(t) >= 7:
                i = int(t[0])
                nodes[i] = tuple(float(x) for x in t[1:7])  # x y demand ready due service
    return nodes, capacity


def parse_routes(path):
    """Lê um arquivo de rotas (formato Dinamics 'Route #k: ...' ou SINTEF
    'Route k : ...'). Retorna (routes, cost_declarado_ou_None)."""
    routes, cost = [], None
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            low = s.lower()
            if low.startswith("route"):
                nums = re.findall(r"\d+", s.split(":", 1)[1] if ":" in s else s)
                # remove um eventual índice de rota antes do ':' já tratado pelo split
                seq = [int(x) for x in nums]
                if seq:
                    routes.append(seq)
            elif low.startswith("cost"):
                m = re.search(r"[-+]?\d+\.?\d*", s)
                cost = float(m.group()) if m else None
    return routes, cost


def eval_routes(nodes, capacity, routes):
    """Distância (truncada), nº de veículos e viabilidade das rotas."""
    depot = nodes[0]
    horizon = depot[4]
    total_dist, vehicles, feasible, viol = 0.0, 0, True, []
    seen = set()
    for r in routes:
        if not r:
            continue
        vehicles += 1
        t, load, prev = 0.0, 0.0, 0
        for c in r:
            seen.add(c)
            x, y, dem, ready, due, serv = nodes[c]
            leg = trunc1(math.hypot(nodes[prev][0] - x, nodes[prev][1] - y))
            total_dist += leg
            t += leg
            if t < ready:
                t = ready
            if t > due + EPS:
                feasible = False; viol.append(f"janela c{c}")
            t += serv
            load += dem
            prev = c
        leg = trunc1(math.hypot(nodes[prev][0] - depot[0], nodes[prev][1] - depot[1]))
        total_dist += leg
        t += leg
        if t > horizon + EPS:
            feasible = False; viol.append("retorno")
        if load > capacity + EPS:
            feasible = False; viol.append(f"capacidade {load}")
    n_cust = len(nodes) - 1
    if len(seen) != n_cust:
        feasible = False; viol.append(f"cobertura {len(seen)}/{n_cust}")
    return round(total_dist, 1), vehicles, feasible, viol


def family_type(name):
    m = re.match(r"([A-Za-z]+)(\d)", name)
    return (m.group(1).upper(), int(m.group(2))) if m else ("?", 0)


def main():
    names = sorted(os.path.splitext(f)[0] for f in os.listdir(INPUT_DIR) if f.endswith(".txt"))
    rows = []
    for name in names:
        nodes, cap = parse_instance(os.path.join(INPUT_DIR, name + ".txt"))
        fam, typ = family_type(name)
        din_path = os.path.join(DINAMICS_DIR, name + ".sol")
        sin_path = os.path.join(SINTEF_DIR, name.lower() + ".txt")
        row = {"instance": name, "family": fam, "type": typ}
        if os.path.isfile(din_path):
            r, c = parse_routes(din_path)
            d_dist, d_veh, d_feas, _ = eval_routes(nodes, cap, r)
            row.update(din_dist=d_dist, din_veh=d_veh, din_feasible=int(d_feas),
                       din_cost_declared=c)
        if os.path.isfile(sin_path):
            r, _ = parse_routes(sin_path)
            s_dist, s_veh, s_feas, _ = eval_routes(nodes, cap, r)
            row.update(sin_dist=s_dist, sin_veh=s_veh, sin_feasible=int(s_feas))
        rows.append(row)

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    cols = ["instance", "family", "type", "din_dist", "din_veh", "din_cost_declared",
            "din_feasible", "sin_dist", "sin_veh", "sin_feasible"]
    with open(OUT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})

    # ---- resumo auditável ----
    both = [r for r in rows if "din_dist" in r and "sin_dist" in r]
    din_lower = sum(1 for r in both if r["din_dist"] < r["sin_dist"] - 1e-9)
    sin_lower = sum(1 for r in both if r["sin_dist"] < r["din_dist"] - 1e-9)
    equal = sum(1 for r in both if abs(r["din_dist"] - r["sin_dist"]) <= 1e-9)
    din_morev = sum(1 for r in both if r["din_veh"] > r["sin_veh"])
    cost_mismatch = [r["instance"] for r in rows
                     if r.get("din_cost_declared") not in (None, "")
                     and abs(r["din_dist"] - r["din_cost_declared"]) > 0.05]
    print(f"instancias com ambas refs: {len(both)}")
    print(f"  Dinamics dist MENOR que SINTEF : {din_lower}/{len(both)}")
    print(f"  SINTEF   dist MENOR que Dinamics: {sin_lower}/{len(both)}")
    print(f"  empatadas em distancia          : {equal}/{len(both)}")
    print(f"  Dinamics usa MAIS veiculos      : {din_morev}/{len(both)}")
    print(f"  recomputo bate a 'Cost' declarada do Dinamics: "
          f"{len(rows) - len(cost_mismatch)}/{len(rows)} (mismatch: {cost_mismatch})")
    print(f"\nCSV: {OUT_CSV}")
    # amostra
    print("\n  inst    din(dist/veh)   sin(dist/veh)")
    for r in [x for x in both if x["instance"] in
              ("C101", "R101", "R112", "R201", "RC205", "C201", "R211", "RC108")]:
        print(f"  {r['instance']:6s} {r['din_dist']:8.1f}/{r['din_veh']:<3d}  "
              f"{r['sin_dist']:8.1f}/{r['sin_veh']:<3d}")


if __name__ == "__main__":
    main()
