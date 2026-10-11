#include <stdlib.h>
#include "sw_renderer_private.h"
#include "image/image_decoder.h"

void swrEvictTextureFromCache(SWRenderer* swr, int textureIndex) {
    swrFreeTexture(swr->textures[textureIndex]);
    swr->textures[textureIndex] = NULL;
}

static bool trimTextureCache(SWRenderer* swr, size_t required) {
    const size_t budget = 24u * 1024u * 1024u;
    if (required > budget) return false;
    size_t used = 0;
    repeat(swr->textureCount, i) if (swr->textures[i]) used += swrTextureBytes(swr->textures[i]);
    while (used + required > budget) {
        int victim = -1;
        uint64_t oldest = UINT64_MAX;
        repeat(swr->textureCount, i) {
            SWTexture* texture = swr->textures[i];
            if (texture && texture->lastUsed < oldest) { oldest = texture->lastUsed; victim = i; }
        }
        if (victim < 0) return false;
        used -= swrTextureBytes(swr->textures[victim]);
        swrEvictTextureFromCache(swr, victim);
    }
    return true;
}

bool swrEnsureTextureIsLoaded(SWRenderer* swr, uint32_t pageId) {
    if (pageId >= swr->textureCount) return false;
    if (swr->textures[pageId]) {
        swr->textures[pageId]->lastUsed = ++swr->textureAccessClock;
        return true;
    }
    DataWin* dw = swr->base.dataWin;
    Texture* txtr = &dw->txtr.textures[pageId];
    const char* setting = getenv("UFO50_PALETTE_TEXTURES");
    bool palette = !setting || strcmp(setting, "0") != 0;
    size_t estimate = sizeof(SWTexture) + (size_t)txtr->textureWidth * txtr->textureHeight *
                      (palette ? 1 : sizeof(uintpixel_t));
    if (!trimTextureCache(swr, estimate)) return false;
    if (!txtr->blobData) DataWin_loadTxtrIfNeeded(dw, pageId);
    if (!txtr->blobData) return false;

    int width, height;
    uint8_t* pixels = ImageDecoder_decodeToRgba(txtr->blobData, (size_t)txtr->blobSize,
        DataWin_isVersionAtLeast(dw, 2022, 5, 0, 0), &width, &height);
    if (!txtr->mapped) { free(txtr->blobData); txtr->blobData = NULL; }
    if (!pixels) { logWarn("SWR: Could not decode texture page %u\n", pageId); return false; }
    SWTexture* texture = swrCreateTexture(pixels, width, height);
    free(pixels);
    if (!trimTextureCache(swr, swrTextureBytes(texture))) { swrFreeTexture(texture); return false; }
    texture->lastUsed = ++swr->textureAccessClock;
    swr->textures[pageId] = texture;
    logInfo("SWR: Loaded TXTR page %u (%dx%d), %zu bytes, %u palette colors\n",
        pageId, width, height, swrTextureBytes(texture), (unsigned)texture->paletteCount);
    return true;
}
