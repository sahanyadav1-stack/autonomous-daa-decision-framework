"""Autonomous DAA decision engine:
request -> property extraction -> problem recognition -> rule-based selection -> execution -> explanation.
Rules depend on problem PROPERTIES (density, divisibility, storage tier, decrease-key share, ...),
never on an algorithm name supplied by the user."""
import time
from dataclasses import dataclass, field

import config
from algorithms.graph import (Graph, kruskal, prim_dense, prim_heap, floyd_warshall,
                              GraphDisconnectedError, NegativeCycleError)
from algorithms.dp import fractional_knapsack, knapsack_01, greedy_density_01, matrix_chain
from algorithms.search import hamiltonian, n_queens, tsp_backtracking, tsp_branch_and_bound
from structures.rbtree import RedBlackTree
from structures.btree import BTree
from structures.binomial_heap import BinomialHeap
from structures.fibonacci_heap import FibonacciHeap
from classify import CLASSES


class UnrecognizedProblem(Exception):
    pass


@dataclass
class Decision:
    problem_type: str
    technique: str
    time_complexity: str
    space_complexity: str
    rejected: list            # [(name, why)]
    reason: str
    properties: dict
    classification: dict
    result: dict = field(default_factory=dict)

    def render(self):
        lines = [
            f"  Identified problem : {self.problem_type}",
            f"  Properties         : {self.properties}",
            f"  Chosen technique   : {self.technique}",
            f"  Expected complexity: time {self.time_complexity} | space {self.space_complexity}",
            f"  Reason             : {self.reason}",
        ]
        for name, why in self.rejected:
            lines.append(f"  Rejected           : {name} -> {why}")
        c = self.classification
        lines.append(f"  Complexity class   : {c['status']}")
        lines.append(f"     optimization    : {c['optimization']}")
        lines.append(f"     decision        : {c['decision']}")
        lines.append(f"     note            : {c['note']}")
        for k, v in self.result.items():
            lines.append(f"  Result.{k:<12}: {v}")
        return "\n".join(lines)


# ---------------------------------------------------------------- recognition
def recognize(req):
    """Return a problem-class label by inspecting the *shape* of the request."""
    if "matrix_dims" in req:
        return "matrix_chain"
    if "items" in req and "capacity" in req:
        return "knapsack_fractional" if req.get("divisible") else "knapsack_01"
    if "grid" in req:
        return "n_queens"
    if "heap_ops" in req:
        return "priority"
    if "index_workload" in req:
        return "index"
    if "cost_matrix" in req and req.get("goal") == "visit_each_and_return_min_cost":
        return "tsp"
    if "graph" in req:
        goal = req.get("goal")
        return {"connect_all_min_cost": "mst", "all_pairs_costs": "apsp",
                "visit_each_vertex_once": "hamiltonian"}.get(goal, "unknown")
    return "unknown"


def _timed(fn, *a, **k):
    t0 = time.perf_counter()
    out = fn(*a, **k)
    return out, (time.perf_counter() - t0) * 1000


# ---------------------------------------------------------------- per-class handlers
def _index(req):
    w = req["index_workload"]
    keys, storage = w["keys"], w.get("storage", "memory")
    n = len(keys)
    props = {"n_keys": n, "storage": storage, "ordered_search": True}
    block = storage in ("disk", "block")
    t = w.get("block_degree", config.BTREE_MIN_DEGREE)

    def run(structure):
        for k in keys:
            structure.insert(k)
        for k in keys:
            structure.search(k)
        return structure
    rbt, bt = run(RedBlackTree()), run(BTree(t))
    res = {
        "RBT": f"height={rbt.height()}, rotations={rbt.rotations}, node_visits/search={rbt.visits / n:.2f}",
        f"B-Tree(t={t})": f"height={bt.height()}, splits={bt.splits}, block_reads/search={bt.node_reads / n:.2f}",
    }
    if block:
        d = Decision("Ordered, block-resident searchable data", f"B-Tree (min degree t={t})",
                     "O(log_t n) block reads; O(t log_t n) CPU", "O(n)",
                     [("Red-Black Tree", "binary nodes mean about log2(n) separate block reads per lookup")],
                     "Data lives in blocks/pages, so minimising the tree height (block reads) dominates cost.",
                     props, CLASSES["ordered_dynamic_set"], res)
    else:
        d = Decision("Ordered, memory-resident searchable data", "Red-Black Tree",
                     "O(log n) per op (<=2 rotations/insert)", "O(n)",
                     [("B-Tree", "wide nodes only pay off when a node = one disk block; in RAM it adds in-node shifting")],
                     "No block-I/O cost to amortise; RBT gives strict O(log n) with very few rotations.",
                     props, CLASSES["ordered_dynamic_set"], res)
    return d


