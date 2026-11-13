"""Offline-only experimental local holder maneuver. Never alters v0.30 inverse."""
import math
def minus(a,b): return (a[0]-b[0],a[1]-b[1])
def plus(a,b): return (a[0]+b[0],a[1]+b[1])
def scale(a,k): return (a[0]*k,a[1]*k)
def length(a): return math.hypot(*a)
def unit(a):
    n=length(a)
    if n<1e-9: raise ValueError('zero direction')
    return scale(a,1/n)
def smooth(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)


def apply_corner_reach(holder, original, reach_mm, support_mm=1.0, min_turn_deg=30.0):
    """Add a compact holder excursion along the apex-facing angle bisector.

    Match original vertices to the closest v0.30 sampled holder positions by
    monotonically increasing index. Support is measured in holder arc length.
    No target deformation, solver modification, or persistent outgoing shift.
    """
    if not math.isfinite(reach_mm) or not 0 <= reach_mm <= 0.20:
        raise ValueError('reach_mm must be finite in [0, 0.20]')
    if not math.isfinite(support_mm) or not 0.5 <= support_mm <= 3.0:
        raise ValueError('support_mm must be finite in [0.5, 3.0]')
    if not math.isfinite(min_turn_deg) or not 15 <= min_turn_deg <= 150:
        raise ValueError('invalid minimum turn angle')
    h = [tuple(p) for p in holder]
    pts = [tuple(p) for p in original]
    if len(h) < 2 or len(pts) < 2 or any(not all(math.isfinite(v) for v in p) for p in h+pts):
        raise ValueError('invalid geometry')
    if reach_mm == 0: return h
    closed = len(pts) > 2 and length(minus(pts[0], pts[-1])) < 1e-6
    # Avoid seam intervention: closed-path seam is intentionally preserved.
    vertices = range(1, len(pts)-1)
    cumulative = [0.0]
    for a,b in zip(h,h[1:]): cumulative.append(cumulative[-1]+length(minus(b,a)))
    out = list(h)
    previous_index = 0
    for j in vertices:
        a = minus(pts[j],pts[j-1]); b = minus(pts[j+1],pts[j])
        if min(length(a),length(b)) < 2*support_mm: continue
        incoming,outgoing = unit(a),unit(b)
        turn = abs(math.degrees(math.atan2(incoming[0]*outgoing[1]-incoming[1]*outgoing[0],
                                                incoming[0]*outgoing[0]+incoming[1]*outgoing[1])))
        if turn < min_turn_deg: continue
        bisector = minus(incoming,outgoing)
        if length(bisector)<1e-8: continue
        # Interior vertices have monotonic ordering in the sampled holder.
        idx = min(range(previous_index,len(h)), key=lambda k: length(minus(h[k],pts[j])))
        previous_index = idx
        # Don't move first/last holder samples, including closed-path seam.
        for k in range(1,len(h)-1):
            d = abs(cumulative[k]-cumulative[idx])
            if d >= support_mm: continue
            weight = 1.0-smooth(d/support_mm)
            out[k] = plus(out[k],scale(unit(bisector),reach_mm*weight))
    if any(not all(math.isfinite(v) for v in p) for p in out):
        raise ValueError('nonfinite holder maneuver')
    return out
