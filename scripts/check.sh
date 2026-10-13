#!/bin/sh
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
python3 -m unittest discover -s tests -v
for script in scripts/*.sh port/*.sh port/*.notfound port/muos/*.sh port/diagnostics/*.sh port/diagnostics/*.port; do sh -n "$script"; done
python3 -m py_compile scripts/*.py
if command -v shellcheck >/dev/null 2>&1; then shellcheck scripts/build-host.sh scripts/build-armhf.sh scripts/zig-cc.sh scripts/build-sp.sh scripts/zig-ar.sh scripts/zig-ranlib.sh scripts/deploy-sp.sh port/script.sh port/muos/*.sh port/diagnostics/*.sh port/diagnostics/*.port; fi
