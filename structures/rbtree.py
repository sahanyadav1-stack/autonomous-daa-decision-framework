"""Red-Black Tree (CLRS) with rotation / node-visit counters."""
RED, BLACK = True, False


class _Node:
    __slots__ = ("key", "color", "left", "right", "parent")

    def __init__(self, key, color):
        self.key, self.color = key, color
        self.left = self.right = self.parent = None


class RedBlackTree:
    def __init__(self):
        self.NIL = _Node(None, BLACK)
        self.NIL.left = self.NIL.right = self.NIL.parent = self.NIL
        self.root = self.NIL
        self.size = 0
        self.rotations = 0
        self.visits = 0   # nodes touched by search()

    def _left_rotate(self, x):
        y = x.right
        x.right = y.left
        if y.left is not self.NIL:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is self.NIL:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y
        self.rotations += 1

    def _right_rotate(self, x):
        y = x.left
        x.left = y.right
        if y.right is not self.NIL:
            y.right.parent = x
        y.parent = x.parent
        if x.parent is self.NIL:
            self.root = y
        elif x is x.parent.right:
            x.parent.right = y
        else:
            x.parent.left = y
        y.right = x
        x.parent = y
        self.rotations += 1

    def insert(self, key):
        y, x = self.NIL, self.root
        while x is not self.NIL:
            y = x
            if key == x.key:
                return False
            x = x.left if key < x.key else x.right
        z = _Node(key, RED)
        z.left = z.right = self.NIL
        z.parent = y
        if y is self.NIL:
            self.root = z
        elif key < y.key:
            y.left = z
        else:
            y.right = z
        self._fixup(z)
        self.size += 1
        return True

    def _fixup(self, z):
        while z.parent.color == RED:
            gp = z.parent.parent
            if z.parent is gp.left:
                u = gp.right
                if u.color == RED:
                    z.parent.color = u.color = BLACK
                    gp.color = RED
                    z = gp
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._right_rotate(z.parent.parent)
            else:
                u = gp.left
                if u.color == RED:
                    z.parent.color = u.color = BLACK
                    gp.color = RED
                    z = gp
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._left_rotate(z.parent.parent)
        self.root.color = BLACK

    def search(self, key):
        x = self.root
        while x is not self.NIL:
            self.visits += 1
            if key == x.key:
                return True
            x = x.left if key < x.key else x.right
        return False

    def height(self):
        def h(n):
            return 0 if n is self.NIL else 1 + max(h(n.left), h(n.right))
        return h(self.root)

    def check_invariants(self):
        assert self.root.color == BLACK, "root must be black"

        def walk(n, lo, hi):
            if n is self.NIL:
                return 1
            assert (lo is None or n.key > lo) and (hi is None or n.key < hi), "BST order"
            if n.color == RED:
                assert n.left.color == BLACK and n.right.color == BLACK, "red-red"
            lb = walk(n.left, lo, n.key)
            rb = walk(n.right, n.key, hi)
            assert lb == rb, "black-height mismatch"
            return lb + (1 if n.color == BLACK else 0)
        walk(self.root, None, None)
        return True
