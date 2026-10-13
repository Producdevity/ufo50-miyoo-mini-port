/* Game-data-free VM dispatch and call-storage regressions. */
// Exercise actual PUSHGLB dispatch, including values that must use the fallback.
int VM_runGlobalReadTests(void) {
    Variable variables[] = {
        {.name = "value", .varID = 901},
        {.name = "missing", .varID = 902},
        {.name = "pi", .varID = VARIABLE_BUILTIN, .builtinVarId = BUILTIN_VAR_PI}
    };
    DataWin data = {.gen8 = {.wadVersion = 17},
        .vari = {.variables = variables, .variableCount = 3}};
    uint32_t code[] = {(uint32_t)OP_PUSHGLB << 24 | GML_TYPE_VARIABLE << 16,
        (uint32_t)VARTYPE_NORMAL << 24, (uint32_t)OP_RET << 24 | GML_TYPE_VARIABLE << 16};
    Runner runner = {.dataWin = &data};
    VMContext test = {.dataWin = &data, .runner = &runner, .bytecodeBase = (uint8_t*)code,
        .codeEnd = sizeof(code), .currentCodeName = "synthetic-global-read",
        .globalScopeInstance = Instance_create(0, STRUCT_OBJECT_INDEX, 0, 0)};
    Instance_setSelfVar(test.globalScopeInstance, 901, RValue_makeReal(42));
    RValue value = executeLoop(&test);
    require(value.type == RVALUE_REAL && value.real == 42 && test.stack.top == 0);

    test.ip = 0; code[1] = (uint32_t)VARTYPE_NORMAL << 24 | 1;
    value = executeLoop(&test);
    require(value.type == RVALUE_UNDEFINED && test.stack.top == 0);
    test.ip = 0; code[1] = (uint32_t)VARTYPE_NORMAL << 24 | 2;
    value = executeLoop(&test);
    require(fabs(RValue_toReal(value) - 3.141592653589793) < 0.0000001);

    Instance_setSelfVar(test.globalScopeInstance, 901, RValue_makeString("owned by slot"));
    test.ip = 0; code[1] = (uint32_t)VARTYPE_NORMAL << 24;
    value = executeLoop(&test);
    require(value.type == RVALUE_STRING && !value.ownsReference && strcmp(value.string, "owned by slot") == 0);
    RValue_free(&value); // A weak result must not release the slot's string.

    GMLArray* array = GMLArray_create(17, 2);
    *GMLArray_slot(array, 1) = RValue_makeReal(123);
    RValue owned = RValue_makeArray(array);
    Instance_setSelfVar(test.globalScopeInstance, 901, owned);
    RValue_free(&owned);
    test.ip = 0;
    value = executeLoop(&test);
    require(value.type == RVALUE_ARRAY && value.array == array && !value.ownsReference && array->refCount == 1);
    RValue_free(&value);

    test.ip = 0; code[1] = (uint32_t)VARTYPE_ARRAY << 24;
    stackPush(&test, RValue_makeInt32(INSTANCE_GLOBAL));
    stackPush(&test, RValue_makeInt32(1));
    value = executeLoop(&test);
    require(RValue_toReal(value) == 123 && test.stack.top == 0 && array->refCount == 1);
    Instance_free(test.globalScopeInstance);
    return 0;
}

static RValue localStorageTestValue(bool array, const char* text) {
    if (!array) return RValue_makeOwnedString(safeStrdup(text));
    GMLArray* result = GMLArray_create(17, 1);
    *GMLArray_slot(result, 0) = RValue_makeOwnedString(safeStrdup(text));
    return RValue_makeArray(result);
}

static const char* localStorageTestText(RValue value) {
    return value.type == RVALUE_ARRAY ? GMLArray_get(value.array, 0).string : value.string;
}

