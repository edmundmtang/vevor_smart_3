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
    vertex_weight: float=3.0
    corner_extra_mm: float=0.10
    y_history_gain: float=1.0
    x_history_gain: float=0.0
    def __post_init__(self):
        for v in vars(self).values():
            if not math.isfinite(v): raise ValueError('Nonfinite model parameter')
        if not (.2<=self.recovery_mm<=5 and 0<=self.blade_offset_mm<=1 and
                .2<=self.x_rotation<=3 and .2<=self.y_rotation<=3 and
                0<=self.min_approach_x_mm<=.4 and 0<=self.min_approach_y_mm<=.4 and
                0<=self.conditioning_mm<=8 and .05<=self.step_mm<=.5 and
                0<self.max_correction_mm<=1.5 and 0<=self.corner_extra_mm<=0.5 and 0<=self.y_history_gain<=3 and 0<=self.x_history_gain<=3 and 1<=self.iterations<=25 and 1<=self.vertex_weight<=5):
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
    """Predict tip from holder using rotation plus persistent approach memory.

    The Y memory is the signed direction of the last substantial Y travel. It
    persists on horizontal runs, instead of decaying to zero with travel length.
    The perpendicular residual is applied only when moving near-horizontal:
    this is an explicit empirical hypothesis, not a machine calibration.
    """
    if len(holder)<2: raise ValueError('Need two holder positions')
    directions=[_direction_at(holder,i) for i in range(len(holder))]
    orientation=directions[0]
    previous=directions[0]
    from_angle=math.atan2(orientation[1],orientation[0])
    to_angle=from_angle
    elapsed=model.recovery_mm
    # Conditioned initial approach: incoming Y sign is known from lead segment.
    y_memory=0.0
    x_memory=0.0
    result=[]
    for i,h in enumerate(holder):
        t=directions[i]
        ds=0.0
        if i:
            ds=length(minus(h,holder[i-1]))
            angle=math.atan2(t[1],t[0])
            prev_angle=math.atan2(previous[1],previous[0])
            change=math.atan2(math.sin(angle-prev_angle),math.cos(angle-prev_angle))
            if abs(change)>0.035 and elapsed>=model.recovery_mm:
                from_angle=math.atan2(orientation[1],orientation[0])
                to_angle=angle
                elapsed=0.
            elif elapsed<model.recovery_mm:
                to_angle=angle
            elapsed=min(model.recovery_mm,elapsed+ds)
            difference=math.atan2(math.sin(to_angle-from_angle),math.cos(to_angle-from_angle))
            gain=math.hypot(t[0]*model.x_rotation,t[1]*model.y_rotation)
            w=smooth(min(1.,elapsed*gain/model.recovery_mm))
            theta=from_angle+w*difference
            orientation=(math.cos(theta),math.sin(theta))
            previous=t
        # A meaningful Y excursion sets the signed approach memory. The memory
        # is retained on horizontal travel (no artificial asymptotic decay).
        # Blend only during active axis movement; avoid responding to tiny
        # numerical deviations introduced by the inverse solver.
        if abs(t[1])>.25:
            y_memory=mix((y_memory,0.),(math.copysign(1.,t[1]),0.),min(1.,abs(t[1])*ds/max(.1,model.recovery_mm)))[0]
        if abs(t[0])>.25:
            x_memory=mix((x_memory,0.),(math.copysign(1.,t[0]),0.),min(1.,abs(t[0])*ds/max(.1,model.recovery_mm)))[0]
        # Signed Y residual on X motion, and X residual on Y motion.
        # Directional weights vanish on the other axis. Both are tunable.
        residual=(model.min_approach_y_mm*model.y_history_gain*y_memory*abs(t[0]),
                  model.min_approach_x_mm*model.x_history_gain*x_memory*abs(t[1]))
        # residual tuple above denotes (Y displacement, X displacement)
        tip=minus(h,scale(orientation,model.blade_offset_mm))
        tip=(tip[0]+residual[1],tip[1]+residual[0])
        result.append(tip)
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
    vertex_angles={}
    for j,v in enumerate(pts):
        idx=min(range(len(target)),key=lambda i:length(minus(target[i],v)))
        vertex_indices.add(idx)
        if 0<j<len(pts)-1:
            a=minus(pts[j],pts[j-1]); b=minus(pts[j+1],pts[j])
            if length(a)>1e-8 and length(b)>1e-8:
                angle=abs(math.atan2(cross(unit(a),unit(b)),sum(x*y for x,y in zip(unit(a),unit(b)))))
                vertex_angles[idx]=max(vertex_angles.get(idx,0.),angle)
    # Increase permissible correction near genuine geometric corners only.
    # This is NOT a hard-coded corner orientation or a guaranteed physical correction.
    corner_caps=[model.max_correction_mm]*len(target)
    radius=max(model.recovery_mm,model.step_mm)
    for idx,angle in vertex_angles.items():
        if angle<math.radians(15): continue
        extra=model.corner_extra_mm*min(1.,angle/(math.pi/2))
        for k in range(max(0,idx-12),min(len(target),idx+13)):
            distance=length(minus(target[k],target[idx]))
            if distance<radius:
                corner_caps[k]=max(corner_caps[k],model.max_correction_mm+extra*(1-distance/radius))
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
            if length(excursion)>corner_caps[i]:
                candidate=plus(t,scale(unit(excursion),corner_caps[i]))
            revised.append(candidate)
        holder=revised
    if any(not all(math.isfinite(v) for v in p) for p in holder): raise ValueError('Nonfinite output')
    if max(length(minus(a,b)) for a,b in zip(holder,holder[1:]))>model.step_mm+2*(model.max_correction_mm+model.corner_extra_mm):
        raise ValueError('Discontinuous holder trajectory')
    return holder
