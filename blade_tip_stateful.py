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
    # Optional outward target excursion at true polygon vertices (default off).
    corner_apex_mm: float=0.0
    # Optional bounded continuous Y-history correction; disabled by default.
    # Negative magnitudes down to -0.40 are allowed ONLY for the v0.27 offline sweep.
    y_history_mm: float=0.0
    history_recovery_mm: float=1.39
    # Experimental: isolate signed history from inverse holder excursions.
    isolate_history: bool=False
    # Finite-support taper of apex excursion along adjacent legs.
    apex_taper_mm: float=0.0
    def __post_init__(self):
        for v in vars(self).values():
            if not isinstance(v,bool) and not math.isfinite(v): raise ValueError('Nonfinite model parameter')
        if not (.2<=self.recovery_mm<=5 and 0<=self.blade_offset_mm<=1 and
                .2<=self.x_rotation<=3 and .2<=self.y_rotation<=3 and
                0<=self.min_approach_x_mm<=.4 and 0<=self.min_approach_y_mm<=.4 and
                0<=self.conditioning_mm<=8 and .05<=self.step_mm<=.5 and
                0<self.max_correction_mm<=1.5 and 0<=self.corner_extra_mm<=0.5 and 0<=self.corner_apex_mm<=0.30 and 0<=self.apex_taper_mm<=1.0 and -.40<=self.y_history_mm<=.25 and .2<=self.history_recovery_mm<=5 and 1<=self.iterations<=25 and 1<=self.vertex_weight<=5):
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

def forward(holder, model, history_reference=None):
    """Stateful phenomenological predictor, with finite turn response and held bias.

    Uses an angular interpolation (safe for reversals) and a spatially averaged
    holder tangent. This is a predictive hypothesis, not a measured blade model.
    """
    if len(holder)<2: raise ValueError('Need two holder positions')
    if history_reference is not None and len(history_reference)!=len(holder):
        raise ValueError('History reference must match holder sampling')
    directions=[_direction_at(holder,i) for i in range(len(holder))]
    orientation=directions[0]; previous=directions[0]; side=0.
    from_angle=math.atan2(orientation[1],orientation[0]); to_angle=from_angle
    elapsed=model.recovery_mm
    result=[]
    y_state=0.0
    history_path=holder if history_reference is None else history_reference
    history_directions=directions if history_reference is None else [_direction_at(history_path,i) for i in range(len(holder))]
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
        tip=plus(minus(h,scale(orientation,model.blade_offset_mm)),scale(normal(t),bias))
        # A continuous signed memory, driven by actual Y displacement rather
        # than tangent noise. It holds on horizontal segments and is bounded.
        # Disabled by default because v0.23's full Y-history correction failed.
        if i and model.y_history_mm:
            # Integrate the *signed physical Y travel*, not the noisy tangent
            # direction. Hold the state when Y travel stops. Unlike a binary
            # sign flip, this response is continuous across reversals.
            dy=history_path[i][1]-history_path[i-1][1]
            if abs(dy)>1e-10:
                y_state=max(-1.,min(1.,y_state+dy/model.history_recovery_mm))
            # Restrict the added lateral error to nearly horizontal motion.
            # Smooth gating avoids abrupt transitions at curved/star vertices.
            horizontal=smooth(max(0.,(abs(history_directions[i][0])-.65)/.35))
            tip=(tip[0],tip[1]+model.y_history_mm*y_state*horizontal)
        result.append(tip)
    return result

