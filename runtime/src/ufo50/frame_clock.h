#ifndef UFO50_FRAME_CLOCK_H
#define UFO50_FRAME_CLOCK_H
/* Keep simulation at the game's speed while scheduling fewer draw passes. */
typedef struct { double credit; } Ufo50FrameClock;
static inline bool Ufo50FrameClock_draw(Ufo50FrameClock* clock, double limit, double logicHz) {
    if (limit <= 0 || logicHz <= 0 || limit >= logicHz) return true;
    clock->credit += limit;
    if (clock->credit + 0.000001 < logicHz) return false;
    clock->credit -= logicHz;
    return true;
}
static inline uint64_t Ufo50FrameClock_deadline(uint64_t previous, uint64_t now, uint64_t period) {
    uint64_t next = previous + period;
    // Discard long pauses and loading stalls, but retain phase after short overruns.
    return now > next && now - next > period * 8 ? now : next;
}
#endif
