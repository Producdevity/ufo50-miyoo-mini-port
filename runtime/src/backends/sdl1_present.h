#ifndef UFO50_SDL1_PRESENT_H
#define UFO50_SDL1_PRESENT_H

#include <SDL/SDL.h>

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

#endif
