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
watchdog_pid=
mkdir -p "$savedir/logs"
log="$savedir/logs/$(date +%Y%m%d-%H%M%S)-$$.log"
exec >"$log" 2>&1
case $(uname -m) in armv7*) ;; *) echo 'This binary requires ARM32 Linux on a Miyoo Mini.'; exit 1;; esac

launch_error() {
    printf 'Launch error: %s\n' "$1"
    if [ -x "$systemdir/bin/infoPanel" ]; then
        "$systemdir/bin/infoPanel" -t "UFO 50" -m "$1\nSee Saves/CurrentProfile/saves/UFO50/logs." --auto || true
    fi
}
[ -s "$gamedir/gamefiles/data.win" ] || {
    launch_error 'Missing gamefiles/data.win. Copy the Windows game folder contents into gamefiles.'
    exit 1
}
[ -x "$gamedir/bin/butterscotch" ] || {
    launch_error 'Port runtime is missing. Copy the complete release onto the SD card.'
    exit 1
}

# shellcheck disable=SC2329 # Called by the EXIT trap.
finish() {
    result=$?
    trap - EXIT INT TERM
    if [ -n "$watchdog_pid" ]; then
        kill -TERM "$watchdog_pid" 2>/dev/null || true
        wait "$watchdog_pid" 2>/dev/null || true
    fi
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

# Onion's OSS bridge sends audio and ioctl requests to audioserver over FIFOs.
# The Ports shortcut must preserve that server; stopping it blocks SDL_OpenAudio.
padsp="$systemdir/../miyoo/lib/libpadsp.so"
audio_fifo=${UFO50_AUDIO_FIFO:-/tmp/audio_fifo_server}
if ! pgrep -f '(^|/)audioserver(\.mod)?([[:space:]]|$)' >/dev/null 2>&1; then
    launch_error 'Onion audio server is not running. Restart Onion and launch UFO50 again.'
    exit 1
fi
if [ ! -p "$audio_fifo" ] || [ ! -s "$padsp" ]; then
    launch_error 'Onion audio bridge is unavailable. Restart Onion and launch UFO50 again.'
    exit 1
fi
unset PADSP_NO_DSP
case "${LD_PRELOAD:-}" in
    *libpadsp.so*) ;;
    '') LD_PRELOAD=$padsp;;
    *) LD_PRELOAD="$padsp:$LD_PRELOAD";;
esac
export LD_PRELOAD
echo 'Audio: Onion audioserver preserved; OSS bridge ready'

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

# Standalone Ports only adds Onion's compatibility libraries when a port has
# its own lib/ directory. This port uses firmware libraries directly.
parasyte="$systemdir/lib/parasyte"
export LD_LIBRARY_PATH="$systemdir/../miyoo/lib:$parasyte:/config/lib:/lib:/usr/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
loader=${UFO50_SYSTEM_LOADER:-/lib/ld-linux-armhf.so.3}
if [ -x "$loader" ]; then
    echo 'Runtime loader: system'
    set -- "$gamedir/bin/butterscotch" data.win "$@"
elif [ -x "$parasyte/ld-linux-armhf.so.3" ]; then
    echo 'Runtime loader: Onion compatibility'
    set -- "$parasyte/ld-linux-armhf.so.3" --library-path "$LD_LIBRARY_PATH" "$gamedir/bin/butterscotch" data.win "$@"
else
    launch_error 'ARM runtime loader is missing. Update Onion and reinstall Ports Collection.'
    exit 1
fi
startup_timeout=${UFO50_STARTUP_TIMEOUT:-60}
case "$startup_timeout" in ''|*[!0-9]*) launch_error 'Invalid startup timeout.'; exit 1;; esac
[ "$startup_timeout" -ge 1 ] && [ "$startup_timeout" -le 300 ] || exit 1

export UFO50_VALIDATE_FILES=1
export UFO50_PLATFORM=miyoo
export UFO50_ROTATE_180="${UFO50_ROTATE_180:-1}"
export UFO50_RENDER_FPS=30
export UFO50_TEXTURE_CACHE_MIB="${UFO50_TEXTURE_CACHE_MIB:-24}"
export UFO50_NATIVE_RESOLUTION=384x216
export UFO50_PERF_LOG="${UFO50_PERF_LOG:-1}"
printf 'Platform: %s\n' "$(uname -m)"
head -n 8 /proc/meminfo 2>/dev/null || true
cat /proc/swaps 2>/dev/null || true
cd "$gamedir/gamefiles"
"$@" --renderer software \
  --lazy-rooms --lazy-textures --lazy-audio --load-type load-per-chunk \
  --window-size 640x480 --save-folder "$savedir" --disable-log-colours &
game_pid=$!
# Watch only startup, never impose a time limit on gameplay. The runtime logs
# readiness after its first displayed frame, not merely after opening SDL.
(
    trap - EXIT INT TERM
    elapsed=0
    while [ "$elapsed" -lt "$startup_timeout" ]; do
        if grep -q '^Startup: first frame presented$' "$log" || ! kill -0 "$game_pid" 2>/dev/null; then exit 0; fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    if grep -q '^Startup: first frame presented$' "$log" || ! kill -0 "$game_pid" 2>/dev/null; then exit 0; fi
    printf 'Startup timed out after %s seconds\n' "$startup_timeout"
    kill -TERM "$game_pid" 2>/dev/null || exit 0
    sleep 2
    kill -KILL "$game_pid" 2>/dev/null || true
) &
watchdog_pid=$!
status=0
wait "$game_pid" || status=$?
game_pid=
kill -TERM "$watchdog_pid" 2>/dev/null || true
wait "$watchdog_pid" 2>/dev/null || true
watchdog_pid=
if grep -q '^Startup timed out' "$log"; then
    launch_error 'Startup stalled. The game was stopped. Share the latest UFO50 log with your Mini model and Onion version.'
elif [ "$status" -ne 0 ]; then
    if grep -q '^Error: Game files:' "$log"; then
        launch_error 'Game files are missing or incomplete. Recopy the Windows game folder contents into gamefiles.'
    else
        launch_error 'The game could not start or stopped unexpectedly. Share the latest UFO50 log with your Mini model and Onion version.'
    fi
fi
printf 'Game exited: %s\n' "$status"
exit "$status"
