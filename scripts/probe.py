#!/usr/bin/env python3
"""Bounded host probe; never writes to a device or the source game directory."""
import argparse,json,os,platform,resource,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('runner',type=Path);p.add_argument('game',type=Path);p.add_argument('output',type=Path)
p.add_argument('--frames',type=int,default=180);p.add_argument('--timeout',type=int,default=30)
p.add_argument('--seed',type=int,default=1234);p.add_argument('--render-fps',type=int,default=0)
p.add_argument('--inputs',type=Path);p.add_argument('--headless',action='store_true');p.add_argument('--unknown-functions',action='store_true')
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);out=a.output.resolve();(out/'saves').mkdir()
env=dict(os.environ,UFO50_RENDER_FPS=str(a.render_fps),UFO50_PERF_LOG='1',SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',ASAN_OPTIONS='detect_leaks=0',UFO50_SCREENSHOT=str(out/'frame.png'),UFO50_SCREENSHOT_FRAME=str(a.frames-1))
cmd=[str(a.runner.resolve()),str(a.game.resolve()),'--renderer','software','--lazy-rooms','--lazy-textures','--lazy-audio','--load-type','load-per-chunk','--window-size','640x480','--save-folder',str(out/'saves'),'--seed',str(a.seed)]
if a.unknown_functions:cmd+=['--print-unknown-functions']
else:cmd+=['--exit-at-frame',str(a.frames),'--dump-frame-json',str(a.frames-1),'--dump-frame-json-file',str(out/'state.json')]
if a.headless:cmd+=['--headless']
if a.inputs:cmd+=['--playback-inputs',str(a.inputs.resolve())]
start=time.monotonic()
with (out/'runtime.log').open('wb') as log:
    try:rc=subprocess.run(cmd,cwd=a.game.resolve().parent,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout).returncode
    except subprocess.TimeoutExpired:rc=124
rss=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
report={'command':cmd,'exit_code':rc,'elapsed_seconds':time.monotonic()-start,'max_rss_bytes':rss if platform.system()=='Darwin' else rss*1024,'host':platform.platform(),'headless':a.headless,'screenshot_created':(out/'frame.png').exists(),'scope':'Host compatibility diagnostic, not Miyoo hardware validation. Sanitizer builds inflate RSS; headless uses no-op audio.'}
(out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if rc==0 else 1)
