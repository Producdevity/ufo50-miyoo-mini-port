# Media credits

## Launcher cover

`port/artwork/UFO50.png` is the official UFO 50 Steam library cover, resized from
300×450 to 240×360 and compressed to a 256-colour PNG (52,780 bytes). Its full
composition and aspect ratio are preserved. The installer puts it in
`Roms/PORTS/Imgs/UFO50.png`, matching the port shortcut's name.

- [Official game page](https://50games.fun/)
- [Steam store page](https://store.steampowered.com/app/1147860/UFO_50/)
- [Original cover](https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1147860/library_600x900.jpg)
- Original SHA-256: `71bfa275e34eb48c623c874e6786e53e163f87be8e1d46b80fb6d39f039b70cf`
- PNG SHA-256: `44bfff057647775ce21bb0b84d4a268af621942d4c65ae9001a76bf6ec863e49`

Artwork © Mossmouth, LLC, supplied for game identification. It is separate from
the port code's AGPL license. Downloaded 2026-10-28. The original JPEG and the
publisher's media kit stay in ignored `.local/artwork/`.

The conversion used ImageMagick to resize and strip metadata, then pngquant
with 256 colours, quality 90–100 and speed 1. No artwork was generated or redrawn.

## Gameplay capture

The README GIF shows Barbuta running in this port's ARM32 software renderer.
It was recorded through the normal Ports launcher on the RG35XX SP development
device with muOS 2601.0. The game viewport is cropped from the active framebuffer;
the image is upright and retains its original 16:9 aspect ratio.

The clip contains 80 frames at 10 frames per second (eight seconds), encoded
without audio. Capture starts after the selected game room has loaded and shows
movement and jumping. The bounded run uses isolated saves and restores the
frontend and inherited governor when it exits.

This footage demonstrates the runtime gameplay path. It does not establish
Miyoo Mini frame rates or physical speaker output.

Capture date: 2026-10-12. Runtime source: `cc01b17e3be69deb6404d1eaac8da93e6aafca85`.
Raw captures, input plans and device logs remain in ignored development evidence.
