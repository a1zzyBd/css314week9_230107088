import argparse, json, statistics, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from salt import get_student_params
from paths import RESULTS, STUDENT_ID

try:
    from numba import njit
    HAVE_NUMBA = True
except ImportError:
    HAVE_NUMBA = False

    def njit(*a, **k):
        return lambda f: f


@njit(cache=True)
def ijk(A, B, C, N, M):
    for i in range(M):
        for j in range(M):
            acc = 0.0
            for k in range(M):
                acc += A[i * N + k] * B[k * N + j]      # B strides by N
            C[i * N + j] = acc


@njit(cache=True)
def ikj(A, B, C, N, M):
    for i in range(M):
        for k in range(M):
            a = A[i * N + k]                             # hoisted
            for j in range(M):
                C[i * N + j] += a * B[k * N + j]         # stride-1


def timeit(fn, A, B, N, M, runs=3):
    ts, C = [], None
    for _ in range(runs):
        C = [0.0] * (N * N) if not HAVE_NUMBA else np.zeros(N * N)
        t0 = time.perf_counter()
        fn(A, B, C, N, M)
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts), np.asarray(C)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student-id", default=STUDENT_ID)
    ap.add_argument("--M", type=int, default=None,
                    help="sub-block size. Default N/2 with Numba, 128 in pure Python")
    args = ap.parse_args()

    p = get_student_params(args.student_id)
    N = p["N"]
    M = args.M or (N // 2 if HAVE_NUMBA else 128)
    rng = np.random.default_rng(p["seed"])
    A_np = rng.random(N * N)
    B_np = rng.random(N * N)
    if HAVE_NUMBA:
        A, B = A_np, B_np
        w = np.zeros(N * N)
        ijk(A, B, w, N, 8); ikj(A, B, w, N, 8)          # compile outside timing
    else:
        A, B = A_np.tolist(), B_np.tolist()              # native lists, faster in pure Python

    print(f"N={N}, M={M}, numba={HAVE_NUMBA}")
    t_naive, C1 = timeit(ijk, A, B, N, M)
    t_inter, C2 = timeit(ikj, A, B, N, M)

    ref = A_np.reshape(N, N)[:M, :M] @ B_np.reshape(N, N)[:M, :M]
    out = dict(N=N, M=M, numba=HAVE_NUMBA, t_naive_s=t_naive,
               t_interchanged_s=t_inter, speedup=t_naive / t_inter,
               max_abs_diff_ijk_vs_ikj=float(np.abs(C1 - C2).max()),
               max_abs_diff_vs_numpy=float(np.abs(C2.reshape(N, N)[:M, :M] - ref).max()),
               tolerance_ok=bool(np.abs(C1 - C2).max() <= 1e-12))
    json.dump(out, open(RESULTS / "loop_interchange.json", "w"), indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
