/* Compare the broad phase with the unchanged full candidate traversal. */
static void Ufo50_checkRectangleQuery(VMContext* ctx, RValue* args) {
    Runner* runner = ctx->runner;
    SpatialGrid* grid = runner->spatialGrid;
    RValue filtered = builtin_collision_rectangle(ctx, args, 7);
    runner->spatialGrid = nullptr;
    RValue reference = builtin_collision_rectangle(ctx, args, 7);
    runner->spatialGrid = grid;
    CHECK_TEST(RValue_toInt32(filtered) == RValue_toInt32(reference));
}

static int Ufo50_runRectangleQueryTests(VMContext* ctx) {
    Runner* runner = ctx->runner;
    DataWin* data = ctx->dataWin;
    CHECK_TEST(!runner->spatialGrid && !arrlen(runner->instances));
    uint8_t mask[8] = {0x81, 0x42, 0x24, 0x18, 0x18, 0x24, 0x42, 0x81};
    uint8_t* masks[] = {mask};
    Sprite sprites[2] = {
        {.width = 8, .height = 8, .marginRight = 7, .marginBottom = 7,
         .sepMasks = 1, .maskCount = 1, .masks = masks, .maskWidth = 8, .maskHeight = 8},
        {.width = 16, .height = 12, .marginRight = 15, .marginBottom = 11, .sepMasks = 2}
    };
    data->sprt.count = 2; data->sprt.sprites = sprites;
    runner->spatialGrid = SpatialGrid_create(512, 512);
    GMLReal positions[] = {-128.5, -64, -0.5, 0, 63.5, 64, 128, 511.5, 640};
    repeat(9, i) {
        Instance* inst = Instance_create(900100 + (8 - i), 0, positions[i], positions[8 - i]);
        inst->spriteIndex = i % 2;
        inst->imageAngle = (i % 3) * 37;
        inst->imageXscale = i % 2 ? -1.5 : 1;
        inst->imageYscale = i % 4 ? 0.75 : 0;
        arrput(runner->instances, inst);
        hmput(runner->instancesById, inst->instanceId, inst);
        SpatialGrid_markInstanceAsDirty(runner->spatialGrid, inst);
    }
    Instance* previousSelf = ctx->currentInstance;
    ctx->currentInstance = runner->instances[4];
    bool previousMode = runner->collisionCompatibilityMode;
    unsigned comparisons = 0;
    repeat(2, compatibility) repeat(3, phase) {
        runner->collisionCompatibilityMode = compatibility;
        repeat(9, i) SpatialGrid_markInstanceAsDirty(runner->spatialGrid, runner->instances[i]);
        if (phase == 1) {
            RValue offset[] = {RValue_makeReal(0), RValue_makeReal(65), RValue_makeReal(-32)};
            builtin_sprite_set_offset(ctx, offset, 3);
            VMBuiltins_setVariable(ctx, runner->instances[1], BUILTIN_VAR_X, "x", RValue_makeReal(64), 0);
            VMBuiltins_setVariable(ctx, runner->instances[1], BUILTIN_VAR_Y, "y", RValue_makeReal(128), 0);
            VMBuiltins_setVariable(ctx, runner->instances[2], BUILTIN_VAR_IMAGE_XSCALE, "image_xscale", RValue_makeReal(-3), 0);
            VMBuiltins_setVariable(ctx, runner->instances[3], BUILTIN_VAR_IMAGE_ANGLE, "image_angle", RValue_makeReal(90), 0);
        } else if (phase == 2) {
            RValue mode[] = {RValue_makeReal(1), RValue_makeReal(1)};
            builtin_sprite_set_bbox_mode(ctx, mode, 2);
            VMBuiltins_setVariable(ctx, runner->instances[5], BUILTIN_VAR_MASK_INDEX, "mask_index", RValue_makeReal(0), 0);
        }
        repeat(9, x) repeat(9, y) repeat(3, shape) repeat(2, precise) repeat(2, notme) {
            GMLReal span = shape == 0 ? 0 : shape == 1 ? 8 : 129.25;
            RValue args[] = {RValue_makeReal(positions[x] + span), RValue_makeReal(positions[y]),
                RValue_makeReal(positions[x]), RValue_makeReal(positions[y] + span),
                RValue_makeReal(INSTANCE_ALL), RValue_makeReal(precise), RValue_makeReal(notme)};
            Ufo50_checkRectangleQuery(ctx, args); comparisons++;
            args[4] = RValue_makeReal(runner->instances[(x + y) % 9]->instanceId);
            Ufo50_checkRectangleQuery(ctx, args); comparisons++;
        }
    }
    // Coordinates outside the grid's representable range retain the full traversal.
    RValue huge[] = {RValue_makeReal(-4194304), RValue_makeReal(-4194304),
        RValue_makeReal(4194304), RValue_makeReal(4194304), RValue_makeReal(INSTANCE_ALL),
        RValue_makeReal(0), RValue_makeReal(0)};
    Ufo50_checkRectangleQuery(ctx, huge); comparisons++;
    // Unindexed candidates must still reach the narrow phase.
    arrsetlen(runner->instances[0]->collisionCells, 0);
    RValue missing[] = {RValue_makeReal(-200), RValue_makeReal(600), RValue_makeReal(0),
        RValue_makeReal(700), RValue_makeReal(INSTANCE_ALL), RValue_makeReal(0), RValue_makeReal(0)};
    Ufo50_checkRectangleQuery(ctx, missing); comparisons++;
    SpatialGrid_free(runner->spatialGrid); runner->spatialGrid = nullptr;
    repeat(9, i) { Instance* inst = runner->instances[i]; hmdel(runner->instancesById, inst->instanceId); Instance_free(inst); }
    arrsetlen(runner->instances, 0); ctx->currentInstance = previousSelf;
    runner->collisionCompatibilityMode = previousMode;
    data->sprt.count = 0; data->sprt.sprites = nullptr;
    logInfo("Rectangle query selftests passed: %u full-traversal comparisons, order, masks, rotation, geometry changes and off-room coordinates\n", comparisons);
    return 0;
}
