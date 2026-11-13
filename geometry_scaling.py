"""Scale intended SVG geometry around each test shape center, before blade compensation.

These factors are *geometry* adjustments, never machine axis calibration.
"""
import math

def scale_group(paths, sx=1.0, sy=1.0):
    if not paths or any(not path for path in paths):
        raise ValueError("Expected nonempty paths")
    if not all(math.isfinite(v) and 0.9 <= v <= 1.1 for v in (sx,sy)):
        raise ValueError("Geometry scale must be finite and within [0.9, 1.1]")
    xs=[float(x) for path in paths for x,_ in path]
    ys=[float(y) for path in paths for _,y in path]
    if not all(math.isfinite(v) for v in xs+ys):
        raise ValueError("Nonfinite geometry coordinate")
    cx=(min(xs)+max(xs))/2
    cy=(min(ys)+max(ys))/2
    return [[(cx+(float(x)-cx)*sx,cy+(float(y)-cy)*sy) for x,y in path] for path in paths]
