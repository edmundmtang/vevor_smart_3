"""Smart3 v1.0 release candidate: SVG -> compensated HPGL -> guarded USB."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'engine'))
from smart3_cut import parse_svg, load_settings, make_hpgl, check_mat_limits, get_physical_bounds
from blade_tip_clean import CleanConfig, compensate
from loop_closure import relocate, add_same_path_overlap
from corner_transition import Transition, transition_holder

VERSION = '1.0.0'
CONFIRM = 'I_ACCEPT_MOVEMENT'
DEFAULT_TRANSITION = Transition(overshoot_mm=.20, approach_mm=.50, recovery_mm=1.50, easing='quintic')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def build(svg):
    svg = Path(svg).resolve()
    if not svg.is_file() or svg.suffix.lower() != '.svg':
        raise ValueError('Expected an existing original SVG input file')
    source = svg.read_bytes()
    targets = parse_svg(svg)
    if not targets:
        raise ValueError('SVG has no cuttable contours')
    settings = load_settings(ROOT / 'engine' / 'settings.txt')
    paths = []
    for original in targets:
        target, _ = relocate(original, 'original')
        target, _ = add_same_path_overlap(target, 0.)
        closed = len(target)>2 and math.dist(target[0],target[-1])<1e-6
        baseline = compensate(target, CleanConfig(), closed=closed)
        holder = transition_holder(baseline, target, DEFAULT_TRANSITION)
        if len(holder) != len(baseline) or max(math.dist(a,b) for a,b in zip(holder,baseline)) > .200001:
            raise ValueError('Corner correction exceeded configured cap')
        paths.append(holder)
    hpgl, commands = make_hpgl(paths,settings)
    physical = get_physical_bounds(paths)
    check_mat_limits(physical, commands, settings)
    report = dict(version=VERSION, status='physically_tested_configuration_not_universally_validated',
                  source=str(svg), source_sha256=digest(source), hpgl_sha256=digest(hpgl.encode('ascii')),
                  settings=settings, baseline='v0.30 stateful inverse',
                  corner=dict(overshoot_mm=.20, approach_mm=.50, recovery_mm=1.50, easing='quintic'),
                  contours=len(paths), holder_bounds_mm=physical, command_bounds_mm=commands,
                  note='Original SVG input only. Do not double compensate generated holder paths.')
    return hpgl,report,targets,paths

def files(svg, output=None):
    stem=Path(output).resolve() if output else Path(svg).resolve().with_suffix('.hpgl')
    if stem.suffix.lower() != '.hpgl':
        raise ValueError('Output must have .hpgl extension')
    return stem,stem.with_suffix('.json')

def write(svg,output=None):
    hpgl,report,targets,paths=build(svg)
    hp,js=files(svg,output)
    hp.write_bytes(hpgl.encode('ascii'))
    js.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return hp,js,report,targets,paths

def verify(svg,output=None):
    hp,js=files(svg,output)
    if not hp.is_file() or not js.is_file():
        raise ValueError('Missing built HPGL/report; run build first')
    saved=json.loads(js.read_text(encoding='utf-8'))
    hpgl,report,targets,paths=build(svg)
    if saved!=report or hp.read_bytes()!=hpgl.encode('ascii'):
        raise ValueError('Job, source, settings or parameters differ from current build; NO CUT SENT')
    return hpgl,report,targets,paths

def preview(svg,targets,paths,output=None):
    import xml.sax.saxutils as xml
    bounds=get_physical_bounds([*targets,*paths]); x0,y0,x1,y1=bounds
    margin=2.; width=x1-x0+2*margin; height=y1-y0+2*margin
    def d(points):
        return 'M '+' '.join(('L ' if i else '')+f'{x:.5f},{y:.5f}' for i,(x,y) in enumerate(points))
    out=Path(output).resolve() if output else Path(svg).resolve().with_name(Path(svg).stem+'_holder_preview.svg')
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.4f}mm" height="{height:.4f}mm" viewBox="{x0-margin:.4f} {y0-margin:.4f} {width:.4f} {height:.4f}">',
           '<g fill="none" stroke="#999" stroke-width="0.08" stroke-dasharray="0.4 0.3">']
    lines += [f'<path d="{xml.escape(d(p))}"/>' for p in targets]
    lines += ['</g><g fill="none" stroke="#1765b3" stroke-width="0.10">']
    lines += [f'<path d="{xml.escape(d(p))}"/>' for p in paths]
    lines += ['</g></svg>']
    out.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return out

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['build','check','preview','cut','run'])
    p.add_argument('svg',type=Path,help='ORIGINAL uncompensated SVG (not holder-path SVG)')
    p.add_argument('--output',type=Path,help='HPGL output path')
    p.add_argument('--confirm-live-test',default='')
    a=p.parse_args(argv)
    try:
        if a.action in ('cut','run') and a.confirm_live_test != CONFIRM:
            raise ValueError('Live operation requires --confirm-live-test I_ACCEPT_MOVEMENT')
        if a.action in ('cut','run') and sys.platform != 'win32':
            raise ValueError('Live USB cutting is supported on Windows only')
        if a.action in ('build','run'):
            hp,js,report,targets,paths=write(a.svg,a.output)
            print('BUILT:',hp,'\nREPORT:',js)
        elif a.action=='preview':
            _,report,targets,paths=build(a.svg)
            print('PREVIEW:',preview(a.svg,targets,paths))
            print('NO CUT SENT')
            return 0
        if a.action in ('check','cut','run'):
            hpgl,report,targets,paths=verify(a.svg,a.output)
            print('PASS: source, HPGL, calibration and parameters match')
            if a.action in ('cut','run'):
                from smart3_cut import send_live_job
                s=report['settings']
                print('WARNING: live movement. Attend cutter and keep stop accessible.',flush=True)
                n=send_live_job(hpgl,report['command_bounds_mm'],s['preserve_origin'],s['finish_mode'],s['cut_force'],s['cut_speed'])
                print(f'USB write returned {n} bytes; physical execution is not confirmed')
        if a.action in ('build','check'):
            print(json.dumps({k:report[k] for k in ('version','contours','corner','holder_bounds_mm','command_bounds_mm')},indent=2))
        if a.action in ('build','check'):
            print('NO CUT SENT')
        return 0
    except (ValueError,OSError,TypeError,KeyError,ImportError,UnicodeError,json.JSONDecodeError) as e:
        p.exit(1,f'BLOCKED: {e}\n')

if __name__=='__main__':
    sys.exit(main())
