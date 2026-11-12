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
    iterations: int=5
    def __post_init__(self):
        for v in vars(self).values():
            if not math.isfinite(v): raise ValueError('Nonfinite model parameter')
        if not (.2<=self.recovery_mm<=5 and 0<=self.blade_offset_mm<=1 and
                .2<=self.x_rotation<=3 and .2<=self.y_rotation<=3 and
                0<=self.min_approach_x_mm<=.4 and 0<=self.min_approach_y_mm<=.4 and
                0<=self.conditioning_mm<=8 and .05<=self.step_mm<=.5 and
                0<self.max_correction_mm<=1.5 and 1<=self.iterations<=15):
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

def forward(holder,model):
    """Predict tip positions at each holder sample, with finite recovery.

    Orientation moves toward travel direction with X/Y dependent response.
    Lateral residual is held with turn-sign memory. The transition completes
    exactly after recovery_mm of travel (no asymptotic tail).
    """
    if len(holder)<2: raise ValueError('Need two holder positions')
    tangents=[unit(minus(b,a)) for a,b in zip(holder,holder[1:])]
    t=tangents[0]; previous=t; orientation=t; side=0.; elapsed=model.recovery_mm
    from_orientation=t; to_orientation=t; result=[]
    for i,h in enumerate(holder):
        if i:
            t=tangents[i-1]
            delta=length(minus(h,holder[i-1]))
            turn=cross(previous,t)
            if abs(turn)>0.015:
                side=1. if turn>0 else -1.
                from_orientation=orientation
                to_orientation=t
                elapsed=0.
            elapsed=min(model.recovery_mm,elapsed+delta)
            w=smooth(elapsed/model.recovery_mm)
            # Anisotropic rotation responsiveness, normalized for unit length.
            weighted=unit((to_orientation[0]*model.x_rotation,to_orientation[1]*model.y_rotation))
            base=unit((from_orientation[0]*model.x_rotation,from_orientation[1]*model.y_rotation))
            orientation=unit(mix(base,weighted,w))
            previous=t
        # Remove trailing offset from holder: steady tip is behind holder.
        # Lateral bias retains signed side from the last actual turn.
        bias=(model.min_approach_x_mm*abs(t[0])+model.min_approach_y_mm*abs(t[1]))*side
        tip=plus(minus(h,scale(orientation,model.blade_offset_mm)),scale(normal(t),bias))
        result.append(tip)
    return result

def inverse(points,model,closed=False):
    """Iterative sampled inverse: shift holder until simulated tip tracks target.

    For closed contours, starts on the last edge (on-contour conditioning).
    For open contours, adds an off-contour lead-in; use sacrificial material.
    All output is experimental and must be dry-run before cutting.
    """
    pts=[tuple(map(float,p)) for p in points]
    if closed:
        if length(minus(pts[0],pts[-1]))>1e-6: raise ValueError('Not closed')
        incoming=unit(minus(pts[0],pts[-2]))
        if length(minus(pts[0],pts[-2])) < model.conditioning_mm+model.recovery_mm:
            # Smooth closed curves have tiny edges: don't extend a tangent
            # off-contour. Start on contour without a conditioning lead.
            lead=pts[0]
        else:
            lead=minus(pts[0],scale(incoming,model.conditioning_mm))
    else:
        lead=minus(pts[0],scale(unit(minus(pts[1],pts[0])),model.conditioning_mm))
    target=sample([lead,*pts],model.step_mm)
    # Allow a trailing offset without altering conditioning start: converge to
    # target after the conditioning run, while holding first point fixed.
    holder=list(target)
    for _ in range(model.iterations):
        predicted=forward(holder,model)
        revised=[]
        for i,(h,p,t) in enumerate(zip(holder,predicted,target)):
            if i==0: revised.append(h); continue
            delta=minus(t,p)
            candidate=plus(h,scale(delta,.72))
            excursion=minus(candidate,t)
            if length(excursion)>model.max_correction_mm:
                candidate=plus(t,scale(unit(excursion),model.max_correction_mm))
            revised.append(candidate)
        holder=revised
    # Reject extreme commanded segment jumps or nonfinite values.
    if any(not all(math.isfinite(v) for v in p) for p in holder): raise ValueError('Nonfinite output')
    if max(length(minus(a,b)) for a,b in zip(holder,holder[1:]))>model.step_mm+2*model.max_correction_mm:
        raise ValueError('Discontinuous holder trajectory')
    return holder
