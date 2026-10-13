# Autonomous DAA Decision Framework (Assignment 6)

A decision-support engine that receives a problem request **without being told an algorithm**, recognises the
problem from its properties, selects a syllabus technique with explicit rules, executes it, and explains the choice
(identified problem, technique, expected complexity, rejected alternatives, reason, complexity class).

```
REQUEST -> PROPERTY EXTRACTOR -> PROBLEM RECOGNIZER -> RULE ENGINE -> EXECUTOR (op counters) -> CLASSIFIER -> EXPLAINER
 (data +     (D, share, drop,      (engine.recognize)    (thresholds    (structures/,     (classify.py)   (Decision.render)
  goal)       divisible, N, ...)                          in config.py)  algorithms/)
```

## Run
```bash
python main.py                  # all 10 recognition cases (14 requests) with full explanations
python main.py --adapt          # decisions flipping when ONE property changes
python main.py --file req.json  # your own request
pip install pytest && pytest -q # 53 test cases
python -m benchmarks.run_benchmarks   # regenerates benchmarks/results.md + results.json
```

## Layout
| Path | Contents |
|---|---|
| `structures/` | Red-Black Tree, B-Tree, Binomial Heap, Fibonacci Heap (all with operation counters + invariant checkers) |
| `algorithms/graph.py` | Kruskal (DSU rank + path compression), Prim (dense matrix), Prim (heap, decrease-key), Floyd-Warshall |
| `algorithms/dp.py` | Fractional Knapsack, 0/1 Knapsack, Matrix Chain Multiplication |
| `algorithms/search.py` | Hamiltonian, N-Queen (with obstacles), TSP backtracking, TSP Branch & Bound (reduced-matrix LB) |
| `engine.py`, `classify.py`, `config.py` | recognition, rules, execution, explanation, NP-class catalogue, thresholds |
| `demo_cases.py`, `main.py` | demo requests and CLI |
| `tests/test_all.py` | normal / boundary / large / difficult tests |
| `benchmarks/` | experiments and their measured results |

## Request format (data + semantic goal, never an algorithm name)
```json
{"graph": {"n": 5, "edges": [[0,1,2],[1,2,3],[0,2,1]]}, "goal": "connect_all_min_cost"}
{"items": [[10,60],[20,100],[30,120]], "capacity": 50, "divisible": false}
{"matrix_dims": [40,20,30,10,30]}
{"grid": {"size": 8, "blocked": [[0,0]]}}
{"cost_matrix": [[0,2,9],[1,0,6],[15,7,0]], "goal": "visit_each_and_return_min_cost"}
{"graph": {"n": 6, "edges": [[0,1],[1,2]]}, "goal": "visit_each_vertex_once", "return_to_start": true}
{"index_workload": {"keys": [5,3,9], "storage": "disk"}}
{"heap_ops": [["insert", 10, 0], ["insert", 20, 1], ["decrease_key", 1, 2], ["extract_min"]]}
```
Goals: `connect_all_min_cost`, `all_pairs_costs`, `visit_each_vertex_once`, `visit_each_and_return_min_cost`.

## Decision rules (all thresholds in `config.py`, derived from `benchmarks/results.md`)
- Edge density D < 0.11 -> Kruskal, else dense Prim (crossover measured; by abstract op count it is ~0.38 and it drifts with V).
- Block-resident ordered data -> B-Tree (t=16); memory-resident -> Red-Black Tree.
- Decrease-key share >= 0.05 **and** mean relative key drop >= 0.10 -> Fibonacci Heap, else Binomial Heap.
- Divisible -> Fractional Knapsack; indivisible -> 0/1 Knapsack DP.
- TSP: exact B&B for N <= 14; above that a state budget applies and the answer is flagged *not proven optimal*.

## Known limitations
- Thresholds are measured with this pure-Python implementation on one machine; re-measure on yours.
- Fibonacci Heap won only for *large* decrease-keys; with tiny key drops Binomial won at every share tested.
- Exact TSP effort depends on the instance, not only on N (an N=15 instance exceeded 400k states, an N=18 one did not).
- B&B stores up to N child matrices of N^2 cells per recursion level: O(N^4) worst-case stack space.
- Floyd-Warshall is Theta(V^3) even on sparse graphs; 0/1 DP memory grows linearly with capacity W.

## Publish to GitHub
```bash
git init && git add . && git commit -m "Autonomous DAA Decision Framework"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```
