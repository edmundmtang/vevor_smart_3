"""Experimental finite-recovery inverse compensator (physical millimeters).

This is a bounded empirical inverse, not an identified physical knife model.
Every corner is given an outgoing overshoot, and a direction/turn-side signed
normal correction is applied to steady portions. The commanded holder geometry
is intentionally allowed to depart from the nominal contour.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
from blade_tip_model import clean, add, sub, mul, left, cross

@dataclass(frozen=True)
class Config:
    recovery_mm: float = 1.39
    per_side_mm: float = 0.09
    overshoot_mm: float = 0.70
    conditioning_mm: float = 3.0
    max_extra_mm: float = 2.0
    def __post_init__(self):
        if not all(math.isfinite(v) for v in vars(self).values()): raise ValueError('Nonfinite compensation parameter')
        if not (0.1 <= self.recovery_mm <= 5 and 0 <= self.per_side_mm <= 0.5 and
                0 <= self.overshoot_mm <= self.recovery_mm and 0 <= self.conditioning_mm <= 10 and
                0 < self.max_extra_mm <= 5): raise ValueError('Compensation parameters out of conservative bounds')

def unit(v):
    d=math.hypot(*v)
    if d < 1e-9: raise ValueError('Degenerate segment')
    return mul(v,1/d)

def compensate_open(points, cfg:Config):
    """Produce a bounded holder path with lead-in and finite corner corrections.

    At each corner: advance along incoming direction beyond the nominal vertex,
    then move to the outgoing segment. The transient is localized to the first
    recovery_mm of outgoing travel; steady side correction is applied using
    the preceding turn sign. This is a testable heuristic, not exact inverse.
    """
    pts=clean(points)
    dirs=[unit(sub(b,a)) for a,b in zip(pts,pts[1:])]
    lengths=[math.dist(a,b) for a,b in zip(pts,pts[1:])]
    if min(lengths) < cfg.recovery_mm*1.25:
        raise ValueError('Segments too short for recovery model; use larger test shapes')
    out=[]
    def put(p):
        if not out or math.dist(out[-1],p)>1e-7: out.append(p)
    start=sub(pts[0],mul(dirs[0],cfg.conditioning_mm))
    put(start)
    put(pts[0])
    previous_side=0
    for i,(a,b,t,length) in enumerate(zip(pts,pts[1:],dirs,lengths)):
        if i:
            turn=cross(dirs[i-1],t)
            if abs(turn)>0.01:
                previous_side=1 if turn>0 else -1
            # Shift outward from the turn to counter mirrored-L persistent gap.
            normal=mul(left(t),-previous_side*cfg.per_side_mm)
            recovery_point=add(a,mul(t,cfg.recovery_mm))
            put(add(recovery_point,normal))
        else:
            normal=(0.,0.)
        if i+1<len(dirs):
            next_turn=cross(t,dirs[i+1])
            # Overshoot in incoming direction to encourage blade swivel.
            # The physical cut during this excursion is unvalidated.
            put(add(b,normal))
            if abs(next_turn)>0.01:
                put(add(add(b,normal),mul(t,cfg.overshoot_mm)))
        else:
            put(add(b,normal))
    return out

def compensate_closed(points,cfg:Config):
    """Closed loops: preserve nominal seam, add same-path approach and closure.

    We deliberately do NOT place an off-contour lead-in for closed loops: the
    conditioning segment retraces the final straight edge before the seam.
    """
    pts=clean(points)
    if math.dist(pts[0],pts[-1])>1e-6: raise ValueError('Expected closed path')
    # A loop can be represented as a repeated open traversal plus same-path
    # conditioning. Keep the final seam closed after the inverse path.
    openpts=pts[:-1]
    if len(openpts)<3: raise ValueError('Closed loop needs three corners')
    # Start on the final edge a short distance before the seam, so conditioning
    # remains on contour. Only safe if the final edge is long enough.
    last=unit(sub(openpts[0],openpts[-1]))
    edge=math.dist(openpts[0],openpts[-1])
    if edge < cfg.conditioning_mm+cfg.recovery_mm:
        raise ValueError('Closing edge too short for on-contour conditioning')
    start=sub(openpts[0],mul(last,cfg.conditioning_mm))
    # Closed loops have no safe general-purpose overshoot; only use compensated
    # open traversal and reconnect, exposing the limitation in documentation.
    path=compensate_open([openpts[0],*openpts[1:],openpts[0]],Config(cfg.recovery_mm,cfg.per_side_mm,cfg.overshoot_mm,0,cfg.max_extra_mm))
    return [start,*path]

def compensate(points,cfg:Config):
    pts=clean(points)
    result=compensate_closed(pts,cfg) if math.dist(pts[0],pts[-1])<1e-6 else compensate_open(pts,cfg)
    # No huge excursions: verify each commanded point is close to original
    # polyline (except permitted lead-in).
    def distance_to_segment(p,a,b):
        v=sub(b,a); vv=v[0]*v[0]+v[1]*v[1]
        u=max(0,min(1,((p[0]-a[0])*v[0]+(p[1]-a[1])*v[1])/vv))
        return math.dist(p,add(a,mul(v,u)))
    for p in result:
        d=min(distance_to_segment(p,a,b) for a,b in zip(pts,pts[1:]))
        if d>max(cfg.conditioning_mm,cfg.max_extra_mm)+1e-7:
            raise ValueError('Compensated point exceeds excursion bound')
    return result
