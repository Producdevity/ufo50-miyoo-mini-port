# Development status

Updated 2026-10-12. The public source is on `master`; packages contain ARM32
runtimes and their exact source, with game assets excluded.

The muOS SP launches through **Ports → UFO50**. Live Barbuta checks demonstrate
movement, jumping, attacking, pause, returning to the library, normal quit and
persistent save reload. Digital audio reaches the codec sink. The measured
Barbuta interval presents 29.996 FPS over 123 seconds; Cyber Owls presents
29.980 FPS over 20 seconds. Vainger with ThinLTO and preserved Draw events
averages 29.489 and 29.539 FPS in two sampled gameplay intervals. With the
native logical SP display, Golfaria averages 29.786 FPS (59.589 logic steps/s)
over 58.517 seconds of gameplay, with 1.543 ms spent presenting each image.
Loading and the final state export are excluded. This is close to the requested
30 FPS but does not establish a locked rate in every scene. A 4.923-second codec
sink capture contains nonzero stereo S16 audio at 44.1 kHz. The framebuffer
capture confirms the game image and aspect-preserving bars on the SP panel.

All 50 seeded host room paths complete with the real offline audio mixer.
Their complete recorded states match the 60 FPS baseline exactly. Draw events
continue at the game logic rate; only main-frame rasterization and presentation
are limited to 30 Hz. User-created surfaces continue updating every step.

The Mini build is ARMv7 hard-float with no GLES/EGL dependency and requires
at most GLIBC 2.17. The mounted card runs Onion v4.3.1-1. Its Ports importer,
standalone launcher and keyboard conventions have been checked. Native ARM32
compatibility and input selftests pass using Mini SDK SDL and the card's C
libraries on the SP. Physical Mini display, sound, memory headroom and frame
rates remain unmeasured. The SP has different hardware and more memory.
These results cover recorded paths, not every level or feature of all 50 games.

## Development log

The entries below record successive milestones. Later fixes supersede earlier
blockers and measurements; in particular, whole-Draw-pass skipping is no longer
used.

## Compatibility chunk 2026-10-11

Native game-data-free regression tests pass on macOS ARM64 and the muOS SP
ARM32 SDL 1.2 build (`--compat-selftest`). They cover nested modern JSON,
trailing commas in shipped language files, optional JSON formatting, overlapping
array copies, array-shift ownership, self/cross-grid copy, file copy, and
GameMaker speed argument order. Python importer tests: 8 passed. Shell checks
pass. Collection/file API backports are pinned in `upstreams.lock.json`.

The title probe exits cleanly. The 8,000-frame game-selection probe still times
out after TXTR page 90 is loaded; gameplay is not verified. These API checks
establish behavior of individual functions, not full game compatibility.

## Tile traversal chunk 2026-10-11

A stack sample placed 98% of the busy host thread in `Runner_draw`'s repeated
search through runtime tile elements. Rendering now traverses those elements
once, retaining their order, visibility and alpha. The fresh 8,000-frame owned
game probe exits successfully in 1.60 seconds on the host, reaches
`rm40_Traps` (Barbuta), and produces its starting-room frame. This is host/headless
compatibility evidence; audio, physical controls and device FPS are unproven.

## Audio chunk 2026-10-11

The real miniaudio mixer passes synthetic WAV tests on the host and SP ARM32:
sparse group IDs, repeated group loading, nonzero stereo PCM, independent group
fades, unload while playing, and a safe rejection of unloaded sounds. Audio
loads now retain group IDs and use lazy per-chunk data loading. The SDL1 callback
also sizes mono underrun clearing by its actual channel count. This proves
mixer behavior; a successful device output path and audible game sound are
separate pending checks.

## ARM32 backend chunk 2026-10-11

SDL1 now reads the firmware-selected controller file and gives explicit SDL
mapping strings precedence. It records the actual raw capabilities and optional
GML button transitions. On the SP it identifies muOS-Keys with 15 buttons,
3 axes and 1 hat. Native regression suites pass.

