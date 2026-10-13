"""Binomial Heap (min-heap). Items are unique ids so decrease_key(item, key) works."""


class _Node:
    __slots__ = ("key", "item", "degree", "parent", "child", "sibling")

    def __init__(self, key, item):
        self.key, self.item = key, item
        self.degree = 0
        self.parent = self.child = self.sibling = None


class BinomialHeap:
    def __init__(self):
        self.head = None
        self.size = 0
        self.nodes = {}
        self.comparisons = 0
        self.links = 0
        self.swaps = 0

    @property
    def ops(self):
        return self.comparisons + self.links + self.swaps

    @staticmethod
    def _link(y, z):          # make y a child of z
        y.parent = z
        y.sibling = z.child
        z.child = y
        z.degree += 1

    @staticmethod
    def _merge_lists(a, b):
        dummy = _Node(None, None)
        tail = dummy
        while a and b:
            if a.degree <= b.degree:
                tail.sibling, a = a, a.sibling
            else:
                tail.sibling, b = b, b.sibling
            tail = tail.sibling
        tail.sibling = a or b
        return dummy.sibling

    def _union_head(self, other_head):
        merged = self._merge_lists(self.head, other_head)
        if merged is None:
            self.head = None
            return
        prev, x = None, merged
        nxt = x.sibling
        while nxt:
            if x.degree != nxt.degree or (nxt.sibling and nxt.sibling.degree == x.degree):
                prev, x = x, nxt
            else:
                self.comparisons += 1
                self.links += 1
                if x.key <= nxt.key:
                    x.sibling = nxt.sibling
                    self._link(nxt, x)
                else:
                    if prev is None:
                        merged = nxt
                    else:
                        prev.sibling = nxt
                    self._link(x, nxt)
                    x = nxt
            nxt = x.sibling
        self.head = merged

    def insert(self, key, item):
        node = _Node(key, item)
        self.nodes[item] = node
        self._union_head(node)
        self.size += 1

    def merge(self, other):
        self.nodes.update(other.nodes)
        self.size += other.size
        self._union_head(other.head)
        self.comparisons += other.comparisons
        self.links += other.links
        self.swaps += other.swaps
        other.head, other.size, other.nodes = None, 0, {}

    def find_min(self):
        best, x = None, self.head
        while x:
            self.comparisons += 1
            if best is None or x.key < best.key:
                best = x
            x = x.sibling
        return None if best is None else (best.key, best.item)

    def extract_min(self):
        if self.head is None:
            raise IndexError("empty heap")
        prev, best, bprev = None, self.head, None
        x = self.head
        while x:
            self.comparisons += 1
            if x.key < best.key:
                best, bprev = x, prev
            prev, x = x, x.sibling
        if bprev is None:
            self.head = best.sibling
        else:
            bprev.sibling = best.sibling
        # reverse best's child list into a new root list
        rev, c = None, best.child
        while c:
            nxt = c.sibling
            c.sibling = rev
            c.parent = None
            rev, c = c, nxt
        self._union_head(rev)
        self.size -= 1
        del self.nodes[best.item]
        return best.key, best.item

    def decrease_key(self, item, new_key):
        y = self.nodes[item]
        if new_key > y.key:
            raise ValueError("new key larger than current key")
        y.key = new_key
        z = y.parent
        while z is not None and y.key < z.key:
            self.comparisons += 1
            self.swaps += 1
            y.key, z.key = z.key, y.key
            y.item, z.item = z.item, y.item
            self.nodes[y.item], self.nodes[z.item] = y, z
            y, z = z, z.parent
        if z is not None:
            self.comparisons += 1

    def __len__(self):
        return self.size
