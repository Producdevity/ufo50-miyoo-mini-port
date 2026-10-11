#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"

cmake -S runtime -B artifacts/host \
  -DBACKEND=sdl2 -DENABLE_LEGACY_GL=OFF -DENABLE_MODERN_GL=OFF \
  -DENABLE_SW_RENDERER=ON -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/host -j "${JOBS:-4}"
