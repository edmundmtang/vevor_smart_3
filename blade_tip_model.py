"""v0.18 offline-only empirical blade-tip model; NOT a validated cutter model.

Coordinates are physical mm. Recovery is compactly supported: after the
specified recovery distance the predicted path is a straight line with a
constant residual lateral bias, not a slowly converging asymptote.
"""
from __future__ import annotations
from dataclasses import dataclass
import math

Point = tuple[float, float]


def add(a: Point, b: Point) -> Point: return (a[0]+b[0], a[1]+b[1])
def sub(a: Point, b: Point) -> Point: return (a[0]-b[0], a[1]-b[1])
def mul(a: Point, k: float) -> Point: return (a[0]*k, a[1]*k)
def left(a: Point) -> Point: return (-a[1], a[0])
def cross(a: Point, b: Point) -> float: return a[0]*b[1]-a[1]*b[0]


def clean(path):
    pts = [(float(x), float(y)) for x,y in path]
    if any(not math.isfinite(v) for p in pts for v in p):
        raise ValueError('Non-finite path point')
    result = []
    for p in pts:
        if not result or math.dist(p, result[-1]) > 1e-9: result.append(p)
    if len(result) < 2: raise ValueError('Need at least two distinct path points')
    return result


@dataclass(frozen=True)
class Parameters:
    recovery_mm: float = 1.40
    steady_gap_mm: float = 0.19
    # The mirrored-L experiment measures relative gap, NOT signed absolute bias.
    # Zero means no inferred signed bias; optional values are illustrative.
    signed_bias_mm: float = 0.0
    conditioning_mm: float = 3.0
    sample_step_mm: float = 0.10

    def __post_init__(self):
        for value in (self.recovery_mm, self.steady_gap_mm, self.signed_bias_mm,
                      self.conditioning_mm, self.sample_step_mm):
            if not math.isfinite(value): raise ValueError('Parameters must be finite')
        if not 0 < self.recovery_mm <= 10: raise ValueError('recovery_mm out of range')
        if not 0 <= self.steady_gap_mm <= 2: raise ValueError('steady_gap_mm out of range')
        if abs(self.signed_bias_mm) > 2: raise ValueError('signed_bias_mm out of range')
        if not 0 <= self.conditioning_mm <= 20: raise ValueError('conditioning_mm out of range')
        if not 0.01 <= self.sample_step_mm <= 1: raise ValueError('sample_step_mm out of range')


def conditioning(path, distance_mm):
    """Add a blade-down straight lead before path; may cross material/waste."""
    pts = clean(path)
    t = mul(sub(pts[1], pts[0]), 1/math.dist(pts[1], pts[0]))
    if distance_mm == 0: return pts
    return [sub(pts[0], mul(t, distance_mm))] + pts


def _segments(pts):
    vec = [sub(b,a) for a,b in zip(pts, pts[1:])]
    lengths = [math.hypot(*v) for v in vec]
    return lengths, [mul(v, 1/l) for v,l in zip(vec,lengths)]


def predict(path, params: Parameters):
    """Predict rounded path plus constant residual normal displacement.

    At a corner, quadratic Bezier smoothing spans at most recovery_mm AFTER
    the corner (and same distance before); it is a phenomenological surrogate,
    not a derived blade-swivel equation. The recovered portion is EXACTLY
    straight. Signed bias is optional and is not calibrated by mirrored-L gap.
    """
    pts = clean(path)
    lengths, tangents = _segments(pts)
    # Trim both sides of each corner, never overlap adjacent corner windows.
    trims = [0.0] * len(pts)
    for i in range(1,len(pts)-1):
        if abs(cross(tangents[i-1], tangents[i])) > 1e-7 or sum(mul(tangents[i-1],1)[j]*tangents[i][j] for j in range(2)) < 0.999999:
            trims[i] = min(params.recovery_mm, lengths[i-1]*0.45, lengths[i]*0.45)
    output = []
    def append(p):
        if not output or math.dist(p,output[-1]) > 1e-8: output.append(p)
    def line(a,b, normal):
        n = max(1,math.ceil(math.dist(a,b)/params.sample_step_mm))
        for k in range(n+1):
            append(add(add(a,mul(sub(b,a),k/n)),mul(normal,params.signed_bias_mm)))
    for i,(a,b) in enumerate(zip(pts,pts[1:])):
        start = add(a,mul(tangents[i],trims[i]))
        end = sub(b,mul(tangents[i],trims[i+1]))
        line(start,end,left(tangents[i]))
        if i+1 < len(pts)-1 and trims[i+1] > 0:
            corner = pts[i+1]
            entry = sub(corner,mul(tangents[i],trims[i+1]))
            leave = add(corner,mul(tangents[i+1],trims[i+1]))
            # A quadratic corner blend; normal bias interpolates from incoming
            # to outgoing side, then remains constant after recovery.
            n = max(2,math.ceil(2*trims[i+1]/params.sample_step_mm))
            for j in range(1,n+1):
                u=j/n
                q=add(add(mul(entry,(1-u)**2),mul(corner,2*u*(1-u))),mul(leave,u*u))
                normal=add(mul(left(tangents[i]),1-u),mul(left(tangents[i+1]),u))
                append(add(q,mul(normal,params.signed_bias_mm)))
    return output


def steady_compensation_candidate(path, params: Parameters):
    """Exploratory inverse of straight-run signed bias only.

    Does NOT invert corner dynamics. If bias is zero, return original contour.
    This is deliberately not a ready-to-cut compensation path.
    """
    pts=clean(path)
    _,tangents=_segments(pts)
    if params.signed_bias_mm == 0: return pts
    normals=[left(t) for t in tangents]
    result=[]
    for i,p in enumerate(pts):
        if i==0: n=normals[0]
        elif i==len(pts)-1: n=normals[-1]
        else:
            n=add(normals[i-1],normals[i])
            norm=math.hypot(*n)
            if norm < 1e-8: raise ValueError('U-turn cannot be offset safely')
            n=mul(n,1/norm)
        result.append(sub(p,mul(n,params.signed_bias_mm)))
    return result


def bounds(paths):
    pts=[p for path in paths for p in path]
    return (min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts))
