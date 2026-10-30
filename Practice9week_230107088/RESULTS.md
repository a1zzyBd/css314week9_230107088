# RESULTS

## Hardware profile
- Platform: Windows-11-10.0.26200-SP0
- Processor: AMD64 Family 23 Model 96 Stepping 1, AuthenticAMD
- Logical cores: 16
- Python: 3.14.2

## Runtimes and Karp-Flatt metric

| Experiment | T1 (s) | T2 (s) | T4 (s) | e(2) | e(4) | Diagnosis |
|---|---|---|---|---|---|---|
| A: Serial Tail | 18.472 | 9.745 | 5.391 | 0.055 | 0.056 | Constant e -> fixed Amdahl serialization |
| B: Lock Contention | 10.274 | 28.693 | 32.515 | 4.586 | 3.887 | Exploding e -> mutex & bus thrashing |
| C: Privatized State | 1.843 | 1.122 | 0.798 | 0.218 | 0.244 | Collapsed e -> linear scalability restored |

## Rubric checks
- Exp A: e(4)/e(2) = 1.01 (target 0.80-1.25)
- Exp B: T4 > T1: True; e(4) = 3.887 vs e(2) = 4.586
- Exp C: T4 < T1: True; E4 = 58% (target > 70%)

## Notes

- **Experiment A:** e(2) = 0.055 and e(4) = 0.056, so e stayed flat (ratio 1.01). The speedup also kept growing, from about 1.9x with 2 workers to 3.4x with 4. This means the loss comes from a fixed serial part, the 0.40 s sleep, which is the Amdahl case. My e is lower than the ~0.12 in the handout because my T1 was long (18.5 s), so the sleep was a smaller part of the total time.

- **Experiment B:** Adding cores made the program slower. T1 was 10.3 s, T2 was 28.7 s and T4 was 32.5 s, so the speedup was below 1. e was 4.6 and 3.9, much higher than in Experiment A. The processes spent their time waiting for the same lock instead of doing work. One thing differed from the handout: e(4) was a little lower than e(2) instead of much higher. I think the contention was already at its worst with 2 processes, so more processes did not make it much worse. The conclusion is the same: the slowdown comes from lock contention, not from serial code.

- **Experiment C:** Removing the shared lock fixed most of the problem. T4 was 0.80 s compared with T1 of 1.84 s, about 2.3x faster, and far faster than Experiment B. However, I did not meet the targets: efficiency was 58% (target over 70%) and e was about 0.22–0.24 (target under 0.03). I think the reason is that the run is very short, so the time to start the worker processes matters a lot, especially on Windows. This is startup overhead, not lock contention. A bigger workload should improve the result.

- **Comparison:** In A, e stays flat, which means a fixed serial part. In B, e is high and the program gets slower, which means contention. In C, e is low, which means good scaling, apart from the startup overhead. So the metric helps tell which kind of problem is slowing the program down.
