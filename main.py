"""Autonomous DAA Decision Framework - CLI.
  python main.py             run all recognition cases
  python main.py --adapt     show decisions flipping when ONE property changes
  python main.py --file r.json   solve your own request (JSON)
"""
import argparse
import json
import sys

from engine import solve, UnrecognizedProblem
from demo_cases import CASES, ADAPTATIONS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapt", action="store_true")
    ap.add_argument("--file")
    a = ap.parse_args()
    if a.file:
        with open(a.file) as f:
            req = json.load(f)
        try:
            print(solve(req).render())
        except UnrecognizedProblem as e:
            print("Unrecognised request:", e)
            sys.exit(1)
    elif a.adapt:
        for title, ra, rb in ADAPTATIONS:
            da, db = solve(ra), solve(rb)
            print(f"=== ADAPTATION: {title} ===")
            print(f"  before -> {da.technique}   ({da.reason})")
            print(f"  after  -> {db.technique}   ({db.reason})")
            print(f"  decision changed: {da.technique != db.technique}\n")
    else:
        for title, req in CASES:
            print(f"=== {title} ===")
            print(solve(req).render())
            print()


if __name__ == "__main__":
    main()
