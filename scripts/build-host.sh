#!/bin/sh
set -eu
root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
case ${UFO50_DIAGNOSTICS:-0} in
  0) diagnostics=OFF;;
  1) diagnostics=ON;;
  *) echo "UFO50_DIAGNOSTICS must be 0 or 1" >&2; exit 1;;
esac

cmake -S runtime -B artifacts/host \
  -DBACKEND=sdl2 -DENABLE_LEGACY_GL=OFF -DENABLE_MODERN_GL=OFF \
  -DENABLE_VM_TRACING="$diagnostics" -DENABLE_VM_GML_PROFILER="$diagnostics" \
  -DENABLE_VM_OPCODE_PROFILER="$diagnostics" -DENABLE_SW_RENDERER=ON -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/host -j "${JOBS:-4}"
