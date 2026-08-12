#!/usr/bin/env python3
"""Registra o ambiente de execução como ARTEFATO, não como texto fixo no .tex.

A seção de reprodutibilidade do relatório traz CPU, versão do compilador e
esquema de sementes escritos à mão. No dia em que a máquina mudar, o relatório
passa a mentir. Este script gera os mesmos dados a partir do sistema, junto com
os resultados, para que o texto os leia em vez de os afirmar.

Saída: results/environment.json + results/environment.tex (macros \\env*)
"""
import json
import os
import platform
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))


def sh(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              cwd=_ROOT, timeout=15).stdout.strip()
    except Exception:
        return ""


def cpu_model():
    try:
        for line in open("/proc/cpuinfo"):
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "desconhecido"


def main():
    env = {
        "cpu": cpu_model(),
        "cpu_threads": os.cpu_count(),
        "os": f"{platform.system()} {platform.release()}",
        "distro": (sh("lsb_release", "-ds") or "").strip('"'),
        "compiler": (sh("g++", "--version").splitlines() or [""])[0],
        "cxx_flags": "-std=c++20 -O2 -Wall -Wextra",
        "python": platform.python_version(),
        "git_commit": sh("git", "rev-parse", "--short", "HEAD"),
        "git_dirty": bool(sh("git", "status", "--porcelain")),
        "seed_scheme": ("make_seed(base, nome_da_instancia, indice) -- a semente combina "
                        "de forma deterministica um valor base, o nome da instancia e o "
                        "indice da execucao, de modo que cada execucao e reproduzivel "
                        "isoladamente"),
    }

    # versões dos pacotes que produzem números no relatório
    pkgs = {}
    for m in ("numpy", "pandas", "scipy", "matplotlib", "scikit_posthocs"):
        try:
            pkgs[m] = __import__(m).__version__
        except Exception:
            pkgs[m] = None
    env["python_packages"] = pkgs

    # configuração experimental vigente
    cfg = os.path.join(_ROOT, "experiments", "config")
    for name in ("tuned.json", "fixed_K.json", "default.json"):
        p = os.path.join(cfg, name)
        if os.path.isfile(p):
            env[name.replace(".json", "")] = json.load(open(p))
    for name in ("train", "test"):
        p = os.path.join(cfg, name + ".txt")
        if os.path.isfile(p):
            env[name + "_size"] = sum(1 for l in open(p) if l.strip())

    outdir = os.path.join(_ROOT, "results")
    os.makedirs(outdir, exist_ok=True)
    json.dump(env, open(os.path.join(outdir, "environment.json"), "w"),
              indent=2, ensure_ascii=False)

    # macros LaTeX, para o .tex referenciar em vez de repetir
    def tex_escape(s):
        return re.sub(r"([&%$#_{}])", r"\\\1", str(s))

    with open(os.path.join(outdir, "environment.tex"), "w") as fh:
        fh.write("% gerado por experiments/analysis/environment.py -- nao editar\n")
        for key, macro in (("cpu", "envCPU"), ("cpu_threads", "envThreads"),
                           ("os", "envOS"), ("compiler", "envCompiler"),
                           ("python", "envPython"), ("git_commit", "envCommit")):
            fh.write(f"\\newcommand{{\\{macro}}}{{{tex_escape(env.get(key, ''))}}}\n")

    print(json.dumps({k: v for k, v in env.items() if k != "python_packages"},
                     indent=2, ensure_ascii=False))
    if env["git_dirty"]:
        print("\nAVISO: o repositorio tem alteracoes nao commitadas; o commit "
              "registrado nao descreve exatamente o codigo executado.")
    print(f"\nartefatos -> {outdir}/environment.json, environment.tex")


if __name__ == "__main__":
    main()