Headless mode no longer initializes video or opens a video mode through a game
resize call. Diagnostic keyboard playback may explicitly suppress physical
pad state. The corrected SP probe completes 6,000 frames in 76 seconds while
the frontend remains active, reaches Barbuta (`rm40_Traps`), and renders the
same scene as the host. Median execution time is 14.14 ms, p95 16.55 ms. This
background/headless run has no audio or physical presentation and is not a
30 FPS acceptance result. Sanitized compatibility and mixer tests also pass
with AddressSanitizer and UBSan (macOS does not support LeakSanitizer).

## Rendering cadence chunk 2026-10-11

The optional `UFO50_RENDER_FPS=30` scheduler retains 60 Hz simulation and
executes the draw pass at 30 Hz. Scheduler regressions pass on host and SP
ARM32, including a non-divisor rate. The same seeded 8,000-step host input
probe reaches the same room with and without the cap. This is a cadence and
compatibility check, not a measured hardware FPS result. SDL1 output now
reports callback frames, nonzero samples and peak amplitude to distinguish
mixer output from an audible-speaker check.

The development entry has launched through the actual muOS Applications
frontend and returned after its bounded test. Rendering and SDL audio
initialization are confirmed; screen sizing, application-visible movement,
nonzero game audio and sustained frame pacing remain under investigation.

## Font selection and frontend gameplay chunk 2026-10-11

`font_exists` now checks live font slots, and sprite-font creation initializes
its slot and marks it present. Previously the game's guarded `scrSetFont`
never selected its own sprite fonts. Host and SP ARM32 regression tests pass;
the host menu probe now shows the game's text. TTF loading remains unsupported.

A real muOS frontend launch reaches Barbuta. The measured SP d-pad produces
GML right transitions and visible player displacement; face input advances
startup and enters the game. SDL audio delivers 4,616,192 frames with
2,056,680 nonzero samples, peak 0.639314, through a PipeWire stream linked to
the codec speaker sink. This verifies digital output, not a physical listening
test. Across 63 gameplay intervals, presented FPS has median 29.72, weighted
mean 29.40, and minimum 25.95. The final screenshot/dump interval is excluded.
The current 640x480 software draw path needs more performance headroom.

## Native presentation chunk 2026-10-11

The SDL1 software backend can retain a 384x216 logical framebuffer while
presenting a nearest-neighbor, aspect-preserving 640x360 image centered on
the 640x480 panel. Desktop resize calls cannot inflate this optional native
framebuffer. Pixel format conversion and pointer coordinates follow the
actual display surface. The SP frontend launch renders the complete UI and
Barbuta scene in this mode, with nonzero real audio output. Frame telemetry
and screenshots are retained outside Git. This is SP evidence; Mini hardware
performance and collection-wide gameplay remain unverified.

## Integer interpreter chunk 2026-10-11

Typed 64-bit AND/OR/XOR/NOT and shifts now retain their width. Previously
the VM narrowed them to 32 bits, so the game's unsigned 32-bit RNG result
became negative and produced invalid shop indexes. Shift sign extension is
explicit, and integer add/subtract/multiply wrap without signed C overflow.
Independent mask/shift regressions pass on host, SP ARM32, and ASan/UBSan.
The seeded Bug Hunter and Velgress probes now complete 6,000 steps; they
previously stalled or aborted. This is headless compatibility evidence.

SDL2 software diagnostics now use an offscreen surface, without initializing
video or opening hidden GPU windows. Array errors include the script name.
The collection sweep uses menu inputs with isolated saves and distinguishes
a game room from a title/high-score screen. Vainger still thrashes the 24 MiB
RGBA texture cache, so larger atlas working sets need a memory improvement.

A five-second capture from the SP codec speaker sink contains 430,080 stereo
samples at 44.1 kHz, 429,963 nonzero, peak 19,311, RMS 4,224. This confirms
real game audio reaches the output sink; the physical speaker listening
check remains separate.

## Palette cache and deadline chunk 2026-10-11

