#ifndef UFO50_SDL1_PRESENT_H
#define UFO50_SDL1_PRESENT_H

#include <SDL/SDL.h>
#include <stdlib.h>
#include <string.h>

// The opaque scaled image overwrites its rectangle. Clear just the borders,
// including when the rectangle changes between frames or buffers are swapped.
static inline void Ufo50_clearVideoBorders(SDL_Surface* screen, const SDL_Rect* image) {
    SDL_Rect borders[4] = {
        {0, 0, (Uint16)screen->w, (Uint16)image->y},
        {0, (Sint16)(image->y + image->h), (Uint16)screen->w,
            (Uint16)(screen->h - image->y - image->h)},
        {0, image->y, (Uint16)image->x, image->h},
        {(Sint16)(image->x + image->w), image->y,
            (Uint16)(screen->w - image->x - image->w), image->h}
    };
    for (int i = 0; i < 4; ++i)
        if (borders[i].w && borders[i].h) SDL_FillRect(screen, &borders[i], 0);
}

typedef struct {
    int sourceWidth, destinationWidth, centerSamples;
    int* columns;
} Ufo50VideoScaler;

// Match the linked SDL library's 16.16 sample positions. Reuse columns and copy
// repeated output rows instead of stretching the same source row again.
static inline int Ufo50_stretchVideo(Ufo50VideoScaler* scaler, SDL_Surface* source,
        SDL_Surface* screen, SDL_Rect* image) {
    int bytes = source->format->BytesPerPixel;
    if ((bytes != 2 && bytes != 4) || source->format->BitsPerPixel != screen->format->BitsPerPixel ||
        source->w > 32767 || source->h > 32767 || !image->w || !image->h ||
        image->x < 0 || image->y < 0 || image->x + image->w > screen->w ||
        image->y + image->h > screen->h)
        return SDL_SoftStretch(source, NULL, screen, image);
    if (!scaler->columns || scaler->sourceWidth != source->w || scaler->destinationWidth != image->w) {
        int* columns = realloc(scaler->columns, image->w * sizeof(*columns));
        if (!columns) return SDL_SoftStretch(source, NULL, screen, image);
        scaler->columns = columns;
        scaler->sourceWidth = source->w;
        scaler->destinationWidth = image->w;
        // SDL12-compat uses SDL2's centered samples and identifies its releases
        // as SDL 1.2.50 and later. Original SDL1 starts at the top-left sample.
        scaler->centerSamples = SDL_Linked_Version()->patch >= 50;
        Uint32 increment = ((Uint32)source->w << 16) / image->w;
        Uint32 position = scaler->centerSamples ? increment / 2 : 0;
        for (unsigned x = 0; x < image->w; ++x, position += increment)
            columns[x] = (int)(position >> 16);
    }
    int sourceLocked = SDL_MUSTLOCK(source), screenLocked = SDL_MUSTLOCK(screen);
    if (sourceLocked && SDL_LockSurface(source) < 0) return -1;
    if (screenLocked && SDL_LockSurface(screen) < 0) {
        if (sourceLocked) SDL_UnlockSurface(source);
        return -1;
    }
    Uint32 increment = ((Uint32)source->h << 16) / image->h;
    Uint32 position = scaler->centerSamples ? increment / 2 : 0;
    int previousRow = -1;
    Uint8* previousOutput = NULL;
    for (unsigned y = 0; y < image->h; ++y, position += increment) {
        int row = (int)(position >> 16);
        Uint8* output = (Uint8*)screen->pixels + (image->y + y) * screen->pitch + image->x * bytes;
        const Uint8* input = (const Uint8*)source->pixels + row * source->pitch;
        if (row == previousRow) memcpy(output, previousOutput, image->w * bytes);
        else if (source->w == image->w) memcpy(output, input, image->w * bytes);
        else if (bytes == 4) {
            Uint32* out = (Uint32*)output;
            const Uint32* in = (const Uint32*)input;
            for (unsigned x = 0; x < image->w; ++x) out[x] = in[scaler->columns[x]];
        } else {
            Uint16* out = (Uint16*)output;
            const Uint16* in = (const Uint16*)input;
            for (unsigned x = 0; x < image->w; ++x) out[x] = in[scaler->columns[x]];
        }
        previousRow = row; previousOutput = output;
    }
    if (screenLocked) SDL_UnlockSurface(screen);
    if (sourceLocked) SDL_UnlockSurface(source);
    return 0;
}

#endif
