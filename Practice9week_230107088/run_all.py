
import os
import platform

from exp_a_serial import run_experiment
from exp_b_contention import run_contended
from exp_c_fixed import run_privatized


def kf(p, t1, tp):
    return ((p * tp / t1) - 1.0) / (p - 1.0)


def bench(fn):
    t = {p: fn(p) for p in (1, 2, 4)}
    return t, kf(2, t[1], t[2]), kf(4, t[1], t[4])


if __name__ == "__main__":
    cores = os.cpu_count()
    print(f"Logical cores: {cores}")
    if cores and cores < 4:
        print("WARNING: fewer than 4 logical cores - results will not show the expected pattern.")

    a, a2, a4 = bench(run_experiment)
    b, b2, b4 = bench(run_contended)
    c, c2, c4 = bench(run_privatized)
    eff4 = c[1] / c[4] / 4 * 100

    rows = [
        ("A: Serial Tail", a, a2, a4, "Constant e -> fixed Amdahl serialization"),
        ("B: Lock Contention", b, b2, b4, "Exploding e -> mutex & bus thrashing"),
        ("C: Privatized State", c, c2, c4, "Collapsed e -> linear scalability restored"),
    ]
    lines = [
        "# RESULTS",
        "",
        "## Hardware profile",
        f"- Platform: {platform.platform()}",
        f"- Processor: {platform.processor() or 'n/a'}",
        f"- Logical cores: {cores}",
        f"- Python: {platform.python_version()}",
        "",
        "## Runtimes and Karp-Flatt metric",
        "",
        "| Experiment | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Diagnosis |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, t, e2, e4, d in rows:
        lines.append(f"| {name} | {t[1]:.3f} | {t[2]:.3f} | {t[4]:.3f} | {e2:.3f} | {e4:.3f} | {d} |")
    lines += [
        "",
        "## Rubric checks",
        f"- Exp A: e(4)/e(2) = {a4 / a2:.2f} (target 0.80-1.25)",
        f"- Exp B: T4 > T1: {b[4] > b[1]}; e(4) = {b4:.3f} vs e(2) = {b2:.3f}",
        f"- Exp C: T4 < T1: {c[4] < c[1]}; E4 = {eff4:.0f}% (target > 70%)",
        "",
        "## Notes",
        "- Write 2-3 sentences here comparing the three e(p) patterns.",
        "",
    ]
    with open("RESULTS.md", "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
