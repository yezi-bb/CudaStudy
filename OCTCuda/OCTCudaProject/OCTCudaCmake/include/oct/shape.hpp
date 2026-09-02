#ifndef OCT_SHAPE_HPP
#define OCT_SHAPE_HPP
namespace oct 
{
    struct Shape
    {
        int N = 0;       // points_pre_aline  一线的点数
        int Ls = 0;      // scan lines  扫描的一帧线数 (静态)
        int Lp = 0;      // pullback lines  拉回的一帧线数 (动态)
        int F = 0;       // reserved pullbacks frame 预留的拉回数
        int H = 0;       // circle height 圆高
        int W = 0;       // circle width 圆宽
    };
} // namespace oct
#endif