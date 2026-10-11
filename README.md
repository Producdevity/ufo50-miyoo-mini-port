# UFO 50 for Miyoo Mini

A native port for Miyoo Mini and Mini Plus running Onion. You need your own
Windows copy of UFO 50.

This is a development build. Controls, audio, saving, loading and quitting have
been tested on a muOS SP. Measured gameplay is close to 30 FPS: Golfaria averages
29.8 FPS and Vainger 29.5 FPS. Display, sound and performance still need to be
tested on a physical Mini.

## Install

1. Enable **Ports Collection** in Onion's Package Manager.
2. Extract `ufo50-miyoo-mini-development.zip` to the root of your SD card.
3. Open your Windows UFO 50 installation folder. In Steam, right-click the game
   and choose **Manage → Browse local files**.
4. Copy the contents of the Windows game folder into
   `Roms/PORTS/Games/UFO50/gamefiles` on the SD card. Keep the audio groups,
   texture files, fonts and language folders together. The Windows executable
   is not needed.
5. Run **~Import ports** in Onion's Ports collection, then open **Action → UFO50**.

The file layout should look like this:

```text
SD card/
  Roms/PORTS/Games/UFO50/
    script.sh
    bin/butterscotch
    gamefiles/
      data.win
      audiogroup_sfx.dat
      ...the remaining game assets and folders...
```

**`data.win` must be at `Roms/PORTS/Games/UFO50/gamefiles/data.win`.** Extract the
files first; putting a ZIP or an extra UFO50 folder inside `gamefiles` will not
work. Game files are not included in the download.

## Controls and saves

| Button | Action |
| --- | --- |
| D-pad | Move / select |
| A or Y | First action / confirm |
| B or X | Second action |
| Start | Pause menu |
| Select | Back / menu |

Use the game's menu to return to the library and quit. Saves are stored in
`Saves/CurrentProfile/saves/UFO50`. Launcher logs are in its `logs` folder.
Reinstalling the port does not require deleting your saves.

The launcher requests 1.5 GHz through Onion's clock helper, as the Balatro port
does, and restores the previous settings when the game closes. Set
`UFO50_CPU_MHZ=off` in `script.sh` if you want to keep your existing clock.

## Development

The SP version appears under **Ports → UFO50**. See
[CONTRIBUTING.md](CONTRIBUTING.md) for builds, asset importing, SP installation
and tests. [docs/status.md](docs/status.md) records measured results and known
limits. All 50 games enter their selected rooms in bounded host tests with the
real audio mixer; those tests do not cover every level or feature.

Source, launchers and build scripts live in this repository. Game files, saves,
recordings and generated builds stay outside Git. Packages include the exact
source used to build the runtime.

## Credits and license

Based on [Butterscotch](https://github.com/cobaltgit/Butterscotch), with thanks to
its contributors, the PortMaster UFO 50 port, and the Onion and muOS developers.
Port and runtime source are AGPL-3.0; dependency licenses are retained. See
[LICENSE](LICENSE) and [NOTICE](NOTICE). UFO 50 belongs to its creators; this
repository does not distribute the game.
