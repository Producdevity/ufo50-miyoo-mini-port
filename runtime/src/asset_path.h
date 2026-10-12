#ifndef UFO50_ASSET_PATH_H
#define UFO50_ASSET_PATH_H
// Return an owned path to an existing file/directory. Exact names win; otherwise
// resolve unique ASCII case-insensitive components without renaming anything.
char* AssetPath_resolveRead(const char* path);
#endif
