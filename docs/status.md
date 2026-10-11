# Development status

2026-10-11: clean source import and build verified. The eight importer tests pass, and a fresh host build completes the existing 8,000-frame init/library/title/Cyber Owls intro path. This is a baseline, not a gameplay or hardware result.

Current development target: RG35XX SP, muOS 2601.0 JACARANDA, build bc38efa0. User authorized device use. Goal: native ARM32 software rendering at 30 FPS with audio and application-visible controls, with a clean game-free release for Miyoo Mini.

The earlier prototype has 65 unresolved function names and an ARM rendering discrepancy. These are open blockers. Actual gameplay, save reload, audio and frame timing must be verified before declaring the port working.
