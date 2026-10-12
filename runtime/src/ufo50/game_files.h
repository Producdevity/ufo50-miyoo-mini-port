/* Small disk checks; do not decode or retain game assets during preflight. */
#ifndef UFO50_GAME_FILES_H
#define UFO50_GAME_FILES_H
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static inline uint32_t Ufo50_fileU32(const unsigned char* p) {
    return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static inline bool Ufo50_checkFormFile(const char* path) {
    FILE* file = fopen(path, "rb");
    if (!file) return false;
    unsigned char header[8];
    bool ok = fread(header, 1, sizeof(header), file) == sizeof(header) &&
        memcmp(header, "FORM", 4) == 0 && fseek(file, 0, SEEK_END) == 0;
    long size = ok ? ftell(file) : -1;
    fclose(file);
    return ok && size >= 8 && (uint64_t)size == (uint64_t)Ufo50_fileU32(header + 4) + 8;
}

static inline bool Ufo50_checkTextureFile(const char* path, int width, int height) {
    FILE* file = fopen(path, "rb");
    if (!file) return false;
    unsigned char header[12];
    bool ok = fread(header, 1, sizeof(header), file) == sizeof(header) &&
        memcmp(header, "2zoq", 4) == 0 &&
        (header[4] | (unsigned)header[5] << 8) == (unsigned)width &&
        (header[6] | (unsigned)header[7] << 8) == (unsigned)height &&
        fseek(file, 0, SEEK_END) == 0;
    long size = ok ? ftell(file) : -1;
    fclose(file);
    return ok && size > 12;
}
#endif
