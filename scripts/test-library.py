#!/usr/bin/env python3
"""Select owned games through recorded menu inputs and collect headless smoke evidence."""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path


def input_plan(index):
    plan = {}

    def tap(frame, key, duration=8):
        plan[str(frame)] = {'keysPressed': [key], 'keysReleased': []}
        plan[str(frame + duration)] = {'keysPressed': [], 'keysReleased': [key]}

    for frame in range(200, 1001, 200):
        tap(frame, 90)
    frame = 1100
    for key, count in [(39, (index - 1) % 10), (40, (index - 1) // 10)]:
        for _ in range(count):
            tap(frame, key)
            frame += 20
    for frame in [1600, 1800, 2000]:
        tap(frame, 90)
    for frame in range(2400, 4200, 200):
        tap(frame, 90 if frame % 400 == 0 else 88)
    tap(4400, 39, 20)
    tap(4500, 90)
    return plan


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runner', type=Path)
    parser.add_argument('game', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--only', type=int, nargs='+', default=list(range(1, 51)))
    parser.add_argument('--frames', type=int, default=6000)
    parser.add_argument('--timeout', type=int, default=30)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    rows = []
    for index in args.only:
        if not 1 <= index <= 50:
            parser.error('Game index must be between 1 and 50')
        plan = args.output / f'input-{index:02d}.json'
        plan.write_text(json.dumps(input_plan(index), indent=2) + '\n')
        output = args.output / f'game-{index:02d}'
        command = [os.sys.executable, str(root / 'scripts/probe.py'),
                   str(args.runner), str(args.game), str(output),
                   '--frames', str(args.frames), '--timeout', str(args.timeout),
                   '--headless', '--render-fps', '30', '--inputs', str(plan)]
        start = time.monotonic()
        with (args.output / f'probe-{index:02d}.log').open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        row = {'index': index, 'exit_code': result.returncode,
               'seconds': time.monotonic() - start,
               'scope': 'Headless menu/room smoke test; no device, audio or gameplay acceptance.'}
        state = output / 'state.json'
        if state.exists():
            data = json.loads(state.read_text())
            global_vars = data['globalVariables']
            row.update(room=data['room'], selected=global_vars.get('selGame'),
                       current=global_vars.get('currGame'), game_id=global_vars.get('currGameID'))
            row['entered_selected_game'] = (global_vars.get('currGame') == index and
                                            data['room']['name'] not in ['rmLibrary', 'rmTitleScreens'])
        rows.append(row)
        (args.output / 'summary.json').write_text(json.dumps(rows, indent=2) + '\n')
        print(json.dumps(row), flush=True)
    return int(any(row['exit_code'] or not row.get('entered_selected_game') for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
