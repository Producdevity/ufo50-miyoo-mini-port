#ifndef UFO50_DISPLAY_OPTIONS_H
#define UFO50_DISPLAY_OPTIONS_H
#include "vm.h"

// The game bypasses its desktop CRT passes at 1x. Read its own setting for a
// native presentation pass; do not change the authored display/game state.
static inline int Ufo50_nativeCrtMode(Runner* runner) {
    if (!runner || !runner->dataWin->gen8.name ||
        strcmp(runner->dataWin->gen8.name, "ufo50") != 0) return 0;
    VMContext* vm = runner->vmContext;
    RValue scale = VM_structGetVariableByVarName(vm, vm->globalScopeInstance, "scale", -1);
    if (RValue_toReal(scale) > 1) return 0;
    RValue mode = VM_structGetVariableByVarName(vm, vm->globalScopeInstance, "scanlines", -1);
    if (mode.type == RVALUE_UNDEFINED) return 0;
    double value = RValue_toReal(mode);
    return value == 1 ? 1 : value == 2 ? 2 : 0;
}
#endif
