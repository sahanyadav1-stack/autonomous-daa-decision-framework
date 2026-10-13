"""Tunable thresholds used by the rule engine. Values come from benchmarks/run_benchmarks.py
(see benchmarks/results.md); re-run it on your machine and update them if the crossover moves."""
DENSITY_THRESHOLD = 0.11             # D at/above which dense-matrix Prim beats Kruskal (wall-clock, V=120 sweep).
                                     # By abstract op count the crossover is D~0.38; it also drifts with V.
DECREASE_KEY_SHARE_THRESHOLD = 0.05  # decrease-key share at/above which Fibonacci can win ...
LARGE_DROP_THRESHOLD = 0.10          # ... but only if decrease-keys are large (mean relative key drop >= this)
BTREE_MIN_DEGREE = 16                # t for block-resident indexes
TSP_EXACT_LIMIT = 14                 # largest N run to completion (Euclidean B&B finished N=14 in <1s, N=16 in ~8s)
TSP_BUDGET_STATES = 100_000          # state budget when N > TSP_EXACT_LIMIT (answer then NOT proven optimal)
