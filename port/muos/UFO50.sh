#!/bin/sh
# UFO50_NATIVE_PORT=1
# muOS selects ARM32 audio modules before invoking this launcher.
# shellcheck disable=SC2034 # Read by the muOS content launcher.
PORT_32BIT="Y"
set -eu
root=${UFO50_DEV_DIR:-/mnt/mmc/.ufo50-dev}
[ ! -f "$root/.deploying" ] || { echo 'UFO 50 update incomplete'; exit 1; }
exec "$root/launch.sh"
