# Reddit feedback, 12 October 2026

Reviewed the [UFO 50 thread](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/ufo_50_on_the_miyoo_mini/) and its public JSON comment tree. The refreshed snapshot reports 14 comments: six top-level comments and eight nested replies. All 14 were retrieved; no `more` nodes or pagination cursors remained. This is a point-in-time snapshot of a live thread.

| Report or request | Source | What the report establishes |
| --- | --- | --- |
| Black screen at launch | [Launch report](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfiuuk4/) | A user cannot reach the game. |
| “Games” folder reported corrupt while copying the release to the SD root; reinstalling the ports collection allowed import, but launch remained black | [Installation report](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfiqtud/) | The same reporter describes both failures and says the game files came from Steam. No device model, firmware version, log, or game version is supplied. |
| Performance information | [First question](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfiqdkb/), [second question](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfiuu06/), [follow-up](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfixp67/) | Readers want to know how well it runs. |

The author requested logs and the device model. Their replies describe approximately [24 FPS in the first few games](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfj1t19/) and [20–30 FPS](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfj1gu7/). These are anecdotal observations, without a documented measurement method or named games.

A later [reply](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfj3id6/)
confirms the original reporter uses a Mini Plus and asks where logs are. Another
[reply](https://www.reddit.com/r/MiyooMini/comments/1x4cqb0/comment/pfj68mm/) suggests
fixing Textures capitalization and copying all audio groups. The remaining
comments share the port page, thank the author, or react with a GIF. They
contain no additional bug report.

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

At the time of the first snapshot, no reporter log was available. The fixes
cover reproduced incomplete-file failures and launch weaknesses; the original
Reddit copy error does not establish an archive fault.

Verification: 36 host checks pass; all 10 launcher checks also pass with the
SP's BusyBox shell. The native Mini build passes compatibility tests, complete
owned-file startup and a missing-texture failure with Mini libraries on the SP.
A normal SP Ports run reaches Barbuta, reports 29.973 FPS over 18.183 seconds
of sampled gameplay, produces nonzero audio callback data and returns to the
frontend. This does not validate the reporter's Mini or its physical speaker.

## Follow-up report and capitalization fix

[GitHub issue #1](https://github.com/Producdevity/ufo50-miyoo-mini-port/issues/1)
arrived during the investigation. A Mini Plus user on Onion 4.4.0 beta reports
that the game works after changing `Textures` to `textures` and adding the
missing audiogroup .dat files. Their [startup log](https://pastebin.com/1zQZb9eV)
shows SDL audio initialized, 30 presentations per second in the library and
zero nonzero audio samples while audio group 2 is missing. This is a
community-reported recovery, not a new test performed by this project.

Owned asset reads now accept unique case-insensitive path components, including
`Textures` and capitalized audio filenames. Existing exact names win; ambiguous
case matches fail. No files are renamed and save-write paths are unchanged.
The full owned-file fixture with capitalized folders/audio names reaches
Barbuta on host and native Mini ARM32, with exactly the same screenshot hash
and offline audio counts as the canonical copy. Native tests on the SP's
case-sensitive /tmp verify exact-name precedence and ambiguity rejection;
a separate full-game startup there checks all 105 textures and 52 used audio
groups and produces nonzero offline audio. The SD itself uses case-insensitive
exFAT, so that /tmp check is the meaningful case-sensitive regression.

The host suite runs 38 tests, with one ambiguity test skipped on its
case-insensitive filesystem. That scenario passes natively on /tmp. All 10
launcher tests pass under the handheld's BusyBox shell. The corrupt-folder
copy report still has no filesystem diagnostic; instructions explain how to
merge the port while retaining other games.
