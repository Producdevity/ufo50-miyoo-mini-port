#!/bin/sh
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"

[ -f .local/deps/include/SDL/SDL.h ] && [ -f .local/deps/lib/libSDL-1.2.so.0 ] || {
  echo 'Run scripts/prepare-sdl.py with a Miyoo ARM32 SDL 1.2 library first.' >&2
  exit 1
}
cmake -S runtime -B artifacts/armhf \
  -DCMAKE_TOOLCHAIN_FILE="$root/build/armhf-zig.cmake" -DCMAKE_SKIP_RPATH=ON \
  -DBACKEND=sdl1 -DAUDIO_BACKEND=sdl1 -DENABLE_LEGACY_GL=OFF \
  -DENABLE_MODERN_GL=OFF -DENABLE_SW_RENDERER=ON \
  -DENABLE_WAD14=OFF -DENABLE_WAD16=OFF -DENABLE_WAD17=ON -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/armhf -j "${JOBS:-4}"
