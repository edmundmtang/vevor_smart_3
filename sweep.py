"""v0.32 experimental sweep: offline builder and guarded live sender.

Original machine implementation lives in engine/ and is never modified here.
"""
import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / 'engine'
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))
from smart3_cut import (parse_svg, load_settings, make_hpgl, check_mat_limits,
                        get_physical_bounds)
from blade_tip_clean import compensate, CleanConfig
from blade_tip_stateful import forward
from loop_closure import relocate, add_same_path_overlap
from corner_transition_v032 import Transition, transition_holder

HPGL_NAME = 'corner_sweep_v032_EXPERIMENTAL.hpgl'
CONFIRM = 'I_ACCEPT_MOVEMENT'


def parameters(overshoot, approach, recovery, easing):
    if len(overshoot) != 3:
        raise ValueError('Exactly three column overshoots required')
    for x in overshoot:
        if type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= .3:
            raise ValueError('Overshoot outside 0..0.30 mm')
    cfgs = [Transition(float(x), approach, recovery, easing) for x in overshoot]
    # Validate even when all-zero control, so invalid options cannot be hidden.
    from corner_transition_v032 import ease
    for cfg in cfgs:
        if not (math.isfinite(cfg.approach_mm) and .2 <= cfg.approach_mm <= 4 and
                math.isfinite(cfg.recovery_mm) and .2 <= cfg.recovery_mm <= 4):
            raise ValueError('Invalid approach/recovery')
        ease(.5, cfg.easing)
    return cfgs


def build(overshoot=(0., .1, .2), approach=.5, recovery=1.5, easing='quintic'):
    cfgs = parameters(overshoot, approach, recovery, easing)
    outlines = parse_svg(ROOT / 'corner_sweep_target.svg')
    if len(outlines) != 15:
        raise ValueError('Unexpected target contour count')
    settings = load_settings(ENGINE / 'settings.txt')
    config = CleanConfig()
    paths = []
    diagnostics = []
    for i, original in enumerate(outlines):
        target, _ = relocate(original, 'original')
        target, _ = add_same_path_overlap(target, 0.)
        closed = len(target) > 2 and target[0] == target[-1]
        baseline = compensate(target, config, closed=closed)
        holder = transition_holder(baseline, target, cfgs[i//5])
        max_delta = max(math.dist(a, b) for a, b in zip(baseline, holder))
        if max_delta > cfgs[i//5].overshoot_mm + 1e-6:
            raise ValueError('Transition exceeds displacement cap')
        # The predictor retains the signed Y-history and orientation state.
        # These diagnostics are hypotheses, NOT evidence of physical accuracy.
        tip = forward(holder, config.model())
        baseline_tip = forward(baseline, config.model())
        predicted_change = max(math.dist(a, b) for a, b in zip(tip, baseline_tip))
        diagnostics.append({'contour':i, 'column':'ABC'[i//5],
                            'max_holder_delta_mm':round(max_delta, 6),
                            'max_predicted_tip_change_mm':round(predicted_change, 6)})
        paths.append(holder)
    hpgl, command_bounds = make_hpgl(paths, settings)
    physical_bounds = get_physical_bounds(paths)
    check_mat_limits(physical_bounds, command_bounds, settings)
    report = {'status':'experimental_unvalidated_physical_cut',
              'version':'v0.32', 'baseline':'v0.30 predictor and calibration unchanged',
              'overshoot_mm_by_column':dict(zip('ABC', [c.overshoot_mm for c in cfgs])),
              'approach_mm':approach, 'recovery_mm':recovery, 'easing':easing,
              'contours':len(paths), 'holder_bounds_mm':physical_bounds,
              'command_bounds_mm':command_bounds, 'settings':settings,
              'diagnostics':diagnostics, 'hpgl':HPGL_NAME}
    return hpgl, report


def write_job(hpgl, report):
    (ROOT / HPGL_NAME).write_bytes(hpgl.encode('ascii'))
    (ROOT / HPGL_NAME.replace('.hpgl','.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


def validate():
    hpgl_file = ROOT / HPGL_NAME
    report_file = hpgl_file.with_suffix('.json')
    if not hpgl_file.is_file() or not report_file.is_file():
        raise ValueError('Missing generated HPGL or report; run build first')
    saved = json.loads(report_file.read_text(encoding='utf-8'))
    if saved.get('version') != 'v0.32' or saved.get('hpgl') != HPGL_NAME:
        raise ValueError('Unexpected report version or file name')
    overshoots = saved.get('overshoot_mm_by_column')
    if not isinstance(overshoots,dict) or set(overshoots) != set('ABC'):
        raise ValueError('Invalid sweep columns')
    hpgl, report = build(tuple(overshoots[k] for k in 'ABC'),
                         saved.get('approach_mm'),saved.get('recovery_mm'),saved.get('easing'))
    if saved != report or hpgl_file.read_bytes() != hpgl.encode('ascii'):
        raise ValueError('Generated job or calibration has changed; NO CUT SENT')
    return hpgl, report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['build','check','cut'])
    p.add_argument('--overshoot',nargs=3,type=float,default=[0,.1,.2])
    p.add_argument('--approach-mm',type=float,default=.5)
    p.add_argument('--recovery-mm',type=float,default=1.5)
    p.add_argument('--easing',choices=['linear','cubic','quintic'],default='quintic')
    p.add_argument('--confirm-live-test',default='')
    a=p.parse_args(argv)
    try:
        if a.action == 'build':
            hpgl, report = build(a.overshoot,a.approach_mm,a.recovery_mm,a.easing)
            write_job(hpgl,report)
            print('Built offline experimental job:',ROOT / HPGL_NAME)
        else:
            hpgl,report=validate()
            print('PASS: regenerated HPGL and report match current calibration and parameters')
            if a.action == 'cut':
                if a.confirm_live_test != CONFIRM:
                    raise ValueError('Live cut requires --confirm-live-test I_ACCEPT_MOVEMENT')
                if sys.platform != 'win32':
                    raise ValueError('Live cut only supported on Windows')
                from smart3_cut import send_live_job
                s=report['settings']
                print('WARNING: experimental physical movement. Attend cutter; stop accessible.',flush=True)
                n=send_live_job(hpgl,report['command_bounds_mm'],s['preserve_origin'],
                                s['finish_mode'],s['cut_force'],s['cut_speed'])
                print(f'USB write returned {n} bytes; this does not confirm execution')
        if a.action != 'cut':
            print(json.dumps({k:report[k] for k in ('version','overshoot_mm_by_column','holder_bounds_mm','command_bounds_mm','contours')},indent=2))
            print('NO CUT SENT')
        return 0
    except (ValueError, OSError, UnicodeError, ImportError, TypeError, KeyError, json.JSONDecodeError) as e:
        p.exit(1,f'BLOCKED: {e}\n')

if __name__ == '__main__':
    sys.exit(main())
