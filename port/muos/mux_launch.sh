#!/bin/sh
# HELP: UFO 50 native ARM32 development build
# ICON: portmaster
# GRID: UFO50 Dev
set -eu
. /opt/muos/script/var/func.sh
SETUP_APP "butterscotch" ""
root="${UFO50_DEV_DIR:-$(GET_VAR "device" "storage/rom/mount")/.ufo50-dev}"
run="$root/runs/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$run/saves"
export LD_LIBRARY_PATH="/usr/lib32:/lib32${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PIPEWIRE_MODULE_DIR="/usr/lib32/pipewire-0.3"
export SPA_PLUGIN_DIR="/usr/lib32/spa-0.2"
export PIPEWIRE_RUNTIME_DIR="/run"
export UFO50_INPUT_TRACE=1
export UFO50_RENDER_FPS=30
export UFO50_NATIVE_RESOLUTION=384x216
export UFO50_PERF_LOG=1
export UFO50_SCREENSHOT="$run/frame.png"
export UFO50_SCREENSHOT_FRAME=11999
cd "$root/gamefiles"
printf '%s\n' "$run" > "$root/last-run"
# A bounded first launch records rendering, audio startup, input and room state.
# Saves stay in this diagnostic run until gameplay compatibility is established.
timeout 300 "$root/bin/butterscotch" data.win --renderer software \
  --lazy-rooms --lazy-textures --lazy-audio --load-type load-per-chunk \
  --window-size 640x480 --save-folder "$run/saves" \
  --exit-at-frame 12000 --dump-frame-json 11999 --dump-frame-json-file "$run/state.json" \
  > "$run/runtime.log" 2>&1
