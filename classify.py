"""Complexity-class catalogue (decision vs optimisation forms stated separately)."""

CLASSES = {
    "ordered_dynamic_set": {
        "status": "Polynomial", "optimization": "n/a (data-structure problem)", "decision": "n/a",
        "note": "Search/insert are O(log n) for both RBT and B-Tree; nothing NP-related."},
    "mergeable_priority_queue": {
        "status": "Polynomial", "optimization": "n/a (data-structure problem)", "decision": "n/a",
        "note": "Binomial: O(log n) per op; Fibonacci: O(1) amortized insert/merge/decrease-key."},
    "minimum_spanning_tree": {
        "status": "Polynomial", "optimization": "Polynomial (Prim/Kruskal, greedy)", "decision": "Polynomial",
        "note": "Cut property makes the greedy choice safe, so no exponential search is needed."},
    "all_pairs_shortest_paths": {
        "status": "Polynomial", "optimization": "Polynomial, Theta(V^3)", "decision": "Polynomial",
        "note": "Negative edges allowed, negative cycles must be detected."},
    "fractional_knapsack": {
        "status": "Polynomial", "optimization": "Polynomial, O(n log n)", "decision": "Polynomial",
        "note": "Divisibility makes greedy-by-density optimal (exchange argument)."},
    "knapsack_01": {
        "status": "Pseudo-polynomial (DP) / NP-Hard (optimization) / NP-Complete (decision)",
        "optimization": "NP-Hard (DP runs in O(nW), pseudo-polynomial)",
        "decision": "NP-Complete (weakly): 'is there a subset with value >= K and weight <= W?'",
        "note": "O(nW) is exponential in the bit-length b = log2(W) of the input, hence pseudo-polynomial."},
    "matrix_chain": {
        "status": "Polynomial", "optimization": "Polynomial, O(m^3) DP", "decision": "Polynomial",
        "note": "Optimal substructure over the split point."},
    "hamiltonian": {
        "status": "NP-Complete (decision)", "optimization": "n/a (pure feasibility problem)",
        "decision": "NP-Complete: 'does a Hamiltonian path/cycle exist?'",
        "note": "A certificate (the path) is verifiable in O(V); backtracking is O(V!) worst case."},
    "n_queens": {
        "status": "Not NP-Complete in its standard form",
        "optimization": "n/a", "decision": "Polynomial for the standard N x N board (a solution exists for every N >= 4 and can be constructed directly)",
        "note": "Only generalisations (e.g. completing a partial placement, or boards with obstacles) are NP-Complete; backtracking is still exponential in the worst case."},
    "tsp": {
        "status": "NP-Hard (optimization) / NP-Complete (decision)",
        "optimization": "NP-Hard: 'find the minimum-cost Hamiltonian tour'",
        "decision": "NP-Complete: 'is there a tour of cost <= K?' (verifiable in O(V), reduction from Hamiltonian Cycle)",
        "note": "Exact search is O((N-1)!) worst case; B&B prunes but is still exponential."},
}
