#!/usr/bin/env python3
"""Compare two runtimes on seeded, uncapped CPU workloads with isolated saves."""
import argparse
import hashlib
import json
import os
import platform
import re
import resource
import signal
import subprocess
import time
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('game', type=Path, help='Owned data.win')
    parser.add_argument('output', type=Path, help='New private evidence directory')
    parser.add_argument('--only', type=int, nargs='+', default=[18, 29])
    parser.add_argument('--frames', type=int, default=9000)
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    if not all(p.is_file() for p in [args.baseline, args.candidate, args.game]):
        parser.error('Both runtimes and owned data.win must exist')
    if args.frames < 6000 or args.repeat < 1 or args.timeout < 1 or any(i < 1 or i > 50 for i in args.only):
        parser.error('Use >=6000 frames, positive repeat/timeout, and game indexes 1–50')
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    spec = spec_from_file_location('library', Path(__file__).with_name('test-library.py'))
    library = module_from_spec(spec)
    spec.loader.exec_module(library)
    env = dict(os.environ, UFO50_RENDER_FPS='30', UFO50_PERF_LOG='0',
               UFO50_OFFLINE_AUDIO='1', UFO50_NATIVE_RESOLUTION='384x216',
               SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    report = dict(scope='Uncapped CPU workload including startup and the offline mixer; '
                       'no physical display, audio output, or hardware FPS acceptance.',
                  platform=platform.platform(), frames=args.frames, repeat=args.repeat,
                  binaries={name: dict(path=str(path.resolve()), sha256=sha256(path))
                            for name, path in [('baseline', args.baseline), ('candidate', args.candidate)]},
                  complete=False, planned_runs=args.repeat * len(args.only) * 2, runs=[])
    failed = False
    for repeat in range(args.repeat):
        for index in args.only:
            inputs = output / f'input-{index}.json'
            inputs.write_text(json.dumps(library.input_plan(index)) + '\n')
            # Reverse order on alternate repeats to reduce warm-cache bias.
            names = ['baseline', 'candidate'] if repeat % 2 == 0 else ['candidate', 'baseline']
            for name in names:
                run = output / f'{index}-{repeat}-{name}'
                run.mkdir(); (run / 'saves').mkdir()
                command = [str(getattr(args, name).resolve()), str(args.game.resolve()),
                           '--renderer', 'software', '--lazy-rooms', '--lazy-textures', '--lazy-audio',
                           '--load-type', 'load-per-chunk', '--window-size', '384x216',
                           '--save-folder', str(run / 'saves'), '--seed', '1234', '--headless',
                           '--playback-inputs', str(inputs), '--exit-at-frame', str(args.frames)]
                before = resource.getrusage(resource.RUSAGE_CHILDREN)
                start = time.monotonic()
                with (run / 'runtime.log').open('wb') as log:
                    try:
                        process = subprocess.Popen(command, cwd=args.game.resolve().parent, env=env,
                                                   stdout=log, stderr=subprocess.STDOUT)
                        try:
                            code = process.wait(timeout=args.timeout)
                        except subprocess.TimeoutExpired:
                            process.kill(); process.wait(); code = 124
                        except BaseException:
                            process.terminate()
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                process.kill(); process.wait()
                            raise
                    except OSError:
                        code = 127
                elapsed = time.monotonic() - start
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                log = (run / 'runtime.log').read_text(errors='replace')
                audio = re.findall(r'Offline audio: frames=(\d+) nonzero_samples=(\d+) peak=([\d.]+)', log)
                rooms = re.findall(r'Room changed: .*? -> (\w+) \(room \d+\)', log)
                row = dict(index=index, repeat=repeat, runtime=name, command=command, exit_code=code,
                           elapsed_seconds=elapsed,
                           cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                           last_room=rooms[-1] if rooms else None, audio=audio[-1] if audio else None)
                failed |= code != 0 or not audio or int(audio[-1][1]) == 0
                report['runs'].append(row)
                (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
                print(json.dumps(row), flush=True)
    report['complete'] = True
    (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    return int(failed)


def stop(signum, frame):
    raise SystemExit(128 + signum)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, stop)
    raise SystemExit(main())
