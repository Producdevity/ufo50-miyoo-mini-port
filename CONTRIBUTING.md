# Development

Runtime source is under `runtime/`, imported from the pinned Butterscotch Onion branch. Port-owned integration lives under `scripts/`, `build/` and `port/`. Runtime changes are maintained directly in source. Keep upstream notices.

Builds and test results go in ignored `artifacts/`. Machine-local dependency references and owned game files go in ignored `.local/`. Never commit original game data, decompiled game scripts, saves, PCM recordings or copied artwork.

Run `sh scripts/check.sh`, then `sh scripts/build-host.sh`. A bounded game probe is:

```sh
python3 scripts/probe.py artifacts/host/butterscotch .local/gamefiles/data.win artifacts/evidence/my-run --frames 8000 --headless --inputs tests/library-inputs.json
```

Importer: `python3 scripts/ufo50.py import /path/to/ufo50.zip .local/gamefiles`. The destination must be new. `.local/gamefiles` can instead point at a previously imported copy.

ARM32 build: provide a compatible Miyoo SDL 1.2 reference with `python3 scripts/prepare-sdl.py /path/to/libSDL-1.2.so.0`, then run `sh scripts/build-armhf.sh`. Zig, CMake, Git and Python are required; host builds additionally need SDL2 development files and pkg-config. SDL libraries are link references and are excluded from packages.

Commit only verified chunks. `python3 scripts/package.py` produces an Onion package containing runtime, launcher and the committed source. Physical SP and Mini results must identify the firmware, artifact hash, resource envelope and tested behavior.
