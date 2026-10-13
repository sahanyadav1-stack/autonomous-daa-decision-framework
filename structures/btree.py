"""B-Tree of minimum degree t with split / node-read counters."""
from bisect import bisect_left, insort


class _Node:
    __slots__ = ("keys", "children", "leaf")

    def __init__(self, leaf):
        self.keys, self.children, self.leaf = [], [], leaf


class BTree:
    def __init__(self, t=16):
        assert t >= 2
        self.t = t
        self.root = _Node(True)
        self.size = 0
        self.splits = 0
        self.node_reads = 0   # nodes touched by search() == block reads

    def _contains(self, key):
        n = self.root
        while True:
            i = bisect_left(n.keys, key)
            if i < len(n.keys) and n.keys[i] == key:
                return True
            if n.leaf:
                return False
            n = n.children[i]

    def search(self, key):
        n = self.root
        while True:
            self.node_reads += 1
            i = bisect_left(n.keys, key)
            if i < len(n.keys) and n.keys[i] == key:
                return True
            if n.leaf:
                return False
            n = n.children[i]

    def _split_child(self, parent, i):
        t = self.t
        y = parent.children[i]
        z = _Node(y.leaf)
        mid = y.keys[t - 1]
        z.keys = y.keys[t:]
        y.keys = y.keys[:t - 1]
        if not y.leaf:
            z.children = y.children[t:]
            y.children = y.children[:t]
        parent.keys.insert(i, mid)
        parent.children.insert(i + 1, z)
        self.splits += 1

    def insert(self, key):
        if self._contains(key):
            return False
        t = self.t
        if len(self.root.keys) == 2 * t - 1:
            s = _Node(False)
            s.children = [self.root]
            self.root = s
            self._split_child(s, 0)
        node = self.root
        while not node.leaf:
            i = bisect_left(node.keys, key)
            if len(node.children[i].keys) == 2 * t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            node = node.children[i]
        insort(node.keys, key)
        self.size += 1
        return True

    def height(self):
        h, n = 1, self.root
        while not n.leaf:
            n = n.children[0]
            h += 1
        return h

    def check_invariants(self):
        t = self.t
        depths = set()

        def walk(n, d, lo, hi, is_root):
            if not is_root:
                assert t - 1 <= len(n.keys) <= 2 * t - 1, "key count bounds"
            else:
                assert len(n.keys) <= 2 * t - 1
            assert n.keys == sorted(n.keys)
            for k in n.keys:
                assert (lo is None or k > lo) and (hi is None or k < hi), "order"
            if n.leaf:
                depths.add(d)
                return
            assert len(n.children) == len(n.keys) + 1
            bounds = [lo] + n.keys + [hi]
            for i, c in enumerate(n.children):
                walk(c, d + 1, bounds[i], bounds[i + 1], False)
        walk(self.root, 1, None, None, True)
        assert len(depths) == 1, "all leaves same depth"
        return True
