# UFO 50 on Miyoo Mini: runtime research

Research date: 2026-09-13. This is a source-based feasibility assessment, not evidence of a working Miyoo build or gameplay. Target: original Miyoo Mini / Mini Plus, not Miyoo Flip.

## Assessment

A native port is worth prototyping, but copying the PortMaster package is insufficient. The best first experiment is the existing **Butterscotch software-renderer Miyoo branch**, followed by an audit of UFO 50's unsupported functions and memory use. A second route is ARM32 gmloader-next with software GLES2. Neither route establishes that all 50 games will run at acceptable speed.

The Miyoo Mini SDK organization lists a dual-core Cortex-A7 SSD202D, 128 MB DDR3 and 640×480 display. The whole 128 MB is a hardware total, not the application's usable budget. The current RHH UFO 50 port describes its intended devices as ARM64 with Mali graphics and usually 1–2 GB RAM, and already compresses audio to save memory. Those are materially different targets. [Miyoo SDK hardware information](https://github.com/MiyooMini), [RHH UFO 50 README](https://github.com/JeodC/RHH-Ports/blob/main/ports/released/gamemakerengine/ufo50/ufo50/README.md)

## PortMaster / gmloader-next route

**ARM32 support exists.** At upstream commit `522d964025e8ecb739c5aeb0f57afaf6f7927849`, gmloader-next CI explicitly builds both `arm64` and `armhf`, with the latter using `arm-linux-gnueabihf`. Its loader is a compatibility layer for Android native libraries, not an ARM64-only bytecode engine. The ARM64 executable shipped for UFO 50 cannot itself execute on Cortex-A7. [Build matrix](https://github.com/JohnnyonFlame/gmloader-next/blob/522d964025e8ecb739c5aeb0f57afaf6f7927849/.github/workflows/build.yml), [loader description](https://github.com/JohnnyonFlame/gmloader-next)

**The graphics contract is GLES2.** `gmloader/main.cpp` creates an SDL OpenGL window and requests an OpenGL ES 2.0 context; `thunks/khronos/gles2.cpp` forwards the runner's GLES calls. Setting `SDL_RENDER_DRIVER=software` does not replace this GL context with SDL's 2D software renderer. A GLES implementation or replacement renderer is required. [Window/context creation](https://github.com/JohnnyonFlame/gmloader-next/blob/522d964025e8ecb739c5aeb0f57afaf6f7927849/gmloader/main.cpp#L207), [GLES thunks](https://github.com/JohnnyonFlame/gmloader-next/blob/522d964025e8ecb739c5aeb0f57afaf6f7927849/thunks/khronos/gles2.cpp)

**Runner version and architecture still need matching.** GameMaker's own Android options currently include Armv7 and Arm64. This shows an ARMv7 runner is not categorically unavailable; it does not prove that any arbitrary old `libyoyo.so` supports the particular UFO 50 data format and functions. Preserve a known runner version, verify ELF architecture and dependencies, and test parsing before attempting performance work. The separate Android UFO 50 conversion project only explicitly claims versions through 1.6.2.4, so its compatibility statement must not be extended to a newer local game. [Official Android options](https://manual.gamemaker.io/lts/en/Settings/Game_Options/Android.htm), [UFO 50 Android project](https://github.com/Skyline969/UFO50AndroidUnofficial)

**Reuse the port's ideas, not its complete patch pipeline.** Current RHH scripts apply audio compression, scale/display changes and ASTC texture conversion through gmtoolkit. ASTC is not automatically suitable for a CPU sprite renderer; preserve the original textures until a specific decoder/storage strategy is selected. The display scripts also invoke texture-group loading and palette shaders, and therefore reveal functions that the alternative runtime must implement or faithfully bypass. [Patcher](https://github.com/JeodC/RHH-Ports/blob/main/ports/released/gamemakerengine/ufo50/ufo50/tools/patchscript), [display initialization](https://github.com/JeodC/RHH-Ports/blob/main/ports/released/gamemakerengine/ufo50/ufo50/tools/gml/gml_GlobalScript_scrInitDisplay.gml), [screen draw handler](https://github.com/JeodC/RHH-Ports/blob/main/ports/released/gamemakerengine/ufo50/ufo50/tools/gml/gml_Object_oScreenHandler_Draw_75.gml)

## Butterscotch: preferred first experiment

Use **`cobaltgit/Butterscotch` tag `onion-v2`, commit `92ed6b8c3766361a201a69d202bcde5873cdad7e`**. The release was published August 24, 2026. Its tree includes `src/sw/` and SDL 1.2 audio. The repository's inspected default `main` at `560aeba6cf0a1d5fd9f17fcd64927c338d219fc3` lacks `src/sw/`; cloning default main silently selects the wrong renderer variant. The earlier release explicitly reports Undertale tested on Mini v2, Mini Plus and Mini v4; that is evidence for this runtime/platform combination, not UFO 50 compatibility. [Onion v2 release](https://github.com/cobaltgit/Butterscotch/releases/tag/onion-v2), [software source](https://github.com/cobaltgit/Butterscotch/tree/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/sw), [earlier device testing](https://github.com/cobaltgit/Butterscotch/releases/tag/onion-port)

The source enables WAD/bytecode 17 as well as older versions, has lazy room/texture/audio loading, and supports per-chunk or mapped-file loading. This offers plausible control over the Mini's memory budget. Matching bytecode version alone is insufficient: the project explicitly warns that implemented functions and interpreter behavior determine compatibility. [WAD switches](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/wad_versions.h), [CLI](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/cli/main.c), [compatibility statement](https://github.com/cobaltgit/Butterscotch#game-compatibility)

Source-verified configuration, to combine with the correct platform toolchain/sysroot:

```sh
cmake -S work/upstream/Butterscotch -B work/build/butterscotch \
  -DCMAKE_BUILD_TYPE=Release -DPLATFORM=cli \
  -DBACKEND=sdl1 -DAUDIO_BACKEND=sdl1 \
  -DENABLE_LEGACY_GL=OFF -DENABLE_MODERN_GL=OFF \
  -DENABLE_SW_RENDERER=ON \
  -DENABLE_WAD14=OFF -DENABLE_WAD16=OFF -DENABLE_WAD17=ON
cmake --build work/build/butterscotch --parallel
./butterscotch gamefiles/data.win --renderer software \
  --lazy-rooms --lazy-textures --lazy-audio --load-type load-per-chunk
```

These are candidate build/run commands, not a recorded successful build. For the first compatibility audit keep VM unknown/stub logging enabled. [CMake options](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/CMakeLists.txt)

### Gaps in the unmodified Onion v2 source

- **External textures:** `data_win.c` skips TGIN parsing, records external TXTR pages with zero offset, and `DataWin_loadTxtrIfNeeded` returns immediately for zero-offset pages. No `texturegroup_*` functions are registered in `vm_builtins.c`. UFO 50's dynamic groups need mapping/loading/unloading support; treating every group as permanently loaded would defeat the memory goal. [Data reader](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/data_win.c), [builtins](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/vm_builtins.c)
- **Texture decoding peak:** the existing image decoder understands GameMaker `fioq` and bzip2 `2zoq`, but reserves up to `12 + width × height × 5` bytes for uncompressed QOI before allocating RGBA. A 2048² page therefore needs roughly 36 MiB for those two buffers alone, excluding the compressed input and renderer storage. Inspect the declared decoded length or convert on the host, and enforce an explicit resident texture budget. The current texture cache evicts on allocation failure/capacity, which is not a measured safe memory policy. [Decoder](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/image/image_decoder.c), [texture cache](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/sw/sw_texture_lru.c)
- **Shaders:** the software renderer reports unsupported shaders and its shader setters do nothing. RHH's screen draw handler checks `global.canDoShaders` and exits if false, so a game fallback may exist; inspect the actual fallback before deciding whether palette/brightness operations need CPU equivalents. Simply declaring shader support would be incorrect. [Software shader methods](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/sw/sw_renderer.c#L1161), [RHH screen handler](https://github.com/JeodC/RHH-Ports/blob/main/ports/released/gamemakerengine/ufo50/ufo50/tools/gml/gml_Object_oScreenHandler_Draw_75.gml)
- **Controls:** the release's SDL1 backend contains hardcoded Miyoo-to-Undertale keyboard mappings. Audit actual UFO 50 inputs before reusing the release executable or claiming controller support. [SDL1 backend](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/backends/sdl1.c#L365)

## Other graphics approaches

| Approach | What is supported by primary sources | Practical implication |
| --- | --- | --- |
| Miyoo SDL2 + legacy SwiftShader | Rparadise's Miyoo SDL2 tree builds `libEGL.so` and `libGLESv2.so` via `make gpu`. | A real software-GLES route exists; benchmark with an ARMv7 runner, because no UFO 50 timing or RAM result is established. |
| Current SwiftShader | Current upstream exposes Vulkan; OpenGL ES uses ANGLE over it. | Do not substitute today's upstream build recipe for the older Miyoo GLES implementation. |
| Mesa software rendering | LLVMpipe documents shader JIT, multithreading and LLVM dependencies; its documented processor coverage does not establish this Cortex-A7 configuration. | This is an exploratory compatibility/performance baseline, not a verified drop-in Miyoo dependency. |
| TinyGL | The maintained C99 project implements software OpenGL 1.1. | It does not supply gmloader-next's GLES2 programmable-shader API. A translation layer or runner renderer replacement would still be necessary. |

Sources: [Miyoo SDL2 build](https://github.com/Rparadise-Team/sdl2_miyoo_new), [current SwiftShader](https://github.com/google/swiftshader), [Mesa LLVMpipe](https://docs.mesa3d.org/drivers/llvmpipe.html), [TinyGL](https://github.com/jserv/tinygl).

## Evidence required for a feasibility verdict

First establish bounded host parsing and several executed game frames from the owned data. Record unknown functions and semantic failures, not just exit status. Then establish ARM32 build/ELF and actual Mini frontend launch. Measure peak RSS, texture/cache use and frame timing separately in the library and representative demanding games, with audio enabled. A title screen or a faster ARM64 surrogate cannot establish that all 50 games work. No physical-device result is claimed by this research note.

## Implementation reference: dynamic texture groups

For the 2024-era TGIN layout, UndertaleModTool's parser reads a chunk format version and a pointer list of groups. All pointers below are absolute file offsets. Each modern group has this header:

| Byte offset from group | Field |
| --- | --- |
| +0 | Group name string pointer |
| +4 | Directory string pointer, added 2022.9 |
| +8 | Extension string pointer, added 2022.9 |
| +12 | Signed load type: 0 in-file, 1 separate group, 2 separate textures |
| +16 | Texture-page list pointer |
| +20 | Sprite list pointer |
| +24 | Font list pointer for non-LTS 2023.1+ |
| +28 | Tileset list pointer for non-LTS 2023.1+ |

Older versions include an extra Spine-sprite-list pointer after the ordinary sprite list. The texture-page list stores a count followed by raw TXTR page IDs. Associate those pages with the group. External filenames follow `data_directory / group_directory / (group_name + "_" + TXTR.indexInGroup + group_extension)`; the index in the filename is not the absolute TXTR ID. [UTMT group serializer/parser](https://github.com/UnderminersTeam/UndertaleModTool/blob/master/UndertaleModLib/Models/UndertaleTextureGroupInfo.cs), [UTMT external texture loader](https://github.com/UnderminersTeam/UndertaleModTool/blob/master/UndertaleModLib/Models/UndertaleEmbeddedTexture.cs)

Independent read-only inspection of the owned local ZIP confirms TGIN payload offset 36,235,912, length 28,648, version 1 and 55 groups. Group 0 is an internal fallback; group 1 is the intro with external TXTR page 1; group 2 is the library with external page 2. The external group directory is `textures`, extension `.yytex`, load type 2. These are local-file observations, not claims about every UFO 50 release.

Use the official API semantics when implementing builtins: load returns 0 on success and -1 on failure. Status 0 means unloaded, 1 loading, 2 compressed data resident, 3 decompressed/fetched and ready. The optional prefetch argument defaults true. `texturegroup_set_mode(true, ...)` requests explicit loading, where unloaded textures use the fallback sprite; it does not authorize automatic loading of all groups. Unload frees a dynamic group and has no return value. [Load](https://manual.gamemaker.io/monthly/en/GameMaker_Language/GML_Reference/Drawing/Textures/texturegroup_load.htm), [status](https://manual.gamemaker.io/monthly/en/GameMaker_Language/GML_Reference/Drawing/Textures/texturegroup_get_status.htm), [mode](https://manual.gamemaker.io/monthly/en/GameMaker_Language/GML_Reference/Drawing/Textures/texturegroup_set_mode.htm), [unload](https://manual.gamemaker.io/monthly/en/GameMaker_Language/GML_Reference/Drawing/Textures/texturegroup_unload.htm)

## Follow-up: struct hashes, JSON and memory budget

Current `ButterscotchRunner/Butterscotch` commit `9e02f39e3f339a1e7d86fcd319f0e7fb582f94bb` has no registered `struct_get_from_hash`, `json_parse` or `json_stringify` implementation. Its existing JSON code handles `json_encode`/`json_decode`, with `JsonWriter` and scalar/array encoding helpers available for adaptation. The inspected open PR list also contained no proposal specifically implementing these missing builtins. This is a bounded current-source check, not a claim that no implementation exists anywhere. [Current builtins](https://github.com/ButterscotchRunner/Butterscotch/blob/9e02f39e3f339a1e7d86fcd319f0e7fb582f94bb/src/vm_builtins.c), [JSON writer](https://github.com/ButterscotchRunner/Butterscotch/blob/9e02f39e3f339a1e7d86fcd319f0e7fb582f94bb/src/json_writer.c), [open PRs](https://github.com/ButterscotchRunner/Butterscotch/pulls)

Compiled struct hashes need variable-reference handling. Underanalyzer's `VariableHashNode` emits an Int32 push with a `VariableHashPatch`; UTMT links that push to a self-scoped `UndertaleVariable`, and instruction serialization includes it in the variable reference machinery. This is not evidence for an arbitrary FNV/Murmur text hash. In the inspected Butterscotch VM, `patchReferenceOperands` replaces the low 27 operand bits with the VARI array index while preserving upper bits. Consequently the prototype can resolve a compiled hash through the masked VARI index and then use the variable's name/varID for the struct lookup. Validate the bound before access and keep runtime-created hash tokens consistent and unambiguous. [Compiler node](https://github.com/UnderminersTeam/Underanalyzer/blob/4ff50a866b4c1a7acee8cebe6a56d6a48709b453/Underanalyzer/Compiler/Nodes/VariableHashNode.cs), [bytecode emitter](https://github.com/UnderminersTeam/Underanalyzer/blob/4ff50a866b4c1a7acee8cebe6a56d6a48709b453/Underanalyzer/Compiler/Bytecode/BytecodeContext.cs), [UTMT linking](https://github.com/UnderminersTeam/UndertaleModTool/blob/f43e12c445c37d50dc6244caa12ccab232983f3f/UndertaleModLib/Compiler/CodeBuilder.cs), [instruction serialization](https://github.com/UnderminersTeam/UndertaleModTool/blob/f43e12c445c37d50dc6244caa12ccab232983f3f/UndertaleModLib/Models/UndertaleCode.cs), [Butterscotch VM](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/vm.c)

The official HTML5 runner is useful for behavior but not for reproducing native hash encoding: its `variable_get_hash` simply returns the name and hash getters forward to named lookup. The native prototype's `VM_structGetVariableByVarName` is a useful lookup helper, and returns a weak value requiring independent ownership when returned by a builtin. [HTML5 variable functions](https://github.com/YoYoGames/GameMaker-HTML5/blob/8a7ea0790cc920cb1b760ca4d474ab9e4cad0b1a/scripts/yyVariable.js#L2811), [struct getter](https://github.com/cobaltgit/Butterscotch/blob/92ed6b8c3766361a201a69d202bcde5873cdad7e/src/vm.c)

`json_stringify` must traverse structs and arrays recursively, with struct members serialized as object properties. The official HTML5 implementation converts undefined and circular back-edges to JSON null; it removes objects from the visited set after recursion, so a repeated non-cyclic reference is serialized again. It preserves NaN/infinity using special string tokens, has special int64/reference handling, supports two-space pretty printing, and applies an optional filter to every value including the root. Reusing ds_map-only `json_encode` without adding struct handling is insufficient. The native runtime can reuse its JSON writer and numeric/string escaping while adding struct traversal, cycle checks and explicit handling or reporting of unsupported options. [Official JSON semantics](https://manual.gamemaker.io/monthly/en/GameMaker_Language/GML_Reference/File_Handling/Encoding_And_Hashing/json_stringify.htm), [official HTML5 JSON implementation](https://github.com/YoYoGames/GameMaker-HTML5/blob/8a7ea0790cc920cb1b760ca4d474ab9e4cad0b1a/scripts/functions/Function_File.js#L1350)

The local [asset audit](../work/evidence/assets.json) records 985,153,536 bytes of RGBA pixels across all texture pages, 17,825,792 bytes for the selected startup groups, and 260,046,848 bytes for texturegroup07 alone. These are decoded-size calculations, not measured resident memory. A cache governed by **resident bytes**, not merely number of pages or one group at a time, is mandatory for this asset set on a 128 MB Mini. Decoding scratch buffers, room data, audio, framebuffer surfaces and the interpreter also consume memory. A single group's decoded total already exceeds physical RAM, so “load one game at a time” alone does not solve the problem.
