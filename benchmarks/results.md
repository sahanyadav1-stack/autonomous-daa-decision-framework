# Measured benchmark results

Python 3.14.0. All values produced by `benchmarks/run_benchmarks.py`.

### MST: Kruskal vs Prim (adjacency matrix)

| graph | density D | MST cost | Kruskal ms | Kruskal ops | Prim ms | Prim ops | faster |
|---|---|---|---|---|---|---|---|
| V=25,E=36 | 0.12 | 8531 | 0.151 | 223 | 0.233 | 1250 | Kruskal |
| V=25,E=240 | 0.80 | 1169 | 0.883 | 1693 | 0.281 | 1250 | Prim(dense) |
| V=100,E=300 | 0.06 | 17527 | 1.808 | 2742 | 3.538 | 20000 | Kruskal |
| V=100,E=4500 | 0.91 | 1538 | 21.086 | 52000 | 3.245 | 20000 | Prim(dense) |

**Measured crossover (V=120):** by wall-clock time D = 0.14; by operation count D = 0.38.

### Prim with priority queue (V=300, E=6000)

| heap | ops | decrease_keys | ms |
|---|---|---|---|
| Binomial | 7871 | 1161 | 9.5 |
| Fibonacci | 7736 | 1161 | 11.5 |

### Floyd-Warshall scaling

| V | inner-loop ops | ms | V^3 |
|---|---|---|---|
| 10 | 1000 | 0.27 | 1000 |
| 20 | 8000 | 2.17 | 8000 |
| 40 | 64000 | 11.42 | 64000 |
| 80 | 512000 | 83.05 | 512000 |

### Index: Red-Black Tree vs B-Tree (t=16), random inserts then search all

| N | RBT height | RBT rotations | RBT visits/search | RBT insert ms | B height | B splits | B reads/search | B insert ms |
|---|---|---|---|---|---|---|---|---|
| 500 | 11 | 293 | 8.25 | 1 | 2 | 19 | 1.96 | 1 |
| 5000 | 15 | 2964 | 11.61 | 17 | 3 | 224 | 2.96 | 14 |
| 50000 | 19 | 29391 | 14.99 | 259 | 4 | 2347 | 3.95 | 233 |

### Heaps: ops (comparisons+links+swaps/cuts) for n=2000 inserts then n mixed ops

| workload | decrease-key share | Binomial ops | Fibonacci ops | fewer ops |
|---|---|---|---|---|
| large key drops | 0.0 | 44332 | 44366 | Binomial |
| large key drops | 0.05 | 44031 | 43144 | Fibonacci |
| large key drops | 0.1 | 43048 | 41225 | Fibonacci |
| large key drops | 0.2 | 41148 | 37611 | Fibonacci |
| large key drops | 0.3 | 38281 | 33938 | Fibonacci |
| large key drops | 0.5 | 31223 | 26382 | Fibonacci |
| large key drops | 0.7 | 23261 | 20331 | Fibonacci |
| large key drops | 0.9 | 13546 | 15275 | Binomial |
| small key drops | 0.0 | 44332 | 44366 | Binomial |
| small key drops | 0.05 | 43703 | 43834 | Binomial |
| small key drops | 0.1 | 42045 | 42510 | Binomial |
| small key drops | 0.2 | 39035 | 39712 | Binomial |
| small key drops | 0.3 | 35484 | 36803 | Binomial |
| small key drops | 0.5 | 27652 | 29688 | Binomial |
| small key drops | 0.7 | 19420 | 22137 | Binomial |
| small key drops | 0.9 | 10264 | 13794 | Binomial |

**First share where Fibonacci uses fewer ops:** {'large key drops': 0.05}

### Heap merge cost (ops to merge two heaps of n keys)

| heap | n | merge ops |
|---|---|---|
| BinomialHeap | 1000 | 12 |
| FibonacciHeap | 1000 | 1 |
| BinomialHeap | 10000 | 10 |
| FibonacciHeap | 10000 | 1 |

