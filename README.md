# UFO 50 for Miyoo Mini

UFO 50 for Miyoo Mini and Mini Plus running Onion. You need your own Windows
copy of the game. This is the first release; not every game and level has been
fully tested.

![Barbuta gameplay](docs/images/gameplay.gif)

[About the capture](docs/media.md)

## Huge thanks to Butterscotch

**This port exists because of [Butterscotch](https://github.com/ButterscotchRunner/Butterscotch).**
Huge shout-out to its creators and contributors for building the open-source
GameMaker runner that does the hard work here. Thanks also to
[cobaltgit's Onion branch](https://github.com/cobaltgit/Butterscotch/tree/onion-v2),
which gave this port its starting point. They deserve the credit for the runner.

## Install

1. Enable **Ports Collection** in Onion's Package Manager.
2. Download `ufo50-miyoo-mini-v0.1.0.zip` from
   [Releases](https://github.com/Producdevity/ufo50-miyoo-mini-port/releases/tag/v0.1.0)
   and extract its `Roms` folder to the root of your SD card.
3. In Steam, right-click UFO 50 and choose **Manage → Browse local files**.
4. Copy the contents of that Windows game folder into
   **`Roms/PORTS/Games/UFO50/gamefiles/`**. Keep the audio groups, textures, fonts
   and `ext` folders together. You do not need the Windows executable.
5. Run **~Import ports**, then open **Action → UFO50**.

The game files should look like this:

```text
Roms/PORTS/Games/UFO50/gamefiles/
  data.win
  audiogroup_sfx.dat
  textures/
  fonts/
  ext/
```

`data.win` must be directly inside `gamefiles`. A ZIP or an extra UFO50 folder
inside it will not work. Game files are not included in the download.

## Controls and saves

| Button | Action |
| --- | --- |
| D-pad | Move / select |
| A or Y | First action / confirm |
| B or X | Second action |
| Start | Pause menu |
| Select | Back / menu |

Use the game's menus to return to the library and quit. Saves are in
`Saves/CurrentProfile/saves/UFO50`. Back them up before updating.

UFO 50 uses a 16:9 picture. Black bars on the Mini's 4:3 screen are normal.

## Problems and source

[Open an issue](https://github.com/Producdevity/ufo50-miyoo-mini-port/issues)
with your Mini model, Onion version and the latest log from
`Saves/CurrentProfile/saves/UFO50/logs`.

Build instructions are in [CONTRIBUTING.md](CONTRIBUTING.md). Source is
AGPL-3.0; see [LICENSE](LICENSE), [NOTICE](NOTICE) and
[third-party licenses](licenses/THIRD_PARTY.txt). Each release includes its
matching source archive. UFO 50 is made by Mossmouth and its creators; the game
is not distributed here.
