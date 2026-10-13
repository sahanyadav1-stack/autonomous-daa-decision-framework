"""Demo requests: the 10 recognition cases + adaptation pairs. Requests carry data and semantic goals only."""
import random


def _rand_graph(n, m, seed=7, wmax=100):
    rnd = random.Random(seed)
    edges, seen = [], set()
    for v in range(1, n):
        u = rnd.randrange(v)
        edges.append((u, v, rnd.randint(1, wmax)))
        seen.add((u, v))
    while len(edges) < m:
        u, v = rnd.sample(range(n), 2)
        a, b = min(u, v), max(u, v)
        if (a, b) not in seen:
            seen.add((a, b))
            edges.append((a, b, rnd.randint(1, wmax)))
    return {"n": n, "edges": edges}


def _tsp_matrix(n, seed=3):
    rnd = random.Random(seed)
    pts = [(rnd.random() * 100, rnd.random() * 100) for _ in range(n)]
    return [[round(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5, 2) if a != b else 0 for b in pts] for a in pts]


def _heap_ops(n, dk_share, big_drop=True, seed=5):
    rnd = random.Random(seed)
    ops = [("insert", rnd.randint(10_000, 1_000_000), i) for i in range(n)]
    cur = {i: ops[i][1] for i in range(n)}
    for _ in range(n):
        if rnd.random() < dk_share:
            i = rnd.randrange(n)
            cur[i] = rnd.randint(0, cur[i] - 1) if big_drop else max(0, cur[i] - rnd.randint(1, 50))
            ops.append(("decrease_key", i, cur[i]))
        else:
            ops.append(("extract_min",))
    return ops


CASES = [
    ("1a. Ordered data, in memory", {"index_workload": {"keys": random.Random(1).sample(range(10 ** 6), 2000), "storage": "memory"}}),
    ("1b. Ordered data, on disk", {"index_workload": {"keys": random.Random(1).sample(range(10 ** 6), 2000), "storage": "disk"}}),
    ("2a. Priorities: few decrease-keys", {"heap_ops": _heap_ops(2000, 0.0)}),
    ("2b. Priorities: decrease-key storm (large drops)", {"heap_ops": _heap_ops(2000, 0.50, True)}),
    ("2c. Priorities: many decrease-keys, tiny drops", {"heap_ops": _heap_ops(2000, 0.50, False)}),
    ("3a. Network connection, sparse", {"graph": _rand_graph(40, 70), "goal": "connect_all_min_cost"}),
    ("3b. Network connection, dense", {"graph": _rand_graph(40, 600), "goal": "connect_all_min_cost"}),
    ("4. All-pairs costs", {"graph": dict(_rand_graph(12, 40), directed=True), "goal": "all_pairs_costs"}),
    ("5a. Divisible resource", {"items": [(10, 60), (20, 100), (30, 120)], "capacity": 50, "divisible": True}),
    ("5b. Indivisible resource", {"items": [(10, 60), (20, 100), (30, 120)], "capacity": 50, "divisible": False}),
    ("6. Matrix evaluation order", {"matrix_dims": [40, 20, 30, 10, 30]}),
    ("7. Visit-every-vertex feasibility", {"graph": {"n": 6, "edges": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0), (1, 4)]},
                                           "goal": "visit_each_vertex_once", "return_to_start": True}),
    ("8. Conflict-free sensor placement", {"grid": {"size": 8, "blocked": [(0, 0), (3, 3)], "rule": "no_shared_row_col_diag"}}),
    ("9. Minimum complete tour (8 sites)", {"cost_matrix": _tsp_matrix(8), "goal": "visit_each_and_return_min_cost"}),
    ("9b. Same, 18 sites", {"cost_matrix": _tsp_matrix(18), "goal": "visit_each_and_return_min_cost"}),
]

_BY = {t[:2]: r for t, r in CASES}

# (title, request A, request B): ONE property changes, the decision must change.
ADAPTATIONS = [
    ("MST density", _BY["3a"], _BY["3b"]),
    ("Resource divisibility", _BY["5a"], _BY["5b"]),
    ("Heap decrease-key share", _BY["2a"], _BY["2b"]),
    ("Heap decrease-key SIZE (share fixed at 0.5)", _BY["2b"], _BY["2c"]),
    ("Index storage tier", _BY["1a"], _BY["1b"]),
    ("TSP size (exact vs budget-capped)", _BY["9."], _BY["9b"]),
]
