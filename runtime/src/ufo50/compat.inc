/* UFO 50 compatibility extensions. Upstream-derived functions are from
 * ButterscotchRunner/Butterscotch 342371d447467cfa643b8987b57977bce8e8075c9.
 * Included here to reuse the VM's private DS pool helpers. AGPL-3.0. */
#define REQUIRE_ARGC_AT_LEAST(name, n, fallback) do { if (argCount < (n)) return (fallback); } while (0)

static int arraySortCompareAsc(const void* a, const void* b) {
    const RValue* ra = (const RValue*) a;
    const RValue* rb = (const RValue*) b;
    if (ra->type == RVALUE_STRING && rb->type == RVALUE_STRING) {
        return strcmp(ra->string != nullptr ? ra->string : "", rb->string != nullptr ? rb->string : "");
    }
    GMLReal da = RValue_toReal(*ra);
    GMLReal db = RValue_toReal(*rb);
    if (da < db) return -1;
    if (da > db) return 1;
    return 0;
}

static int arraySortCompareDesc(const void* a, const void* b) {
    return arraySortCompareAsc(b, a);
}

static RValue builtin_ds_list_sort(VMContext* ctx, RValue* args, MAYBE_UNUSED int32_t argCount) {
    Runner* runner = (Runner*) ctx->runner;
    int32_t id = RValue_toInt32(args[0]);
    bool ascending = RValue_toBool(args[1]);
    DsList* list = dsListGet(runner, id);
    if (list == nullptr) return RValue_makeUndefined();
    int len = arrlen(list->items);
    if (len < 2) return RValue_makeUndefined();
    qsort(list->items, len, sizeof(RValue), ascending ? arraySortCompareAsc : arraySortCompareDesc);
    return RValue_makeUndefined();
}

static RValue builtin_array_concat(MAYBE_UNUSED VMContext* ctx, RValue* args, int32_t argCount) {
    REQUIRE_ARGC_AT_LEAST("array_concat", 1, RValue_makeArray(GMLArray_create(ctx->dataWin->gen8.wadVersion, 0)));
    if (args[0].type != RVALUE_ARRAY || args[0].array == nullptr) return RValue_makeUndefined();

    GMLArray* out = GMLArray_clone(args[0].array, IS_WAD17_OR_HIGHER(ctx) ? ctx->currentArrayOwner : nullptr);
    int32_t outLen = GMLArray_length1D(out);

    for (int32_t i = 1; i < argCount; i++) {
        if (args[i].type != RVALUE_ARRAY || args[i].array == nullptr) {
            GMLArray_decRef(out);
            return RValue_makeUndefined();
        }

        GMLArray* src = args[i].array;
        int32_t addLen = GMLArray_length1D(src);
        if (addLen > 0) {
            GMLArray_growTo(out, outLen + addLen);
            repeat(addLen, j) {
                RValue* slot = GMLArray_slot(out, outLen + j);
                *slot = RValue_makeIndependent(GMLArray_get(src, j));
            }
        }
        outLen += addLen;
    }

    if (IS_WAD17_OR_HIGHER(ctx)) out->owner = ctx->currentArrayOwner;
    return RValue_makeArray(out);
}

