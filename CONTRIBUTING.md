# Development

Runtime source is under `runtime/`, imported from the pinned Butterscotch Onion
branch. Integration lives under `scripts/`, `build/`, and `port/`. Keep upstream
notices. Builds and evidence go in ignored `artifacts/`; local dependency
references and owned game inputs go in ignored `.local/`. Never commit original
assets, decompiled game scripts, saves, PCM recordings, or copied artwork.

## Dependencies and builds

Use Git, Python 3.10+, CMake, and Zig 0.16.0. Host builds additionally need SDL2
development files and pkg-config. On macOS these can be provided by Homebrew.

```sh
sh scripts/check.sh
sh scripts/build-host.sh
artifacts/host/butterscotch --compat-selftest
python3 scripts/test-audio.py artifacts/host/butterscotch
```

For ARM32, supply an actual Miyoo SDK or firmware SDL 1.2 library as a **link-time
reference**. `prepare-sdl.py` fetches the locked official SDL headers and records
the library hash. It does not distribute or install that library.

```sh
python3 scripts/prepare-sdl.py /path/to/Miyoo/libSDL-1.2.so.0
sh scripts/build-armhf.sh
```

For the SP, obtain its real ARM32 SDL library:

```sh
mkdir -p .local/deps-sp/lib
scp muos-sp:/usr/lib32/libSDL-1.2.so.1.2.65 .local/deps-sp/lib/libSDL-1.2.so.0
sh scripts/build-sp.sh
```

Default builds remove VM tracing and profiler checks. For investigation, set
`UFO50_DIAGNOSTICS=1` when building and use `--profile-gml-scripts 300`. Keep
instrumented performance measurements distinct from release measurements.
Each cross-build records its source commit, dirty state, binary hash, compiler,
SDL reference/header provenance, diagnostic features, and target ELF metadata.

## Owned assets and bounded tests

```sh
python3 scripts/ufo50.py import /path/to/UFO50.zip .local/gamefiles
python3 scripts/ufo50.py audit .local/gamefiles
python3 scripts/test-library.py artifacts/host/butterscotch .local/gamefiles/data.win artifacts/evidence/my-library
```

Importer destinations must be new. `.local/gamefiles` may instead point to a
previously imported owned copy. The library test uses isolated saves and seeded
menu inputs; it checks visited game rooms. It is a headless compatibility smoke
check with no-op audio, not complete gameplay or hardware acceptance.

```sh
python3 scripts/probe.py artifacts/host/butterscotch .local/gamefiles/data.win artifacts/evidence/my-run --frames 6000 --headless --inputs tests/library-inputs.json
```

Use a separate sanitizer build for runtime changes:

```sh
cmake -S runtime -B artifacts/asan -DBACKEND=sdl2 -DENABLE_LEGACY_GL=OFF -DENABLE_MODERN_GL=OFF -DENABLE_SW_RENDERER=ON -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_FLAGS='-fsanitize=address,undefined -fno-omit-frame-pointer' -DCMAKE_EXE_LINKER_FLAGS='-fsanitize=address,undefined'
cmake --build artifacts/asan -j4
ASAN_OPTIONS=detect_leaks=0 artifacts/asan/butterscotch --compat-selftest
```

## SP diagnostics and packaging

Use the normal Ports launcher for behavioral device proof. A file
`/mnt/mmc/.ufo50-dev/benchmark-frames` containing 60–36000 enables a bounded run
with isolated saves, final screenshot/state dump, telemetry, and private core
capture. Optional `test-inputs.json` enables recorded keyboard inputs and
suppresses physical gamepad state. Remove both files before normal play.
`timeout 660` bounds diagnostics even if the game stops advancing frames.
Do not change firmware launch-state files to start a test.

For performance, retain the binary hash, firmware, scene, presentation count,
simulation rate, sampling interval, audio route, CPU frequency, and peak RSS.
Do not equate host build, headless smoke, device rendering, controls, audio,
save/reload, and measured FPS. Physical Mini proof remains a separate gate.

Commit every verified chunk. Rebuild after committing, then package:

```sh
sh scripts/build-armhf.sh
sh scripts/build-sp.sh
python3 scripts/package.py
```

Packaging rejects dirty/stale source records, altered binaries, unsupported
ELF ABIs/dependencies, RPATHs, and private game-data paths. Both development ZIPs
include an exact `git archive` of the matching source commit. `SHA256SUMS` covers
the ZIPs; each manifest identifies its target and binary/source hashes.

For collection audio and draw-cadence diagnostics without a physical output device:

```sh
python3 scripts/test-library.py artifacts/host/butterscotch .local/gamefiles/data.win artifacts/evidence/audio30 --offline-audio
python3 scripts/test-library.py artifacts/host/butterscotch .local/gamefiles/data.win artifacts/evidence/audio60 --offline-audio --render-fps 60
```

Offline mode advances the real mixer at simulated room time and records PCM
counts without writing recordings. It cannot verify device output, perceived
sound quality, or performance. Ordinary headless mode continues using no-op
audio. `--fixed-delta-time` also permits simulated-time tests without audio.
