# Development status

2026-10-11: clean source import and build verified. The eight importer tests pass, and a fresh host build completes the existing 8,000-frame init/library/title/Cyber Owls intro path. This is a baseline, not a gameplay or hardware result.

Current development target: RG35XX SP, muOS 2601.0 JACARANDA, build bc38efa0. User authorized device use. Goal: native ARM32 software rendering at 30 FPS with audio and application-visible controls, with a clean game-free release for Miyoo Mini.

The earlier prototype has 65 unresolved function names and an ARM rendering discrepancy. These are open blockers. Actual gameplay, save reload, audio and frame timing must be verified before declaring the port working.

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
