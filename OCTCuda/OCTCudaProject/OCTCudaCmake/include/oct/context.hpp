#ifndef OCT_CONTEXT_HPP
#define OCT_CONTEXT_HPP
#include "shape.hpp"
#include "cuda_utils.hpp"

namespace oct {

class Context {
public:
    bool init(const Shape& s);
    bool shutdown(bool free_calib = true);
    bool reinit();
    cuda_utils::VramSnapshot mem_info() const;
    bool ok() const;
    bool reset_device();
    const Shape& last_shape() const { return shape_; }
    bool allocated() const { return allocated_; }

private:
    Shape shape_{};
    bool allocated_ = false;
};

}  // namespace oct
#endif