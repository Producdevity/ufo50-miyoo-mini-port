/* Compare rectangle broad-phase checks with the original cell enumeration. */
static bool Ufo50_enumeratedCellOverlap(const Instance* instance, SpatialGridRange range) {
    for (size_t i = 0; i < arrlenu(instance->collisionCells); i++) {
        uint32_t cell = instance->collisionCells[i];
        uint16_t x = SpatialGrid_unpackGridX(cell), y = SpatialGrid_unpackGridY(cell);
        if (x >= range.minGridX && x <= range.maxGridX &&
            y >= range.minGridY && y <= range.maxGridY) return true;
    }
    return false;
}

static int Ufo50_runSpatialRangeTests(void) {
    SpatialGridRange bounds[] = {{0, 0, 0, 0}, {3, 6, 4, 7}, {0, 0, 9, 11},
        {255, 255, 260, 260}, {32767, 65534, 32768, 65535}};
    Instance instance = {0};
    unsigned comparisons = 0;
    for (size_t r = 0; r < sizeof(bounds) / sizeof(bounds[0]); r++) {
        SpatialGridRange b = bounds[r];
        arrsetlen(instance.collisionCells, 0);
        for (unsigned x = b.minGridX; x <= b.maxGridX; x++)
            for (unsigned y = b.minGridY; y <= b.maxGridY; y++)
                arrput(instance.collisionCells, SpatialGrid_packGridCoordinates(x, y));
        // All combinations of edges and their neighbors, including empty ranges.
        uint16_t xs[] = {(uint16_t)(b.minGridX - 1), b.minGridX,
            (uint16_t)(b.minGridX + 1), b.maxGridX, (uint16_t)(b.maxGridX + 1)};
        uint16_t ys[] = {(uint16_t)(b.minGridY - 1), b.minGridY,
            (uint16_t)(b.minGridY + 1), b.maxGridY, (uint16_t)(b.maxGridY + 1)};
        repeat(5, x1) repeat(5, x2) repeat(5, y1) repeat(5, y2) {
            SpatialGridRange query = {xs[x1], ys[y1], xs[x2], ys[y2]};
            CHECK_TEST(SpatialGrid_instanceOverlapsRange(&instance, query) ==
                       Ufo50_enumeratedCellOverlap(&instance, query));
            comparisons++;
        }
    }
    arrsetlen(instance.collisionCells, 0);
    CHECK_TEST(!SpatialGrid_instanceOverlapsRange(&instance, (SpatialGridRange){0, 0, 65535, 65535}));
    arrfree(instance.collisionCells);
    logInfo("Spatial range selftests passed: %u independent cell comparisons, edges, empty ranges and 16-bit coordinates\n", comparisons);
    return 0;
}
