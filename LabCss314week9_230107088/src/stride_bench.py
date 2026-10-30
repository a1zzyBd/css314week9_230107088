import csv, statistics, time, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import RESULTS

STRIDES = [1, 2, 4, 8, 16, 32, 64, 128]


def main():
    data = np.ones(16_777_216, dtype=np.float64)   # ~134 MB, larger than L3
    rows = []
    for s in STRIDES:
        view = data[::s]
        n = view.size
        times = []
        for it in range(10):                        # 5 warmup + 5 recorded
            t0 = time.perf_counter_ns()
            total = view.sum()
            t1 = time.perf_counter_ns()
            if it >= 5:
                times.append(t1 - t0)
        med = statistics.median(times)
        rows.append((s, n, med, med / n))
        print(f"stride {s:4d}: {med / n:8.3f} ns/element")
    with open(RESULTS / "stride_results.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["stride", "elements_touched", "median_time_ns", "latency_per_element_ns"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
