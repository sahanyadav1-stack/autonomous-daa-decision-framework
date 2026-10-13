"""Experiments for the report. Run from the project root:  python -m benchmarks.run_benchmarks
Writes benchmarks/results.json and benchmarks/results.md. All numbers are measured, none hard-coded."""
import json
import math
import os
import random
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from algorithms.graph import Graph, kruskal, prim_dense, prim_heap, floyd_warshall
from algorithms.dp import fractional_knapsack, knapsack_01, greedy_density_01, matrix_chain
from algorithms.search import hamiltonian, n_queens, tsp_backtracking, tsp_branch_and_bound
from structures.rbtree import RedBlackTree
from structures.btree import BTree
from structures.binomial_heap import BinomialHeap
from structures.fibonacci_heap import FibonacciHeap

R = {}
MD = []


def ms(fn, *a, reps=1, **k):
    best, out = float("inf"), None
    for _ in range(reps):
        t0 = time.perf_counter()
        out = fn(*a, **k)
        best = min(best, (time.perf_counter() - t0) * 1000)
    return out, best


def table(title, header, rows):
    MD.append(f"\n### {title}\n")
    MD.append("| " + " | ".join(header) + " |")
    MD.append("|" + "|".join("---" for _ in header) + "|")
    for r in rows:
        MD.append("| " + " | ".join(str(x) for x in r) + " |")
    print(f"\n== {title} ==")
    print(" | ".join(header))
    for r in rows:
        print(" | ".join(str(x) for x in r))


def rand_graph(n, m, seed):
    rnd = random.Random(seed)
    edges, seen = [], set()
    for v in range(1, n):
        u = rnd.randrange(v)
        edges.append((u, v, rnd.randint(1, 1000)))
        seen.add((u, v))
    while len(edges) < m:
        u, v = rnd.sample(range(n), 2)
        a, b = min(u, v), max(u, v)
        if (a, b) not in seen:
            seen.add((a, b))
            edges.append((a, b, rnd.randint(1, 1000)))
    return Graph(n, edges)


def euclid(n, seed):
    rnd = random.Random(seed)
    pts = [(rnd.random() * 100, rnd.random() * 100) for _ in range(n)]
    return [[round(math.dist(a, b), 2) for b in pts] for a in pts]


# ------------------------------------------------------------ 1. MST
def bench_mst():
    rows = []
    for n, m in ((25, 36), (25, 240), (100, 300), (100, 4500)):
        g = rand_graph(n, m, 11)
        (kc, _, ks), tk = ms(kruskal, g, reps=5)
        (pc, _, ps), tp = ms(prim_dense, g, reps=5)
        assert kc == pc
        rows.append((f"V={n},E={m}", f"{g.density:.2f}", f"{kc}", f"{tk:.3f}", ks["ops"], f"{tp:.3f}", ps["ops"],
                     "Kruskal" if tk < tp else "Prim(dense)"))
    table("MST: Kruskal vs Prim (adjacency matrix)", ["graph", "density D", "MST cost", "Kruskal ms", "Kruskal ops",
                                                       "Prim ms", "Prim ops", "faster"], rows)
    R["mst_cases"] = rows
    # crossover sweep
    n, sweep = 120, []
    maxm = n * (n - 1) // 2
    cross_t = cross_ops = None
    for D in [x / 100 for x in range(2, 100, 3)]:
        m = max(n - 1, int(D * maxm))
        g = rand_graph(n, m, 21)
        (_, _, ks), tk = ms(kruskal, g, reps=3)
        (_, _, ps), tp = ms(prim_dense, g, reps=3)
        sweep.append((round(g.density, 3), tk, tp, ks["ops"], ps["ops"]))
        if cross_t is None and tp <= tk:
            cross_t = round(g.density, 3)
        if cross_ops is None and ps["ops"] <= ks["ops"]:
            cross_ops = round(g.density, 3)
    R["mst_crossover_time_D"], R["mst_crossover_ops_D"] = cross_t, cross_ops
    MD.append(f"\n**Measured crossover (V={n}):** by wall-clock time D = {cross_t}; by operation count D = {cross_ops}.")
    print("crossover D (time, ops):", cross_t, cross_ops)
    # heap-based Prim comparison
    g = rand_graph(300, 6000, 5)
    (_, _, sb), tb = ms(prim_heap, g, BinomialHeap)
    (_, _, sf), tf = ms(prim_heap, g, FibonacciHeap)
    table("Prim with priority queue (V=300, E=6000)", ["heap", "ops", "decrease_keys", "ms"],
          [("Binomial", sb["ops"], sb["decrease_keys"], f"{tb:.1f}"), ("Fibonacci", sf["ops"], sf["decrease_keys"], f"{tf:.1f}")])
    R["prim_heap"] = {"binomial": sb, "fibonacci": sf}