Immutable atlas pages with at most 256 converted colors now use lossless
8-bit indices. Mutable render surfaces remain full color; larger palettes
fall back to RGBA. The cache tracks actual storage and evicts the least
recently used page within a 24 MiB budget. Decoder scratch is additional
transient memory. Pixel regressions pass on host, SP ARM32 and ASan/UBSan;
seeded Barbuta PNGs match byte for byte with palette mode enabled/disabled.
Seven previously timed-out titles now enter their game rooms, including
Mini & Max, Grimstone and Cyber Owls. Big Bell Race and Vainger still fail.

Frame deadlines retain phase after short overruns, avoiding cumulative
simulation slowdown. A normal SP frontend run with real audio completes
12,000 steps. The sustained Barbuta interval measured 29.996 presented FPS and 60.000 simulation Hz over 123.1 seconds.
This is one SP scene with recorded inputs, not collection-wide or Mini
performance acceptance. The final forced screenshot/dump is excluded.

## Grid search chunk 2026-10-11

Inclusive, row-major `ds_grid_value_x/y/exists` searches now handle reversed
coordinates, clamped bounds, mixed numeric types, strings and no-match values.
Independent regressions pass on host, SP ARM32 and ASan/UBSan. Palette tests
also cover transparent and partial-alpha colors. Vainger's missing API
warning is resolved; its offscreen atlas loading still prevents a successful
room smoke test.

## Grid writes and early culling chunk 2026-10-11

The inherited `ds_grid_set` rejected its normal four arguments. Grid writes
now work, and new/resized cells start at numeric zero. Read/write/string
ownership/resize regressions pass on host, SP ARM32 and ASan/UBSan. Big Bell
Race now completes its 6,000-step room smoke test in 1.0 seconds, previously
a level-setup loop. Sprite culling now precedes atlas decoding, with flipped,
fractional and camera-offset bounds covered by independent tests. Vainger's
remaining visible working set still exceeds the 24 MiB atlas budget.

## Packed atlas chunk 2026-10-11

Small lossless palettes now use 1, 2 or 4 bits per pixel, retaining 8-bit
indices for larger palettes. Odd-length buffers, alpha and exact converted
colors pass on host, SP ARM32 and ASan/UBSan. Barbuta's seeded screenshot
matches the previous RGBA/8-bit versions byte for byte. Vainger now enters
`rm07_GravGuns` and completes 6,000 steps in 8.8 host seconds within the
unchanged 24 MiB cache budget. This remains a headless compatibility result.

## Collection room sweep 2026-10-11

All 50 seeded host menu/room probes now exit successfully and visit their
selected game's room. Kick Club returns to high scores after game over;
the report now retains visited rooms instead of treating that as a launch
failure. Each probe executes 6,000 simulation steps, uses isolated saves,
and renders at 30 Hz with no-op headless audio. These are compatibility
smoke checks, not completed gameplay tests or device FPS acceptance.

## Runtime tiles and cleanup chunk 2026-10-11

Runtime tile creation/destruction is backported with explicit ownership.
Created tiles use GMS2 sprite definitions and draw on dynamic layers.
Missing/double deletes are harmless; room teardown frees owned elements.
The atlas cache also recognizes generated surface sprites outside the
original texture pages. Renderer teardown now frees textures, surfaces,
framebuffer and metadata, including teardown while drawing to a surface.
Host, SP ARM32 and ASan/UBSan regressions pass. Vainger, Mini & Max, Seaside
Drive and Cyber Owls complete their post-change room probes.

### muOS Ports integration

The development runtime launches from `/mnt/sdcard/ROMS/Ports/UFO50.sh`
through the installed muOS content loader, which selects ARM32 SDL/audio via
`PORT_32BIT=Y`. The frontend then invokes the dedicated launcher in
`/mnt/mmc/.ufo50-dev`; no launch-state files are synthesized. The visible Ports
selection and runtime parent process were captured in the private evidence.
Normal launches use persistent dedicated saves. Explicit bounded benchmarks
use separate saves and optional recorded keyboard input. Deployment uploads
staged files, verifies the binary SHA256, and refuses to replace a running
runtime. The obsolete Applications diagnostic entry is removed.

