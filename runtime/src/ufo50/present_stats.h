#ifndef UFO50_PRESENT_STATS_H
#define UFO50_PRESENT_STATS_H
#include <stdint.h>
#include <string.h>

// Half-millisecond buckets, collected only when performance logging is enabled.
// Keep the preceding flip across reporting windows so boundary gaps are counted.
typedef struct {
    uint64_t previous, maximum, count, longIntervals;
    uint32_t buckets[128];
} Ufo50PresentStats;

static inline void Ufo50PresentStats_add(Ufo50PresentStats* stats, uint64_t now, uint64_t period) {
    if (stats->previous && now > stats->previous) {
        uint64_t interval = now - stats->previous;
        unsigned bucket = interval / 500000u;
        if (bucket >= 128) bucket = 127;
        stats->buckets[bucket]++;
        stats->count++;
        if (interval > stats->maximum) stats->maximum = interval;
        if (period && interval > period + period / 2) stats->longIntervals++;
    }
    stats->previous = now;
}

// Upper bound of the percentile bucket; overflow uses the exact maximum.
static inline double Ufo50PresentStats_p95(const Ufo50PresentStats* stats) {
    if (!stats->count) return 0;
    uint64_t target = (stats->count * 95 + 99) / 100, count = 0;
    for (unsigned i = 0; i < 128; i++) {
        count += stats->buckets[i];
        if (count >= target) return i == 127 ? stats->maximum / 1000000.0 : (i + 1) * 0.5;
    }
    return 0;
}

static inline void Ufo50PresentStats_reset(Ufo50PresentStats* stats) {
    uint64_t previous = stats->previous;
    memset(stats, 0, sizeof(*stats));
    stats->previous = previous;
}
#endif