static RValue builtin_array_copy(MAYBE_UNUSED VMContext* ctx, RValue* args, int32_t argCount) {
    REQUIRE_ARGC_AT_LEAST("array_copy", 5, RValue_makeUndefined());
    if (args[0].type != RVALUE_ARRAY || args[0].array == nullptr)
        return RValue_makeUndefined();
    if (args[2].type != RVALUE_ARRAY || args[2].array == nullptr)
        return RValue_makeUndefined();
    GMLArray* dst = args[0].array;
    GMLArray* src = args[2].array;
    require(dst->type == src->type); // don't allow legacy<->modern copies
    int32_t dstIndex = (int32_t)RValue_toReal(args[1]);
    int32_t srcIndex = (int32_t)RValue_toReal(args[3]);
    int32_t length = (int32_t)RValue_toReal(args[4]);
    if (dstIndex < 0) dstIndex = 0;
    if (srcIndex < 0) srcIndex = 0;
    if (length <= 0) return RValue_makeUndefined();
    int32_t srcLen = GMLArray_length1D(src);
    // clamp source range
    if (srcIndex >= srcLen)
        return RValue_makeUndefined();
    if (length > srcLen - srcIndex)
        length = srcLen - srcIndex;
    GMLArray_growTo(dst, dstIndex + length);
     // temp buffer handles array_copy when the source and destination overlap
    RValue* temp = (RValue*)safeCalloc(length, sizeof(RValue));
    repeat(length, i) {
        temp[i] = RValue_makeIndependent(GMLArray_get(src, srcIndex + i));
    }
    {
    repeat(length, i) {
        RValue* slot = GMLArray_slot(dst, dstIndex + i);
        if (slot != nullptr) {
            RValue_free(slot);
            *slot = temp[i];
        } else {
            RValue_free(&temp[i]);
        }
    }
    }
    free(temp);
    return RValue_makeUndefined();
}

static RValue builtin_internal_array_get(VMContext* ctx, RValue* args, int32_t argCount) {
    REQUIRE_ARGC_AT_LEAST("@@array_get@@", 2, RValue_makeUndefined());
    if (args[0].type != RVALUE_ARRAY) return RValue_makeUndefined();
    return RValue_makeIndependent(GMLArray_get(args[0].array, RValue_toInt32(args[1])));
}

static RValue builtin_file_copy(VMContext* ctx, RValue* args, int32_t argCount) {
    REQUIRE_ARGC_AT_LEAST("file_copy", 2, RValue_makeBool(false));
    const char* source = (args[0].type == RVALUE_STRING ? args[0].string : "");
    const char* destination = (args[1].type == RVALUE_STRING ? args[1].string : "");
    if (!*source || !*destination) return RValue_makeBool(false);

    FileSystem* fs = ctx->runner->fileSystem;
    uint8_t* data = nullptr;
    int32_t size = 0;
    if (fs->vtable->readFileBinary(fs, source, &data, &size)) {
        bool copied = fs->vtable->writeFileBinary(fs, destination, data, size);
        free(data);
        return RValue_makeBool(copied);
    }

    // In-memory file systems may store text files separately from binary files.
    char* text = fs->vtable->readFileText(fs, source);
    if (text == nullptr) return RValue_makeBool(false);
    bool copied = fs->vtable->writeFileText(fs, destination, text);
    free(text);
    return RValue_makeBool(copied);
}

static RValue builtin_ds_grid_copy(VMContext* ctx, RValue* args, MAYBE_UNUSED int32_t argCount) {
    REQUIRE_ARGC_AT_LEAST("ds_grid_copy", 2, RValue_makeUndefined());
    DsGrid* dst = dsGridGet(ctx->runner, RValue_toInt32(args[0]));
    DsGrid* src = dsGridGet(ctx->runner, RValue_toInt32(args[1]));
    if (dst == nullptr || src == nullptr || dst == src) return RValue_makeUndefined();
    for (int32_t i = 0; i < dst->width * dst->height; i++) {
        RValue_free(&dst->items[i]);
    }
    free(dst->items);
    size_t count = (size_t)src->width * (size_t)src->height;
    dst->width = src->width;
    dst->height = src->height;
    dst->items = count > 0 ? (RValue*)safeCalloc(count, sizeof(RValue)) : nullptr;
    if (dst->items != nullptr) {
        {
        for (size_t i = 0; i < count; i++) {
            dst->items[i] = RValue_makeIndependent(src->items[i]);
        }
        }
    }
    return RValue_makeUndefined();
}


static RValue builtin_ufo_game_set_speed(VMContext* ctx, RValue* args, int32_t count) {
    if (count < 2) return RValue_makeUndefined();
    GMLReal speed = RValue_toReal(args[0]);
    int type = RValue_toInt32(args[1]);
    GMLReal fps = type == 0 ? speed : (speed > 0 ? 1000000.0 / speed : 0);
    if (!isfinite(fps) || fps <= 0 || fps > 1000) return RValue_makeUndefined();
    ctx->runner->gameSpeedOverride = fps;
    if (ctx->runner->currentRoom) ctx->runner->currentRoom->speed = (uint32_t)fps;
    return RValue_makeUndefined();
}

