#!/bin/sh
# Experimental runtime. Physical Miyoo validation is still outstanding.
set -eu
gamedir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$gamedir/logs" "$gamedir/saves"
log="$gamedir/logs/$(date +%Y%m%d-%H%M%S)-$$.log"
exec >"$log" 2>&1
case $(uname -m) in armv7*) ;; *) echo 'This binary requires ARM32 Linux on a Miyoo Mini.';exit 1;; esac
[ -f "$gamedir/gamefiles/data.win" ] || {
  echo 'Missing gamefiles/data.win. Use the host import tool; see README.md.'
  exit 1
}
[ -x "$gamedir/bin/butterscotch" ] || chmod +x "$gamedir/bin/butterscotch"
cd "$gamedir/gamefiles"
exec "$gamedir/bin/butterscotch" ./data.win --renderer software \
  --lazy-rooms --lazy-textures --lazy-audio --load-type load-per-chunk \
  --window-size 640x480 --save-folder "$gamedir/saves" "$@"
