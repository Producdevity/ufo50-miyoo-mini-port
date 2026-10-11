#!/bin/sh
# Uses the SP's real ARM32 SDL library as the link reference.
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
case ${UFO50_DIAGNOSTICS:-0} in
  0) diagnostics=OFF;;
  1) diagnostics=ON;;
  *) echo "UFO50_DIAGNOSTICS must be 0 or 1" >&2; exit 1;;
esac
[ -f .local/deps-sp/lib/libSDL-1.2.so.0 ] || {
  echo 'Copy the development SP ARM32 SDL 1.2 library into .local/deps-sp/lib first.' >&2
  exit 1
}
# Refresh compiler detection after toolchain changes; retain built object files.
cmake --fresh -S runtime -B artifacts/sp \
  -DCMAKE_TOOLCHAIN_FILE="$root/build/armhf-zig.cmake" -DCMAKE_SKIP_RPATH=ON -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON \
  -DSDL_LIBRARY="$root/.local/deps-sp/lib/libSDL-1.2.so.0" \
  -DBACKEND=sdl1 -DAUDIO_BACKEND=sdl1 -DENABLE_LEGACY_GL=OFF \
  -DENABLE_MODERN_GL=OFF -DENABLE_VM_TRACING="$diagnostics" -DENABLE_VM_GML_PROFILER="$diagnostics" \
  -DENABLE_VM_OPCODE_PROFILER="$diagnostics" -DENABLE_SW_RENDERER=ON \
  -DENABLE_WAD14=OFF -DENABLE_WAD16=OFF -DENABLE_WAD17=ON -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/sp -j "${JOBS:-4}"
python3 scripts/record-build.py sp .local/deps-sp/lib/libSDL-1.2.so.0
