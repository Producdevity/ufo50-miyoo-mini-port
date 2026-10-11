#!/bin/sh
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
run="$root/runs/$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$run" "$root/saves"
governor=/sys/devices/system/cpu/cpufreq/policy0/scaling_governor
governor_initial=
game_pid=
# Restore the exact inherited governor and stop only our own child on interruption.
# shellcheck disable=SC2329 # Called by the EXIT trap.
finish() {
    result=$?
    trap - EXIT INT TERM
    if [ -n "$game_pid" ]; then
        kill -TERM "$game_pid" 2>/dev/null || true
        wait "$game_pid" 2>/dev/null || true
    fi
    if [ -n "$governor_initial" ]; then
        printf '%s\n' "$governor_initial" > "$governor" || echo 'Governor restore failed' >&2
    fi
    exit "$result"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
if [ "${UFO50_SP_PERFORMANCE:-1}" = 1 ] && [ -w "$governor" ]; then
    original=$(cat "$governor")
    case "$original" in ''|*[!a-zA-Z0-9_-]*) exit 1;; esac
    if [ "$original" != performance ]; then
        governor_initial=$original
        printf 'performance\n' > "$governor"
    fi
    printf 'governor_initial=%s\nmax_khz=%s\n' "$original" \
        "$(cat /sys/devices/system/cpu/cpufreq/policy0/scaling_max_freq)" > "$run/platform.txt"
fi

export LD_LIBRARY_PATH="/usr/lib32:/lib32${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PIPEWIRE_MODULE_DIR="/usr/lib32/pipewire-0.3"
export SPA_PLUGIN_DIR="/usr/lib32/spa-0.2"
export PIPEWIRE_RUNTIME_DIR="/run"
export UFO50_RENDER_FPS=30
export UFO50_TEXTURE_CACHE_MIB="${UFO50_TEXTURE_CACHE_MIB:-24}"
export UFO50_NATIVE_RESOLUTION=384x216
# SDL12-compat scales this logical display to the SP panel in its renderer.
export SDL12COMPAT_SCALE_METHOD=nearest
export SDL12COMPAT_SYNC_TO_VBLANK=0
export UFO50_PERF_LOG=1
save="$root/saves"
set --
# Benchmarks are explicitly enabled, bounded, and use isolated saves.
if [ -f "$root/benchmark-frames" ]; then
    frames=$(cat "$root/benchmark-frames")
    case "$frames" in ''|*[!0-9]*) echo 'Invalid benchmark frame count'; exit 1;; esac
    [ "$frames" -ge 60 ] && [ "$frames" -le 36000 ] || exit 1
    # Core files remain private inside the bounded diagnostic run.
    # shellcheck disable=SC3045 # muOS BusyBox supports core-size limits.
    ulimit -c unlimited || true
    save="$run/saves"
    mkdir -p "$save"
    export UFO50_INPUT_TRACE=1
    export UFO50_SCREENSHOT="$run/frame.png"
    export UFO50_SCREENSHOT_FRAME=$((frames - 1))
    set -- --exit-at-frame "$frames" --dump-frame-json "$((frames - 1))" \
        --dump-frame-json-file "$run/state.json"
    if [ -f "$root/test-inputs.json" ]; then
        set -- "$@" --playback-inputs "$root/test-inputs.json" --seed 1234
        export UFO50_KEYBOARD_PLAYBACK=1
    fi
    set -- timeout 660 "$root/bin/butterscotch" data.win "$@"
else
    set -- "$root/bin/butterscotch" data.win
fi
cd "$root/gamefiles"
printf '%s\n' "$run" > "$root/last-run"
status=0
"$@" --renderer software --lazy-rooms --lazy-textures --lazy-audio \
    --load-type load-per-chunk --window-size 384x216 --save-folder "$save" \
    > "$run/runtime.log" 2>&1 &
game_pid=$!
wait "$game_pid" || status=$?
game_pid=
if [ -f "$root/benchmark-frames" ] && [ -f core ]; then
    mv core "$run/core"
fi
exit "$status"
