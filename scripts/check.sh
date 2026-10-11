#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
python3 -m unittest discover -s tests -v
for script in scripts/*.sh port/*.sh port/*.notfound; do sh -n "$script"; done
python3 -m py_compile scripts/*.py
if command -v shellcheck >/dev/null 2>&1; then shellcheck scripts/build-host.sh scripts/build-armhf.sh scripts/zig-cc.sh; fi