### Audio metadata crash regression

The normal Ports Cyber Owls run crashed near simulation frame 3200 with real
SDL audio. The same input sequence with real audio reproduced the failure under
host UBSan: `audio_get_name` dereferenced an unloaded sparse audio-group slot.
The lookup now skips unloaded groups; a synthetic metadata regression covers
valid and out-of-range indexes across those holes. Host sanitizer selftests
and the audio-enabled 4500-step Cyber Owls replay pass. The repaired SP Ports
replay also reaches its bounded completion and returns to the frontend. This
fix demonstrates why headless/no-op-audio room smoke tests alone are insufficient.

### Layer-element lookup index

A five-second host sample attributed 336 of 420 main-thread samples to linear
layer-element lookups from Vainger's type/visibility queries. The runner now
indexes element IDs to array positions, rebuilding after creation, deletion,
movement, room transfer, or layer destruction. It stores positions rather than
pointers so array reallocations are safe. Regression tests exercise 128 tiles,
shifted indexes after deletion, movement, same-layer movement, and destruction.
Host ASan/UBSan selftests pass. The seeded 6000-step Vainger screenshot is
byte-identical; host elapsed time falls from 12.84 to 3.50 seconds. The SP's
sampled later scene improves from roughly 3 to 24 presented FPS, still below
the requested 30. Mini & Max and Cyber Owls host room probes also pass.

### Explicit Miyoo integration profile

The Onion launcher selects native 384x216 rendering, 30 Hz presentation, the
Miyoo keyboard profile, and persistent saves/logs under
`Saves/CurrentProfile/saves/UFO50`. The shortcut detects `gamefiles/data.win`
and uses Onion's standard audio-server/performance lifecycle. The keyboard
profile follows MinUI's Miyoo platform definitions: Space=A, left Ctrl=B,
left Shift=X, left Alt=Y, Return=Start, right Ctrl=Select. A/Y map to Z, B/X to
X, Start to the owned game's default D pause binding, and Select to Escape.
Generic SDL keyboards and the SP's mapped gamepads remain independent.
The native ARM32 `--input-selftest` passes on the SP loader. This verifies the
translation, not physical Mini hardware. Sources:
https://github.com/shauninman/MinUI/blob/main/workspace/miyoomini/platform/platform.h
and https://onionui.github.io/docs/ports .

### Release build and package gates

Disabling VM tracing, GML profiling, and opcode profiling removes diagnostic
checks from release builds. Seeded Vainger, Mini & Max and Cyber Owls host
probes pass; Vainger's screenshot is byte-identical. Vainger host probe time
falls from 3.50 to 2.66 seconds. Its SP sampled later scene improves from
24.523 FPS / 49.077 simulation Hz to 27.985 FPS / 56.005 Hz over 28.408 seconds;
this still misses 30 FPS. Audio-enabled device runs complete normally.

Cross-builds now record source revision/dirty state, binary SHA256, SDL reference
hash and header revision, compiler versions, diagnostics settings, and ELF
metadata. Both binaries are little-endian ARM32 EABI5 hard-float with the
`/lib/ld-linux-armhf.so.3` interpreter, no RPATH/RUNPATH, and a highest required
glibc symbol version of 2.17. The real Miyoo SDK libc is 2.28. Packages require
clean matching source/build records and include the exact committed source.
Six synthetic ELF cases cover target acceptance and rejection of wrong
architecture, soft float, newer glibc, embedded search paths, and truncation;
all 14 Python checks pass. A dirty worktree is rejected before packaging.

### Configurable atlas cache and live SP controls

The software renderer accepts `UFO50_TEXTURE_CACHE_MIB` (4–64 MiB) for controlled
memory experiments and permits one oversized atlas after evicting the others.
The default remains 24 MiB. A 12 MiB full-library sweep timed out in Vainger
and Star Waspir: Vainger repeatedly decoded five atlases, including a roughly
14.5 MiB combined working set. Lowering the cache is not a valid Mini memory fix.
The restored 24 MiB configuration passes all 50 selected-room probes; host
ASan/UBSan cache and compatibility selftests and the synthetic mixer test pass.