def apex_targets(points, amount_mm, closed=False, taper_mm=0.0):
    """Optional finite vertex extension along the exterior angle bisector.

    Only genuine turns >=30 degrees are modified. A straight run, endpoints,
    and an open path's initial/terminal position are unchanged. This changes
    the inverse solver's target near a vertex, NOT the global scale.
    """
    pts=[tuple(map(float,p)) for p in points]
    if not amount_mm: return pts
    if len(pts)<3: return pts
    if closed and length(minus(pts[0],pts[-1]))>1e-6:
        raise ValueError('Closed apex target requires matching endpoints')
    count=len(pts)-1 if closed else len(pts)
    out=list(pts)
    indices=range(count) if closed else range(1,count-1)
    for j in indices:
        prev=pts[(j-1)%count]
        nxt=pts[(j+1)%count]
        a=minus(pts[j],prev)
        b=minus(nxt,pts[j])
        if min(length(a),length(b))<1e-7: continue
        incoming=unit(a); outgoing=unit(b)
        angle=abs(math.atan2(cross(incoming,outgoing),
                             incoming[0]*outgoing[0]+incoming[1]*outgoing[1]))
        if angle<math.radians(30): continue
        # Extension follows the vector from the interior of the V to its apex.
        bisector=minus(incoming,outgoing)
        if length(bisector)<1e-7: continue
        # Avoid excessive excursions on tiny segments.
        extent=min(amount_mm,0.15*length(a),0.15*length(b))
        out[j]=plus(pts[j],scale(unit(bisector),extent))
    if closed: out[-1]=out[0]
    return out

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
    fitted_pts=apex_targets(pts,model.corner_apex_mm,closed=closed)
    target=sample([lead,*fitted_pts],model.step_mm)
    # The unmodified intended path supplies history during inverse optimization.
    # Match the same sample count using arc-length parameterization rather than
    # introducing artificial Y motion from an extended corner apex.
    def resample_to_count(polyline, count):
        cumulative=[0.]
        for a,b in zip(polyline,polyline[1:]):
            cumulative.append(cumulative[-1]+length(minus(b,a)))
        total=cumulative[-1]
        if total<=1e-9: raise ValueError("Degenerate history reference")
        result=[]; j=0
        for i in range(count):
            at=total*i/(count-1)
            while j<len(cumulative)-2 and cumulative[j+1]<at: j+=1
            fraction=(at-cumulative[j])/max(1e-12,cumulative[j+1]-cumulative[j])
            result.append(mix(polyline[j],polyline[j+1],fraction))
        return result
    history_reference=resample_to_count([lead,*pts],len(target)) if model.isolate_history else None
    # Localize apex displacement with a finite-support taper on both legs.
    # The target is smoothly deformed near vertices instead of introducing a
    # single sharp excursion, which can cause a flap on the outgoing leg.
    if model.apex_taper_mm and model.corner_apex_mm:
        base=resample_to_count([lead,*pts],len(target))
        target=list(base)
        for j in range(1,len(pts)-(1 if closed else 1)):
            if j>=len(fitted_pts): continue
            delta=minus(fitted_pts[j],pts[j])
            if length(delta)<1e-9: continue
            idx=min(range(len(base)),key=lambda i:length(minus(base[i],pts[j])))
            distances=[0.]*len(base)
            for k in range(idx-1,-1,-1): distances[k]=distances[k+1]+length(minus(base[k+1],base[k]))
            for k in range(idx+1,len(base)): distances[k]=distances[k-1]+length(minus(base[k],base[k-1]))
            for k,d in enumerate(distances):
                if d<model.apex_taper_mm:
                    # smooth peak at vertex, zero at taper boundary
                    weight=1.-smooth(d/model.apex_taper_mm)
                    target[k]=plus(target[k],scale(delta,weight))

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
    # Keep the best predicted fit, never blindly accept the final iteration.
    def fit(path):
        predicted=forward(path,model,history_reference=history_reference)
        return sum(length(minus(p,t))**2 for p,t in zip(predicted,target))/len(target)
    best_holder=list(holder)
    best_error=fit(holder)
    for _ in range(model.iterations):
        predicted=forward(holder,model,history_reference=history_reference)
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
        err=fit(holder)
        if err<best_error:
            best_error=err
            best_holder=list(holder)
    holder=best_holder
    if any(not all(math.isfinite(v) for v in p) for p in holder): raise ValueError('Nonfinite output')
    if max(length(minus(a,b)) for a,b in zip(holder,holder[1:]))>model.step_mm+2*(model.max_correction_mm+model.corner_extra_mm):
        raise ValueError('Discontinuous holder trajectory')
    return holder
