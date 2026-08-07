#!/usr/bin/env python3
"""Stratified train/test split of the 56 Solomon instances.

Splits within each stratum (family x type: C1, C2, R1, R2, RC1, RC2) so both
sets cover every stratum. Reproducible via a fixed seed. irace tunes on train;
all reported results are computed on test.
"""
import argparse
import os
import random
import re
from collections import defaultdict


def stratum(name):
    m = re.match(r"([A-Za-z]+)(\d)", name)
    return f"{m.group(1).upper()}{m.group(2)}" if m else "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances-dir", default="../data/instances/solomon")
    ap.add_argument("--train-frac", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--train-out", default="config/train.txt")
    ap.add_argument("--test-out", default="config/test.txt")
    args = ap.parse_args()

    names = sorted(os.path.splitext(f)[0] for f in os.listdir(args.instances_dir)
                   if f.endswith(".txt"))
    by_stratum = defaultdict(list)
    for n in names:
        by_stratum[stratum(n)].append(n)

    rng = random.Random(args.seed)
    train, test = [], []
    for s in sorted(by_stratum):
        group = sorted(by_stratum[s])
        rng.shuffle(group)
        k = max(1, round(len(group) * args.train_frac))
        train += group[:k]
        test += group[k:]

    os.makedirs(os.path.dirname(args.train_out), exist_ok=True)
    open(args.train_out, "w").write("\n".join(sorted(train)) + "\n")
    open(args.test_out, "w").write("\n".join(sorted(test)) + "\n")
    print(f"treino={len(train)} teste={len(test)} (total {len(names)})")
    print("treino:", " ".join(sorted(train)))
    print("teste :", " ".join(sorted(test)))


if __name__ == "__main__":
    main()
