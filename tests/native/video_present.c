// Compare presentation against the full-clear SDL path on native ARM32.
#include <stdio.h>
#include <string.h>
#include "sdl1_present.h"

static Ufo50VideoScaler scaler;

static int check(int bits, int sw, int sh, SDL_Rect* image, int rotate180, int mode) {
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
    SDL_Rect physical = *image;
    if (rotate180) { physical.x = 640 - image->x - image->w; physical.y = 480 - image->y - image->h; }
    Ufo50_clearVideoBorders(out, &physical);
    if (SDL_SoftStretch(src, NULL, ref, image) < 0 ||
        Ufo50_stretchVideo(&scaler, src, out, image, rotate180) < 0) return 2;
    Ufo50Crt crt = {0};
    if (Ufo50_applyVideoCrt(&crt, out, &physical, mode, rotate180) < 0) return 4;
    // Independent scalar color reference, using SDL's actual format decoding.
    if (mode) for (int y = image->y; y < image->y + image->h; y++)
        for (int x = image->x; x < image->x + image->w; x++) {
            int bytes = ref->format->BytesPerPixel;
            Uint8* at = (Uint8*)ref->pixels + y * ref->pitch + x * bytes;
            Uint32 pixel = 0;
            memcpy(&pixel, at, (size_t)bytes);
            Uint8 r, g, b;
            SDL_GetRGB(pixel, ref->format, &r, &g, &b);
            int row = (y - image->y) % 2;
            int phase = ((x - image->x) + (y - image->y)) % 2;
            int dark = row * (mode == 1 ? 18 : 64);
            int mask = mode == 1 ? 13 : 26;
            int channels[3] = {(int)r - dark - phase * mask,
                (int)g - dark - (1 - phase) * mask, (int)b - dark - (1 - phase) * mask};
            Uint32 shaded = SDL_MapRGB(ref->format,
                channels[0] < 0 ? 0 : channels[0], channels[1] < 0 ? 0 : channels[1],
                channels[2] < 0 ? 0 : channels[2]);
            Uint32 colors = ref->format->Rmask | ref->format->Gmask | ref->format->Bmask;
            shaded = (pixel & ~colors) | (shaded & colors);
            memcpy(at, &shaded, (size_t)bytes);
        }
    int result = 0;
    // Independent oracle: sample the finished SDL reference in panel order.
    int bytes = out->format->BytesPerPixel;
    for (int y = 0; y < out->h && !result; ++y)
        for (int x = 0; x < out->w; ++x) {
            int rx = rotate180 ? ref->w - 1 - x : x;
            int ry = rotate180 ? ref->h - 1 - y : y;
            if (memcmp((Uint8*)ref->pixels + ry * ref->pitch + rx * bytes,
                       (Uint8*)out->pixels + y * out->pitch + x * bytes,
                       (size_t)bytes)) { result = 3; break; }
        }
    SDL_FreeSurface(src); SDL_FreeSurface(ref); SDL_FreeSurface(out);
    return result;
}

int main(void) {
    if (SDL_Init(0) < 0) return 1;
    SDL_Rect cases[] = {{0,60,640,360}, {80,0,480,480}, {0,0,640,480},
        {7,11,619,457}, {0,0,317,213}, {321,239,319,241},
        {319,239,1,1}, {1,1,638,478}, {0,0,384,216}};
    int count = 0;
    Ufo50Crt golden = {0};
    Ufo50_crtMode(&golden, 1);
    if (Ufo50_crtPixel(&golden, 0xffffffff, 0, 0) != 0xfffff2f2 ||
        Ufo50_crtPixel(&golden, 0xffffffff, 0, 1) != 0xffe0eded ||
        Ufo50_crtPixel(&golden, 0x34000000, 0, 1) != 0x34000000) return 5;
    Ufo50_crtMode(&golden, 2);
    if (Ufo50_crtPixel(&golden, 0xffffffff, 0, 0) != 0xffffe5e5) return 5;
    Ufo50_crtMode(&golden, 0);
    if (Ufo50_crtPixel(&golden, 0x12345678, 3, 5) != 0x12345678) return 5;
    for (int mode = 0; mode <= 2; ++mode)
    for (int rotate = 0; rotate <= 1; ++rotate)
        for (int bits = 16; bits <= 32; bits += 8)
            for (int size = 0; size < 3; ++size)
                for (unsigned i = 0; i < sizeof(cases)/sizeof(cases[0]); ++i) {
                    int error = check(bits, size == 0 ? 384 : size == 1 ? 17 : 641,
                        size == 0 ? 216 : size == 1 ? 13 : 481, &cases[i], rotate, mode);
                    if (error) {
                        fprintf(stderr, "case %d failed: %d (%s)\n", count, error, SDL_GetError());
                        return 1;
                    }
                    ++count;
                }
    free(scaler.columns);
    SDL_Quit();
    printf("Video presentation: %d pixel comparisons passed\n", count);
    return 0;
}
