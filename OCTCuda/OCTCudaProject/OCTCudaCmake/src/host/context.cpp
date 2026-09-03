#ifndef OCT_CONTEXT_CPP
#define OCT_CONTEXT_CPP
#include "oct/context.hpp"

namespace oct {

bool Context::init(const Shape& s)
{
    shape_ = s;
    allocated_ = true;
    return true;
}

bool Context::shutdown(bool /*free_calib*/)
{
    allocated_ = false;
    return true;
}

bool Context::reinit()
{
    if (!allocated_) return false;
    Shape s = shape_;
    shutdown(false);
    return init(s);
}

cuda_utils::VramSnapshot Context::mem_info() const
{
    return cuda_utils::vram_snapshot();
}

bool Context::ok() const
{
    return cuda_utils::check_cuda_ok();
}

bool Context::reset_device()
{
    allocated_ = false;
    return cuda_utils::reset_device();
}

}  // namespace oct
#endif