### Matched dataset (weights 10,20,30; values 60,100,120; W=50)

| method | value | choice |
|---|---|---|
| Fractional greedy | 240.0 | [1.0, 1.0, 0.67] |
| 0/1 DP (exact) | 220 | [1, 2] |
| Greedy by density applied to 0/1 | 160 | [0, 1] |

### 0/1 DP pseudo-polynomial growth (n=100) vs fractional greedy

| n | capacity W | DP states | DP ms | DP peak MB | fractional ms |
|---|---|---|---|---|---|
| 100 | 1000 | 100100 | 238 | 1.7 | 0.104 |
| 100 | 5000 | 500100 | 1653 | 13.7 | 0.126 |
| 100 | 20000 | 2000100 | 8446 | 72.0 | 0.132 |

### Matrix Chain Multiplication

| chain length | DP ops | ms | optimal mults | left-to-right mults | saving |
|---|---|---|---|---|---|
| 10 | 165 | 0.39 | 149530 | 405926 | 2.7x |
| 20 | 1330 | 1.05 | 370734 | 1553317 | 4.2x |
| 40 | 10660 | 4.78 | 960039 | 5403403 | 5.6x |
| 80 | 85320 | 50.65 | 1178586 | 4865100 | 4.1x |
| 160 | 682640 | 414.69 | 2363460 | 38584608 | 16.3x |

### Hamiltonian path: complete bipartite K(k,k+2) (no solution, worst case)

| graph | result | states | exhausted | ms |
|---|---|---|---|---|
| K(3,5) n=8 | none | 2280 | True | 4.0 |
| K(4,6) n=10 | none | 54960 | True | 101.9 |
| K(5,7) n=12 | none | 1924020 | True | 2583.2 |
| K(6,8) n=14 | none | 2000008 | False | 2226.9 |
| K(7,9) n=16 | none | 2000009 | False | 3821.6 |

### N-Queen backtracking

| N | states (first solution) | ms | #solutions | states (all) | ms (all) |
|---|---|---|---|---|---|
| 4 | 8 | 0.07 | 2 | 16 | 0 |
| 6 | 31 | 0.08 | 4 | 152 | 0 |
| 8 | 113 | 0.29 | 92 | 2056 | 8 |
| 10 | 102 | 0.41 | 724 | 35538 | 161 |
| 12 | 261 | 0.98 | - | - | - |

### TSP: plain backtracking vs reduced-matrix Branch and Bound (random Euclidean)

| N | optimal cost | B&B generated | B&B pruned | B&B finished | B&B ms | BT states | BT ms | fewer states |
|---|---|---|---|---|---|---|---|---|
| 6 | 279.01 | 52 | 35 | True | 2 | 325 | 0 | 84.0% |
| 7 | 253.06 | 46 | 31 | True | 2 | 1956 | 4 | 97.6% |
| 8 | 277.91 | 305 | 231 | True | 13 | 13699 | 18 | 97.8% |
| 9 | 265.02 | 1589 | 1181 | True | 60 | 109600 | 161 | 98.6% |
| 10 | 267.66 | 1235 | 984 | True | 49 | 986409 | 1417 | 99.9% |
| 11 | 240.86 | 6531 | 5276 | True | 260 | - | - | - |
| 12 | 286.12 | 27692 | 21743 | True | 1064 | - | - | - |
| 13 | 326.42 | 29402 | 24680 | True | 1179 | - | - | - |
| 14 | 300.62 | 5644 | 4888 | True | 230 | - | - | - |
| 15 | 298.85 | 400001 | 323233 | False | 20747 | - | - | - |
| 16 | 300.11 | 27997 | 24462 | True | 1227 | - | - | - |
| 18 | 355.47 | 238014 | 201774 | True | 11465 | - | - | - |

(N-1)! growth: 9!=362,880; 13!=6,227,020,800; 21!=5.11e+19
