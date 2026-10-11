/* Game-data-free regression tests for UFO 50 compatibility code. */
#include "noop_audio_system.h"
#include "noop_file_system.h"
#include "ufo50/frame_clock.h"
#define CHECK_TEST(expr) requireMessage((expr), "Compatibility regression: " #expr)
int Ufo50_runCompatibilityTests(void) {
    Ufo50FrameClock clock = {0};
    int draws = 0;
    repeat(600, i) draws += Ufo50FrameClock_draw(&clock, 30, 60);
    CHECK_TEST(draws == 300);
    clock.credit = 0; draws = 0;
    repeat(500, i) draws += Ufo50FrameClock_draw(&clock, 30, 50);
    CHECK_TEST(draws == 300);
    CHECK_TEST(Ufo50FrameClock_draw(&clock, 30, 30));
    CHECK_TEST(Ufo50FrameClock_deadline(1000, 1120, 100) == 1100);
    CHECK_TEST(Ufo50FrameClock_deadline(1100, 1150, 100) == 1200);
    CHECK_TEST(Ufo50FrameClock_deadline(1000, 2500, 100) == 2500);
    uint32_t pixels[512];
    repeat(512, i) pixels[i] = ((i % 16) * 0x11111111u);
    SWTexture* paletted = swrCreateTexture((const uint8_t*)pixels, 32, 16);
    CHECK_TEST(paletted->indices && paletted->paletteCount == 16);
    CHECK_TEST(paletted->indexBits == 4);
    repeat(512, i) CHECK_TEST(swrTexturePixel(paletted, i) == swrConvertPixelTexture(pixels[i]));
    SWTexture* copy = swrCopyTexture(paletted);
    repeat(512, i) CHECK_TEST(copy->buffer[i] == swrTexturePixel(paletted, i));
    swrFreeTexture(copy); swrFreeTexture(paletted);
    repeat(512, i) pixels[i] = 0xff000000u | i;
    SWTexture* rgba = swrCreateTexture((const uint8_t*)pixels, 32, 16);
    CHECK_TEST(rgba->buffer && !rgba->indices);
    repeat(512, i) CHECK_TEST(swrTexturePixel(rgba, i) == swrConvertPixelTexture(pixels[i]));
    swrFreeTexture(rgba);
    SWRenderer bounds = {0};
    bounds.scaleX = bounds.scaleY = 2;
    bounds.viewX = 100; bounds.viewY = 50;
    bounds.portX = 10; bounds.portY = 20; bounds.maxX = 210; bounds.maxY = 120;
    CHECK_TEST(!swrSpriteOutsideView(&bounds, 100, 50, 8, 8));
    CHECK_TEST(swrSpriteOutsideView(&bounds, 200, 50, 8, 8));
    CHECK_TEST(!swrSpriteOutsideView(&bounds, 200, 50, -8, 8));
    CHECK_TEST(swrSpriteOutsideView(&bounds, 92, 50, 8, 8));
    CHECK_TEST(!swrSpriteOutsideView(&bounds, 92.5f, 50, 8, 8));
    CHECK_TEST(swrSpriteOutsideView(&bounds, 100, 100, 8, 8));
    uint32_t tiny[9] = {0, 0xffffffff, 0, 0xffffffff, 0, 0xffffffff, 0, 0xffffffff, 0};
    SWTexture* bits = swrCreateTexture((const uint8_t*)tiny, 9, 1);
    CHECK_TEST(bits->indexBits == 1 && swrTextureBytes(bits) == sizeof(SWTexture) + 2);
    repeat(9, i) CHECK_TEST(swrTexturePixel(bits, i) == swrConvertPixelTexture(tiny[i]));
    swrFreeTexture(bits);
    tiny[2] = tiny[6] = 0x80808080;
    bits = swrCreateTexture((const uint8_t*)tiny, 9, 1);
    CHECK_TEST(bits->indexBits == 2 && swrTextureBytes(bits) == sizeof(SWTexture) + 3);
    repeat(9, i) CHECK_TEST(swrTexturePixel(bits, i) == swrConvertPixelTexture(tiny[i]));
    swrFreeTexture(bits);
    DataWin data = {0};
    data.gen8.wadVersion = 17;
    data.gen8.defaultWindowWidth = 64;
    data.gen8.defaultWindowHeight = 64;
    VMContext* ctx = VM_create(&data);
    CHECK_TEST(VM_runIntegerTests(ctx) == 0);
    Renderer* renderer = SWRenderer_create();
    FileSystem* fs = NoopFileSystem_create();
    AudioSystem* audio = (AudioSystem*) NoopAudioSystem_create();
    Runner* runner = Runner_create(&data, ctx, renderer, fs, audio, 1234);

    Font fonts[2] = {{0}, {0}};
    fonts[0].present = true;
    data.font.fonts = fonts; data.font.count = 2;
    RValue fontArg = RValue_makeReal(0);
    CHECK_TEST(RValue_toBool(builtin_ufo_font_exists(ctx, &fontArg, 1)));
    fontArg = RValue_makeReal(1);
    CHECK_TEST(!RValue_toBool(builtin_ufo_font_exists(ctx, &fontArg, 1)));
    fontArg = RValue_makeReal(-1);
    CHECK_TEST(!RValue_toBool(builtin_ufo_font_exists(ctx, &fontArg, 1)));
    data.font.fonts = nullptr; data.font.count = 0;

    RValue jsonArgs[] = {RValue_makeString("{\"items\":[\"one\",{\"value\":42,},],\"flag\":true,}")};
    RValue parsed = builtin_json_parse(ctx, jsonArgs, 1);
    CHECK_TEST(parsed.type == RVALUE_STRUCT);
    RValue items = VM_structGetVariableByVarName(ctx, parsed.structInst, "items", -1);
    CHECK_TEST(items.type == RVALUE_ARRAY && GMLArray_length1D(items.array) == 2);
    RValue nested = GMLArray_get(items.array, 1);
    CHECK_TEST(nested.type == RVALUE_STRUCT);
    CHECK_TEST(RValue_toInt32(VM_structGetVariableByVarName(ctx, nested.structInst, "value", -1)) == 42);
    RValue stringifyArgs[] = {parsed, RValue_makeBool(true)};
    RValue encoded = builtin_json_stringify(ctx, stringifyArgs, 2);
    CHECK_TEST(encoded.type == RVALUE_STRING && strchr(encoded.string, '\n'));
    RValue roundTrip = builtin_json_parse(ctx, &encoded, 1);
    CHECK_TEST(roundTrip.type == RVALUE_STRUCT);
    CHECK_TEST(RValue_toBool(VM_structGetVariableByVarName(ctx, roundTrip.structInst, "flag", -1)));
    RValue_free(&roundTrip); RValue_free(&encoded); RValue_free(&parsed);

    GMLArray* array = GMLArray_create(17, 3);
    *GMLArray_slot(array, 0) = RValue_makeOwnedString(safeStrdup("a"));
    *GMLArray_slot(array, 1) = RValue_makeOwnedString(safeStrdup("b"));
    *GMLArray_slot(array, 2) = RValue_makeOwnedString(safeStrdup("c"));
    RValue arrayValue = RValue_makeArray(array);
    RValue copyArgs[] = {arrayValue, RValue_makeReal(1), arrayValue, RValue_makeReal(0), RValue_makeReal(2)};
    builtin_array_copy(ctx, copyArgs, 5);
    CHECK_TEST(strcmp(GMLArray_get(array, 2).string, "b") == 0);
    RValue shifted = builtin_ufo_array_shift(ctx, &arrayValue, 1);
    CHECK_TEST(strcmp(shifted.string, "a") == 0 && GMLArray_length1D(array) == 2);
    RValue_free(&shifted); RValue_free(&arrayValue);

    RValue gridArgs[] = {RValue_makeReal(2), RValue_makeReal(2)};
    RValue grid = builtin_ds_grid_create(ctx, gridArgs, 2);
    RValue getCell[] = {grid, RValue_makeReal(1), RValue_makeReal(1)};
    RValue initialCell = builtin_ds_grid_get(ctx, getCell, 3);
    CHECK_TEST(initialCell.type == RVALUE_REAL && initialCell.real == 0);
    RValue setCell[] = {grid, RValue_makeReal(1), RValue_makeReal(1), RValue_makeString("written")};
    builtin_ds_grid_set(ctx, setCell, 4);
    RValue written = builtin_ds_grid_get(ctx, getCell, 3);
    CHECK_TEST(written.type == RVALUE_STRING && strcmp(written.string, "written") == 0);
    RValue_free(&written);
    RValue resize[] = {grid, RValue_makeReal(3), RValue_makeReal(3)};
    builtin_ds_grid_resize(ctx, resize, 3);
    written = builtin_ds_grid_get(ctx, getCell, 3);
    CHECK_TEST(written.type == RVALUE_STRING && strcmp(written.string, "written") == 0);
    RValue_free(&written);
    getCell[1] = getCell[2] = RValue_makeReal(2);
    CHECK_TEST(RValue_toReal(builtin_ds_grid_get(ctx, getCell, 3)) == 0);
    builtin_ds_grid_resize(ctx, (RValue[]){grid, gridArgs[0], gridArgs[1]}, 3);
    RValue clearArgs[] = {grid, RValue_makeOwnedString(safeStrdup("cell"))};
    builtin_ufo_ds_grid_clear(ctx, clearArgs, 2);
    RValue selfCopy[] = {grid, grid}; builtin_ds_grid_copy(ctx, selfCopy, 2);
    CHECK_TEST(strcmp(dsGridGet(runner, RValue_toInt32(grid))->items[3].string, "cell") == 0);
    RValue other = builtin_ds_grid_create(ctx, gridArgs, 2);
    RValue gridCopy[] = {other, grid}; builtin_ds_grid_copy(ctx, gridCopy, 2);
    builtin_ds_grid_destroy(ctx, &grid, 1);
    CHECK_TEST(strcmp(dsGridGet(runner, RValue_toInt32(other))->items[3].string, "cell") == 0);
    RValue search[] = {other, RValue_makeReal(1), RValue_makeReal(1),
                       RValue_makeReal(-10), RValue_makeReal(-10), RValue_makeString("cell")};
    CHECK_TEST(RValue_toInt32(builtin_ufo_ds_grid_value_x(ctx, search, 6)) == 0);
    CHECK_TEST(RValue_toInt32(builtin_ufo_ds_grid_value_y(ctx, search, 6)) == 0);
    CHECK_TEST(RValue_toBool(builtin_ufo_ds_grid_value_exists(ctx, search, 6)));
    search[5] = RValue_makeString("missing");
    CHECK_TEST(!RValue_toBool(builtin_ufo_ds_grid_value_exists(ctx, search, 6)));
    CHECK_TEST(RValue_toInt32(builtin_ufo_ds_grid_value_x(ctx, search, 6)) == -1);
    DsGrid* searched = dsGridGet(runner, RValue_toInt32(other));
    RValue_free(&searched->items[1]); searched->items[1] = RValue_makeInt32(42);
    RValue_free(&searched->items[2]); searched->items[2] = RValue_makeReal(42);
    search[5] = RValue_makeReal(42);
    CHECK_TEST(RValue_toInt32(builtin_ufo_ds_grid_value_x(ctx, search, 6)) == 1);
    CHECK_TEST(RValue_toInt32(builtin_ufo_ds_grid_value_y(ctx, search, 6)) == 0);
    search[1] = search[3] = RValue_makeReal(0);
    CHECK_TEST(RValue_toInt32(builtin_ufo_ds_grid_value_y(ctx, search, 6)) == 1);
    CHECK_TEST(RValue_toInt32(builtin_ufo_ds_grid_value_y(ctx, search, 5)) == -1);
    builtin_ds_grid_destroy(ctx, &other, 1); RValue_free(&clearArgs[1]);

    CHECK_TEST(fs->vtable->writeFileText(fs, "input.txt", "owned-file"));
    RValue fileArgs[] = {RValue_makeString("input.txt"), RValue_makeString("output.txt")};
    CHECK_TEST(RValue_toBool(builtin_file_copy(ctx, fileArgs, 2)));
    char* copied = fs->vtable->readFileText(fs, "output.txt");
    CHECK_TEST(copied && strcmp(copied, "owned-file") == 0); free(copied);

    RValue speedArgs[] = {RValue_makeReal(60), RValue_makeReal(0)};
    builtin_ufo_game_set_speed(ctx, speedArgs, 2);
    CHECK_TEST(runner->gameSpeedOverride == 60);
    speedArgs[0] = RValue_makeReal(20000); speedArgs[1] = RValue_makeReal(1);
    builtin_ufo_game_set_speed(ctx, speedArgs, 2);
    CHECK_TEST(runner->gameSpeedOverride == 50);

    RValue depth = RValue_makeReal(-10);
    RValue layer = builtin_layer_create(ctx, &depth, 1);
    RValue tileArgs[] = {layer, RValue_makeReal(12), RValue_makeReal(34), RValue_makeReal(0),
                        RValue_makeReal(4), RValue_makeReal(8), RValue_makeReal(16), RValue_makeReal(24)};
    RValue tileId = builtin_layer_tile_create(ctx, tileArgs, 8);
    RuntimeLayerElement* tile = Runner_findLayerElementById(runner, RValue_toInt32(tileId), nullptr);
    CHECK_TEST(tile && tile->tileElementOwned && tile->tileElement->x == 12 && tile->tileElement->height == 24);
    builtin_layer_tile_destroy(ctx, &tileId, 1);
    CHECK_TEST(!Runner_findLayerElementById(runner, RValue_toInt32(tileId), nullptr));
    builtin_layer_tile_destroy(ctx, &tileId, 1); // deleting a missing tile is harmless
    builtin_layer_tile_create(ctx, tileArgs, 8); // runner teardown owns this tile
    SWRenderer* swr = (SWRenderer*)renderer;
    swr->textures[swr->textureCount] = swrCreateTexture(nullptr, 8, 8);
    CHECK_TEST(swrEnsureTextureIsLoaded(swr, swr->textureCount));
    renderer->vtable->beginFrame(renderer, 64, 64, 64, 64);
    int surface = renderer->vtable->createSurface(renderer, 8, 8);
    CHECK_TEST(surface >= 0 && renderer->vtable->setRenderTarget(renderer, surface, false));
    Runner_free(runner); VM_free(ctx);
    audio->vtable->destroy(audio); renderer->vtable->destroy(renderer); NoopFileSystem_destroy(fs);
    free(data.tpag.items);
    logInfo("Compatibility selftests passed: nested JSON, formatting, overlapping arrays, grid ownership, file copy, timing\n");
    return 0;
}
#undef CHECK_TEST
