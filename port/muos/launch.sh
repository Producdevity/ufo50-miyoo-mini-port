#!/bin/sh
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
run="$root/runs/$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$run" "$root/saves"
export LD_LIBRARY_PATH="/usr/lib32:/lib32${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PIPEWIRE_MODULE_DIR="/usr/lib32/pipewire-0.3"
export SPA_PLUGIN_DIR="/usr/lib32/spa-0.2"
export PIPEWIRE_RUNTIME_DIR="/run"
export UFO50_RENDER_FPS=30
export UFO50_NATIVE_RESOLUTION=384x216
export UFO50_PERF_LOG=1
save="$root/saves"
set --
# Benchmarks are explicitly enabled, bounded, and use isolated saves.
if [ -f "$root/benchmark-frames" ]; then
    frames=$(cat "$root/benchmark-frames")
    case "$frames" in ''|*[!0-9]*) echo 'Invalid benchmark frame count'; exit 1;; esac
    [ "$frames" -ge 60 ] && [ "$frames" -le 36000 ] || exit 1
    # Core files remain private inside the bounded diagnostic run.
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
    --load-type load-per-chunk --window-size 640x480 --save-folder "$save" \
    > "$run/runtime.log" 2>&1 || status=$?
if [ -f "$root/benchmark-frames" ] && [ -f core ]; then
    mv core "$run/core"
fi
exit "$status"
