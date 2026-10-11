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
