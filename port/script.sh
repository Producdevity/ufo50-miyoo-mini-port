#!/bin/sh
set -eu
gamedir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
savedir=${UFO50_SAVE_DIR:-/mnt/SDCARD/Saves/CurrentProfile/saves/UFO50}
systemdir=${UFO50_SYSTEM_DIR:-/mnt/SDCARD/.tmp_update}
clock=$systemdir/bin/cpuclock
governor=${UFO50_GOVERNOR_FILE:-/sys/devices/system/cpu/cpufreq/policy0/scaling_governor}
clock_initial=
governor_initial=
game_pid=
mkdir -p "$savedir/logs"
log="$savedir/logs/$(date +%Y%m%d-%H%M%S)-$$.log"
exec >"$log" 2>&1
case $(uname -m) in armv7*) ;; *) echo 'This binary requires ARM32 Linux on a Miyoo Mini.'; exit 1;; esac
[ -f "$gamedir/gamefiles/data.win" ] || {
  echo 'Missing gamefiles/data.win. Copy your owned Windows UFO 50 assets here; see README.md.'
  exit 1
}

# shellcheck disable=SC2329 # Called by the EXIT trap.
finish() {
    result=$?
    trap - EXIT INT TERM
    if [ -n "$game_pid" ]; then
        kill -TERM "$game_pid" 2>/dev/null || true
        wait "$game_pid" 2>/dev/null || true
    fi
    if [ -n "$clock_initial" ]; then
        "$clock" "$clock_initial" || echo 'Clock restore failed'
    fi
    if [ -n "$governor_initial" ]; then
        printf '%s\n' "$governor_initial" > "$governor" || echo 'Governor restore failed'
    fi
    exit "$result"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Match the installed Balatro port's 1.5 GHz request, restoring inherited settings.
target=${UFO50_CPU_MHZ:-1500}
if [ "$target" != off ]; then
    case "$target" in ''|*[!0-9]*) echo 'UFO50_CPU_MHZ must be off or 1200-1600'; exit 1;; esac
    [ "$target" -ge 1200 ] && [ "$target" -le 1600 ] || exit 1
    if [ -x "$clock" ] && [ -r "$governor" ] && [ -w "$governor" ]; then
        initial=$("$clock")
        original=$(cat "$governor")
        case "$initial" in ''|*[!0-9]*) echo 'Invalid inherited CPU clock'; exit 1;; esac
        case "$original" in ''|*[!a-zA-Z0-9_-]*) echo 'Invalid inherited governor'; exit 1;; esac
        clock_initial=$initial
        governor_initial=$original
        "$clock" "$target"
        printf 'performance\n' > "$governor"
        printf 'Clock: %s MHz; inherited %s MHz, governor %s\n' "$target" "$initial" "$original"
    fi
fi

export UFO50_PLATFORM=miyoo
export UFO50_RENDER_FPS=30
export UFO50_TEXTURE_CACHE_MIB="${UFO50_TEXTURE_CACHE_MIB:-24}"
export UFO50_NATIVE_RESOLUTION=384x216
export UFO50_PERF_LOG="${UFO50_PERF_LOG:-1}"
printf 'Platform: %s\n' "$(uname -m)"
head -n 8 /proc/meminfo 2>/dev/null || true
cat /proc/swaps 2>/dev/null || true
cd "$gamedir/gamefiles"
"$gamedir/bin/butterscotch" data.win --renderer software \
  --lazy-rooms --lazy-textures --lazy-audio --load-type load-per-chunk \
  --window-size 640x480 --save-folder "$savedir" "$@" &
game_pid=$!
status=0
wait "$game_pid" || status=$?
game_pid=
exit "$status"
