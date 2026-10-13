/* Native software CRT presentation. Game framebuffers and saves stay untouched. */
#ifndef UFO50_CRT_H
#define UFO50_CRT_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#if defined(__ARM_NEON) && __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
#include <arm_neon.h>
#define UFO50_CRT_NEON 1
#endif

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
// Saturating subtraction gives exactly the same channel values as the LUT.
// Process display rows in place; neither path reads beyond the image rectangle.
static inline void Ufo50_crtRow32(const Ufo50Crt* crt, uint8_t* row,
        int width, int uprightY, int rotate180) {
    int x = 0;
#ifdef UFO50_CRT_NEON
    unsigned phase = ((rotate180 ? width - 1 : 0) ^ uprightY) & 1;
    uint8_t dark = (uprightY & 1) * (crt->mode == 1 ? 18 : 64);
    uint8_t mask = crt->mode == 1 ? 13 : 26;
    uint8_t r = dark + phase * mask, gb = dark + (phase ^ 1) * mask;
    uint8_t offsets[16] = {gb, gb, r, 0, r, r, gb, 0,
                          gb, gb, r, 0, r, r, gb, 0};
    uint8x16_t subtract = vld1q_u8(offsets);
    for (; x + 4 <= width; x += 4) {
        uint8x16_t pixels = vld1q_u8(row + x * 4);
        vst1q_u8(row + x * 4, vqsubq_u8(pixels, subtract));
    }
#endif
    for (; x < width; x++) {
        uint32_t pixel;
        memcpy(&pixel, row + x * 4, 4);
        pixel = Ufo50_crtPixel(crt, pixel, rotate180 ? width - 1 - x : x, uprightY);
        memcpy(row + x * 4, &pixel, 4);
    }
}

static inline void Ufo50_crtRow565(const Ufo50Crt* crt, uint8_t* row,
        int width, int uprightY, int rotate180, int linearExpansion) {
    int x = 0;
#ifdef UFO50_CRT_NEON
    unsigned phase = ((rotate180 ? width - 1 : 0) ^ uprightY) & 1;
    uint16_t dark = (uprightY & 1) * (crt->mode == 1 ? 18 : 64);
    uint16_t mask = crt->mode == 1 ? 13 : 26;
    uint16_t r = dark + phase * mask, gb = dark + (phase ^ 1) * mask;
    uint16_t redOffsets[8] = {r, gb, r, gb, r, gb, r, gb};
    uint16_t otherOffsets[8] = {gb, r, gb, r, gb, r, gb, r};
    uint16x8_t redSubtract = vld1q_u16(redOffsets);
    uint16x8_t otherSubtract = vld1q_u16(otherOffsets);
    for (; x + 8 <= width; x += 8) {
        uint16x8_t pixels = vld1q_u16((const uint16_t*)(row + x * 2));
        uint16x8_t red = vshrq_n_u16(pixels, 11);
        uint16x8_t green = vandq_u16(vshrq_n_u16(pixels, 5), vdupq_n_u16(63));
        uint16x8_t blue = vandq_u16(pixels, vdupq_n_u16(31));
        if (linearExpansion) {
            // SDL2 expands by floor(value * 255 / max), SDL1 repeats bits.
            // These integer reciprocals are exact over all 5/6-bit inputs.
            red = vshrq_n_u16(vmulq_n_u16(red, 1053), 7);
            green = vshrq_n_u16(vaddq_u16(vmulq_n_u16(green, 259), vdupq_n_u16(3)), 6);
            blue = vshrq_n_u16(vmulq_n_u16(blue, 1053), 7);
        } else {
            red = vorrq_u16(vshlq_n_u16(red, 3), vshrq_n_u16(red, 2));
            green = vorrq_u16(vshlq_n_u16(green, 2), vshrq_n_u16(green, 4));
            blue = vorrq_u16(vshlq_n_u16(blue, 3), vshrq_n_u16(blue, 2));
        }
        red = vshlq_n_u16(vshrq_n_u16(vqsubq_u16(red, redSubtract), 3), 11);
        green = vshlq_n_u16(vshrq_n_u16(vqsubq_u16(green, otherSubtract), 2), 5);
        blue = vshrq_n_u16(vqsubq_u16(blue, otherSubtract), 3);
        vst1q_u16((uint16_t*)(row + x * 2), vorrq_u16(vorrq_u16(red, green), blue));
    }
#endif
    for (; x < width; x++) {
        uint16_t pixel;
        memcpy(&pixel, row + x * 2, 2);
        unsigned r = pixel >> 11, g = (pixel >> 5) & 63, b = pixel & 31;
        r = linearExpansion ? r * 255 / 31 : r << 3 | r >> 2;
        g = linearExpansion ? g * 255 / 63 : g << 2 | g >> 4;
        b = linearExpansion ? b * 255 / 31 : b << 3 | b >> 2;
        uint32_t rgb = r << 16 | g << 8 | b;
        rgb = Ufo50_crtPixel(crt, rgb, rotate180 ? width - 1 - x : x, uprightY);
        pixel = ((rgb >> 19) << 11) | (((rgb >> 10) & 63) << 5) | ((rgb >> 3) & 31);
        memcpy(row + x * 2, &pixel, 2);
    }
}
#endif
