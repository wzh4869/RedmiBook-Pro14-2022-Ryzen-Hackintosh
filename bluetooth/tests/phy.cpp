#include <cassert>
#include <cstdio>
#include <cstdint>
#include <cstdarg>
#include <cstring>
#include <sys/mman.h>
#include "../PatchEngine.hpp"
#include "../generated/Patches.hpp"
int main() {
    unsigned char page[4096], saved[4096];
    for (auto &spec : patchSpecs) {
        memcpy(page,spec.originalPage,4096);
        assert(applyPage(spec,spec.fileOffset,page,4096)==PatchResult::Applied);
        assert(!memcmp(page+spec.pageOffset,spec.replacement,spec.size));
        assert(applyPage(spec,spec.fileOffset,page,4096)==PatchResult::AlreadyApplied);
        memcpy(page,spec.originalPage,4096); page[0]^=1; memcpy(saved,page,4096);
        assert(applyPage(spec,spec.fileOffset,page,4096)==PatchResult::Mismatch);
        assert(!memcmp(page,saved,4096));
        assert(applyPage(spec,spec.fileOffset+4096,page,4096)==PatchResult::NoMatch);
        assert(!memcmp(page,saved,4096));
        assert(applyPage(spec,spec.fileOffset,nullptr,4096)==PatchResult::Mismatch);
        auto invalid=spec; invalid.pageOffset=4090; invalid.size=32;
        assert(applyPage(invalid,invalid.fileOffset,page,4096)==PatchResult::Mismatch);
        invalid.pageOffset=SIZE_MAX;
        assert(applyPage(invalid,invalid.fileOffset,page,4096)==PatchResult::Mismatch);
    }
    puts("PASS: real patch engine, exact page, one-byte replacement, idempotence, mismatch and bounds checks.");
}
