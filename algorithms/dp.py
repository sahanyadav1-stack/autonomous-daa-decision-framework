"""Fractional Knapsack (greedy), 0/1 Knapsack (DP), Matrix Chain Multiplication (DP)."""


def fractional_knapsack(items, capacity):
    """items: list of (weight, value). Returns (value, fractions, stats). O(n log n)."""
    n = len(items)
    order = sorted(range(n), key=lambda i: items[i][1] / items[i][0], reverse=True)
    fr, rem, val = [0.0] * n, capacity, 0.0
    for i in order:
        w, v = items[i]
        if rem <= 0:
            break
        take = min(1.0, rem / w)
        fr[i] = take
        val += take * v
        rem -= take * w
    return val, fr, {"ops": n}


def knapsack_01(items, capacity):
    """items: list of (int weight, value). Returns (value, chosen indices, stats). O(nW) time and space."""
    n = len(items)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    states = 0
    for i in range(1, n + 1):
        w, v = items[i - 1]
        prev, cur = dp[i - 1], dp[i]
        for c in range(capacity + 1):
            states += 1
            cur[c] = prev[c]
            if w <= c and prev[c - w] + v > cur[c]:
                cur[c] = prev[c - w] + v
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if dp[i][c] != dp[i - 1][c]:
            chosen.append(i - 1)
            c -= items[i - 1][0]
    return dp[n][capacity], sorted(chosen), {"states": states, "table_cells": (n + 1) * (capacity + 1)}


def greedy_density_01(items, capacity):
    """Density-greedy used as a *0/1 heuristic*: shows why greedy is not exact for 0/1."""
    order = sorted(range(len(items)), key=lambda i: items[i][1] / items[i][0], reverse=True)
    rem, val, chosen = capacity, 0, []
    for i in order:
        if items[i][0] <= rem:
            rem -= items[i][0]
            val += items[i][1]
            chosen.append(i)
    return val, sorted(chosen)


def matrix_chain(dims):
    """dims has length m+1 for m matrices. Returns (min_cost, parenthesisation, naive_cost, stats). O(m^3)."""
    m = len(dims) - 1
    if m < 1:
        return 0, "", 0, {"ops": 0}
    cost = [[0] * m for _ in range(m)]
    split = [[0] * m for _ in range(m)]
    ops = 0
    for length in range(2, m + 1):
        for i in range(m - length + 1):
            j = i + length - 1
            cost[i][j] = float("inf")
            for k in range(i, j):
                ops += 1
                c = cost[i][k] + cost[k + 1][j] + dims[i] * dims[k + 1] * dims[j + 1]
                if c < cost[i][j]:
                    cost[i][j], split[i][j] = c, k

    def paren(i, j):
        if i == j:
            return f"A{i + 1}"
        k = split[i][j]
        return f"({paren(i, k)} x {paren(k + 1, j)})"

    naive = sum(dims[0] * dims[k] * dims[k + 1] for k in range(1, m))   # ((A1A2)A3)...
    return cost[0][m - 1], paren(0, m - 1), naive, {"ops": ops}