Through the live SP's measured SDL controller mapping, A visibly jumps in
Barbuta, X attacks, the D-pad moves, and Start opens the in-game menu. The menu's
Back to Library and Quit confirmations work and return to the normal muOS
frontend. The game creates persistent save data in the normal save directory.
These are application-visible physical-controller-path results; they do not
replace physical Mini controls or a complete collection gameplay pass.

### SP session performance governor

The SP launcher requests the stock `performance` governor for its own session
and restores the exact inherited governor through an EXIT trap. It also owns
and waits for its runtime child, terminating only that child on interruption.
A normal Ports Vainger replay verifies `ondemand -> performance -> ondemand`,
with every sampled CPU frequency at the existing stock 1,512,000 kHz limit.
No frequency limits are changed. The later 28.264-second sampled interval
averages 28.765 FPS / 57.564 simulation Hz; some intervals reach 30 FPS, but
the requested sustained target still fails. Earlier gameplay averages 28.453
FPS. Observed peak VmHWM is 111,104 KiB. The SP loads a sizeable SDL compatibility
and GPU stack, so its total RSS does not establish the physical Mini's headroom.

### Native-size sprite blits and clipped-flip safety

A native-size, untinted, normal-blend sprite path separates palette and RGBA
storage once per row and writes opaque pixels directly. An expanded independent
pixel oracle exposed a pre-existing clipped-flip overread in the generic path:
clipping X also shifted Y by one texel. Destination clipping now preserves the
original source transform and bounds every sample that lies outside an atlas.
The oracle checks scaling, both flips, clipping, tint, alpha, and palette/RGBA
storage. Host ASan/UBSan and all 50 room probes pass. Forty-nine final frames
match the previous renderer byte for byte; Paintball's clipped edge changes.
Seeded 30/60 draw probes for Barbuta, Vainger, Star Waspir and Cyber Owls reach
identical rooms and player/entity positions; their globals differ only in the
three wall-clock timestamps. This is limited parity evidence, not a complete
Draw-event semantics or full-collection gameplay certification.

### Full collection offline audio diagnostics

Explicit headless offline-audio mode initializes the real no-device miniaudio
engine, uses simulated room time, synchronously resolves streamed files, and
drains PCM each step. Normal interactive audio is unchanged. All 50 seeded
6000-step room probes complete with nonzero PCM, totaling 220,579,380 mixed
frames. Synthetic initialization, sample advancement, sparse groups, and fades
pass under ASan/UBSan. Cyber Owls and Star Waspir instrumented audio probes pass;
Vainger requires a longer instrumented timeout. These are host mixer/compatibility
results, not physical speakers or exhaustive gameplay coverage.

The full 30/60 real-mixer comparison exposes entity or RNG differences in some
games. Skipping entire Draw-event passes is therefore not a valid general 30 FPS
implementation. Preserving Draw-event semantics while reducing framebuffer work
is a required follow-up before a distributable default is accepted.

### Preserve Draw-event behavior at 30 FPS

Draw events now run on every simulation step. Only writes to the main software
framebuffer and display presentation are limited to 30 Hz; user-created surfaces
remain writable every step. This replaces the earlier whole-Draw-pass skip,
which changed entity state or RNG in nine recorded game paths.

Headless fixed-time diagnostics also use a simulated monotonic and calendar
clock. With identical input plans and the real offline mixer, all 50 complete
state snapshots match the 60 FPS baseline exactly, with no variables filtered
out. Compatibility tests cover discarded main-frame writes and continued
user-surface writes; host ASan/UBSan tests pass. This is bounded path parity,
not exhaustive gameplay coverage. Interactive clocks remain unchanged.

### ARM ThinLTO build and live Vainger timing

Both ARM targets enable CMake interprocedural optimization using Zig's LLVM
archive wrappers. Compiler detection is refreshed on each configure so stale
CMake compiler metadata cannot leave IPO without its archiver. The native
ARM32 build passes compatibility and input selftests on the SP.

