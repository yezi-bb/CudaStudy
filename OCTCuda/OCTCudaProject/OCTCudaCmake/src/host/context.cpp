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

bool Context::shutdown(b