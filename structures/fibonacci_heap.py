"""Fibonacci Heap (min-heap) with circular doubly-linked lists, cascading cuts."""


class _Node:
    __slots__ = ("key", "item", "degree", "parent", "child", "left", "right", "mark")

    def __init__(self, key, item):
        self.key, self.item = key, item
        self.degree = 0
        self.parent = self.child = None
        self.left = self.right = self
        self.mark = False


class FibonacciHeap:
    def __init__(self):
        self.min = None
        self.size = 0
        self.nodes = {}
        self.comparisons = 0
        self.links = 0
        self.cuts = 0

    @property
    def ops(self):
        return self.comparisons + self.links + self.cuts

    @staticmethod
    def _splice_in(node, ring):      # insert node to the right of ring
        node.left, node.right = ring, ring.right
        ring.right.left = node
        ring.right = node

    @staticmethod
    def _unlink(node):
        node.left.right = node.right
        node.right.left = node.left

    def _add_root(self, node):
        node.parent = None
        if self.min is None:
            node.left = node.right = node
            self.min = node
        else:
            self._splice_in(node, self.min)
            self.comparisons += 1
            if node.key < self.min.key:
                self.min = node

    def insert(self, key, item):
        node = _Node(key, item)
        self.nodes[item] = node
        self._add_root(node)
        self.size += 1

    def merge(self, other):
        self.nodes.update(other.nodes)
        self.comparisons += other.comparisons
        self.links += other.links
        self.cuts += other.cuts
        if other.min is not None:
            if self.min is None:
                self.min = other.min
            else:
                a, b = self.min, other.min
                a_right, b_left = a.right, b.left
                a.right, b.left = b, a
                a_right.left, b_left.right = b_left, a_right
                self.comparisons += 1
                if other.min.key < self.min.key:
                    self.min = other.min
        self.size += other.size
        other.min, other.size, other.nodes = None, 0, {}

    def find_min(self):
        return None if self.min is None else (self.min.key, self.min.item)

    def _children(self, z):
        out, c = [], z.child
        if c is not None:
            while True:
                out.append(c)
                c = c.right
                if c is z.child:
                    break
        return out

    def extract_min(self):
        z = self.min
        if z is None:
            raise IndexError("empty heap")
        for c in self._children(z):
            c.parent = None
            self._splice_in(c, z)
        self._unlink(z)
        z.child = None
        if z is z.right:
            self.min = None
            roots = []
        else:
            roots = []
            r = z.right
            start = r
            while True:
                roots.append(r)
                r = r.right
                if r is start:
                    break
            self.min = z.right
        self.size -= 1
        del self.nodes[z.item]
        if roots:
            self._consolidate(roots)
        return z.key, z.item

    def _consolidate(self, roots):
        table = {}
        for w in roots:
            x = w
            d = x.degree
            while d in table:
                y = table.pop(d)
                self.comparisons += 1
                if y.key < x.key:
                    x, y = y, x
                self._link(y, x)
                d += 1
            table[d] = x
        self.min = None
        for node in table.values():
            node.left = node.right = node
            node.parent = None
            if self.min is None:
                self.min = node
            else:
                self._splice_in(node, self.min)
                self.comparisons += 1
                if node.key < self.min.key:
                    self.min = node

    def _link(self, y, x):           # y becomes child of x (y already out of root ring)
        self.links += 1
        y.parent = x
        if x.child is None:
            y.left = y.right = y
            x.child = y
        else:
            self._splice_in(y, x.child)
        x.degree += 1
        y.mark = False

    def decrease_key(self, item, new_key):
        x = self.nodes[item]
        if new_key > x.key:
            raise ValueError("new key larger than current key")
        x.key = new_key
        y = x.parent
        self.comparisons += 1
        if y is not None and x.key < y.key:
            self._cut(x, y)
            self._cascading_cut(y)
        self.comparisons += 1
        if x.key < self.min.key:
            self.min = x

    def _cut(self, x, y):
        self.cuts += 1
        if x.right is x:
            y.child = None
        else:
            if y.child is x:
                y.child = x.right
            self._unlink(x)
        y.degree -= 1
        x.mark = False
        x.parent = None
        self._splice_in(x, self.min)

    def _cascading_cut(self, y):
        z = y.parent
        while z is not None:
            if not y.mark:
                y.mark = True
                return
            self._cut(y, z)
            y, z = z, z.parent

    def __len__(self):
        return self.size
