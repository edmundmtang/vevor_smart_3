"""v0.32 OFFLINE candidate: composable corner overshoot + finite recovery.

Input holder is produced by unchanged v0.30 stateful inverse (including Y history).
This module is geometry-only and does not alter the predictor or USB transport.
"""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class Transition:
    overshoot_mm: float = 0.10
    approach_mm: float = 0.50
    recovery_mm: float = 1.50
    easing: str = 'quintic'
    min_turn_deg: float = 30.0


def ease(t, kind):
    t = max(0., min(1., t))
    if kind == 'cubic': return t*t*(3-2*t)
    if kind == 'quintic': return t*t*t*(10+t*(-15+6*t))
    if kind == 'linear': return t
    raise ValueError('unknown easing')


def transition_holder(holder, target, config=Transition()):
    """Locally displace the v0.30 holder forward along incoming tangent.

    A smooth approach grows the overshoot; a smooth recovery removes it after
    the nearest apex sample. This is a *candidate*, not a kinematic guarantee
    that the tip reaches the corner. Never changes target or Y-history state.
    """
    vals=(config.overshoot_mm,config.approach_mm,config.recovery_mm,config.min_turn_deg)
    if any(not math.isfinite(v) for v in vals) or not 0<=vals[0]<=0.3 or not .2<=vals[1]<=4 or not .2<=vals[2]<=4 or not 15<=vals[3]<=150:
        raise ValueError('invalid transition parameters')
    ease(.5,config.easing)
    h=[tuple(map(float,p)) for p in holder]
    p=[tuple(map(float,q)) for q in target]
    if len(h)<2 or len(p)<2 or any(len(q)!=2 or not all(map(math.isfinite,q)) for q in h+p):
        raise ValueError('invalid points')
    if config.overshoot_mm==0: return h
    arc=[0.]
    for a,b in zip(h,h[1:]): arc.append(arc[-1]+math.dist(a,b))
    out=list(h)
    previous=0
    for j in range(1,len(p)-1):
        va=(p[j][0]-p[j-1][0],p[j][1]-p[j-1][1]); vb=(p[j+1][0]-p[j][0],p[j+1][1]-p[j][1])
        na=math.hypot(*va); nb=math.hypot(*vb)
        if min(na,nb)<2*max(config.approach_mm,config.recovery_mm): continue
        a=(va[0]/na,va[1]/na); b=(vb[0]/nb,vb[1]/nb)
        angle=abs(math.degrees(math.atan2(a[0]*b[1]-a[1]*b[0],a[0]*b[0]+a[1]*b[1])))
        if angle<config.min_turn_deg: continue
        idx=min(range(previous,len(h)),key=lambda k: math.dist(h[k],p[j])); previous=idx
        if idx==0 or idx==len(h)-1: continue
        for k in range(1,len(h)-1):
            ds=arc[k]-arc[idx]
            if -config.approach_mm<ds<=0:
                w=ease(1+ds/config.approach_mm,config.easing)
            elif 0<ds<config.recovery_mm:
                w=1-ease(ds/config.recovery_mm,config.easing)
            else: continue
            out[k]=(out[k][0]+a[0]*config.overshoot_mm*w,
                    out[k][1]+a[1]*config.overshoot_mm*w)
    if any(not all(map(math.isfinite,q)) for q in out): raise ValueError('nonfinite output')
    return out
