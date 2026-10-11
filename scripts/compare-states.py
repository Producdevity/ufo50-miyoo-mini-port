#!/usr/bin/env python3
"""Compare complete seeded library state snapshots without filtering game variables."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    failures = []
    for index in range(1, 51):
        try:
            plan = f'input-{index:02d}.json'
            if json.loads((args.baseline / plan).read_text()) != json.loads((args.candidate / plan).read_text()):
                raise ValueError('input plans differ')
            state = f'game-{index:02d}/state.json'
            baseline = json.loads((args.baseline / state).read_text())
            candidate = json.loads((args.candidate / state).read_text())
            if baseline != candidate:
                fields = [key for key in baseline.keys() | candidate.keys()
                          if baseline.get(key) != candidate.get(key)]
                failures.append(dict(index=index, different_fields=sorted(fields)))
        except (OSError, ValueError) as error:
            failures.append(dict(index=index, error=str(error)))
    print(json.dumps(dict(checked_games=50, failures=failures,
                         scope='Exact host state parity for recorded paths, not exhaustive gameplay.'), indent=2))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
