"""Guarded transmitter for an already-compensated v0.31 sweep.

Rebuilds the job from source and compares bytes before using the existing
v0.30 USB sender. No SVG-to-HPGL compensation is performed on the supplied file.
"""
import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

from build_sweep import build

ROOT = Path(__file__).resolve().parent
CONFIRMATION = 'I_ACCEPT_MOVEMENT'


def validate(project, hpgl_path):
    project = Path(project).resolve()
    hpgl_path = Path(hpgl_path).resolve()
    if not hpgl_path.is_file():
        raise ValueError(f'HPGL file missing: {hpgl_path}')
    report_path = hpgl_path.with_suffix('.json')
    if not report_path.is_file():
        raise ValueError('Matching JSON report is required; NO DATA SENT')
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('baseline') != 'v0.30' or report.get('hpgl') != hpgl_path.name:
        raise ValueError('Unexpected sweep report or HPGL filename; NO DATA SENT')
    reach = report.get('reach_mm_by_column')
    if not isinstance(reach, dict) or set(reach) != set('ABC'):
        raise ValueError('Invalid reach parameters; NO DATA SENT')
    values = [reach[k] for k in 'ABC']
    if any(type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= .3 for x in values):
        raise ValueError('Reach must be finite and within 0..0.30 mm; NO DATA SENT')
    support = report.get('support_mm')
    if type(support) not in (int, float) or not math.isfinite(support) or not .1 <= support <= 3.0:
        raise ValueError('Support must be finite and within 0.1..3 mm; NO DATA SENT')
    with tempfile.TemporaryDirectory() as td:
        rebuilt_path = Path(td) / hpgl_path.name
        rebuilt = build(project, rebuilt_path, values, support)
        if hpgl_path.read_bytes() != rebuilt_path.read_bytes():
            raise ValueError('HPGL differs from freshly rebuilt sweep; NO DATA SENT')
    if report != rebuilt:
        raise ValueError('Report differs from freshly rebuilt sweep (including calibration); NO DATA SENT')
    # Reject a renamed or noncanonical file path to avoid confusion with other jobs.
    if hpgl_path.name != 'corner_sweep_v031_EXPERIMENTAL.hpgl':
        raise ValueError('Unexpected HPGL filename; NO DATA SENT')
    return hpgl_path.read_text(encoding='ascii'), rebuilt


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', type=Path, required=True)
    p.add_argument('--hpgl-file', type=Path, default=ROOT/'corner_sweep_v031_EXPERIMENTAL.hpgl')
    p.add_argument('--cut', action='store_true', help='Send one experimental live USB job')
    p.add_argument('--confirm-live-test', default='')
    a = p.parse_args(argv)
    try:
        hpgl, report = validate(a.project, a.hpgl_file)
        print('Verified: HPGL and report match a fresh v0.31 rebuild using current v0.30 calibration.')
        print('Holder bounds (mm):', report['holder_bounds_mm'])
        print('Reach (mm):', report['reach_mm_by_column'])
        if not a.cut:
            print('NO CUT SENT: validation only. Add --cut and explicit confirmation for live motion.')
            return 0
        if a.confirm_live_test != CONFIRMATION:
            raise ValueError('LIVE CUT BLOCKED: --confirm-live-test I_ACCEPT_MOVEMENT required; NO DATA SENT')
        if sys.platform != 'win32':
            raise ValueError('LIVE CUT BLOCKED: Windows required; NO DATA SENT')
        sys.path.insert(0, str(a.project.resolve()))
        from smart3_cut import send_live_job
        s = report['settings']
        print('WARNING: experimental USB write, no execution acknowledgement. Keep clear of machine.', flush=True)
        count = send_live_job(hpgl, report['command_bounds_mm'], s['preserve_origin'],
                              s['finish_mode'], s['cut_force'], s['cut_speed'])
        print(f'USB write completed: {count} bytes (not proof of cutter execution)')
        return 0
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError, ImportError) as e:
        p.exit(1, f'Error: {e}\n')


if __name__ == '__main__':
    sys.exit(main())