# ------------------------------------------------------------ 2. Floyd-Warshall
def bench_fw():
    rows = []
    for n in (10, 20, 40, 80):
        g = rand_graph(n, n * 4, 3)
        g.directed = True
        (_, st), t = ms(floyd_warshall, g)
        rows.append((n, st["ops"], f"{t:.2f}", n ** 3))
    for i in range(1, len(rows)):
        pass
    table("Floyd-Warshall scaling", ["V", "inner-loop ops", "ms", "V^3"], rows)
    R["fw"] = rows


# ------------------------------------------------------------ 3. Index
def bench_index():
    rows = []
    for n in (500, 5000, 50000):
        keys = random.Random(9).sample(range(10 ** 7), n)
        rbt, bt = RedBlackTree(), BTree(16)
        _, ti_r = ms(lambda: [rbt.insert(k) for k in keys])
        _, ti_b = ms(lambda: [bt.insert(k) for k in keys])
        for k in keys:
            rbt.search(k)
            bt.search(k)
        rbt.check_invariants()
        bt.check_invariants()
        rows.append((n, rbt.height(), rbt.rotations, f"{rbt.visits / n:.2f}", f"{ti_r:.0f}",
                     bt.height(), bt.splits, f"{bt.node_reads / n:.2f}", f"{ti_b:.0f}"))
    table("Index: Red-Black Tree vs B-Tree (t=16), random inserts then search all",
          ["N", "RBT height", "RBT rotations", "RBT visits/search", "RBT insert ms",
           "B height", "B splits", "B reads/search", "B insert ms"], rows)
    R["index"] = rows


# ------------------------------------------------------------ 4. Heaps
def heap_run(H, n, share, seed, big_drop):
    rnd = random.Random(seed)
    h = H()
    cur = {}
    for i in range(n):
        cur[i] = rnd.randint(10 ** 4, 10 ** 6)
        h.insert(cur[i], i)
    for _ in range(n):
        if rnd.random() < share and cur:
            i = rnd.choice(list(cur))
            cur[i] = rnd.randint(0, cur[i] - 1) if big_drop else max(0, cur[i] - rnd.randint(1, 50))
            h.decrease_key(i, cur[i])
        else:
            if len(h):
                _, it = h.extract_min()
                cur.pop(it, None)
    return h.ops


def bench_heap():
    rows, cross = [], {}
    for big in (True, False):
        label = "large key drops" if big else "small key drops"
        for share in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9):
            b = heap_run(BinomialHeap, 2000, share, 4, big)
            f = heap_run(FibonacciHeap, 2000, share, 4, big)
            rows.append((label, share, b, f, "Fibonacci" if f < b else "Binomial"))
            if f < b and label not in cross:
                cross[label] = share
    table("Heaps: ops (comparisons+links+swaps/cuts) for n=2000 inserts then n mixed ops",
          ["workload", "decrease-key share", "Binomial ops", "Fibonacci ops", "fewer ops"], rows)
    R["heap_rows"], R["heap_crossover_share"] = rows, cross
    MD.append(f"\n**First share where Fibonacci uses fewer ops:** {cross}")
    print("heap crossover:", cross)
    # merge cost
    rm = []
    for n in (1000, 10000):
        for H in (BinomialHeap, FibonacciHeap):
            a, b = H(), H()
            for i in range(n):
                a.insert(i * 2, ("a", i))
                b.insert(i * 2 + 1, ("b", i))
            before = a.ops + b.ops
            a.merge(b)
            rm.append((H.__name__, n, a.ops - before))
    table("Heap merge cost (ops to merge two heaps of n keys)", ["heap", "n", "merge ops"], rm)
    R["heap_merge"] = rm


# ------------------------------------------------------------ 5. Knapsack
def bench_knap():
    items = [(10, 60), (20, 100), (30, 120)]
    fv, fr, _ = fractional_knapsack(items, 50)
    dv, dc, ds = knapsack_01(items, 50)
    gv, gc = greedy_density_01(items, 50)
    table("Matched dataset (weights 10,20,30; values 60,100,120; W=50)", ["method", "value", "choice"],
          [("Fractional greedy", fv, [round(x, 2) for x in fr]), ("0/1 DP (exact)", dv, dc),
           ("Greedy by density applied to 0/1", gv, gc)])
    R["knap_matched"] = {"frac": fv, "dp": dv, "greedy01": gv, "dp_states": ds["states"]}
    rows, rnd = [], random.Random(2)
    for W in (1000, 5000, 20000):
        its = [(rnd.randint(5, 200), rnd.randint(10, 500)) for _ in range(100)]
        tracemalloc.start()
        (v, _, st), t = ms(knapsack_01, its, W)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        (fv2, _, _), tf = ms(fractional_knapsack, its, W)
        rows.append((100, W, st["states"], f"{t:.0f}", f"{peak / 1e6:.1f}", f"{tf:.3f}"))
    table("0/1 DP pseudo-polynomial growth (n=100) vs fractional greedy",
          ["n", "capacity W", "DP states", "DP ms", "DP peak MB", "fractional ms"], rows)
    R["knap_scale"] = rows


