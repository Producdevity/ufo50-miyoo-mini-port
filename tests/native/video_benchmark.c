// Display-pass CPU benchmark; no game files, window, input or audio device.
#include <stdio.h>
#include <time.h>
#include "sdl1_present.h"

static double nowSeconds(void) {
    struct timespec time;
    clock_gettime(CLOCK_MONOTONIC, &time);
    return time.tv_sec + time.tv_nsec * 1e-9;
}

int main(void) {
    if (SDL_Init(0) < 0) return 1;
    for (int bits = 16; bits <= 32; bits += 16) {
        Uint32 r = bits == 16 ? 0xf800 : 0xff0000;
        Uint32 g = bits == 16 ? 0x07e0 : 0xff00;
        Uint32 b = bits == 16 ? 0x001f : 0xff;
        SDL_Surface* source = SDL_CreateRGBSurface(0, 384, 216, bits, r, g, b, 0);
        SDL_Surface* screen = SDL_CreateRGBSurface(0, 640, 480, bits, r, g, b, 0);
        if (!source || !screen) return 2;
        for (int y = 0; y < source->h; y++) for (int x = 0; x < source->w; x++) {
            SDL_Rect pixel = {x, y, 1, 1};
            SDL_FillRect(source, &pixel, SDL_MapRGB(source->format,
                (Uint8)(x * 37 + y), (Uint8)(y * 13 + x), (Uint8)(x + y * 7)));
        }
        for (int size = 0; size <= 1; size++) for (int mode = 0; mode <= 2; mode++) {
            SDL_Rect image = size ? (SDL_Rect){0, 60, 640, 360} : (SDL_Rect){0, 0, 384, 216};
            Ufo50VideoScaler scaler = {0};
            Ufo50Crt crt = {0};
            double start = 0;
            unsigned checksum = 0;
            for (int i = -20; i < 300; i++) {
                if (!i) start = nowSeconds();
                if (Ufo50_stretchVideo(&scaler, source, screen, &image, 1) < 0) return 3;
                SDL_Rect physical = Ufo50_videoImageRect(screen, &image, 1);
                if (Ufo50_applyVideoCrt(&crt, screen, &physical, mode, 1) < 0) return 4;
                checksum += ((Uint8*)screen->pixels)[physical.y * screen->pitch + physical.x * screen->format->BytesPerPixel + i + 20];
            }
            printf("bits=%d width=%d height=%d mode=%d ms=%.6f checksum=%u\n",
                bits, image.w, image.h, mode, (nowSeconds() - start) * 1000 / 300, checksum);
            free(scaler.columns);
        }
        SDL_FreeSurface(source); SDL_FreeSurface(screen);
    }
    SDL_Quit();
    return 0;
}
