# Development

Runtime source is under `runtime/`, imported from the pinned Butterscotch Onion
branch. Integration lives under `scripts/`, `build/`, and `port/`. Keep upstream
notices. Builds and evidence go in ignored `artifacts/`; local dependency
references and owned game inputs go in ignored `.local/`. Never commit original
assets, decompiled game scripts, saves, PCM recordings, or extracted artwork.
Short gameplay captures for the README live in `docs/images/`; record their
origin in `docs/media.md`.

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

## Library music layers

`tests/library-music-inputs.json` opens the game library and leaves it idle.
Its normal, garden and infinity music layers start together, but only the
selected layer should be audible. The audio selftest checks that a layer
started at zero gain is silent from its first buffer and can later fade in.

## Star Waspir shadows

`tests/star-waspir-shadow-inputs.json` starts a fresh single-player run and
waits at the beginning of wave one. The ship's offset shadow must be a solid
colour rather than a second full-colour ship. The synthetic renderer tests
also check silhouette coverage with transparent pixels, palettes, scaling,
clipped flips and rotation.

```sh
python3 scripts/probe.py artifacts/host/butterscotch .local/gamefiles/data.win artifacts/evidence/waspir-shadow --frames 3500 --timeout 30 --headless --offline-audio --render-fps 30 --inputs tests/star-waspir-shadow-inputs.json
```

## Party House purchase audio

This replay buys two Old Friends and waits in the shop long enough for the
purchase effects to finish. The shop music should keep playing. Use fresh saves
and seed 1234 (the probe default):

```sh
python3 scripts/probe.py artifacts/host/butterscotch .local/gamefiles/data.win artifacts/evidence/party-purchase --frames 11000 --timeout 120 --headless --offline-audio --render-fps 30 --inputs tests/party-house-purchase-inputs.json
```

The final state should be Party House (menu index 25, internal ID 36), in
`rm36_PartyKing`, with the selected Old Friend's supply at 2. The offline mixer
check does not test speaker output. On a device, record the sink output after
both purchases and confirm music continues after the effects end.

## SP diagnostics and packaging

Use the normal Ports launcher for behavioral device proof. A file
`/mnt/mmc/.ufo50-dev/benchmark-frames` containing 60–36000 enables a bounded run
with isolated saves, final screenshot/state dump, telemetry, and private core
capture. Optional `test-inputs.json` enables recorded keyboard inputs and
suppresses physical gamepad state. An optional `test-config.json` seeds that run's isolated config, for display
setting comparisons. Remove all three files before normal play.
`timeout 660` bounds diagnostics even if the game stops advancing frames.
Do not change firmware launch-state files to start a test.

For performance, retain the binary hash, firmware, scene, presentation count,
simulation rate, sampling interval, audio route, CPU frequency, and peak RSS.
Do not equate host build, headless smoke, device rendering, controls, audio,
save/reload, and measured FPS. Physical Mini proof remains a separate gate.

Commit every verified chunk. Rebuild after committing, then package:

```sh
sh scripts/build-armhf.sh
python3 scripts/package.py --version "$(cat VERSION)"
```

Packaging rejects dirty/stale source records, altered binaries, unsupported
ELF ABIs/dependencies, RPATHs, and private game-data paths. The versioned Mini release contains one install ZIP and a separate exact
`git archive` of its source commit. Only the `Roms` tree goes in the install ZIP;
source, previews and device evidence stay outside it. `SHA256SUMS` covers the
install and source archives. The manifest lives inside the UFO50 game folder.
For a development SP package, use `python3 scripts/package.py --target sp`.

For collection audio and draw-cadence diagnostics without a physical output device:

```sh
python3 scripts/test-library.py artifacts/host/butterscotch .local/gamefiles/data.win artifacts/evidence/audio30 --offline-audio
python3 scripts/test-library.py artifacts/host/butterscotch .local/gamefiles/data.win artifacts/evidence/audio60 --offline-audio --render-fps 60
```

Offline mode advances the real mixer at simulated room time and records PCM
counts without writing recordings. It cannot verify device output, perceived
sound quality, or performance. Ordinary headless mode continues using no-op
audio. `--fixed-delta-time` also permits simulated-time tests without audio.

For a mounted Onion card, the deployment helper preserves an existing
`gamefiles/` directory and saves. On a first install, supply an imported owned
asset directory:

