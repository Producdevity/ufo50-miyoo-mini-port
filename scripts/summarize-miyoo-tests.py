#!/usr/bin/env python3
"""Read a completed on-Mini test directory without filtering out long intervals."""
import argparse
import json
import re
from pathlib import Path


def summarize(directory):
    if not (directory / 'complete').is_file():
        raise ValueError('The three-case test did not complete')
    runtime = (directory / 'runtime.sha256').read_text().split()[0]
    if not re.fullmatch('[0-9a-f]{64}', runtime):
        raise ValueError('Missing runtime fingerprint')
    result = []
    for index in [18, 29, 34]:
        case = directory / f'game-{index}'
        plan = json.loads((case / 'plan.json').read_text())
        state = json.loads((case / 'state.json').read_text())
        logs = list((case / 'saves/logs').glob('*.log'))
        if len(logs) != 1:
            raise ValueError('Expected one retained launcher log per case')
        log = logs[0].read_text()
        if ((case / 'exit-status').read_text().strip() != '0' or (case / 'timed-out').exists() or
                'Bye! :3' not in log or 'Game exited: 0' not in log or
                re.search(r'^Input: frame=', log, re.MULTILINE) or 'Playback ended' in log):
            raise ValueError(f'Game {index} did not complete a protected replay')
        globals_ = state['globalVariables']
        if (plan['index'] != index or state['frame'] != 4999 or globals_['currGame'] != index or
                globals_['scanlines'] != 2 or globals_['scale'] != 1 or
                state['room']['name'] in ['rmLibrary', 'rmTitleScreens']):
            raise ValueError(f'Wrong game/config/state in case {index}')
        rows = [{k:float(v) for k,v in re.findall(r'(\w+)=([\d.]+)', line)}
                for line in log.splitlines() if line.startswith('Perf: ')]
        rows = [row for row in rows if 3000 <= row['frame'] <= 4500]
        if not rows:
            raise ValueError('No gameplay timing rows')
        timing = [{k:float(v) for k,v in re.findall(r'(\w+)=([\d.]+)', line)}
                  for line in log.splitlines() if line.startswith('Perf timing: ')]
        timing = [row for row in timing if 3000 <= row['frame'] <= 4500]
        memory = [{k:int(v) for k,v in re.findall(r'(\w+)=([\d]+)', line)}
                  for line in log.splitlines() if line.startswith('Perf memory: ')]
        memory = [row for row in memory if 3000 <= row['frame'] <= 4500]
        audio = re.search(r'Audio output: callbacks=(\d+) frames=(\d+) nonzero_samples=(\d+) peak=([\d.]+)', log)
        if not audio or int(audio[3]) == 0:
            raise ValueError('No nonzero audio callback output')
        seconds = sum(row['seconds'] for row in rows)
        steps = sum(row['steps'] for row in rows)
        result.append(dict(index=index, title=globals_['mGameTitle'][index], room=state['room'],
                           seconds=seconds, presentations_per_second=sum(row['presents'] for row in rows)/seconds,
                           logic_steps_per_second=steps/seconds,
                           mean_work_ms=sum(row['steps']*row['work_ms'] for row in rows)/steps,
                           max_interval_ms=max(row['interval_max_ms'] for row in rows),
                           long_intervals=int(sum(row['long_intervals'] for row in rows)),
                           max_work_ms=max((row['work_max_ms'] for row in timing), default=None),
                           max_wait_ms=max((row['wait_max_ms'] for row in timing), default=None),
                           max_wait_late_ms=max((row['wait_late_max_ms'] for row in timing), default=None),
                           requested_hz_min=min((row['hz_min'] for row in timing), default=None),
                           peak_rss_kib=max((row['hwm_kib'] for row in memory), default=None),
                           major_faults=sum(row['major_faults'] for row in memory) if memory else None,
                           audio_nonzero_samples=int(audio[3]), log=str(logs[0])))
    return dict(runtime_sha256=runtime, runs=result,
                scope='On-device replay at the launcher clock request. Inspect retained clock, memory and timing lines; snapshots are pre-CRT and do not prove physical speaker quality. Long intervals use 1.5 times the scheduled presentation period; all reported gaps remain counted.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize(args.directory), indent=2))


if __name__ == '__main__':
    main()