static RValue localStorageTestCallback(VMContext* ctx, RValue* args, int32_t argCount) {
    (void)args; (void)argCount;
    uint32_t slot = resolveLocalSlot(ctx, 700);
    if (ctx->currentCodeIndex == 1) {
        if (ctx->localVarCount > VM_MAX_STACK_LOCALS) require(!ctx->localVarsOnStack);
        ctx->localVars[slot] = RValue_makeOwnedString(safeStrdup("nested event"));
        return RValue_makeUndefined();
    }
    bool array = RValue_toBool(ctx->scriptArgs[0]);
    require(ctx->scriptArgsOnStack && ctx->scriptArgCount == 1);
    bool parent = ctx->callDepth == 1;
    ctx->localVars[slot] = localStorageTestValue(array, parent ? "parent" : "child");
    if (parent) {
        RValue* original = ctx->localVars;
        require(ctx->localVarsOnStack && ctx->localVarCount == 1);
        RValue mode = RValue_makeBool(array);
        RValue child = VM_callCodeIndex(ctx, 0, &mode, 1);
        require(strcmp(localStorageTestText(child), "child") == 0 && child.ownsReference);
        RValue_free(&child);
        require(ctx->scriptArgsOnStack && ctx->scriptArgCount == 1);
        require(ctx->localVars == original && ctx->localVarsOnStack && ctx->localVarCount == 1);
        Instance* eventInstance = Instance_create(123, 0, 0, 0);
        Runner_executeEvent(ctx->runner, eventInstance, EVENT_CREATE, 0);
        Instance_free(eventInstance);
        require(ctx->localVars == original && ctx->localVarsOnStack && ctx->localVarCount == 1);
        // The recursive call extended this code's shared map while we were suspended.
        resolveLocalSlot(ctx, 717);
    } else {
        for (int id = 701; id <= 717; id++) resolveLocalSlot(ctx, id);
    }
    VM_writeToScriptArgs(ctx, 3, RValue_makeString("grown argument"));
    require(ctx->scriptArgsOnStack && ctx->scriptArgCount == 4);
    RValue argument = localStorageTestValue(array, "escaped argument");
    VM_writeToScriptArgs(ctx, 20, argument);
    RValue_free(&argument);
    require(!ctx->scriptArgsOnStack && ctx->scriptArgCount == 21);
    require(strcmp(ctx->scriptArgs[3].string, "grown argument") == 0);
    require(strcmp(localStorageTestText(ctx->scriptArgs[20]), "escaped argument") == 0);
    require(!ctx->localVarsOnStack && ctx->localVarCount == 18);
    require(strcmp(localStorageTestText(ctx->localVars[slot]), parent ? "parent" : "child") == 0);
    RValue result = ctx->localVars[slot];
    result.ownsReference = false;
    return result;
}

int VM_runLocalStorageTests(void) {
    uint32_t bytecode[] = {(uint32_t)OP_CALL << 24 | GML_TYPE_VARIABLE << 16,
        0, (uint32_t)OP_RET << 24 | GML_TYPE_VARIABLE << 16};
    CodeEntry entries[] = {
        {.name = "synthetic-recursive-locals", .length = sizeof(bytecode)},
        {.name = "synthetic-nested-event", .length = sizeof(bytecode)}
    };
    Function function = {.name = "growLocals"};
    EventAction action = {.codeId = 1};
    ObjectEvent event = {.actionCount = 1, .actions = &action};
    GameObject object = {.present = true, .name = "synthetic", .parentId = -1};
    object.eventLists[EVENT_CREATE] = (ObjectEventList){.eventCount = 1, .events = &event};
    DataWin data = {.gen8 = {.wadVersion = 17}, .bytecodeBuffer = (uint8_t*)bytecode,
        .code = {.count = 2, .entries = entries}, .objt = {.count = 1, .objects = &object},
        .func = {.functionCount = 1, .functions = &function}};
    for (int array = 0; array <= 1; array++) {
        IntIntHashMap maps[2] = {0};
        FuncCallCache cache = {.builtin = (void*)localStorageTestCallback, .scriptCodeIndex = -1};
        VMContext ctx = {.dataWin = &data, .codeLocalsSlotMaps = maps, .funcCallCache = &cache,
            .funcCallCacheCount = 1, .currentCodeIndex = -1};
        Runner runner = {.dataWin = &data, .vmContext = &ctx, .pendingRoom = -1};
        ctx.runner = &runner;
        EventSlotMap_build(&runner.eventSlotMap, &data);
        ResolvedEventTable_build(&runner.eventTable, &data, &runner.eventSlotMap);
        RValue mode = RValue_makeBool(array);
        RValue result = VM_callCodeIndex(&ctx, 0, &mode, 1);
        require(result.ownsReference && strcmp(localStorageTestText(result), "parent") == 0);
        require(ctx.localVars == nullptr && !ctx.localVarsOnStack && ctx.callDepth == 0 && ctx.stack.top == 0);
        require(ctx.scriptArgs == nullptr && !ctx.scriptArgsOnStack && ctx.scriptArgCount == 0);
        RValue_free(&result);
        for (int id = 701; id <= 717; id++) IntIntHashMap_getOrInsertSequential(&maps[1], id);
        RValue largeArgs[21];
        repeat(21, i) largeArgs[i] = localStorageTestValue(i % 2, "caller argument");
        result = VM_callCodeIndex(&ctx, 1, largeArgs, 21);
        require(result.type == RVALUE_UNDEFINED && ctx.scriptArgs == nullptr);
        repeat(21, i) {
            require(strcmp(localStorageTestText(largeArgs[i]), "caller argument") == 0);
            if (largeArgs[i].type == RVALUE_ARRAY) require(largeArgs[i].array->refCount == 1);
            RValue_free(&largeArgs[i]);
        }
        IntIntHashMap_free(&maps[0]); IntIntHashMap_free(&maps[1]);
        EventSlotMap_destroy(&runner.eventSlotMap);
        ResolvedEventTable_free(&runner.eventTable);
    }
    return 0;
}

