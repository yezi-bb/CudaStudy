#include "oct/context.hpp"
#include <cstdio>

int main()
{
    oct::Context ctx;
    oct::Shape s;
    s.N = 64;
    s.Ls = 8;
    s.Lp = 8;
    s.F = 2;
    s.H = 32;
    s.W = 32;

    if (!ctx.init(s)) {
        std::fprintf(stderr, "init failed\n");
        return 1;
    }

    auto v = ctx.mem_info();
    std::printf("VRAM total=%zu free=%zu used=%zu\n",
        v.total_bytes, v.free_bytes, v.used_bytes);

    ctx.shutdown();
    char c = getchar();
    return ctx.ok() ? 0 : 1;
}