# ------------------------------------------------------------ 6. MCM
def bench_mcm():
    rows, rnd = [], random.Random(8)
    for m in (10, 20, 40, 80, 160):
        dims = [rnd.randint(5, 100) for _ in range(m + 1)]
        (c, _, naive, st), t = ms(matrix_chain, dims)
        rows.append((m, st["ops"], f"{t:.2f}", c, naive, f"{naive / c:.1f}x"))
    table("Matrix Chain Multiplication", ["chain length", "DP ops", "ms", "optimal mults", "left-to-right mults", "saving"], rows)
    R["mcm"] = rows


# ------------------------------------------------------------ 7. Hamiltonian + N-Queen
def bench_hn():
    rows = []
    for k in (3, 4, 5, 6, 7):          # K_{k,k+2}: no Hamiltonian path -> backtracking must exhaust
        n = 2 * k + 2
        edges = [(i, k + j) for i in range(k) for j in range(k + 2)]
        (p, st), t = ms(hamiltonian, n, edges, False, 2_000_000)
        rows.append((f"K({k},{k + 2}) n={n}", "none" if p is None else "found", st["states"], st["complete"], f"{t:.1f}"))
    table("Hamiltonian path: complete bipartite K(k,k+2) (no solution, worst case)", ["graph", "result", "states", "exhausted", "ms"], rows)
    R["ham"] = rows
    rows = []
    for n in (4, 6, 8, 10, 12):
        (f1, c1, s1), t1 = ms(n_queens, n, (), False)
        if n <= 10:
            (fa, ca, sa), ta = ms(n_queens, n, (), True)
        else:
            ca, sa, ta = "-", {"states": "-"}, 0
        rows.append((n, s1["states"], f"{t1:.2f}", ca, sa["states"], f"{ta:.0f}" if n <= 10 else "-"))
    table("N-Queen backtracking", ["N", "states (first solution)", "ms", "#solutions", "states (all)", "ms (all)"], rows)
    R["nq"] = rows


# ------------------------------------------------------------ 8. TSP
def bench_tsp():
    rows = []
    for n in (6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18):
        C = euclid(n, 100 + n)
        bb, tbb = ms(tsp_branch_and_bound, C, 400_000)
        row = [n, f"{bb[0]:.2f}", bb[2]["generated"], bb[2]["pruned"], bb[2]["complete"], f"{tbb:.0f}"]
        if n <= 10:
            bt, tbt = ms(tsp_backtracking, C)
            assert abs(bt[0] - bb[0]) < 1e-6
            full = bt[2]["states"]
            row += [full, f"{tbt:.0f}", f"{100 * (1 - bb[2]['generated'] / full):.1f}%"]
        else:
            row += ["-", "-", "-"]
        rows.append(tuple(row))
    table("TSP: plain backtracking vs reduced-matrix Branch and Bound (random Euclidean)",
          ["N", "optimal cost", "B&B generated", "B&B pruned", "B&B finished", "B&B ms", "BT states", "BT ms", "fewer states"], rows)
    R["tsp"] = rows
    MD.append(f"\n(N-1)! growth: 9!={math.factorial(9):,}; 13!={math.factorial(13):,}; 21!={math.factorial(21):.2e}")


if __name__ == "__main__":
    print("Python", sys.version.split()[0])
    MD.append("# Measured benchmark results\n")
    MD.append(f"Python {sys.version.split()[0]}. All values produced by `benchmarks/run_benchmarks.py`.")
    for fn in (bench_mst, bench_fw, bench_index, bench_heap, bench_knap, bench_mcm, bench_hn, bench_tsp):
        t0 = time.time()
        fn()
        print(f"[{fn.__name__} done in {time.time() - t0:.1f}s]")
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "results.json"), "w") as f:
        json.dump(R, f, indent=1, default=str)
    with open(os.path.join(here, "results.md"), "w") as f:
        f.write("\n".join(MD) + "\n")
