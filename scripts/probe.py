#!/usr/bin/env python3
"""Run a bounded host probe with isolated saves; never deploy or modify game assets."""
import argparse
import json
import os
import platform
import resource
import subprocess
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runner', type=Path)
    parser.add_argument('game', type=Path, help='Owned data.win file')
    parser.add_argument('output', type=Path, help='New private evidence directory')
    parser.add_argument('--frames', type=int, default=180)
    parser.add_argument('--timeout', type=int, default=30)
    parser.add_argument('--seed', type=int, default=1234)
    parser.add_argument('--render-fps', type=int, default=0)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--offline-audio', action='store_true')
    parser.add_argument('--fixed-delta-time', action='store_true')
    parser.add_argument('--unknown-functions', action='store_true')
    args = parser.parse_args()
    if not args.runner.is_file() or not args.game.is_file():
        parser.error('runner and game must be files; game is the owned data.win')
    if args.frames < 1 or args.timeout < 1 or not 0 <= args.render_fps <= 240:
        parser.error('frames and timeout must be positive; render-fps must be 0–240')
    if (args.offline_audio or args.fixed_delta_time) and not args.headless:
        parser.error('offline audio and simulated time require --headless')
    args.output.mkdir(parents=True, exist_ok=False)
    output = args.output.resolve()
    (output / 'saves').mkdir()
    env = dict(os.environ, UFO50_RENDER_FPS=str(args.render_fps), UFO50_PERF_LOG='1',
               SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
               ASAN_OPTIONS='detect_leaks=0', UFO50_SCREENSHOT=str(output / 'frame.png'),
               UFO50_SCREENSHOT_FRAME=str(args.frames - 1))
    if args.offline_audio:
        env['UFO50_OFFLINE_AUDIO'] = '1'
    if args.fixed_delta_time:
        env['UFO50_FIXED_DELTA_TIME'] = '1'
    command = [str(args.runner.resolve()), str(args.game.resolve()), '--renderer', 'software',
               '--lazy-rooms', '--lazy-textures', '--lazy-audio', '--load-type', 'load-per-chunk',
               '--window-size', '640x480', '--save-folder', str(output / 'saves'),
               '--seed', str(args.seed)]
    if args.unknown_functions:
        command.append('--print-unknown-functions')
    else:
        command += ['--exit-at-frame', str(args.frames), '--dump-frame-json', str(args.frames - 1),
                    '--dump-frame-json-file', str(output / 'state.json')]
    if args.headless:
        command.append('--headless')
    if args.inputs:
        command += ['--playback-inputs', str(args.inputs.resolve())]
    start = time.monotonic()
    with (output / 'runtime.log').open('wb') as log:
        try:
            code = subprocess.run(command, cwd=args.game.resolve().parent, env=env,
                                  stdout=log, stderr=subprocess.STDOUT,
                                  timeout=args.timeout).returncode
        except subprocess.TimeoutExpired:
            code = 124
    rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    report = dict(command=command, exit_code=code, elapsed_seconds=time.monotonic() - start,
                  max_rss_bytes=rss if platform.system() == 'Darwin' else rss * 1024,
                  host=platform.platform(), headless=args.headless, offline_audio=args.offline_audio,
                  fixed_delta_time=args.fixed_delta_time or args.offline_audio,
                  screenshot_created=(output / 'frame.png').exists(),
                  scope='Host compatibility diagnostic, not Miyoo hardware validation. '
                        'Sanitizers inflate RSS. Ordinary headless uses no-op audio; '
                        'offline audio drains the real mixer without an output device.')
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return int(code != 0)


if __name__ == '__main__':
    raise SystemExit(main())