static RValue builtin_ufo_struct_get(VMContext* ctx, RValue* args, int32_t count) {
    if (count < 2 || args[0].type != RVALUE_STRUCT || !args[0].structInst) return RValue_makeUndefined();
    char* name = RValue_toString(args[1]);
    RValue out = RValue_makeIndependent(VM_structGetVariableByVarName(ctx,args[0].structInst,name,-1));
    free(name); return out;
}

static RValue builtin_ufo_array_last(VMContext* ctx, RValue* args, int32_t count) {
    (void)ctx;
    if (count < 1 || args[0].type != RVALUE_ARRAY || !args[0].array) return RValue_makeUndefined();
    int32_t length=GMLArray_length1D(args[0].array);
    return length ? RValue_makeIndependent(GMLArray_get(args[0].array,length-1)) : RValue_makeUndefined();
}

static RValue builtin_ufo_array_shift(VMContext* ctx, RValue* args, int32_t count) {
    (void)ctx;
    if (count < 1 || args[0].type != RVALUE_ARRAY || !args[0].array || args[0].array->type != GML_MODERN_ARRAY) return RValue_makeUndefined();
    GMLArray* a=args[0].array; int32_t length=a->modern.length;
    if (!length) return RValue_makeUndefined();
    RValue out=a->modern.data[0];
    memmove(a->modern.data,a->modern.data+1,(length-1)*sizeof(RValue));
    a->modern.data[--a->modern.length]=RValue_makeUndefined();
    return out;
}

static RValue builtin_ufo_array_shuffle(VMContext* ctx, RValue* args, int32_t count) {
    if (count < 1 || args[0].type != RVALUE_ARRAY || !args[0].array) return RValue_makeUndefined();
    GMLArray* a=GMLArray_clone(args[0].array,nullptr);
    for (int32_t i=GMLArray_length1D(a)-1;i>0;--i) {
        int32_t j=Random_nextUInt32(&ctx->runner->random) % (i+1);
        RValue temp=*GMLArray_slot(a,i); *GMLArray_slot(a,i)=*GMLArray_slot(a,j); *GMLArray_slot(a,j)=temp;
    }
    return RValue_makeArray(a);
}

static RValue builtin_ufo_ds_grid_clear(VMContext* ctx, RValue* args, int32_t count) {
    if (count < 2) return RValue_makeUndefined();
    DsGrid* grid=dsGridGet(ctx->runner,RValue_toInt32(args[0]));
    if (!grid) return RValue_makeUndefined();
    for (int32_t i=0;i<grid->width*grid->height;i++) {
        RValue next=RValue_makeIndependent(args[1]); RValue_free(&grid->items[i]); grid->items[i]=next;
    }
    return RValue_makeUndefined();
}

static RValue builtin_ufo_ds_grid_set_region(VMContext* ctx, RValue* args, int32_t count) {
    if (count < 6) return RValue_makeUndefined();
    DsGrid* grid=dsGridGet(ctx->runner,RValue_toInt32(args[0]));
    if (!grid) return RValue_makeUndefined();
    int x1=RValue_toInt32(args[1]),y1=RValue_toInt32(args[2]),x2=RValue_toInt32(args[3]),y2=RValue_toInt32(args[4]);
    if (x1>x2) { int t=x1;x1=x2;x2=t; } if (y1>y2) { int t=y1;y1=y2;y2=t; }
    if(x1<0)x1=0;if(y1<0)y1=0;if(x2>=grid->width)x2=grid->width-1;if(y2>=grid->height)y2=grid->height-1;
    for(int y=y1;y<=y2;y++)for(int x=x1;x<=x2;x++) {
        RValue* slot=&grid->items[y*grid->width+x];RValue next=RValue_makeIndependent(args[5]);RValue_free(slot);*slot=next;
    }
    return RValue_makeUndefined();
}

