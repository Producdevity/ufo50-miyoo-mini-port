#ifndef _SW_RENDERER_H
#define _SW_RENDERER_H

#include "renderer.h"

Renderer* SWRenderer_create(void);
int SWRenderer_runCacheTests(void);

bool SWRenderer_writeScreenshot(Renderer* renderer, const char* path);

void SWRenderer_clearFrameBuffer(Renderer* renderer, uint32_t color);

#endif//_SW_RENDERER_H
