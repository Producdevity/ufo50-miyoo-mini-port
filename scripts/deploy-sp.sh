#!/bin/sh
# Install only the native runtime/launchers; owned game files are imported separately.
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
target=${1:-muos-sp}
[ -f artifacts/sp/butterscotch ] || { echo 'Build the SP runtime first' >&2; exit 1; }
ssh "$target" 'set -eu
if pidof butterscotch >/dev/null; then echo "Close the running game before deploying" >&2; exit 1; fi
mkdir -p /mnt/mmc/.ufo50-dev/bin /mnt/sdcard/ROMS/Ports
[ -f /mnt/mmc/.ufo50-dev/gamefiles/data.win ] || { echo "Import owned assets first" >&2; exit 1; }
touch /mnt/mmc/.ufo50-dev/.deploying'
scp artifacts/sp/butterscotch "$target:/mnt/mmc/.ufo50-dev/bin/butterscotch.next"
scp port/muos/launch.sh "$target:/mnt/mmc/.ufo50-dev/launch.sh.next"
scp port/muos/UFO50.sh "$target:/mnt/sdcard/ROMS/Ports/UFO50.sh.next"
expected=$(shasum -a 256 artifacts/sp/butterscotch | cut -d ' ' -f 1)
actual=$(ssh "$target" 'sha256sum /mnt/mmc/.ufo50-dev/bin/butterscotch.next' | cut -d ' ' -f 1)
[ "$expected" = "$actual" ] || { echo 'Upload hash mismatch' >&2; exit 1; }
ssh "$target" 'set -eu
chmod 755 /mnt/mmc/.ufo50-dev/bin/butterscotch.next /mnt/mmc/.ufo50-dev/launch.sh.next /mnt/sdcard/ROMS/Ports/UFO50.sh.next
mv /mnt/mmc/.ufo50-dev/bin/butterscotch.next /mnt/mmc/.ufo50-dev/bin/butterscotch
mv /mnt/mmc/.ufo50-dev/launch.sh.next /mnt/mmc/.ufo50-dev/launch.sh
mv /mnt/sdcard/ROMS/Ports/UFO50.sh.next /mnt/sdcard/ROMS/Ports/UFO50.sh
rm /mnt/mmc/.ufo50-dev/.deploying'
printf 'Verified SP runtime: %s\n' "$expected"
