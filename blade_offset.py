"""Experimental swivel drag-knife holder-path model (physical millimeters).

For a blade tip at P moving with unit tangent T, approximate holder center H=P+d*T.
At a polygon corner the holder pivots around the stationary blade tip on a
radius-d arc from the incoming to outgoing tangent. This is a *model*, not a
verified Smart 3 mechanism. Pivot arcs are off the nominal blade-tip contour.
"""
import math


def compensate(path, offset_mm, max_arc_step_deg=10.0):
    if not math.isfinite(offset_mm) or offset_mm < 0 or offset_mm > 2:
        raise ValueError('Blade offset must be finite and between 0 and 2 mm')
    if not math.isfinite(max_arc_step_deg) or not 1 <= max_arc_step_deg <= 45:
        raise ValueError('Arc step must be between 1 and 45 degrees')
    pts = list(path)
    if offset_mm == 0:
        return pts, 'disabled'
    if len(pts) < 2:
        return pts, 'degenerate/unchanged'
    # Keep the seam closure and any additional same-path overlap in order.
    cleaned = [pts[0]]
    for pt in pts[1:]:
        if math.dist(pt, cleaned[-1]) > 1e-9:
            cleaned.append(pt)
    if len(cleaned) < 2:
        return pts, 'degenerate/unchanged'
    directions = []
    for a,b in zip(cleaned,cleaned[1:]):
        length=math.dist(a,b)
        directions.append(((b[0]-a[0])/length,(b[1]-a[1])/length))
    def holder(p,t):
        return (p[0]+offset_mm*t[0],p[1]+offset_mm*t[1])
    result=[holder(cleaned[0],directions[0])]
    pivots=0
    for i,t in enumerate(directions):
        corner=cleaned[i+1]
        result.append(holder(corner,t))
        if i+1 == len(directions):
            continue
        next_t=directions[i+1]
        angle=math.atan2(t[0]*next_t[1]-t[1]*next_t[0], t[0]*next_t[0]+t[1]*next_t[1])
        if abs(angle)<1e-8:
            continue
        pivots+=1
        start=math.atan2(t[1],t[0])
        steps=max(1,math.ceil(abs(math.degrees(angle))/max_arc_step_deg))
        for j in range(1,steps+1):
            theta=start+angle*j/steps
            result.append((corner[0]+offset_mm*math.cos(theta),corner[1]+offset_mm*math.sin(theta)))
    return result, f'offset {offset_mm:.3f} mm; {pivots} pivot(s); {len(result)} holder points'