def _priority(req):
    ops = req["heap_ops"]
    kinds = [o[0] for o in ops]
    total = len(kinds)
    share = lambda k: kinds.count(k) / total if total else 0.0
    cur, drops = {}, []
    for o in ops:                      # property: how far do decrease-keys move an item?
        if o[0] == "insert":
            cur[o[2]] = o[1]
        elif o[0] == "decrease_key" and o[1] in cur and o[2] < cur[o[1]]:
            old = cur[o[1]]
            drops.append((old - o[2]) / old if old > 0 else 0.0)
            cur[o[1]] = o[2]
    mean_drop = sum(drops) / len(drops) if drops else 0.0
    dk = share("decrease_key")
    props = {"ops": total, "decrease_key_share": round(dk, 3), "mean_relative_key_drop": round(mean_drop, 3),
             "merge_share": round(share("merge"), 3)}

    def run(H):
        h = H()
        for o in ops:
            if o[0] == "insert":
                h.insert(o[1], o[2])
            elif o[0] == "extract_min":
                if len(h):
                    h.extract_min()
            elif o[0] == "decrease_key":
                if o[1] in h.nodes and o[2] < h.nodes[o[1]].key:
                    h.decrease_key(o[1], o[2])
            elif o[0] == "merge":
                other = H()
                for k, it in o[1]:
                    other.insert(k, it)
                h.merge(other)
        return h
    (bh, tb), (fh, tf) = _timed(run, BinomialHeap), _timed(run, FibonacciHeap)
    res = {"BinomialHeap": f"ops={bh.ops}, time={tb:.2f}ms",
           "FibonacciHeap": f"ops={fh.ops}, time={tf:.2f}ms"}
    if dk >= config.DECREASE_KEY_SHARE_THRESHOLD and mean_drop >= config.LARGE_DROP_THRESHOLD:
        return Decision("Mergeable priority queue, many large decrease-keys", "Fibonacci Heap",
                        "decrease-key O(1) amortized, extract-min O(log n) amortized", "O(n)",
                        [("Binomial Heap", "each large decrease-key sifts up through O(log n) levels")],
                        f"decrease-key share {dk:.2f} >= {config.DECREASE_KEY_SHARE_THRESHOLD} and mean relative drop "
                        f"{mean_drop:.2f} >= {config.LARGE_DROP_THRESHOLD}: lazy cuts amortise the expensive sift-ups.",
                        props, CLASSES["mergeable_priority_queue"], res)
    return Decision("Mergeable priority queue, insert/extract/merge (or small decrease-key) dominated", "Binomial Heap",
                    "insert/merge/extract-min/decrease-key O(log n)", "O(n)",
                    [("Fibonacci Heap", "O(1) decrease-key saves little when keys barely move; its 4-pointer nodes and consolidation cost remain")],
                    f"decrease-key share {dk:.2f}, mean relative drop {mean_drop:.2f}: below the thresholds "
                    f"({config.DECREASE_KEY_SHARE_THRESHOLD} / {config.LARGE_DROP_THRESHOLD}), so the simpler structure wins.",
                    props, CLASSES["mergeable_priority_queue"], res)


