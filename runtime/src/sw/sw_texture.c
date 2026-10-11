#include <stdlib.h>
#include "sw_renderer_private.h"

SWTexture* swrCreateTextureEx(const void* srcBuffer, int width, int height, bool convert)
{
    SWTexture* txt = (SWTexture*) safeCalloc(1, sizeof(SWTexture));
    txt->buffer = (uintpixel_t*) safeMalloc(width * height * sizeof(uintpixel_t));
    
    size_t sz = width * height;
    
    if (srcBuffer)
    {
        if (convert) {
            const uint32_t* rgbaSrc = (const uint32_t*) srcBuffer;
            for (size_t i = 0; i < sz; i++)
                txt->buffer[i] = swrConvertPixelTexture(rgbaSrc[i]);
        }
        else {
            const uintpixel_t* rgbaSrc = (const uintpixel_t*) srcBuffer;
            for (size_t i = 0; i < sz; i++)
                txt->buffer[i] = rgbaSrc[i];
        }
    }
    else
    {
        memset(txt->buffer, 0, width * height * sizeof(uintpixel_t));
    }
    
    txt->width = (uint16_t) width;
    txt->height = (uint16_t) height;
    
    return txt;
}

SWTexture* swrCreateTexture(const uint8_t* srcBuffer, int width, int height)
{
    const char* setting = getenv("UFO50_PALETTE_TEXTURES");
    if (!srcBuffer || (setting && strcmp(setting, "0") == 0))
        return swrCreateTextureEx(srcBuffer, width, height, true);

    SWTexture* texture = safeCalloc(1, sizeof(*texture));
    size_t count = (size_t)width * height;
    texture->indices = safeMalloc(count);
    texture->width = width; texture->height = height;
    uintpixel_t keys[512] = {0};
    uint16_t values[512] = {0};
    bool used[512] = {0};
    const uint32_t* pixels = (const uint32_t*)srcBuffer;
    for (size_t i = 0; i < count; i++) {
        uintpixel_t color = swrConvertPixelTexture(pixels[i]);
        unsigned slot = ((uint32_t)color * 2654435761u) >> 23;
        while (used[slot] && keys[slot] != color) slot = (slot + 1) & 511u;
        if (!used[slot]) {
            if (texture->paletteCount == 256) {
                swrFreeTexture(texture);
                return swrCreateTextureEx(srcBuffer, width, height, true);
            }
            used[slot] = true; keys[slot] = color;
            values[slot] = texture->paletteCount;
            texture->palette[texture->paletteCount++] = color;
        }
        texture->indices[i] = (uint8_t)values[slot];
    }
    return texture;
}

SWTexture* swrCopyTexture(SWTexture* texture)
{
    SWTexture* copy = swrCreateTextureEx(NULL, texture->width, texture->height, false);
    for (size_t i = 0, count = (size_t)texture->width * texture->height; i < count; i++)
        copy->buffer[i] = swrTexturePixel(texture, i);
    return copy;
}

void swrFreeTexture(SWTexture* texture)
{
    if (UNLIKELY(!texture))
        return;
    
    free(texture->indices);
    free(texture->buffer);
    free(texture);
}
