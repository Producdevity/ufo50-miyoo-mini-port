# Reddit feedback, 12 October 2026

Reviewed the [UFO 50 thread](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/ufo_50_on_the_miyoo_mini/) and its public JSON comment tree. The snapshot reports 12 comments: six top-level comments and six nested replies. All 12 were retrieved; no `more` nodes or pagination cursors remained. This is a point-in-time snapshot of a live thread.

| Report or request | Source | What the report establishes |
| --- | --- | --- |
| Black screen at launch | [Launch report](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfiuuk4/) | A user cannot reach the game. |
| “Games” folder reported corrupt while copying the release to the SD root; reinstalling the ports collection allowed import, but launch remained black | [Installation report](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfiqtud/) | The same reporter describes both failures and says the game files came from Steam. No device model, firmware version, log, or game version is supplied. |
| Performance information | [First question](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfiqdkb/), [second question](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfiuu06/), [follow-up](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfixp67/) | Readers want to know how well it runs. |

The author requested logs and the device model. Their replies describe approximately [24 FPS in the first few games](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfj1t19/) and [20–30 FPS](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfj1gu7/). These are anecdotal observations, without a documented measurement method or named games.

The remaining comments share the port page, thank the author, or react with a GIF. They contain no additional bug report.

Investigation should reproduce a clean release install, check launch prerequisites and diagnostics, and distinguish archive problems from an existing SD filesystem problem. The reports alone do not identify a root cause. Performance claims need device and scene measurements.

The full retrieved tree and flattened comment list are kept privately under `artifacts/evidence/reddit-feedback/`; only this issue inventory is checked in.

## Changes and verification

The release ZIP downloaded from GitHub passes CRC verification and matches the
published SHA256. No malformed archive or pathname was found. The copy failure
happens before the game runs; its SD filesystem state cannot be diagnosed from
the comment alone. Installation instructions now explicitly merge the two
UFO50 paths and preserve existing port folders.

The inherited texture loader warns and continues when an external texture is
missing. Reproducing a missing texture folder confirms an incomplete copy can
reach that path. The runtime now checks external texture headers/dimensions and
FORM lengths for data.win and audio groups actually referenced by sounds before
creating the VM or opening video/audio. Empty audio groups declared by the game
are allowed. These are disk checks, not full compressed-asset integrity checks.

The launcher now selects firmware library paths explicitly, with an Onion
loader fallback. Onion's [standalone launcher](https://github.com/OnionUI/Onion/blob/main/static/packages/Emu/Ports%20Collection/Emu/PORTS/launch_standalone.sh)
only adds its compatibility path for ports containing lib/ or libs/. Errors use
Onion's [infoPanel](https://github.com/OnionUI/Onion/blob/main/src/infoPanel/infoPanel.c).
A watchdog stops a startup that hasn't presented its first frame after 60
seconds; after readiness it places no time limit on play. Original clock and
governor settings are restored when the process exits.

The reporter's black-screen root cause remains unconfirmed without their log.
These fixes cover reproduced incomplete-file failures and launch weaknesses;
they do not establish that the reporter's device is fixed.

Verification: 36 host checks pass; all 10 launcher checks also pass with the
SP's BusyBox shell. The native Mini build passes compatibility tests, complete
owned-file startup and a missing-texture failure with Mini libraries on the SP.
A normal SP Ports run reaches Barbuta, reports 29.973 FPS over 18.183 seconds
of sampled gameplay, produces nonzero audio callback data and returns to the
frontend. This does not validate the reporter's Mini or its physical speaker.