def _mst(req):
    gd = req["graph"]
    g = Graph(gd["n"], gd["edges"], gd.get("directed", False))
    D = g.density
    props = {"V": g.n, "E": len(g.edges), "density_D": round(D, 3)}
    (kc, kt, ks), tk = _timed(kruskal, g)
    (pc, pt, ps), tp = _timed(prim_dense, g)
    res = {"Kruskal": f"cost={kc}, ops={ks['ops']}, time={tk:.3f}ms",
           "Prim(dense)": f"cost={pc}, ops={ps['ops']}, time={tp:.3f}ms",
           "costs_equal": abs(kc - pc) < 1e-9}
    if D < config.DENSITY_THRESHOLD:
        return Decision("Minimum spanning tree, sparse graph", "Kruskal (DSU: union by rank + path compression)",
                        "O(E log E)", "O(V + E)",
                        [("Prim (adjacency matrix)", f"O(V^2)={g.n ** 2} scans, wasteful when E is small")],
                        f"D={D:.2f} < {config.DENSITY_THRESHOLD}: sorting few edges is cheaper than V^2 matrix scans.",
                        props, CLASSES["minimum_spanning_tree"], res)
    return Decision("Minimum spanning tree, dense graph", "Prim (adjacency matrix, no heap)",
                    "O(V^2)", "O(V^2)",
                    [("Kruskal", f"must sort ~{len(g.edges)} edges: O(E log E) ~ O(V^2 log V)")],
                    f"D={D:.2f} >= {config.DENSITY_THRESHOLD}: O(V^2) beats sorting Theta(V^2) edges.",
                    props, CLASSES["minimum_spanning_tree"], res)


def _apsp(req):
    gd = req["graph"]
    g = Graph(gd["n"], gd["edges"], gd.get("directed", True))
    try:
        (d, st), t = _timed(floyd_warshall, g)
        out = {"ops": st["ops"], "time": f"{t:.3f}ms", "dist[0]": [None if x == float('inf') else x for x in d[0]]}
    except NegativeCycleError:
        out = {"error": "NegativeCycleError: shortest paths undefined"}
    return Decision("All-pairs shortest path costs", "Floyd-Warshall (DP over intermediate vertices)",
                    "Theta(V^3)", "Theta(V^2)",
                    [("V x single-source runs", "outside the prescribed syllabus; also needs separate negative-edge handling"),
                     ("Prim/Kruskal", "MST gives a connecting tree, not pairwise shortest costs")],
                    "Every pair (i, j) is needed and V is small enough for cubic time; negative edges are allowed.",
                    {"V": g.n, "E": len(g.edges), "goal": "all_pairs"}, CLASSES["all_pairs_shortest_paths"], out)


def _knapsack(req, divisible):
    items = [tuple(i) for i in req["items"]]
    W = req["capacity"]
    props = {"n": len(items), "capacity": W, "divisible": divisible}
    if divisible:
        v, fr, st = fractional_knapsack(items, W)
        return Decision("Resource allocation with divisible items", "Fractional Knapsack (greedy by value/weight)",
                        "O(n log n)", "O(n)",
                        [("0/1 Knapsack DP", "unnecessary: fractions are allowed so greedy is provably optimal")],
                        "Items may be split (x_i in [0,1]) so the exchange argument on density holds.",
                        props, CLASSES["fractional_knapsack"],
                        {"value": round(v, 3), "fractions": [round(x, 3) for x in fr]})
    v, chosen, st = knapsack_01(items, int(W))
    gv, gc = greedy_density_01(items, int(W))
    return Decision("Resource selection with indivisible items", "0/1 Knapsack (dynamic programming)",
                    "O(nW) pseudo-polynomial", "O(nW)",
                    [("Fractional/greedy by density", f"not optimal for 0/1: greedy value {gv} vs DP optimum {v}")],
                    "Items are all-or-nothing (x_i in {0,1}); greedy can leave capacity unusable, so exact DP is required.",
                    props, CLASSES["knapsack_01"],
                    {"value": v, "chosen": chosen, "dp_states": st["states"], "greedy_value": gv})


def _matrix_chain(req):
    dims = req["matrix_dims"]
    c, p, naive, st = matrix_chain(dims)
    return Decision("Optimal matrix evaluation order", "Matrix Chain Multiplication (interval DP)",
                    "O(m^3)", "O(m^2)",
                    [("Left-to-right multiplication", f"costs {naive} scalar multiplications vs optimal {c}")],
                    "Multiplication is associative but the scalar-multiplication count depends on the parenthesisation.",
                    {"matrices": len(dims) - 1, "dims": dims}, CLASSES["matrix_chain"],
                    {"min_scalar_mults": c, "order": p, "naive_mults": naive, "dp_ops": st["ops"]})


