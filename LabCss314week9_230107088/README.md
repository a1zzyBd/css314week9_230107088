# CS482 Practicum - Student 230107088

CS482 Practicum Results Analysis
Student 230107088 · AMD Ryzen 7 4800H · Windows 11 · Python 3.14.2
Everything ran and the results are consistent with the theory. The derived numbers below were calculated by hand from the printed times, so check them against the TSV files.
Milestone 0: host profile
The machine has 8 physical cores and 16 logical threads, so SMT is on. The caches are 4 MB L2 (total across cores), 8 MB L3 and 64-byte lines. l1 is null because Windows doesn't report it. For the write-up, take the L1 data cache size (32 KB per core on Zen 2) from AMD's spec sheet.
Milestone 1: locality
• Stride cliff: latency per element goes from 1.74 ns at stride 1 to 5.0 ns at stride 8, about 3x, then levels off around 7-9 ns. The jump between stride 1 and stride 8 is the cache-line effect: at stride 8 every read pulls in a new 64-byte line.
• Plateau noise: stride 64 (6.8 ns) is lower than stride 32 (8.5 ns), which is noise. Rerun with the laptop plugged in and nothing else open for a cleaner curve.
• Loop interchange: i-k-j is 3.12x faster than i-j-k (1.24 s vs 3.88 s). The results are identical (diff = 0.0) because both orders add the terms in the same sequence.
Milestone 2: false sharing
Variant
T(1)
T(8)
T(8)/T(1)
unpadded
2.03 s
4.27 s
2.11
padded
2.03 s
2.63 s
1.29
privatized
0.37 s
0.55 s
1.48
Karp-Flatt for P = 2, 4, 8, rounded (e_spec uses the PDF's formula, e_scaled the corrected one):
Variant
e_spec
e_scaled
unpadded
1.50, 1.68, 2.27
0.25, 0.17, 0.16
padded
1.10, 1.17, 1.34
0.048, 0.043, 0.042
• The effect is real: at P=8 the unpadded version is about 63% slower than the padded one (4.27 s vs 2.63 s), and the PDF's e_spec rises for unpadded while staying lower for padded.
• The effect is modest, not a collapse: Python's interpreter overhead hides much of it, and a C version would show a far bigger gap. Say this in the write-up rather than overselling it.
• e_scaled doesn't rise: it stays roughly flat at 0.16-0.25 for unpadded, about 4-6x above padded. The penalty is paid at P=2 and doesn't grow after that.
• Padded also drifts upward: likely lower turbo clocks with more cores active, plus process startup and SMT effects.
• Privatized is noisy: 0.37 s is short enough that startup jitter matters, so don't read much into its Karp-Flatt values.
Milestone 3: scaling
P
Strong speedup
Strong efficiency
Weak efficiency (T1/TP)
2
1.57
78%
72%
4
1.80
45%
43%
8
1.89
24%
23%
• Amdahl fit: s = 0.41 and S_max = 2.4. This "serial fraction" isn't really serial code. It mostly reflects the memory-bandwidth limit plus the per-sweep Pool.map synchronization. Say so in the write-up.
• Gustafson comparison: weak scaling didn't beat strong scaling here (efficiency is about the same). Gustafson assumes the parallel part scales freely, but all cores share one memory bus. Scaled speedup tops out around 1.9x, the same ceiling as the strong study.
• Roofline: the arithmetic intensity is 0.25 FLOP/byte, far below the ridge point of about 20, so the kernel is memory-bandwidth bound. The 37.7 MB working set doesn't fit in the 8 MB L3, which agrees.
• Bandwidth figure: the 18 GB/s is a single-thread copy measurement, and the DDR4 peak is higher. Using the spec-sheet peak lowers the ridge point but doesn't change the conclusion. Pass --peak-bw-gbs and rerun for a more rigorous number.
• Gap to the bound: measured throughput is about 0.42 GFLOP/s at P=8, well under the roofline bound of about 4.6. NumPy creates temporary arrays and every sweep has a synchronization cost, so the run sits well below what the hardware could deliver.
