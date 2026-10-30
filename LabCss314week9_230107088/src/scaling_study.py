import argparse, csv, json, math, statistics, sys, time
from multiprocessing import Pool, shared_memory, freeze_support
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from salt import get_student_params
from paths import RESULTS, STUDENT_ID

ITERS = 50
_att = {}


def _attach(name, shape):
    if name not in _att:
        s = shared_memory.SharedMemory(name=name)
        _att[name] = (s, np.ndarray(shape, dtype=np.float64, buffer=s.buf))
    return _att[name][1]


def sweep(args):
    na, nb, shape, r0, r1 = args
    src, dst = _attach(na, shape), _attach(nb, shape)
    dst[r0:r1, 1:-1] = 0.25 * (src[r0 - 1:r1 - 1, 1:-1] + src[r0 + 1:r1 + 1, 1:-1] +
                               src[r0:r1, :-2] + src[r0:r1, 2:])


def run(N, P, seed, reps=3):
    shape = (N, N)
    init = np.random.default_rng(seed).random(shape)
    shms = [shared_memory.SharedMemory(create=True, size=init.nbytes) for _ in range(2)]
    bufs = [np.ndarray(shape, dtype=np.float64, buffer=s.buf) for s in shms]
    bounds = np.linspace(1, N - 1, P + 1).astype(int)
    times = []
    try:
        with Pool(P) as pool:
            for r in range(reps + 1):                    # first pass = warmup
                bufs[0][:] = init; bufs[1][:] = init
                t0 = time.perf_counter()
                for it in range(ITERS):
                    a, b = it % 2, (it + 1) % 2
                    pool.map(sweep, [(shms[a].name, shms[b].name, shape,
                                      int(bounds[i]), int(bounds[i + 1])) for i in range(P)],
                             chunksize=1)
                if r > 0:
                    times.append(time.perf_counter() - t0)
        checksum = float(bufs[ITERS % 2].sum())
    finally:
        del bufs
        for s in shms:
            s.close()
            try:
                s.unlink()
            except FileNotFoundError:
                pass
    return statistics.median(times), checksum


def measure_bandwidth_gbs():
    a = np.ones(1 << 25); b = np.empty_like(a)
    best = 0
    for _ in range(5):
        t0 = time.perf_counter(); np.copyto(b, a); dt = time.perf_counter() - t0
        best = max(best, 2 * a.nbytes / dt / 1e9)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student-id", default=STUDENT_ID)
    ap.add_argument("--peak-gflops", type=float, default=None)
    ap.add_argument("--peak-bw-gbs", type=float, default=None)
    ap.add_argument("--max-p", type=int, default=None, help="override max worker count")
    args = ap.parse_args()

    prm = get_student_params(args.student_id)
    N, seed = prm["N"], prm["seed"]
    host = json.load(open(RESULTS / "host_profile.json"))
    pmax = args.max_p or host["physical_cores"]
    Ps = [p for p in (1, 2, 4, 8, 16, 32) if p <= pmax]
    if pmax not in Ps:
        Ps.append(pmax)

    rows, strong, ref_sum = [], {}, None
    for P in Ps:
        t, cs = run(N, P, seed)
        strong[P] = t
        if P == 1:
            ref_sum = cs
        assert cs == ref_sum, f"checksum mismatch at P={P}: {cs} vs {ref_sum}"
        print(f"strong P={P} N={N} T={t:.3f}s", flush=True)
    t1 = strong[1]
    xs, ys = [], []
    for P in Ps:
        S = t1 / strong[P]
        rows.append(["strong", P, N, strong[P], S, S / P * 100, "", ""])
        if P > 1:
            xs.append(1 - 1 / P); ys.append(1 / S - 1 / P)
    s = sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs) if xs else 0.0
    s = min(max(s, 1e-9), 1.0)
    print(f"Amdahl serial fraction s = {s:.4f}, S_max = {1 / s:.1f}")

    weak = {}
    for P in Ps:
        NP = math.ceil(N * math.sqrt(P))
        weak[P] = (NP, run(NP, P, seed)[0])
        print(f"weak   P={P} N={NP} T={weak[P][1]:.3f}s", flush=True)
    N1, w1 = weak[1]
    for P in Ps:
        NP, tp = weak[P]
        S_scaled = ((NP * NP) / tp) / ((N1 * N1) / w1)   # throughput ratio
        rows.append(["weak", P, NP, tp, S_scaled, w1 / tp * 100, "", ""])
    rows.append(["amdahl_fit", "", N, "", "", "", s, 1 / s])

    with open(RESULTS / "scaling_metrics.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["study", "P", "N", "T_P_s", "speedup", "efficiency_pct",
                    "serial_fraction", "S_max"])
        w.writerows(rows)

    flops, bytes_ = 4, 16
    ai = flops / bytes_
    bw = args.peak_bw_gbs or measure_bandwidth_gbs()
    ghz = (host.get("base_mhz") or 2500) / 1000
    peak = args.peak_gflops or host["physical_cores"] * ghz * 16
    ridge = peak / bw
    ws = 2 * N * N * 8
    l3 = host["caches"].get("l3") or 0
    summary = dict(flops_per_point=flops, dram_bytes_per_point=bytes_,
                   arithmetic_intensity=ai, peak_gflops_estimate=peak,
                   bandwidth_gbs=bw, ridge_point=ridge,
                   attainable_gflops=min(peak, ai * bw),
                   working_set_bytes=ws, l3_bytes=l3, fits_in_l3=ws <= l3,
                   regime="memory-bandwidth bound" if ai < ridge else "compute bound")
    json.dump(summary, open(RESULTS / "roofline_summary.json", "w"), indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    freeze_support()
    main()