With all Draw events preserved, the live SP Vainger run completes 6,000 steps.
The frame 2,200–4,399 interval presents 29.489 FPS at 58.977 logic steps/second
over 37.370 seconds; frames 4,400–5,998 present 29.539 FPS at 59.077 steps/second
over 27.286 seconds. The real output callback mixes 4,712,448 frames with
8,179,722 nonzero samples. These intervals exclude the final diagnostic dump.
The launcher requests the stock 1.512 GHz performance governor and restores
its inherited setting. This approaches the target on the SP; it does not prove
stable 30 FPS across the collection or performance on the Mini.

### Mini launcher integration

The mounted card is Onion v4.3.1-1. Its actual Ports importer and standalone
launcher search with `find -iname`: the data checker must use `data.win`, not
`gamefiles/data.win`. The required file remains in the `gamefiles/` directory.
The launcher now owns its 1.5 GHz clock/performance request and restores the
inherited frequency and governor. Fixture tests cover nonzero runtime exits,
SIGTERM child cleanup, exact restoration and rejection of invalid settings.
`UFO50_PERF_LOG=0` now disables performance logging as intended.

The native ARM32 compatibility and Mini-key mapping selftests pass on the SP
with the Mini SDK SDL 1.2 and the mounted card's glibc/loader. This tests ABI and
logic only. The card's hardware SDL also needs SigmaStar libraries supplied by
Mini firmware; it cannot operate the SP's different display/audio hardware.

### Save-preserving installation helper

`deploy-miyoo.py` validates the clean source/build record, package CRC, ARM ABI,
runtime and source archive hashes, and launcher/source files before SD writes.
It archives the existing UFO 50 installation, shortcuts and saves, stages the
new runtime plus owned assets, verifies every staged file, and promotes the
staging directory. Final asset and save manifests must match the originals.
Fixture tests cover preservation, backup contents, rollback after promotion,
missing assets and refusal to replace existing owned inputs. Package archives
now include an empty `gamefiles/` directory and plain copying instructions.

### Isolate SDL1 headless input

Explicit headless SDL1 mode no longer opens joysticks or polls physical input.
Recorded inputs still feed the runner directly; interactive input is unchanged.
On the SP with Mini SDK SDL, the first two 6,000-step real-mixer paths now
complete in 27.2 and 17.7 seconds, compared with roughly 100 seconds when SDL
polled the SP's input devices. PCM counts match the earlier runs. The first state comparison differs only
in controller-presence fields (`joySlot`, `joyConnected`, and `padCount`),
as expected when the probe stops exposing the SP joystick; gameplay fields match. Native compatibility and Mini key-mapping selftests
pass. All 36 referenced SDL symbols are exported by the mounted card's SDL.
This isolates the ABI/logic probe; it does not simulate the Mini's device timing.

### Mini first-run diagnostics and menu refresh

Development launches record memory/swap at startup and presented frame counts
in the private save-log directory. `UFO50_PERF_LOG=0` disables timing output.
The SD installer backs up Onion's generated Ports list cache and removes it only
after file verification, allowing the new `.port` entry to be discovered.
Rollback restores the cache along with the original shortcut and installation.
The existing Onion startup/swap configuration is left intact.

### Complete native ARM32 collection sweep

All 50 recorded 6,000-step paths enter their selected game and finish with
nonzero PCM using the Mini build on the SP, Mini SDK SDL 1.2, and the card's
loader/C libraries. The offline mixer produced 220,579,380 stereo frames.
Peak process RSS was 83,431,424 bytes, including diagnostic state export.
These are bounded compatibility paths; they do not establish Mini hardware
FPS, physical audio output, or complete gameplay coverage.

### Reuse collision target order

Golfaria profiling found repeated collision-target sorting. Each target object
now keeps a sorted candidate list, invalidated along the affected ancestor
chains when instances are added, removed, or changed. Collision handlers still
iterate independent snapshots; creation-order lists used elsewhere are intact.
A synthetic regression covers nested snapshots, creation, removal, object
changes and room-list clearing. All 50 host snapshots match the previous
build exactly with the same seeded inputs and real offline mixer. ASan/UBSan
compatibility tests pass. Device performance is checked separately.

