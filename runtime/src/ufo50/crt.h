/* Native software CRT presentation. Game framebuffers and saves stay untouched. */
#ifndef UFO50_CRT_H
#define UFO50_CRT_H
#include <stdint.h>
#include <stddef.h>

typedef struct {
    int mode;
    uint8_t channel[4][256];
} Ufo50Crt;

static inline void Ufo50_crtMode(Ufo50Crt* crt, int mode) {
    if (mode < 0 || mode > 2) mode = 0;
    if (crt->mode == mode) return;
    crt->mode = mode;
    // Off / Soft / Hard, using the scanline and phosphor strengths of the
    // game's 2x option. Lookup tables replace per-pixel floating-point work.
    int line = mode == 1 ? 18 : mode == 2 ? 64 : 0;
    int mask = mode == 1 ? 13 : mode == 2 ? 26 : 0;
    for (int shade = 0; shade < 4; shade++) {
        int subtract = (shade & 2 ? line : 0) + (shade & 1 ? mask : 0);
        for (int value = 0; value < 256; value++)
            crt->channel[shade][value] = value > subtract ? value - subtract : 0;
    }
}

static inline uint32_t Ufo50_crtPixel(const Ufo50Crt* crt, uint32_t pixel, int x, int y) {
    if (!crt->mode) return pixel;
    unsigned row = (unsigned)(y & 1) << 1;
    unsigned phase = (unsigned)((x ^ y) & 1);
    unsigned r = crt->channel[row + phase][(pixel >> 16) & 255];
    unsigned g = crt->channel[row + (phase ^ 1)][(pixel >> 8) & 255];
    unsigned b = crt->channel[row + (phase ^ 1)][pixel & 255];
    return (pixel & 0xff000000u) | r << 16 | g << 8 | b;
}
#endif
