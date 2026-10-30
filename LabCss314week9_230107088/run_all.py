import subprocess, sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
STEPS = ["profile_env.py", "stride_bench.py", "dense_kernel.py",
         "false_sharing.py", "scaling_study.py", "check_results.py"]
for s in STEPS:
    print(f"\n=== {s} ===", flush=True)
    r = subprocess.run([sys.executable, str(SRC / s)])
    if r.returncode != 0:
        print(f"{s} failed (exit {r.returncode})")
        sys.exit(r.returncode)
