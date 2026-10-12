# Gameplay capture

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
