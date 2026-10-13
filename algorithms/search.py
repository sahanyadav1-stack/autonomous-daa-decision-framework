"""Backtracking / Branch and Bound: Hamiltonian, N-Queen, TSP (plain backtracking and reduced-matrix B&B)."""
INF = float("inf")


def hamiltonian(n, edges, cycle=False, max_states=None):
    """Backtracking. Returns (path or None, stats). Worst case O(n!)."""
    adj = [set() for _ in range(n)]
    for e in edges:
        u, v = e[0], e[1]
        adj[u].add(v)
        adj[v].add(u)
    states = [0]
    path, seen = [], [False] * n
    limit_hit = [False]

    def dfs(u):
        if limit_hit[0]:
            return False
        if len(path) == n:
            return (not cycle) or (path[0] in adj[u])
        for v in sorted(adj[u]):
            if not seen[v]:
                states[0] += 1
                if max_states is not None and states[0] > max_states:
                    limit_hit[0] = True
                    return False
                seen[v] = True
                path.append(v)
                if dfs(v):
                    return True
                path.pop()
                seen[v] = False
        return False

    starts = [0] if cycle else range(n)
    for s in starts:
        path[:] = [s]
        seen[:] = [False] * n
        seen[s] = True
        if dfs(s):
            return list(path), {"states": states[0], "complete": True}
        if limit_hit[0]:
            break
    return None, {"states": states[0], "complete": not limit_hit[0]}


def n_queens(n, blocked=(), find_all=False):
    """Row-wise backtracking with column/diagonal conflict sets.
    blocked: cells (r, c) unusable (obstacles). Returns (first_solution, count, stats)."""
    blocked = set(map(tuple, blocked))
    cols, d1, d2 = set(), set(), set()
    placement, first, count, states = [], [None], [0], [0]

    def place(r):
        if r == n:
            count[0] += 1
            if first[0] is None:
                first[0] = list(placement)
            return not find_all
        for c in range(n):
            if c in cols or (r - c) in d1 or (r + c) in d2 or (r, c) in blocked:
                continue
            states[0] += 1
            cols.add(c); d1.add(r - c); d2.add(r + c); placement.append(c)
            if place(r + 1):
                return True
            cols.discard(c); d1.discard(r - c); d2.discard(r + c); placement.pop()
        return False

    place(0)
    return first[0], count[0], {"states": states[0]}


def tsp_backtracking(C, max_states=None):
    """Plain DFS over permutations, no pruning. Returns (cost, tour, stats). O((n-1)!)."""
    n = len(C)
    best, best_tour, states = [INF], [None], [0]
    path, seen = [0], [False] * n
    seen[0] = True
    stop = [False]

    def dfs(u, cost):
        if stop[0]:
            return
        if len(path) == n:
            total = cost + C[u][0]
            if total < best[0]:
                best[0], best_tour[0] = total, path + [0]
            return
        for v in range(n):
            if not seen[v]:
                states[0] += 1
                if max_states is not None and states[0] > max_states:
                    stop[0] = True
                    return
                seen[v] = True
                path.append(v)
                dfs(v, cost + C[u][v])
                path.pop()
                seen[v] = False
    if n == 1:
        return 0, [0, 0], {"states": 0, "complete": True}
    dfs(0, 0)
    return best[0], best_tour[0], {"states": states[0], "complete": not stop[0]}


def _reduce(m):
    """In-place row/column reduction of cost matrix. Returns total subtracted (lower-bound increment)."""
    n, total = len(m), 0
    for i in range(n):
        r = min(m[i])
        if r != INF and r > 0:
            total += r
            m[i] = [x - r for x in m[i]]
    for j in range(n):
        c = min(m[i][j] for i in range(n))
        if c != INF and c > 0:
            total += c
            for i in range(n):
                m[i][j] -= c
    return total


def tsp_branch_and_bound(C, max_states=None):
    """Depth-first B&B with reduced-cost-matrix lower bound (Little et al.). LB <= OPT, prune if LB >= best.
    Returns (cost, tour, stats{generated, pruned, expanded, max_depth, complete})."""
    n = len(C)
    if n == 1:
        return 0, [0, 0], {"generated": 0, "pruned": 0, "expanded": 0, "complete": True}
    root = [row[:] for row in C]
    for i in range(n):
        root[i][i] = INF
    lb0 = _reduce(root)
    best, best_path = [INF], [None]
    st = {"generated": 1, "pruned": 0, "expanded": 0, "complete": True}
    stop = [False]

    def rec(m, lb, path):
        if stop[0]:
            return
        st["expanded"] += 1
        i = path[-1]
        if len(path) == n:
            if lb < best[0]:
                best[0], best_path[0] = lb, path + [0]
            return
        kids = []
        for j in range(n):
            if j in path or m[i][j] == INF:
                continue
            cm = [row[:] for row in m]
            step = cm[i][j]
            cm[i] = [INF] * n
            for r in range(n):
                cm[r][j] = INF
            if len(path) + 1 < n:
                cm[j][0] = INF
            clb = lb + step + _reduce(cm)
            st["generated"] += 1
            kids.append((clb, j, cm))
            if max_states is not None and st["generated"] > max_states:
                stop[0] = True
                st["complete"] = False
                return
        kids.sort(key=lambda t: t[0])
        for clb, j, cm in kids:
            if clb >= best[0]:
                st["pruned"] += 1
                continue
            rec(cm, clb, path + [j])
            if stop[0]:
                return

    rec(root, lb0, [0])
    return best[0], best_path[0], st
