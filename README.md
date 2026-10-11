# UFO 50 for Miyoo Mini

A native ARM32 UFO 50 port based on the Butterscotch interpreter and software
renderer. Development uses an RG35XX SP running muOS; the target hardware is the
Miyoo Mini and Mini Plus running Onion. **This is a development build. Physical
Miyoo validation and 30 FPS across the collection are still outstanding.**

The owned Windows game runs directly from its assets. The PortMaster port was
investigated as the starting point, but its GameMaker runner/GLES path does not
fit the original Mini. This project uses native ARM32, software rendering,
packed palette textures, bounded texture caching, and an SDL audio mixer.
It does not require the PortMaster runtime on the Mini.

## Verified so far

- All 50 games reach their selected game rooms in bounded host smoke tests.
- The SP launches the native runtime from **Ports → UFO50** and returns through
  the normal muOS loader. There is no Applications entry.
- Barbuta sustains 29.996 presented FPS over a 123-second sampled interval;
  Cyber Owls sustains 29.980 FPS over a 20-second sampled gameplay interval.
  Simulation remains approximately 60 steps/second in those intervals.
- Actual game audio reaches the SP's codec sink. Physical-controller events
  reach the game; dedicated action/pause/save regression testing continues.
- Vainger exposes heavier CPU and memory demands and is still being optimized.

These measurements describe the tested SP scenes, not every game or the Mini.
Read [current evidence and limits](docs/status.md) and the
[source-based research](docs/research-2026-09.md). Proprietary inputs, screenshots,
saves, audio recordings, and generated reports stay outside Git.

## Install on Miyoo Mini / Mini Plus

Enable Onion's Ports Collection. Extract the Miyoo development archive to the
SD root. Supply your owned Windows UFO 50 files using the host importer:

```sh
python3 scripts/ufo50.py import /path/to/UFO50.zip /path/to/SD/Roms/PORTS/Games/UFO50/gamefiles
```

The destination must be new; the importer refuses overwrites, ambiguous game
roots, unsafe ZIP paths, and symlinks. It imports game assets only, excluding
executables and saves. Keep the original ZIP. Run Onion's `~Import ports`, then
launch UFO 50 from Ports. Saves and logs belong to
`Saves/CurrentProfile/saves/UFO50`, separate from the install directory.

The runtime links to the firmware's SDL 1.2; libraries from the SP or Miyoo Flip
must not be substituted. A physical Mini launch, input, audio, memory, and
performance pass is required before treating this package as a validated release.

## Install on the muOS SP development device

The SP archive has two roots: copy `mmc/` contents to `/mnt/mmc/` and `sdcard/`
contents to `/mnt/sdcard/`. Import owned assets into
`/mnt/mmc/.ufo50-dev/gamefiles/`. The shortcut is
`/mnt/sdcard/ROMS/Ports/UFO50.sh`; launch **Ports → UFO50**.
Normal saves persist under `/mnt/mmc/.ufo50-dev/saves/`; logs are in `runs/`.

For this repository's configured development device:

```sh
sh scripts/build-sp.sh
sh scripts/deploy-sp.sh muos-sp
```

Deployment verifies the runtime hash, stages replacements, and refuses to
replace a running game. It preserves gamefiles and saves. Existing saves should
be backed up before any manual installation.

## Build and investigate

See [CONTRIBUTING.md](CONTRIBUTING.md) for dependencies, reproducible builds,
regression checks, bounded probes, and device diagnostics. The repository uses
`master`. Game data is not required for synthetic compatibility/audio tests.

```sh
sh scripts/check.sh
sh scripts/build-host.sh
artifacts/host/butterscotch --compat-selftest
python3 scripts/test-audio.py artifacts/host/butterscotch
```

Cross-builds use Zig 0.16.0, ARMv7 hard-float, and pinned SDL 1.2 headers. Packages
require a clean source commit and matching build records, check the ELF ABI and
dynamic dependencies, include the exact committed source and licenses, and
exclude game data. Development archives are generated with:

```sh
sh scripts/build-armhf.sh
sh scripts/build-sp.sh
python3 scripts/package.py
```

## License and credits

Port and vendored runtime source are AGPL-3.0; retained dependencies have their
own licenses. See [NOTICE](NOTICE), [LICENSE](LICENSE), and the source archive
included in each package. Credit belongs to the Butterscotch developers and
contributors, the PortMaster developers for their earlier UFO 50 work, and the
Onion/muOS communities. UFO 50 and its assets belong to their respective owners;
this repository does not contain the game or distribute it.
