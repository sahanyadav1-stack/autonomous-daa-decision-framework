import itertools
import math
import random

import pytest

import config
from algorithms.dp import fractional_knapsack, greedy_density_01, knapsack_01, matrix_chain
from algorithms.graph import (DisjointSet, Graph, GraphDisconnectedError, NegativeCycleError,
                              floyd_warshall, kruskal, prim_dense, prim_heap)
from algorithms.search import hamiltonian, n_queens, tsp_backtracking, tsp_branch_and_bound
from demo_cases import ADAPTATIONS, CASES
from engine import UnrecognizedProblem, recognize, solve
from structures.binomial_heap import BinomialHeap
from structures.btree import BTree
from structures.fibonacci_heap import FibonacciHeap
from structures.rbtree import RedBlackTree


def rand_graph(n, m, seed=0):
    rnd = random.Random(seed)
    edges, seen = [], set()
    for v in range(1, n):
        u = rnd.randrange(v)
        edges.append((u, v, rnd.randint(1, 50)))
        seen.add((u, v))
    while len(edges) < m:
        u, v = rnd.sample(range(n), 2)
        a, b = min(u, v), max(u, v)
        if (a, b) not in seen:
            seen.add((a, b))
            edges.append((a, b, rnd.randint(1, 50)))
    return Graph(n, edges)


def euclid(n, seed):
    rnd = random.Random(seed)
    p = [(rnd.random() * 100, rnd.random() * 100) for _ in range(n)]
    return [[round(math.dist(a, b), 2) for b in p] for a in p]


# ------------------------------------------------------------------ trees
@pytest.mark.parametrize("order", ["sequential", "random", "reverse"])
def test_rbt_invariants_and_height(order):
    keys = list(range(2000))
    if order == "random":
        random.Random(1).shuffle(keys)
    if order == "reverse":
        keys.reverse()
    t = RedBlackTree()
    for k in keys:
        t.insert(k)
    assert t.check_invariants()
    assert t.size == 2000 and all(t.search(k) for k in keys) and not t.search(-1)
    assert t.height() <= 2 * math.log2(t.size + 1)


@pytest.mark.parametrize("deg", [2, 3, 16])
@pytest.mark.parametrize("order", ["sequential", "random"])
def test_btree_invariants(deg, order):
    keys = list(range(1500))
    if order == "random":
        random.Random(2).shuffle(keys)
    t = BTree(deg)
    for k in keys:
        t.insert(k)
    assert t.check_invariants()
    assert all(t.search(k) for k in keys) and not t.search(10 ** 9)


def test_tree_duplicates_ignored():
    for t in (RedBlackTree(), BTree(4)):
        assert t.insert(5) and not t.insert(5)
        assert t.size == 1


def test_btree_shallower_than_rbt():
    keys = random.Random(3).sample(range(10 ** 6), 20000)
    r, b = RedBlackTree(), BTree(16)
    for k in keys:
        r.insert(k)
        b.insert(k)
    assert b.height() < r.height() / 3


# ------------------------------------------------------------------ heaps
@pytest.mark.parametrize("H", [BinomialHeap, FibonacciHeap])
def test_heap_sorted_extraction_with_decrease_key(H):
    rnd = random.Random(4)
    h, cur = H(), {}
    for i in range(800):
        cur[i] = rnd.randint(1000, 5000)
        h.insert(cur[i], i)
    for _ in range(500):
        i = rnd.choice(list(cur))
        cur[i] = max(0, cur[i] - rnd.randint(0, 800))
        h.decrease_key(i, cur[i])
    out = []
    while len(h):
        k, i = h.extract_min()
        assert cur[i] == k
        out.append(k)
    assert out == sorted(cur.values())


@pytest.mark.parametrize("H", [BinomialHeap, FibonacciHeap])
def test_heap_merge_and_errors(H):
    a, b = H(), H()
    for i in range(50):
        a.insert(i * 2, ("a", i))
        b.insert(i * 2 + 1, ("b", i))
    a.merge(b)
    assert len(a) == 100 and len(b) == 0
    assert [a.extract_min()[0] for _ in range(100)] == list(range(100))
    with pytest.raises(IndexError):
        a.extract_min()
    a.insert(5, "x")
    with pytest.raises(ValueError):
        a.decrease_key("x", 9)


def test_fibonacci_cascading_cuts_happen():
    h = FibonacciHeap()
    for i in range(64):
        h.insert(1000 + i, i)
    h.insert(0, "m")
    h.extract_min()                       # consolidates into deep trees
    for i in range(63, 0, -1):
        h.decrease_key(i, i)              # forces cuts
    assert h.cuts > 0
    assert [h.extract_min()[0] for _ in range(len(h))] == list(range(1, 64)) + [1000]


