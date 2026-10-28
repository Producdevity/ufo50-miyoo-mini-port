UFO 50 for Miyoo Mini and Mini Plus (Onion)

1. Enable Ports Collection in Onion's Package Manager.
2. Merge the ZIP's Roms folder into the root of your SD card. Keep existing
   Games and Shortcuts folders; overwrite only UFO50 port files.
3. Copy the contents of your Windows UFO 50 game folder into:

   Roms/PORTS/Games/UFO50/gamefiles/

   data.win must be directly inside gamefiles, alongside the audio groups,
   textures, fonts and ext folders. Do not put a ZIP or another UFO50 folder
   there. Copy every audiogroup*.dat file alongside data.win. Either textures
   or Textures is accepted. You do not need the Windows executable.
4. Run ~Import ports, then open Action > UFO50.

Official cover artwork is included in Roms/PORTS/Imgs/UFO50.png.
To add just the cover to an existing install, copy that PNG to the same path.

D-pad: move/select. A or Y: first action/confirm. B or X: second action.
Start: pause menu. Select: back/menu.

Use the game's menus to return to the library and quit.
Saves: Saves/CurrentProfile/saves/UFO50
Logs: Saves/CurrentProfile/saves/UFO50/logs
Back up your saves before updating.

UFO 50 uses a 16:9 picture. Black bars on the Mini's 4:3 screen are normal.
For scanlines, open Pause > Settings > Video Settings > CRT Effect and
choose Soft or Hard. Off keeps the normal picture.

The port targets 30 FPS. Heavier games can run slower.

If startup stalls for 60 seconds, the launcher stops it and shows an error.
For missing/incomplete files, recopy the whole Windows game folder. For any
other launch failure, share the latest log, Mini model and Onion version at:
https://github.com/Producdevity/ufo50-miyoo-mini-port/issues

If your computer reports a corrupt Games folder, stop the copy, back up the
card and check its filesystem. Copying this port should merge into existing
folders, keeping your other ports and saves.

Huge thanks to the Butterscotch team and cobaltgit's Onion branch for the
GameMaker runner that makes this port possible.
https://github.com/ButterscotchRunner/Butterscotch
https://github.com/cobaltgit/Butterscotch/tree/onion-v2

UFO 50 belongs to its creators and is not included. You need your own copy.
Port source and matching release source:
https://github.com/Producdevity/ufo50-miyoo-mini-port
