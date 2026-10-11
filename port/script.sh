#!/bin/sh
# Development build: physical Miyoo acceptance remains outstanding.
set -eu
gamedir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
savedir=${UFO50_SAVE_DIR:-/mnt/SDCARD/Saves/CurrentProfile/saves/UFO50}
mkdir -p "$savedir/logs"
log="$savedir/logs/$(date +%Y%m%d-%H%M%S)-$$.log"
exec >"$log" 2>&1
case $(uname -m) in armv7*) ;; *) echo 'This binary requires ARM32 Linux on a Miyoo Mini.'; exit 1;; esac
[ -f "$gamedir/gamefiles/data.win" ] || {
  echo 'Missing gamefiles/data.win. Import your owned assets; see README.md.'
  exit 1
}
export UFO50_PLATFORM=miyoo
export UFO50_RENDER_FPS=30
export UFO50_NATIVE_RESOLUTION=384x216
export UFO50_PERF_LOG=${UFO50_PERF_LOG:-0}
cd "$gamedir/gamefiles"
exec "$gamedir/bin/butterscotch" data.win --renderer software \
  --lazy-rooms --lazy-textures --lazy-audio --load-type load-per-chunk \
  --window-size 640x480 --save-folder "$savedir" "$@"
