#!/bin/sh
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
export ZIG_GLOBAL_CACHE_DIR="$root/artifacts/zig-cache"
export ZIG_LOCAL_CACHE_DIR="$root/artifacts/zig-cache/local"
exec zig cc -target arm-linux-gnueabihf.2.28 -mcpu=cortex_a7 "$@"
