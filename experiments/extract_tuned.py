#!/usr/bin/env python3
"""Read the irace logs and emit tuned.json = {algo: "--switch val ..."}.

Parses the 'Best configurations as commandlines' section of each algorithm's
irace log and keeps the top configuration's parameter switches.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ALGOS = ["grasp", "rgrasp", "tabu"]


def best_cmdline(log_path):
    lines = open(log_path, encoding="utf-8", errors="ignore").read().splitlines()
    for i, l in enumerate(lines):
        if "as commandlines" in l:
            for j in range(i + 1, len(lines)):
                s = lines[j].strip()
                if not s or s.startswith("#"):
                    continue
                parts = s.split()
                return " ".join(parts[1:])   # drop the leading config ID
    return ""


def main():
    # K (orçamento declarado), anexado aos parâmetros de qualidade calibrados pelo irace
    fixedK = {}
    fk = os.path.join(HERE, "config", "fixed_K.json")
    if os.path.isfile(fk):
        fixedK = json.load(open(fk))
    out = {}
    for algo in ALGOS:
        log = os.path.join(HERE, "..", "results", "irace", algo, "irace.log")
        if os.path.isfile(log):
            cmd = best_cmdline(log)
            if cmd:
                if algo in fixedK:
                    cmd = f"{cmd} --max-no-improve {fixedK[algo]}".strip()
                out[algo] = cmd
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