### Cull tile raster work before asset lookup

The software renderer exposes conservative world bounds for its current target.
Legacy tiles outside those bounds return before resolving texture metadata;
GMS2 tile grids iterate the visible cell range with padding for rounding.
Discarded main frames have an empty raster region, while user-created surfaces
keep their own region and continue updating at the logic rate. All 50 seeded
host states and final PNGs match the collision-cache baseline exactly.
Sanitized compatibility tests pass, including main-frame discard and surface
raster bounds.

### Avoid the unused SDL timer thread

SDL1 initialization no longer requests the callback timer subsystem. The port
uses its monotonic frame clock and SDL_Delay; SDL initializes its tick counter
regardless of subsystem flags ([SDL source](https://github.com/libsdl-org/SDL-1.2/blob/main/src/SDL.c)).
The ARM32 build passes compatibility/input tests and completes the recorded
Golfaria and Valbrace paths with real offline PCM and clean shutdown using
the card's glibc and Mini SDK SDL, without supplying libgcc_s to that fixture.

### Reject distant collision candidates through the spatial grid

Collision dispatch keeps the entire sorted target snapshot but tests occupied
grid cells before calculating candidate boxes. After a handler runs, it refreshes
the grid and the self range, so an existing target moved into range can still
receive its event in the original order. Sprite origin, bounding mode, creation
and deletion changes refresh affected instances. A regression moves an existing
instance between cells by changing its sprite origin, then expands its box.
All 50 complete seeded host states match the previous build exactly; sanitized
compatibility tests pass. The slower geometry-cache experiment was reverted
after native performance testing.

### Skip automatic traversal for discarded main frames

The runner avoids default instance graphics and automatic layer element
traversal when the software renderer is discarding the main frame. Draw events
and both layer scripts still execute; a script that binds a user surface
continues rendering into it. All 50 seeded host states and final PNGs match
the previous build exactly, and sanitized compatibility tests pass.

### Cache Draw response bits

Each object keeps one byte indicating which standard Draw phases have a
resolved handler. Draw dispatch can skip the immutable event-table scan for
nonresponders, while responding objects still use the same code and owner
resolution. The cache costs one byte per object. All 50 seeded host states
and final PNGs remain identical, and sanitized compatibility tests pass.

### Clear only the display borders

SDL1 presentation clears the bars outside the scaled image; SDL_SoftStretch
overwrites the image rectangle. A native ARM32 oracle compares all visible
pixels against the previous full-clear path in 48 cases, with both RGB565 and
32-bit surfaces, asymmetric borders, and different previous contents. Both the
SP library and Mini SDK library pass. Presentation time is recorded separately
from drawing. Python and launcher checks pass.

### Reuse display scaler samples

The SDL1 display scaler caches horizontal source positions and copies repeated
output rows. It preserves original SDL1 top-left samples and SDL12-compat's
centered samples ([SDL12-compat](https://github.com/libsdl-org/sdl12-compat/blob/main/src/SDL12_compat.c),
[SDL2 scaler](https://github.com/libsdl-org/SDL/blob/SDL2/src/video/SDL_stretch.c)).
The 48 native pixel comparisons pass independently with each library, including
cache rebuilds between different source sizes and display rectangles. This
changes presentation only; game surfaces and Draw events use the same renderer.

### Use the native logical display on muOS

The SP launcher requests a 384×216 SDL1 logical display. Its installed
SDL12-compat renderer scales this to the 640×480 panel with nearest sampling
and aspect-preserving bars. This avoids converting and uploading a full
640×480 surface in the compatibility layer. Display synchronization is disabled
in that layer; the runner retains its own 60 Hz logic / 30 Hz presentation clock.
The Mini launcher retains its hardware display mode and software scaler. The
standalone pixel oracle now includes equal-width copies: 54 cases pass with
each SDL library.