/* Region search follows GameMaker's inclusive, clamped, row-major traversal. */
static bool ufoGridValuesEqual(RValue a, RValue b) {
    bool aNumeric = a.type == RVALUE_REAL || a.type == RVALUE_INT32 ||
                    a.type == RVALUE_BOOL || a.type == RVALUE_ASSETREF;
    bool bNumeric = b.type == RVALUE_REAL || b.type == RVALUE_INT32 ||
                    b.type == RVALUE_BOOL || b.type == RVALUE_ASSETREF;
#ifndef NO_RVALUE_INT64
    aNumeric |= a.type == RVALUE_INT64;
    bNumeric |= b.type == RVALUE_INT64;
#endif
    if (aNumeric && bNumeric)
        return GMLReal_fabs(RValue_toReal(a) - RValue_toReal(b)) < GML_MATH_EPSILON;
    if (a.type == RVALUE_STRING && b.type == RVALUE_STRING)
        return a.string && b.string && strcmp(a.string, b.string) == 0;
    return false;
}

static int ufoGridFind(VMContext* ctx, RValue* args, int32_t count, int axis) {
    if (count < 6) return -1;
    DsGrid* grid = dsGridGet(ctx->runner, RValue_toInt32(args[0]));
    if (!grid || grid->width <= 0 || grid->height <= 0) return -1;
    int x1 = RValue_toInt32(args[1]), y1 = RValue_toInt32(args[2]);
    int x2 = RValue_toInt32(args[3]), y2 = RValue_toInt32(args[4]);
    if (x1 > x2) { int tmp = x1; x1 = x2; x2 = tmp; }
    if (y1 > y2) { int tmp = y1; y1 = y2; y2 = tmp; }
    x1 = x1 < 0 ? 0 : (x1 >= grid->width ? grid->width - 1 : x1);
    x2 = x2 < 0 ? 0 : (x2 >= grid->width ? grid->width - 1 : x2);
    y1 = y1 < 0 ? 0 : (y1 >= grid->height ? grid->height - 1 : y1);
    y2 = y2 < 0 ? 0 : (y2 >= grid->height ? grid->height - 1 : y2);
    for (int y = y1; y <= y2; y++) {
        for (int x = x1; x <= x2; x++) {
            if (ufoGridValuesEqual(grid->items[y * grid->width + x], args[5]))
                return axis == 0 ? x : y;
        }
    }
    return -1;
}

static RValue builtin_ufo_ds_grid_value_x(VMContext* ctx, RValue* args, int32_t count) {
    return RValue_makeInt32(ufoGridFind(ctx, args, count, 0));
}
static RValue builtin_ufo_ds_grid_value_y(VMContext* ctx, RValue* args, int32_t count) {
    return RValue_makeInt32(ufoGridFind(ctx, args, count, 1));
}
static RValue builtin_ufo_ds_grid_value_exists(VMContext* ctx, RValue* args, int32_t count) {
    return RValue_makeBool(ufoGridFind(ctx, args, count, 0) >= 0);
}

