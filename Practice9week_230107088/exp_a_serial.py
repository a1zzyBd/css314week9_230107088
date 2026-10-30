"""Experiment A - The Stubborn Serial Tail.

Parallel work is clean, but the master sleeps 0.40 s before dispatching.
Expectation: Karp-Flatt e(p) stays roughly constant across p (fixed serial path).
"""
import math
import time
from multiprocessing import Pool


def heavy_math(n):
    return sum(math.sin(i) * math.cos(i) for i in range(1, n))


def run_experiment(workers, total_chunks=16, chunk_size=2_000_000):
    t0 = time.perf_counter()
    time.sleep(0.40)  # Intentional sequential bottleneck
    with Pool(processes=workers) as pool:
        pool.map(heavy_math, [chunk_size] * total_chunks)
    return time.perf_counter() - t0


def karp_flatt(p, t1, tp):
    return ((p * tp / t1) - 1.0) / (p - 1.0)


if __name__ == "__main__":
    cores = [1, 2, 4]
    runtimes = {p: run_experiment(p) for p in cores}
    t1 = runtimes[1]
    print(f"P=1 | Runtime={t1:.3f}s")
    results = {}
    for p in (2, 4):
        tp = runtimes[p]
        sp = t1 / tp
        e = karp_flatt(p, t1, tp)
        results[p] = e
        print(f"P={p} | Runtime={tp:.3f}s | Speedup={sp:.2f}x | Karp-Flatt e={e:.3f}")
    ratio = results[4] / results[2]
    print(f"e(4)/e(2) = {ratio:.2f}  (rubric target: 0.80 - 1.25)")