def _hamiltonian(req):
    gd = req["graph"]
    cyc = req.get("return_to_start", False)
    path, st = hamiltonian(gd["n"], gd["edges"], cycle=cyc)
    return Decision("Hamiltonian " + ("cycle" if cyc else "path") + " feasibility",
                    "Backtracking (extend path, prune visited vertices)",
                    "O(V!) worst case", "O(V)",
                    [("Brute-force over all permutations", "no early pruning on missing edges")],
                    "Question is pure feasibility (visit every vertex exactly once); no cost to optimise.",
                    {"V": gd["n"], "E": len(gd["edges"]), "return_to_start": cyc}, CLASSES["hamiltonian"],
                    {"feasible": path is not None, "path": path, "states": st["states"]})


def _nqueens(req):
    gr = req["grid"]
    n, blocked = gr["size"], gr.get("blocked", [])
    first, cnt, st = n_queens(n, blocked, find_all=False)
    return Decision("Conflict-free placement (no two on a shared row/column/diagonal)",
                    "Backtracking with conflict sets (N-Queen formulation)",
                    "O(N!) worst case", "O(N)",
                    [("Brute-force over N^2 choose N placements", "ignores conflicts until the end")],
                    "Mutually conflicting sensors/transmitters on a grid reduce to non-attacking queens.",
                    {"grid": f"{n}x{n}", "obstacles": len(blocked)}, CLASSES["n_queens"],
                    {"feasible": first is not None, "columns_per_row": first, "states": st["states"]})


def _tsp(req):
    C = req["cost_matrix"]
    n = len(C)
    props = {"N_sites": n}
    budget = None if n <= config.TSP_EXACT_LIMIT else config.TSP_BUDGET_STATES
    (bc, tour, st), t = _timed(tsp_branch_and_bound, C, budget)
    res = {"tour": tour, "cost": bc, "bnb_generated": st["generated"], "bnb_pruned": st["pruned"],
           "bnb_time": f"{t:.2f}ms", "proved_optimal": st["complete"]}
    if n <= 9:
        (btc, _, bst), tb = _timed(tsp_backtracking, C)
        res["backtracking_states"] = bst["states"]
        res["backtracking_time"] = f"{tb:.2f}ms"
    why = ("N <= %d: exact search is practical." % config.TSP_EXACT_LIMIT) if n <= config.TSP_EXACT_LIMIT else \
        ("N > %d: exact search is capped at %d generated states; result is the best tour found, NOT proven optimal."
         % (config.TSP_EXACT_LIMIT, config.TSP_BUDGET_STATES))
    tech = "Branch and Bound (reduced-matrix lower bound)" if n <= config.TSP_EXACT_LIMIT else \
        "Budget-capped Branch and Bound (anytime search; result NOT proven optimal)"
    return Decision("Minimum-cost complete tour (TSP)", tech,
                    "O((N-1)!) worst case, far fewer states in practice", "O(N^2) per node; O(N^4) worst case on the recursion stack (N levels x up to N child matrices of N^2)",
                    [("Plain backtracking", "enumerates (N-1)! tours with no bounding")],
                    "Needs the optimal tour, so prune a branch whenever LB >= best known tour. " + why,
                    props, CLASSES["tsp"], res)


def solve(req):
    kind = recognize(req)
    if kind == "unknown":
        raise UnrecognizedProblem("could not map the request to any prescribed DAA problem class")
    handlers = {"index": _index, "priority": _priority, "mst": _mst, "apsp": _apsp,
                "knapsack_fractional": lambda r: _knapsack(r, True),
                "knapsack_01": lambda r: _knapsack(r, False), "matrix_chain": _matrix_chain,
                "hamiltonian": _hamiltonian, "n_queens": _nqueens, "tsp": _tsp}
    return handlers[kind](req)
