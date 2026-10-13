#!/bin/sh
# Optional diagnostic entry. Normal UFO50 play never calls this script.
set -eu
gamedir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
inputs="$gamedir/miyoo-tests"
output=${UFO50_TEST_DIR:-/mnt/SDCARD/Saves/CurrentProfile/saves/UFO50-tests}
timeout=${UFO50_TEST_TIMEOUT:-240}
case "$timeout" in ''|*[!0-9]*) exit 1;; esac
[ "$timeout" -ge 1 ] && [ "$timeout" -le 900 ] || exit 1
for index in 18 29 34; do
    [ -s "$inputs/input-$index.json" ] || exit 1
done
[ -s "$inputs/config.json" ] && [ -x "$gamedir/script.sh" ] || exit 1
mkdir -p "$output"
run="$output/$(date +%Y%m%d-%H%M%S)-$$"
mkdir "$run"
exec >"$run/driver.log" 2>&1
child=
watchdog=
# shellcheck disable=SC2329 # Called by the EXIT trap.
finish() {
    result=$?
    trap - EXIT INT TERM HUP
    if [ -n "$watchdog" ]; then
        kill -TERM "$watchdog" 2>/dev/null || true
        wait "$watchdog" 2>/dev/null || true
    fi
    if [ -n "$child" ]; then
        kill -TERM "$child" 2>/dev/null || true
        wait "$child" 2>/dev/null || true
    fi
    exit "$result"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
sha256sum "$gamedir/bin/butterscotch" > "$run/runtime.sha256"
for index in 18 29 34; do
    case_dir="$run/game-$index"
    mkdir -p "$case_dir/saves"
    cp "$inputs/config.json" "$case_dir/saves/config.json"
    printf '{"index":%s,"frames":5000,"seed":1234,"crt":2,"window":[3000,4500]}\n' "$index" > "$case_dir/plan.json"
    UFO50_SAVE_DIR="$case_dir/saves" UFO50_KEYBOARD_PLAYBACK=1 \
      UFO50_INPUT_TRACE=1 UFO50_PERF_LOG=1 \
      UFO50_SCREENSHOT="$case_dir/frame.png" UFO50_SCREENSHOT_FRAME=4999 \
      "$gamedir/script.sh" --playback-inputs "$inputs/input-$index.json" \
      --seed 1234 --exit-at-frame 5000 --dump-frame-json 4999 \
      --dump-frame-json-file "$case_dir/state.json" &
    child=$!
    (
        trap - EXIT INT TERM HUP
        elapsed=0
        while [ "$elapsed" -lt "$timeout" ]; do
            kill -0 "$child" 2>/dev/null || exit 0
            sleep 1
            elapsed=$((elapsed + 1))
        done
        touch "$case_dir/timed-out"
        kill -TERM "$child" 2>/dev/null || exit 0
        sleep 2
        kill -KILL "$child" 2>/dev/null || true
    ) &
    watchdog=$!
    status=0
    wait "$child" || status=$?
    child=
    kill -TERM "$watchdog" 2>/dev/null || true
    wait "$watchdog" 2>/dev/null || true
    watchdog=
    printf '%s\n' "$status" > "$case_dir/exit-status"
    [ "$status" -eq 0 ] && [ ! -e "$case_dir/timed-out" ] || exit 1
    [ -s "$case_dir/state.json" ] || exit 1
    grep -q '^Bye! :3$' "$case_dir"/saves/logs/*.log || exit 1
    printf 'Completed game %s\n' "$index"
done
printf 'All three runs completed.\n'
touch "$run/complete"
