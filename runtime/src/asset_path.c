#include "asset_path.h"
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#ifndef _WIN32
#include <dirent.h>
#include <ctype.h>

static int equalCase(const char* a, const char* b) {
    while (*a && *b) {
        if (tolower((unsigned char)*a++) != tolower((unsigned char)*b++)) return 0;
    }
    return *a == *b;
}
#endif

char* AssetPath_resolveRead(const char* path) {
    if (!path || !*path) return NULL;
    size_t length = strlen(path);
    char* result = malloc(length + 2);
    if (!result) return NULL;
    struct stat st;
    if (stat(path, &st) == 0) {
        memcpy(result, path, length + 1);
        return result;
    }
#ifdef _WIN32
    free(result);
    return NULL;
#else
    char* input = malloc(length + 1);
    if (!input) { free(result); return NULL; }
    memcpy(input, path, length + 1);
    size_t used = 0;
    if (*input == '/') result[used++] = '/';
    result[used] = 0;
    char* part = input;
    while (*part) {
        while (*part == '/') part++;
        if (!*part) break;
        char* end = strchr(part, '/');
        if (end) *end = 0;
        DIR* dir = opendir(used ? result : ".");
        if (!dir) goto fail;
        size_t componentLength = strlen(part);
        if (used && result[used - 1] != '/') result[used++] = '/';
        size_t prefix = used;
        int matches = 0;
        struct dirent* entry;
        while ((entry = readdir(dir))) {
            if (strlen(entry->d_name) != componentLength || !equalCase(entry->d_name, part)) continue;
            matches++;
            memcpy(result + prefix, entry->d_name, componentLength + 1);
            if (strcmp(entry->d_name, part) == 0) { matches = 1; break; }
        }
        closedir(dir);
        if (matches != 1) goto fail;
        used = prefix + componentLength;
        if (!end) break;
        part = end + 1;
    }
    free(input);
    if (stat(result, &st) == 0) return result;
    free(result);
    return NULL;
fail:
    free(input);
    free(result);
    return NULL;
#endif
}
