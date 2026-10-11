#!/usr/bin/env python3
"""Select owned games through recorded menu inputs and collect headless smoke evidence."""
import argparse
import json
import os
import re
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
    parser.add_argument('--render-fps', type=int, choices=[30, 60], default=30)
    parser.add_argument('--offline-audio', action='store_true')
    parser.add_argument('--fixed-delta-time', action='store_true')
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
                   '--headless', '--render-fps', str(args.render_fps), '--inputs', str(plan)]
        if args.offline_audio:
            command.append('--offline-audio')
        if args.fixed_delta_time:
            command.append('--fixed-delta-time')
        start = time.monotonic()
        with (args.output / f'probe-{index:02d}.log').open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        row = {'index': index, 'exit_code': result.returncode,
               'seconds': time.monotonic() - start,
               'offline_audio': args.offline_audio, 'render_fps': args.render_fps,
               'scope': 'Headless menu/room smoke test; optional offline mixer, no device or gameplay acceptance.'}
        state = output / 'state.json'
        if state.exists():
            data = json.loads(state.read_text())
            global_vars = data['globalVariables']
            row.update(room=data['room'], selected=global_vars.get('selGame'),
                       current=global_vars.get('currGame'), game_id=global_vars.get('currGameID'))
            row['final_in_game'] = data['room']['name'] not in ['rmLibrary', 'rmTitleScreens']
            runtime_log = (output / 'runtime.log').read_text()
            visited = re.findall(r'Room changed: .*? -> (\w+) \(room \d+\)', runtime_log)
            row['visited_game_rooms'] = [room for room in visited
                                         if room not in ['rmLibrary', 'rmTitleScreens']]
            row['entered_selected_game'] = (global_vars.get('currGame') == index and
                                            bool(row['visited_game_rooms']))
        if args.offline_audio:
            audio_log = (output / 'runtime.log').read_text()
            match = re.search(r'Offline audio: frames=(\d+) nonzero_samples=(\d+) peak=([\d.]+)', audio_log)
            if match:
                row['audio'] = dict(frames=int(match[1]), nonzero_samples=int(match[2]), peak=float(match[3]))
        rows.append(row)
        (args.output / 'summary.json').write_text(json.dumps(rows, indent=2) + '\n')
        print(json.dumps(row), flush=True)
    return int(any(row['exit_code'] or not row.get('entered_selected_game') or (args.offline_audio and not row.get('audio', {}).get('nonzero_samples')) for row in rows))


if __name__ == '__main__':
    raise SystemExit(main())