def test_binomial_merge_cost_logarithmic_vs_fib_constant():
    def merge_ops(H, n):
        a, b = H(), H()
        for i in range(n):
            a.insert(2 * i, ("a", i))
            b.insert(2 * i + 1, ("b", i))
        before = a.ops + b.ops          # work already done building the two heaps
        a.merge(b)
        return a.ops - before           # work done by the merge itself
    assert merge_ops(FibonacciHeap, 4000) <= 1                      # O(1)
    assert 1 <= merge_ops(BinomialHeap, 4000) <= 2 * math.log2(8000) + 2   # O(log n)


# ------------------------------------------------------------------ MST / FW
@pytest.mark.parametrize("n,m", [(2, 1), (10, 20), (30, 60), (30, 400), (60, 1700)])
def test_mst_algorithms_agree(n, m):
    g = rand_graph(n, m, n + m)
    kc, kt, _ = kruskal(g)
    pc, pt, _ = prim_dense(g)
    bc, _, _ = prim_heap(g, BinomialHeap)
    fc, _, _ = prim_heap(g, FibonacciHeap)
    assert kc == pc == bc == fc
    assert len(kt) == len(pt) == n - 1


def test_mst_single_vertex_and_disconnected():
    assert kruskal(Graph(1, []))[0] == 0
    assert prim_dense(Graph(1, []))[0] == 0
    g = Graph(4, [(0, 1, 1), (2, 3, 1)])
    for f in (kruskal, prim_dense):
        with pytest.raises(GraphDisconnectedError):
            f(g)
    with pytest.raises(GraphDisconnectedError):
        prim_heap(g, BinomialHeap)


def test_dsu_find_union():
    d = DisjointSet(5)
    assert d.union(0, 1) and d.union(1, 2) and not d.union(0, 2)
    assert d.find(0) == d.find(2) != d.find(4)


def test_floyd_warshall_correct_and_cubic():
    g = Graph(4, [(0, 1, 5), (1, 2, -2), (2, 3, 1), (0, 3, 10)], directed=True)
    d, st = floyd_warshall(g)
    assert d[0][3] == 4 and d[0][2] == 3
    assert st["ops"] == 4 ** 3
    ops = [floyd_warshall(Graph(n, [(i, (i + 1) % n, 1) for i in range(n)], True))[1]["ops"] for n in (10, 20, 40)]
    assert ops[1] == 8 * ops[0] and ops[2] == 8 * ops[1]


def test_floyd_warshall_negative_cycle():
    with pytest.raises(NegativeCycleError):
        floyd_warshall(Graph(3, [(0, 1, 1), (1, 2, -3), (2, 0, 1)], directed=True))


# ------------------------------------------------------------------ knapsack / MCM
def test_greedy_fails_on_01_but_fractional_is_optimal():
    items = [(10, 60), (20, 100), (30, 120)]
    fv, _, _ = fractional_knapsack(items, 50)
    dv, chosen, _ = knapsack_01(items, 50)
    gv, _ = greedy_density_01(items, 50)
    assert fv == 240 and dv == 220 and gv == 160 and chosen == [1, 2]


def test_knapsack_matches_bruteforce():
    rnd = random.Random(5)
    for _ in range(30):
        items = [(rnd.randint(1, 15), rnd.randint(1, 40)) for _ in range(8)]
        W = rnd.randint(5, 40)
        best = max(sum(items[i][1] for i in s) for r in range(9) for s in itertools.combinations(range(8), r)
                   if sum(items[i][0] for i in s) <= W)
        assert knapsack_01(items, W)[0] == best


def test_knapsack_boundaries():
    assert knapsack_01([], 10)[0] == 0
    assert knapsack_01([(5, 10)], 0)[0] == 0
    assert knapsack_01([(5, 10)], 4)[0] == 0
    assert fractional_knapsack([(4, 8)], 2)[0] == 4.0


def test_knapsack_dp_states_grow_with_capacity():
    items = [(3, 4)] * 20
    assert knapsack_01(items, 200)[2]["states"] == 20 * 201
    assert knapsack_01(items, 2000)[2]["states"] == 20 * 2001      # linear in W (pseudo-polynomial)


def test_matrix_chain():
    c, p, naive, st = matrix_chain([40, 20, 30, 10, 30])
    assert c == 26000 and naive > c
    assert matrix_chain([10, 20])[0] == 0 and matrix_chain([5, 6, 7])[0] == 210
    # brute force over all parenthesisations
    dims = [5, 10, 3, 12, 5, 50, 6]

    def brute(i, j):
        return 0 if i == j else min(brute(i, k) + brute(k + 1, j) + dims[i] * dims[k + 1] * dims[j + 1] for k in range(i, j))
    assert matrix_chain(dims)[0] == brute(0, 5)


