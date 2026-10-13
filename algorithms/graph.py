"""Graph algorithms: Kruskal (DSU), Prim (dense matrix and heap), Floyd-Warshall."""
INF = float("inf")


class GraphDisconnectedError(Exception):
    pass


class NegativeCycleError(Exception):
    pass


class Graph:
    """Undirected/directed weighted graph on vertices 0..n-1 (edge list is the source of truth)."""

    def __init__(self, n, edges, directed=False):
        self.n, self.edges, self.directed = n, [tuple(e) for e in edges], directed

    @property
    def density(self):
        if self.n < 2:
            return 0.0
        possible = self.n * (self.n - 1) / (1 if self.directed else 2)
        return len(self.edges) / possible

    def matrix(self):
        m = [[INF] * self.n for _ in range(self.n)]
        for i in range(self.n):
            m[i][i] = 0
        for u, v, w in self.edges:
            if w < m[u][v]:
                m[u][v] = w
            if not self.directed and w < m[v][u]:
                m[v][u] = w
        return m

    def adj(self):
        a = [[] for _ in range(self.n)]
        for u, v, w in self.edges:
            a[u].append((v, w))
            if not self.directed:
                a[v].append((u, w))
        return a


class DisjointSet:
    def __init__(self, n):
        self.p, self.r, self.find_calls = list(range(n)), [0] * n, 0

    def find(self, x):
        self.find_calls += 1
        root = x
        while self.p[root] != root:
            root = self.p[root]
        while self.p[x] != root:          # path compression
            self.p[x], x = root, self.p[x]
        return root

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.r[ra] < self.r[rb]:
            ra, rb = rb, ra
        self.p[rb] = ra
        if self.r[ra] == self.r[rb]:
            self.r[ra] += 1
        return True


def merge_sort(items, key, counter):
    """Bottom-up merge sort that counts comparisons in counter[0]."""
    a = list(items)
    n, width = len(a), 1
    while width < n:
        out = []
        for lo in range(0, n, 2 * width):
            mid, hi = min(lo + width, n), min(lo + 2 * width, n)
            i, j = lo, mid
            while i < mid and j < hi:
                counter[0] += 1
                if key(a[j]) < key(a[i]):
                    out.append(a[j]); j += 1
                else:
                    out.append(a[i]); i += 1
            out.extend(a[i:mid])
            out.extend(a[j:hi])
        a, width = out, width * 2
    return a


def kruskal(g):
    """O(E log E). Returns (cost, edges, stats)."""
    cmp = [0]
    ordered = merge_sort(g.edges, lambda e: e[2], cmp)
    ds, tree, cost = DisjointSet(g.n), [], 0
    for u, v, w in ordered:
        if ds.union(u, v):
            tree.append((u, v, w))
            cost += w
            if len(tree) == g.n - 1:
                break
    if len(tree) != max(g.n - 1, 0):
        raise GraphDisconnectedError("graph is not connected")
    return cost, tree, {"sort_comparisons": cmp[0], "find_calls": ds.find_calls,
                        "ops": cmp[0] + ds.find_calls}


def prim_dense(g):
    """O(V^2) adjacency-matrix Prim (no heap)."""
    n, m = g.n, g.matrix()
    if n == 0:
        return 0, [], {"ops": 0}
    key, parent, used = [INF] * n, [-1] * n, [False] * n
    key[0], ops, cost, tree = 0, 0, 0, []
    for _ in range(n):
        u, best = -1, INF
        for v in range(n):
            ops += 1
            if not used[v] and key[v] < best:
                u, best = v, key[v]
        if u == -1:
            raise GraphDisconnectedError("graph is not connected")
        used[u] = True
        if parent[u] != -1:
            tree.append((parent[u], u, best))
            cost += best
        row = m[u]
        for v in range(n):
            ops += 1
            if not used[v] and row[v] < key[v]:
                key[v], parent[v] = row[v], u
    return cost, tree, {"ops": ops}


def prim_heap(g, heap_cls):
    """Prim with a priority queue using decrease-key: O(E log V) binomial, O(E + V log V) Fibonacci."""
    n, adj = g.n, g.adj()
    if n == 0:
        return 0, [], {"ops": 0}
    key, parent, used = [INF] * n, [-1] * n, [False] * n
    h = heap_cls()
    for v in range(n):
        h.insert(0 if v == 0 else INF, v)
    key[0], cost, tree, decs = 0, 0, [], 0
    for _ in range(n):
        k, u = h.extract_min()
        if k == INF:
            raise GraphDisconnectedError("graph is not connected")
        used[u] = True
        if parent[u] != -1:
            tree.append((parent[u], u, k))
            cost += k
        for v, w in adj[u]:
            if not used[v] and w < key[v]:
                key[v], parent[v] = w, u
                h.decrease_key(v, w)
                decs += 1
    return cost, tree, {"ops": h.ops, "decrease_keys": decs}


def floyd_warshall(g):
    """Theta(V^3) time, Theta(V^2) space. Raises NegativeCycleError."""
    n = g.n
    d = g.matrix()
    ops = 0
    for k in range(n):
        dk = d[k]
        for i in range(n):
            di = d[i]
            dik = di[k]
            for j in range(n):
                ops += 1
                s = dik + dk[j]
                if s < di[j]:
                    di[j] = s
    if any(d[i][i] < 0 for i in range(n)):
        raise NegativeCycleError("negative cycle detected")
    return d, {"ops": ops}
