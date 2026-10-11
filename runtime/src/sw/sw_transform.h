#ifndef _SW_TRANSFORM_H
#define _SW_TRANSFORM_H

FORCE_INLINE void swrTransformPosIfNeeded(SWRenderer* swr, float* dx, float* dy)
{
    if (dx) {
        *dx -= swr->viewX;
        *dx *= swr->scaleX;
        *dx += swr->portX;
    }
    if (dy) {
        *dy -= swr->viewY;
        *dy *= swr->scaleY;
        *dy += swr->portY;
    }
}

FORCE_INLINE void swrTransformSizeIfNeeded(SWRenderer* swr, float* dx, float* dy)
{
    if (dx) *dx *= swr->scaleX;
    if (dy) *dy *= swr->scaleY;
}

FORCE_INLINE void swrTransformPosIntIfNeeded(SWRenderer* swr, int32_t* dx, int32_t* dy)
{
    if (dx) {
        *dx -= swr->viewX;
        *dx = (int)(*dx * swr->scaleX);
        *dx += swr->portX;
    }
    if (dy) {
        *dy -= swr->viewY;
        *dy = (int)(*dy * swr->scaleY);
        *dy += swr->portY;
    }
}

FORCE_INLINE void swrTransformSizeIntIfNeeded(SWRenderer* swr, int32_t* dx, int32_t* dy)
{
    if (dx) *dx = (int)(*dx * swr->scaleX);
    if (dy) *dy = (int)(*dy * swr->scaleY);
}

FORCE_INLINE void swrReverseTransformSizeIfNeeded(SWRenderer* swr, float* dx, float* dy)
{
    if (dx) *dx = *dx / swr->scaleX;
    if (dy) *dy = *dy / swr->scaleY;
}

FORCE_INLINE void swrReverseTransformSizeIntIfNeeded(SWRenderer* swr, int32_t* dx, int32_t* dy)
{
    if (dx) *dx = (int)(*dx / swr->scaleX);
    if (dy) *dy = (int)(*dy / swr->scaleY);
}

/* Match the rasterizer's integer bounds before decoding an atlas page. */
FORCE_INLINE bool swrSpriteOutsideView(SWRenderer* swr, float x, float y, float w, float h) {
    swrTransformPosIfNeeded(swr, &x, &y);
    swrTransformSizeIfNeeded(swr, &w, &h);
    int dx = swrFloor(x), dy = swrFloor(y);
    int dw = swrCeiling(w), dh = swrCeiling(h);
    if (dw < 0) { dx += dw; dw = -dw; }
    if (dh < 0) { dy += dh; dh = -dh; }
    return dw == 0 || dh == 0 || dx + dw <= swr->portX ||
           dy + dh <= swr->portY || dx >= swr->maxX || dy >= swr->maxY;
}

#endif//_SW_TRANSFORM_H
