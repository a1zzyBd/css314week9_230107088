# lab-karp-flatt

Files: `exp_a_serial.py`, `exp_b_contention.py`, `exp_c_fixed.py`, `run_all.py`, `RESULTS.md`

Run on a machine with 4+ logical cores:

    python3 exp_a_serial.py
    python3 exp_b_contention.py
    python3 exp_c_fixed.py
    python3 run_all.py        # runs everything, writes RESULTS.md

Git workflow:

    git checkout -b practice-<230107088>
    git add exp_a_serial.py && git commit -m "Part 1: Experiment A complete"
    git add exp_b_contention.py && git commit -m "Part 2: Captured lock contention pathology and Karp-Flatt surge"
    git add exp_c_fixed.py RESULTS.md && git commit -m "Part 3 & 4: Completed privatization fix and verified RESULTS.md"
    git push origin practice-<230107088
