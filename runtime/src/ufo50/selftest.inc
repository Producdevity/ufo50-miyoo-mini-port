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
    DataWin data = {0};
    data.gen8.wadVersion = 17;
    data.gen8.defaultWindowWidth = 64;
    data.gen8.defaultWindowHeight = 64;
    VMContext* ctx = VM_create(&data);
    Renderer* renderer = SWRenderer_create();
    FileSystem* fs = NoopFileSystem_create();
    AudioSystem* audio = (AudioSystem*) NoopAudioSystem_create();
    Runner* runner = Runner_create(&data, ctx, renderer, fs, audio, 1234);

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
    RValue clearArgs[] = {grid, RValue_makeOwnedString(safeStrdup("cell"))};
    builtin_ufo_ds_grid_clear(ctx, clearArgs, 2);
    RValue selfCopy[] = {grid, grid}; builtin_ds_grid_copy(ctx, selfCopy, 2);
    CHECK_TEST(strcmp(dsGridGet(runner, RValue_toInt32(grid))->items[3].string, "cell") == 0);
    RValue other = builtin_ds_grid_create(ctx, gridArgs, 2);
    RValue gridCopy[] = {other, grid}; builtin_ds_grid_copy(ctx, gridCopy, 2);
    builtin_ds_grid_destroy(ctx, &grid, 1);
    CHECK_TEST(strcmp(dsGridGet(runner, RValue_toInt32(other))->items[3].string, "cell") == 0);
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

    Runner_free(runner); VM_free(ctx);
    audio->vtable->destroy(audio); renderer->vtable->destroy(renderer); NoopFileSystem_destroy(fs);
    logInfo("Compatibility selftests passed: nested JSON, formatting, overlapping arrays, grid ownership, file copy, timing\n");
    return 0;
}
#undef CHECK_TEST