static RValue builtin_ufo_string_trim(VMContext* ctx, RValue* args, int32_t count) {
    (void)ctx;
    if(count<1)return RValue_makeOwnedString(safeStrdup(""));
    char* text=RValue_toString(args[0]);size_t begin=0,end=strlen(text);
    while(begin<end && isspace((unsigned char)text[begin]))begin++;
    while(end>begin && isspace((unsigned char)text[end-1]))end--;
    memmove(text,text+begin,end-begin);text[end-begin]=0;return RValue_makeOwnedString(text);
}
static RValue builtin_ufo_audio_group_set_gain(VMContext* ctx, RValue* args, int32_t count) {
    AudioSystem* audio = ctx->runner->audioSystem;
    if (count >= 3 && audio->vtable->setGroupGain) {
        int32_t time = RValue_toInt32(args[2]);
        audio->vtable->setGroupGain(audio, RValue_toInt32(args[0]), RValue_toReal(args[1]), time > 0 ? time : 0);
    }
    return RValue_makeUndefined();
}
static RValue builtin_ufo_audio_group_unload(VMContext* ctx, RValue* args, int32_t count) {
    AudioSystem* audio = ctx->runner->audioSystem;
    if (count && audio->vtable->groupUnload) audio->vtable->groupUnload(audio, RValue_toInt32(args[0]));
    return RValue_makeUndefined();
}
static RValue builtin_ufo_font_exists(VMContext* ctx, RValue* args, int32_t count) {
    if (count < 1) return RValue_makeBool(false);
    int32_t index = RValue_toInt32(args[0]);
    return RValue_makeBool(index >= 0 && (uint32_t)index < ctx->dataWin->font.count &&
                          ctx->dataWin->font.fonts[index].present);
}
static RValue builtin_layer_tile_create(VMContext* ctx, RValue* args, MAYBE_UNUSED int32_t argCount) {
    REQUIRE_ARGC_AT_LEAST("layer_tile_create", 8, RValue_makeReal(-1.0));
    Runner* runner = ctx->runner;
    int32_t layerId = resolveLayerIdArg(runner, args[0]);
    RuntimeLayer* runtimeLayer = Runner_findRuntimeLayerById(runner, layerId);
    if (runtimeLayer == nullptr)
        return RValue_makeReal(-1.0);

    int32_t x = RValue_toInt32(args[1]);
    int32_t y = RValue_toInt32(args[2]);
    int32_t tileset = RValue_toInt32(args[3]);
    int32_t left = RValue_toInt32(args[4]);
    int32_t top = RValue_toInt32(args[5]);
    int32_t width = RValue_toInt32(args[6]);
    int32_t height = RValue_toInt32(args[7]);

    RoomTile* tile = (RoomTile *)safeMalloc(sizeof(RoomTile));
    ZERO_STRUCT(*tile);
    tile->x = x;
    tile->y = y;
    tile->backgroundDefinition = tileset;
    tile->useSpriteDefinition = DataWin_isVersionAtLeast(ctx->dataWin, 2, 0, 0, 0);
    tile->sourceX = left;
    tile->sourceY = top;
    tile->width = (uint32_t)width;
    tile->height = (uint32_t)height;
    tile->tileDepth = runtimeLayer->depth;
    tile->scaleX = 1.0f;
    tile->scaleY = 1.0f;
    tile->color = 0xFFFFFF;
    tile->alpha = 1.0f;

    RuntimeLayerElement el = {0};
    el.id = Runner_getNextLayerId(runner);
    el.type = RuntimeLayerElementType_Tile;
    el.visible = true;
    el.alpha = 1.0f;
    el.blend = 0xFFFFFFu;
    el.tileElement = tile;
    el.tileElementOwned = true;
    arrput(runtimeLayer->elements, el);
    Runner_markLayerElementsDirty(runner);
    runner->drawableListStructureDirty = true;
    return RValue_makeReal((GMLReal) el.id);
}

static RValue builtin_layer_tile_destroy(VMContext* ctx, RValue* args, MAYBE_UNUSED int32_t argCount) {
    Runner* runner = ctx->runner;
    int32_t id = RValue_toInt32(args[0]);
    RuntimeLayer* owningLayer = nullptr;
    RuntimeLayerElement* el = Runner_findLayerElementById(runner, id, &owningLayer);
    if (el == nullptr || owningLayer == nullptr || el->type != RuntimeLayerElementType_Tile)
        return RValue_makeUndefined();
    if (el->tileElement != nullptr && el->tileElementOwned) {
        free(el->tileElement);
        el->tileElement = nullptr;
        el->tileElementOwned = false;
    }
    size_t count = arrlenu(owningLayer->elements);
    repeat(count, i) {
        if (&owningLayer->elements[i] == el) {
            arrdel(owningLayer->elements, i);
            Runner_markLayerElementsDirty(runner);
            break;
        }
    }
    return RValue_makeUndefined();
}


#undef REQUIRE_ARGC_AT_LEAST
