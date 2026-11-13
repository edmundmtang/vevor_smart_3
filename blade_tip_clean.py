"""v0.30 single-model experimental drag-knife compensation (offline-safe).

One forward predictor is used by the inverse solver and diagnostics. It has
one persistent lateral state; no extra approach bias, no target apex excursion,
no intended-path-driven pseudo-state, and no post-inverse geometric correction.

Not calibrated to physical cuts; the default mode is OFF in smart3_cut.py.
"""
from dataclasses import dataclass
from dataclasses import replace
import math
from blade_tip_stateful import Model, forward, inverse, sample, minus, length, unit, normal

@dataclass(frozen=True)
class CleanConfig:
    blade_offset_mm: float = .20
    rotation_recovery_mm: float = 1.39
    lateral_history_mm: float = -.300
    lateral_recovery_mm: float = 1.39
    sample_step_mm: float = .15
    correction_cap_mm: float = .85
    iterations: int = 12

    def model(self):
        # These parameters are disabled rather than counterbalanced.
        return Model(blade_offset_mm=self.blade_offset_mm,
                     recovery_mm=self.rotation_recovery_mm,
                     y_history_mm=self.lateral_history_mm,
                     history_recovery_mm=self.lateral_recovery_mm,
                     step_mm=self.sample_step_mm,
                     max_correction_mm=self.correction_cap_mm,
                     iterations=self.iterations,
                     min_approach_x_mm=0., min_approach_y_mm=0.,
                     corner_apex_mm=0., apex_taper_mm=0.,
                     corner_extra_mm=0., isolate_history=False)

def compensate(points, config=CleanConfig(), closed=False):
    """Return holder points, without changing the intended cut target.

    For closed paths the model retains the original seam behavior; no additional
    overlap, lead-out, or geometry scaling is applied.
    """
    pts=[tuple(map(float,p)) for p in points]
    if len(pts)<2 or any(not all(math.isfinite(v) for v in p) for p in pts):
        raise ValueError('Invalid contour')
    if closed and length(minus(pts[0],pts[-1]))>1e-6:
        raise ValueError('Closed contour must repeat its first point')
    m=config.model()
    result=inverse(pts,m,closed=closed)
    if any(not all(math.isfinite(v) for v in p) for p in result):
        raise ValueError('Nonfinite holder path')
    return result

def normal_residuals(holder, intended, config=CleanConfig()):
    """Signed normal error against the ORIGINAL target, for matching samples.

    The forward result is a *model prediction*, not a measured physical cut.
    """
    if len(holder)!=len(intended) or len(holder)<2:
        raise ValueError('Holder/target sample counts must match')
    tip=forward(holder,config.model())
    result=[]
    for i,(p,t) in enumerate(zip(tip,intended)):
        j=max(0,i-1); k=min(len(intended)-1,i+1)
        tangent=unit(minus(intended[k],intended[j]))
        n=normal(tangent)
        d=minus(p,t)
        result.append(d[0]*n[0]+d[1]*n[1])
    return result


def component_audit(config=CleanConfig()):
    """Human-readable list of the active and disabled correction channels."""
    m=config.model()
    return {
        'physical blade offset (mm)':m.blade_offset_mm,
        'orientation recovery (mm)':m.recovery_mm,
        'single signed Y history (mm)':m.y_history_mm,
        'history recovery (mm)':m.history_recovery_mm,
        'extra turn-direction bias (mm)':m.min_approach_x_mm+m.min_approach_y_mm,
        'artificial target apex extension (mm)':m.corner_apex_mm,
        'apex target taper (mm)':m.apex_taper_mm,
        'history based on intended rather than holder path':m.isolate_history,
        'independent outgoing normal shift (mm)':0.,
    }
