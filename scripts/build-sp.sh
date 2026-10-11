#!/bin/sh
# Uses the SP's real ARM32 SDL library as the link reference.
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
[ -f .local/deps-sp/lib/libSDL-1.2.so.0 ] || {
  echo 'Copy the development SP ARM32 SDL 1.2 library into .local/deps-sp/lib first.' >&2
  exit 1
}
cmake -S runtime -B artifacts/sp \
  -DCMAKE_TOOLCHAIN_FILE="$root/build/armhf-zig.cmake" -DCMAKE_SKIP_RPATH=ON \
  -DSDL_LIBRARY="$root/.local/deps-sp/lib/libSDL-1.2.so.0" \
  -DBACKEND=sdl1 -DAUDIO_BACKEND=sdl1 -DENABLE_LEGACY_GL=OFF \
  -DENABLE_MODERN_GL=OFF -DENABLE_SW_RENDERER=ON \
  -DENABLE_WAD14=OFF -DENABLE_WAD16=OFF -DENABLE_WAD17=ON -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/sp -j "${JOBS:-4}"