```sh
python3 scripts/deploy-miyoo.py --sd /Volumes/MIYOO --gamefiles .local/gamefiles
```

The helper checks the clean package/build provenance before writing and retains
a recoverable backup under `artifacts/sd-backups/`. Verify the deployment report
and eject the card safely. Installing verified files is separate from testing
gameplay on the physical Mini.

The SDL1 border-clear check runs without game files or a display. Build it with
the same SDL headers and link library as the Mini runtime:

```sh
scripts/zig-cc.sh -O2 -I.local/deps/include -Iruntime/src/backends \
  tests/native/video_present.c .local/deps/lib/libSDL-1.2.so.0 \
  -o artifacts/video-present-test
```

Run the executable with the Mini SDK SDL library available on the ARM32 test
device. It compares 486 complete 16-bit, 24-bit and 32-bit images in both orientations against SDL's full-clear
scaling path, including uneven borders, stale pixels from a previous frame and all three
CRT settings.
Performance logs report `present_ms` separately from game drawing.

`tests/native/video_benchmark.c` measures the scaling and CRT CPU paths without
a window or game files. Build it like the pixel check. Retain the SDL identity,
CPU governor, clock, binary hash and before/after output when comparing runs.
It does not measure display flips or game FPS.

`Perf:` lines include presentation interval p95 and maximum, plus intervals
longer than 1.5 times the scheduled display period. The p95 is the upper bound
of a half-millisecond bucket. Exclude loading, menus and state export from a
gameplay window; keep the original lines with the report.

For bounded SDL1 keyboard replays, keep the recording active through the exit
frame. An empty entry at that frame is sufficient. Otherwise the physical
controller becomes active when the recording ends, and firmware wake inputs
can change the game. Check the input trace before accepting a timing comparison.
Use `scripts/compare-states.py --only 21 33 23 18 29` when comparing a selected
set of longer library paths; the default still checks all fifty games.
On Linux, `Perf memory:` records peak resident memory in KiB and major page
faults since the previous sample. The first sample includes startup faults.
These fields help distinguish CPU-heavy frames from paging on the Mini.
They are collected once per second only when performance logging is enabled.

`Perf timing:` records the maximum step work, frame wait, wait overshoot and
requested update-rate range for each reporting window. Use it to distinguish a
costly frame from a late wake-up or a game's deliberate rate change. Headless
runs do not wait, so their wait and rate fields are zero.

For repeated CPU comparisons, run `scripts/benchmark-runtime.py BASELINE
CANDIDATE data.win OUTPUT` with isolated evidence paths. It alternates ordering
and drains the real mixer at simulated time. These uncapped workloads include
startup and cannot establish device FPS or speaker output.

For copied target libraries, add `--loader /path/to/ld-linux-armhf.so.3` and
`--library-path /path/to/target-libs`. The report retains the real runtime hashes
and records the loader separately. This still uses the development device's
CPU and kernel; copied Mini libraries do not make it a physical Mini test.

## Collect Mini timing logs

The optional **Action → UFO50-FPS-Test** entry runs Golfaria, Vainger and
Overbold with Hard CRT and exits after three bounded replays. Each uses fresh
saves under `Saves/CurrentProfile/saves/UFO50-tests`; regular saves and the normal
UFO50 entry stay separate. Inputs remain masked through the end of each replay.
The test takes about five minutes at full speed and stops any case after four
minutes if it cannot finish.

From the clean release checkout, install the verified release first, then add
the test entry:

```sh
python3 scripts/setup-miyoo-tests.py --sd /Volumes/MIYOO
```

Eject the card safely and launch **UFO50-FPS-Test** on the Mini once. It returns
to Ports when finished. Remount the card and inspect the new directory under
`Saves/CurrentProfile/saves/UFO50-tests`:

```sh
python3 scripts/summarize-miyoo-tests.py /path/to/the/new/test-directory
```

The report retains long intervals, including game-requested hit pauses. Keep the
original logs when comparing work time, waits, memory and audio output. The PNGs
show game rendering before the final native CRT pass; callback counts do not
establish physical speaker quality.

The diagnostic entry is a developer add-on and stays out of the normal install
ZIP. Its installer backs up the card's UFO50 installation, verifies unchanged
game files and saves, and clears only Onion's generated Ports list cache.
