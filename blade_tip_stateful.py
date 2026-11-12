"""Experimental stateful blade-tip predictor and bounded inverse (millimeters).

Phenomenological model, not physically validated. A finite-support orientation
transition and hysteretic lateral offset are separate state variables. Never
assume the tip eventually converges to the nominal line. No USB operations.
"""
from dataclasses import dataclass
import math

def plus(a,b): return (a[0]+b[0],a[1]+b[1])
def minus(a,b): return (a[0]-b[0],a[1]-b[1])
def scale(a,k): return (a[0]*k,a[1]*k)
def length(a): return math.hypot(*a)
def unit(a):
    l=length(a)
    if l<1e-9: raise ValueError('Zero-length segment')
    return scale(a,1/l)
def normal(a): return (-a[1],a[0])
def cross(a,b): return a[0]*b[1]-a[1]*b[0]
def mix(a,b,t): return plus(scale(a,1-t),scale(b,t))
def smooth(t):
    t=max(0,min(1,t)); return t*t*(3-2*t)

@dataclass(frozen=True)
class Model:
    recovery_mm: float=1.39
    blade_offset_mm: float=0.20
    x_rotation: float=1.0
    y_rotation: float=1.0
    min_approach_x_mm: float=0.09
    min_approach_y_mm: float=0.0
    conditioning_mm: float=3.0
    step_mm: float=0.15
    max_correction_mm: float=0.65
    iterations: int=12
    vertex_weight: float=2.5
    def __post_init__(self):
        for v in vars(self).values():
            if not math.isfinite(v): raise ValueError('Nonfinite model parameter')
        if not (.2<=self.recovery_mm<=5 and 0<=self.blade_offset_mm<=1 and
                .2<=self.x_rotation<=3 and .2<=self.y_rotation<=3 and
                0<=self.min_approach_x_mm<=.4 and 0<=self.min_approach_y_mm<=.4 and
                0<=self.conditioning_mm<=8 and .05<=self.step_mm<=.5 and
                0<self.max_correction_mm<=1.5 and 1<=self.iterations<=25 and 1<=self.vertex_weight<=5):
            raise ValueError('Model parameter outside experimental safety bounds')

def sample(points,step):
    out=[tuple(map(float,points[0]))]
    for p in points[1:]:
        a=out[-1]; b=tuple(map(float,p)); dist=length(minus(b,a))
        if dist<1e-8: continue
        n=max(1,math.ceil(dist/step))
        out.extend(mix(a,b,k/n) for k in range(1,n+1))
    if len(out)<2: raise ValueError('Empty path')
    return out

def _direction_at(points, i, window_mm=0.45):
    """Windowed tangent avoids interpreting numerical correction jitter as blade turns."""
    lo=i; hi=i
    dist=0.
    while lo>0 and dist<window_mm:
        dist+=length(minus(points[lo],points[lo-1])); lo-=1
    dist=0.
    while hi<len(points)-1 and dist<window_mm:
        dist+=length(minus(points[hi+1],points[hi])); hi+=1
    d=minus(points[hi],points[lo])
    if length(d)<1e-9:
        d=minus(points[min(i+1,len(points)-1)],points[max(i-1,0)])
    return unit(d)

def forward(holder, model):
    """Stateful phenomenological predictor, with finite turn response and held bias.

    Uses an angular interpolation (safe for reversals) and a spatially averaged
    holder tangent. This is a predictive hypothesis, not a measured blade model.
    """
    if len(holder)<2: raise ValueError('Need two holder positions')
    directions=[_direction_at(holder,i) for i in range(len(holder))]
    orientation=directions[0]; previous=directions[0]; side=0.
    from_angle=math.atan2(orientation[1],orientation[0]); to_angle=from_angle
    elapsed=model.recovery_mm
    result=[]
    for i,h in enumerate(holder):
        t=directions[i]
        if i:
            ds=length(minus(h,holder[i-1]))
            angle=math.atan2(t[1],t[0])
            prev_angle=math.atan2(previous[1],previous[0])
            change=math.atan2(math.sin(angle-prev_angle),math.cos(angle-prev_angle))
            if abs(change)>0.035 and elapsed>=model.recovery_mm:
                from_angle=math.atan2(orientation[1],orientation[0]); to_angle=angle
                elapsed=0.
                side=1. if change>0 else -1.
            elif elapsed<model.recovery_mm:
                to_angle=angle
            elapsed=min(model.recovery_mm,elapsed+ds)
            difference=math.atan2(math.sin(to_angle-from_angle),math.cos(to_angle-from_angle))
            gain=math.hypot(t[0]*model.x_rotation,t[1]*model.y_rotation)
            w=smooth(min(1.,elapsed*gain/model.recovery_mm))
            theta=from_angle+w*difference
            orientation=(math.cos(theta),math.sin(theta))
            previous=t
        bias=side*(model.min_approach_x_mm*abs(t[0])+model.min_approach_y_mm*abs(t[1]))
        result.append(plus(minus(h,scale(orientation,model.blade_offset_mm)),scale(normal(t),bias)))
    return result

def inverse(points,model,closed=False):
    """Regularized inverse fit of a sampled holder path to the intended cut.

    Vertex points receive additional weight. Smoothing discourages jagged holder
    corrections that would trigger spurious simulated turns. This solver cannot
    guarantee perfect corners and is not approved for production cuts.
    """
    pts=[tuple(map(float,p)) for p in points]
    if len(pts)<2: raise ValueError('Need at least two points')
    if closed:
        if length(minus(pts[0],pts[-1]))>1e-6: raise ValueError('Not closed')
        incoming=unit(minus(pts[0],pts[-2]))
        # Do not invent an off-contour lead for closed paths. Retrace the last
        # edge for conditioning when long enough; otherwise start on-contour.
        last_len=length(minus(pts[0],pts[-2]))
        lead=minus(pts[0],scale(incoming,min(model.conditioning_mm,last_len)))
    else:
        lead=minus(pts[0],scale(unit(minus(pts[1],pts[0])),model.conditioning_mm))
    target=sample([lead,*pts],model.step_mm)
    # Pin each original vertex, including both sides of a closed seam.
    vertex_indices=set()
    for v in pts:
        idx=min(range(len(target)),key=lambda i:length(minus(target[i],v)))
        vertex_indices.add(idx)
    holder=list(target)
    for _ in range(model.iterations):
        predicted=forward(holder,model)
        corrections=[]
        for i,(p,t) in enumerate(zip(predicted,target)):
            if i==0: corrections.append((0.,0.)); continue
            weight=model.vertex_weight if i in vertex_indices else 1.
            corrections.append(scale(minus(t,p),min(.9,.48+.11*weight)))
        revised=[]
        for i,(h,t) in enumerate(zip(holder,target)):
            if i==0: revised.append(h); continue
            c=corrections[i]
            if i not in vertex_indices and 0<i<len(holder)-1:
                c=plus(scale(c,.72),scale(plus(corrections[i-1],corrections[i+1]),.14))
            candidate=plus(h,c)
            excursion=minus(candidate,t)
            if length(excursion)>model.max_correction_mm:
                candidate=plus(t,scale(unit(excursion),model.max_correction_mm))
            revised.append(candidate)
        holder=revised
    if any(not all(math.isfinite(v) for v in p) for p in holder): raise ValueError('Nonfinite output')
    if max(length(minus(a,b)) for a,b in zip(holder,holder[1:]))>model.step_mm+2*model.max_correction_mm:
        raise ValueError('Discontinuous holder trajectory')
    return holder
