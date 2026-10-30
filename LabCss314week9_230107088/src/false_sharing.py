import csv, ctypes, statistics, sys, time
import multiprocessing as mp
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import RESULTS

K = 5_000_000
PS = [1, 2, 4, 8]


def worker(mode, arr, wid, iters, barrier, times):
    barrier.wait()
    t0 = time.perf_counter()
    if mode == "unpadded":
        for _ in range(iters):
            arr[wid] += 1                    # indices 0-7 share one 64-byte line
    elif mode == "padded":
        idx = wid * 8                        # 8 x int64 = 64 bytes apart
        for _ in range(iters):
            arr[idx] += 1
    else:                                    # privatized
        local = 0
        for _ in range(iters):
            local += 1
        arr[wid * 8] = local                 # single write at the end
    times[wid] = time.perf_counter() - t0


def run(mode, P, reps=3):
    results = []
    for _ in range(reps):
        arr = mp.RawArray(ctypes.c_int64, 64)        # lock-free, zero-initialised
        times = mp.RawArray(ctypes.c_double, 8)
        barrier = mp.Barrier(P)
        procs = [mp.Process(target=worker, args=(mode, arr, p, K, barrier, times))
                 for p in range(P)]
        for p in procs: p.start()
        for p in procs: p.join()
        total = sum(arr[:])
        assert total == P * K, f"{mode} P={P}: {total} != {P * K}"
        results.append(max(times[:P]))
    return statistics.median(results)


def main():
    T = {}
    for m in ("unpadded", "padded", "privatized"):
        T[m] = {}
        for P in PS:
            T[m][P] = run(m, P)
            print(f"{m:10s} P={P}  T={T[m][P]:.3f}s", flush=True)
    with open(RESULTS / "false_sharing_karp_flatt.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["variant", "P", "K_per_worker", "T_P_s", "speedup_spec", "e_spec",
                    "scaled_speedup", "e_scaled", "total_count_ok"])
        for m in T:
            t1 = T[m][1]
            for P in PS:
                tp = T[m][P]
                if P == 1:
                    w.writerow([m, P, K, tp, "", "", "", "", True])
                    continue
                e_spec = (P * tp / t1 - 1) / (P - 1)          # formula as written in the PDF
                e_scaled = (tp / t1 - 1) / (P - 1)            # scaled speedup version
                w.writerow([m, P, K, tp, t1 / tp, e_spec, P * t1 / tp, e_scaled, True])


if __name__ == "__main__":
    mp.freeze_support()
    main()
