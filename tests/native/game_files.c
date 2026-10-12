#include "ufo50/game_files.h"
#include "asset_path.h"
#include <stdlib.h>
int main(int argc, char** argv) {
    if (argc == 3 && strcmp(argv[1], "resolve") == 0) {
        char* path = AssetPath_resolveRead(argv[2]);
        if (!path) return 1;
        puts(path);
        free(path);
        return 0;
    }
    if (argc == 3 && strcmp(argv[1], "form") == 0)
        return Ufo50_checkFormFile(argv[2]) ? 0 : 1;
    if (argc == 5 && strcmp(argv[1], "texture") == 0)
        return Ufo50_checkTextureFile(argv[2], atoi(argv[3]), atoi(argv[4])) ? 0 : 1;
    return 2;
}