# ------------------------------------------------------------------ search
def test_n_queens_known_counts():
    assert [n_queens(n, (), True)[1] for n in range(1, 9)] == [1, 0, 0, 2, 10, 4, 40, 92]


def test_n_queens_solution_valid_and_blocked():
    sol, _, _ = n_queens(8, [(0, 0), (1, 2)])
    assert sol is not None and sol[0] != 0 and sol[1] != 2
    assert len({c for c in sol}) == 8 and len({r - c for r, c in enumerate(sol)}) == 8 and len({r + c for r, c in enumerate(sol)}) == 8
    assert n_queens(3)[0] is None


def test_hamiltonian():
    assert hamiltonian(5, [(0, 1), (1, 2), (2, 3), (3, 4)])[0] is not None
    assert hamiltonian(4, [(0, 1), (0, 2), (0, 3)])[0] is None          # star: no Hamiltonian path
    assert hamiltonian(4, [(0, 1), (1, 2), (2, 3)], cycle=True)[0] is None
    assert hamiltonian(4, [(0, 1), (1, 2), (2, 3), (3, 0)], cycle=True)[0] is not None
    assert hamiltonian(1, [])[0] == [0]


@pytest.mark.parametrize("n", [2, 3, 5, 6, 7, 8])
def test_tsp_bnb_equals_bruteforce(n):
    for seed in range(4):
        C = euclid(n, seed * 10 + n)
        bf = min(sum(C[p[i]][p[i + 1]] for i in range(n - 1)) + C[p[-1]][0]
                 for p in ((0,) + q for q in itertools.permutations(range(1, n))))
        bt, _, _ = tsp_backtracking(C)
        bb, tour, st = tsp_branch_and_bound(C)
        assert abs(bt - bf) < 1e-6 and abs(bb - bf) < 1e-6
        assert tour[0] == tour[-1] == 0 and sorted(tour[:-1]) == list(range(n))
        assert abs(sum(C[tour[i]][tour[i + 1]] for i in range(n)) - bb) < 1e-6


def test_tsp_bnb_prunes_massively_and_budget_flag():
    C = euclid(9, 1)
    bt = tsp_backtracking(C)[2]["states"]
    st = tsp_branch_and_bound(C)[2]
    assert st["generated"] < 0.1 * bt and st["pruned"] > 0
    _, _, capped = tsp_branch_and_bound(euclid(18, 3), 2000)
    assert capped["complete"] is False


# ------------------------------------------------------------------ decision engine
def test_every_demo_case_recognised_and_explained():
    for title, req in CASES:
        d = solve(req)
        assert d.technique and d.rejected and d.reason and d.classification["status"], title
        assert d.time_complexity and d.space_complexity


@pytest.mark.parametrize("title,a,b", ADAPTATIONS)
def test_changing_one_property_changes_decision(title, a, b):
    assert solve(a).technique != solve(b).technique


def test_decisions_do_not_depend_on_names():
    req = {"graph": {"n": 30, "edges": [(i, i + 1, 1 + i) for i in range(29)]}, "goal": "connect_all_min_cost",
           "algorithm": "prim"}                     # a user-supplied name must be ignored
    assert "Kruskal" in solve(req).technique


def test_engine_density_rule_matches_config():
    sparse = {"graph": {"n": 30, "edges": [(i, i + 1, 1) for i in range(29)]}, "goal": "connect_all_min_cost"}
    dense = {"graph": {"n": 30, "edges": [(i, j, 1 + (i + j) % 9) for i in range(30) for j in range(i + 1, 30)]},
             "goal": "connect_all_min_cost"}
    assert "Kruskal" in solve(sparse).technique and "Prim" in solve(dense).technique
    assert solve(dense).result["costs_equal"]


def test_unrecognised_request():
    assert recognize({"hello": 1}) == "unknown"
    with pytest.raises(UnrecognizedProblem):
        solve({"hello": 1})


def test_classification_distinguishes_forms():
    tsp = solve(CASES[-2][1]).classification
    assert "NP-Hard" in tsp["optimization"] and "NP-Complete" in tsp["decision"]
    q = solve({"grid": {"size": 8}}).classification
    assert "Not NP-Complete" in q["status"]
    k = solve({"items": [(1, 2)], "capacity": 3, "divisible": False}).classification
    assert "pseudo" in k["status"].lower()
    h = solve({"graph": {"n": 3, "edges": [(0, 1), (1, 2)]}, "goal": "visit_each_vertex_once"}).classification
    assert "NP-Complete" in h["decision"]


def test_tsp_over_limit_is_flagged_not_optimal():
    d = solve(CASES[-1][1])
    assert d.result["proved_optimal"] is False and "NOT proven optimal" in d.technique
