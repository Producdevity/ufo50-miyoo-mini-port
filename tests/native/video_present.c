// Compare presentation against the full-clear SDL path on native ARM32.
#include <stdio.h>
#include <string.h>
#include "sdl1_present.h"

static Ufo50VideoScaler scaler;

static int check(int bits, int sw, int sh, SDL_Rect* image) {
    Uint32 r = bits == 16 ? 0xf800 : 0x00ff0000;
    Uint32 g = bits == 16 ? 0x07e0 : 0x0000ff00;
    Uint32 b = bits == 16 ? 0x001f : 0x000000ff;
    SDL_Surface* src = SDL_CreateRGBSurface(0, sw, sh, bits, r, g, b, 0);
    SDL_Surface* ref = SDL_CreateRGBSurface(0, 640, 480, bits, r, g, b, 0);
    SDL_Surface* out = SDL_CreateRGBSurface(0, 640, 480, bits, r, g, b, 0);
    if (!src || !ref || !out) return 1;
    for (int y = 0; y < sh; ++y)
        for (int x = 0; x < sw; ++x) {
            SDL_Rect pixel = {x, y, 1, 1};
            SDL_FillRect(src, &pixel, SDL_MapRGB(src->format,
                (Uint8)(x * 37 + y), (Uint8)(y * 13 + x), (Uint8)(x + y * 7)));
        }
    // Different stale contents exercise clearing after an aspect change.
    SDL_FillRect(ref, NULL, 0xdeadbeef);
    SDL_FillRect(out, NULL, 0x13579bdf);
    SDL_FillRect(ref, NULL, 0);
    Ufo50_clearVideoBorders(out, image);
    if (SDL_SoftStretch(src, NULL, ref, image) < 0 ||
        Ufo50_stretchVideo(&scaler, src, out, image) < 0) return 2;
    int result = 0;
    for (int y = 0; y < out->h; ++y)
        if (memcmp((Uint8*)ref->pixels + y * ref->pitch,
                   (Uint8*)out->pixels + y * out->pitch,
                   out->w * out->format->BytesPerPixel)) { result = 3; break; }
    SDL_FreeSurface(src); SDL_FreeSurface(ref); SDL_FreeSurface(out);
    return result;
}

int main(void) {
    if (SDL_Init(0) < 0) return 1;
    SDL_Rect cases[] = {{0,60,640,360}, {80,0,480,480}, {0,0,640,480},
        {7,11,619,457}, {0,0,317,213}, {321,239,319,241},
        {319,239,1,1}, {1,1,638,478}, {0,0,384,216}};
    int count = 0;
    for (int bits = 16; bits <= 32; bits += 16)
        for (int size = 0; size < 3; ++size)
            for (unsigned i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i) {
                int error = check(bits, size == 0 ? 384 : size == 1 ? 17 : 641,
                    size == 0 ? 216 : size == 1 ? 13 : 481, &cases[i]);
                if (error) { fprintf(stderr, "case %d failed: %d (%s)\n", count, error, SDL_GetError()); return 1; }
                ++count;
            }
    free(scaler.columns);
    SDL_Quit();
    printf("Video presentation: %d pixel comparisons passed\n", count);
    return 0;
}
