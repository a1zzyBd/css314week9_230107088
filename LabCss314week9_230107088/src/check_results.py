"""Local sanity check (NOT the course's verify_outputs.py)."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import RESULTS

ok = True
def report(flag, msg):
    global ok
    ok &= flag
    print(("[PASS] " if flag else "[FAIL] ") + msg)

for f in ["host_profile.json", "salted_params.json", "stride_results.tsv",
          "loop_interchange.json", "false_sharing_karp_flatt.tsv",
          "scaling_metrics.tsv", "roofline_summary.json"]:
    report((RESULTS / f).exists(), f"{f} exists")

if (RESULTS / "loop_interchange.json").exists():
    d = json.load(open(RESULTS / "loop_interchange.json"))
    report(d["tolerance_ok"], f"ijk vs ikj within 1e-12 (speedup {d['speedup']:.2f}x)")
if (RESULTS / "stride_results.tsv").exists():
    r = list(csv.DictReader(open(RESULTS / "stride_results.tsv"), delimiter="\t"))
    l = {int(x["stride"]): float(x["latency_per_element_ns"]) for x in r}
    report(l[8] > l[1], f"stride-8 latency ({l[8]:.2f} ns) > stride-1 ({l[1]:.2f} ns)")
if (RESULTS / "false_sharing_karp_flatt.tsv").exists():
    r = list(csv.DictReader(open(RESULTS / "false_sharing_karp_flatt.tsv"), delimiter="\t"))
    report(all(x["total_count_ok"] == "True" for x in r), "all counters reached P*K")
    t = {(x["variant"], int(x["P"])): float(x["T_P_s"]) for x in r}
    print(f"       unpadded T(8)/T(1) = {t[('unpadded', 8)] / t[('unpadded', 1)]:.2f}, "
          f"padded T(8)/T(1) = {t[('padded', 8)] / t[('padded', 1)]:.2f}")
sys.exit(0 if ok else 1)
