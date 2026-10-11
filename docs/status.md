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
