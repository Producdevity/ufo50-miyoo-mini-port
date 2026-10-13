#ifndef _SW_RENDERER_H
#define _SW_RENDERER_H

#include "renderer.h"

Renderer* SWRenderer_create(void);
int SWRenderer_runCacheTests(void);
int SWRenderer_runSpriteTests(void);

bool SWRenderer_writeScreenshot(Renderer* renderer, const char* path);

void SWRenderer_setOutputCrt(Renderer* renderer, int mode);
int SWRenderer_getOutputCrt(Renderer* renderer);

void SWRenderer_setFrameRendering(Renderer* renderer, bool enabled);

void SWRenderer_clearFrameBuffer(Renderer* renderer, uint32_t color);

#endif//_SW_RENDERER_H
