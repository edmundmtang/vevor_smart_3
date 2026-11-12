"""Single-sheet, nine-cell mirrored-L force/speed experiment for Smart 3.

Experimental: firmware acceptance of mid-job FS/VS commands is unverified.
Requires the existing smart3_cut.py and smart3_usb_probe.py beside this file.
"""
from __future__ import annotations
import argparse
import csv
import math
import sys
from pathlib import Path
from smart3_cut import (load_settings, check_mat_limits, get_physical_bounds,
                        send_live_job, UNITS_PER_MM)

FORCES = (150, 175, 200)
SPEEDS = (50, 75, 100)
# Compact test, 3 columns x 3 rows, mm from cutter's selected origin.
# Each pair uses two separate 3-vertex open paths. Their main edges coincide.
PITCH_X, PITCH_Y = 35.0, 27.0
START_X, START_Y = 14.0, 13.0
APPROACH, MAIN = 6.0, 16.0


def paths_at(cx, cy):
    # Opposite 90-degree turns, same +X travel on coincident horizontal main lines.
    return [[(cx,cy-APPROACH),(cx,cy),(cx+MAIN,cy)],
            [(cx,cy+APPROACH),(cx,cy),(cx+MAIN,cy)]]


def build(settings):
    header = ['SP1;'] if settings['preserve_origin'] else ['IN;', 'SP1;']
    commands = list(header)
    outlines, records = [], []
    for ri, force in enumerate(FORCES):
        for ci, speed in enumerate(SPEEDS):
            cx, cy = START_X+ci*PITCH_X, START_Y+ri*PITCH_Y
            paths = paths_at(cx,cy)
            outlines.extend(paths)
            # PU ensures pen is lifted before changing parameters.
            commands.extend(['PU;', f'FS{force};', f'VS{speed};'])
            for path in paths:
                pts = []
                for x,y in path:
                    tx = x*settings['x_scale']+settings['x_offset']
                    ty = y*settings['y_scale']+settings['y_offset']
                    if not (math.isfinite(tx) and math.isfinite(ty)) or tx < 0 or ty < 0:
                        raise ValueError('Invalid corrected geometry')
                    pt = (round(tx*UNITS_PER_MM),round(ty*UNITS_PER_MM))
                    if not pts or pt != pts[-1]: pts.append(pt)
                if len(pts) != 3:
                    raise ValueError('Calibration segment collapsed after coordinate rounding')
                commands.append(f'PU{pts[0][0]},{pts[0][1]};')
                commands.extend(f'PD{x},{y};' for x,y in pts[1:])
            records.append((f'R{ri+1}C{ci+1}',force,speed,cx,cy))
    commands.extend(['PU;'] if settings['finish_mode']=='minimal' else ['PU0,0;','SP2;','PG;'])
    return '\n'.join(commands)+'\n', outlines, records


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dry-run',action='store_true',help='Generate only (default behavior)')
    p.add_argument('--cut',action='store_true',help='Send experimental single USB job')
    p.add_argument('--confirm-live-test',default='')
    p.add_argument('--output',type=Path,default=Path('force_speed_grid.hpgl'))
    p.add_argument('--manifest',type=Path,default=Path('force_speed_grid_measurements.csv'))
    args=p.parse_args()
    if args.cut and args.dry_run: p.error('Choose either --dry-run or --cut')
    if args.cut and args.confirm_live_test!='I_ACCEPT_MOVEMENT':
        p.error('LIVE CUT BLOCKED: use --confirm-live-test I_ACCEPT_MOVEMENT')
    if args.cut and sys.platform!='win32': p.error('Live USB cutting requires Windows')
    settings=load_settings()
    hpgl, outlines, records=build(settings)
    physical=get_physical_bounds(outlines)
    corrected=[min(x*settings['x_scale']+settings['x_offset'] for path in outlines for x,y in path),
               min(y*settings['y_scale']+settings['y_offset'] for path in outlines for x,y in path),
               max(x*settings['x_scale']+settings['x_offset'] for path in outlines for x,y in path),
               max(y*settings['y_scale']+settings['y_offset'] for path in outlines for x,y in path)]
    check_mat_limits(physical, corrected, settings)
    args.output.write_text(hpgl,encoding='ascii')
    with args.manifest.open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f)
        writer.writerow(['cell','force','speed','corner_x_mm','main_y_mm','nominal_gap_mm','measured_settled_gap_mm','corner_recovery_mm','notes'])
        for cell,force,speed,x,y in records:
            writer.writerow([cell,force,speed,x,y,0,'','',''])
    print('Nine-cell mirrored-L grid: rows force 150/175/200, columns speed 50/75/100')
    print('Each cell: two 3-vertex cuts, 0 mm nominal gap, 6 mm approaches, 16 mm main lines')
    print(f'Physical bounds: X {physical[0]:.2f}..{physical[2]:.2f} mm; Y {physical[1]:.2f}..{physical[3]:.2f} mm')
    print(f'Corrected bounds: X {corrected[0]:.2f}..{corrected[2]:.2f} mm; Y {corrected[1]:.2f}..{corrected[3]:.2f} mm')
    print(f'HPGL: {args.output.resolve()} | Measurement sheet: {args.manifest.resolve()}')
    print('WARNING: Mid-job FS/VS changes are NOT validated on this cutter. Verify by observing the job.')
    if args.cut:
        print('WARNING: Experimental USB write; device may move unexpectedly; no ACK or execution guarantee.',flush=True)
        sent=send_live_job(hpgl,corrected,settings['preserve_origin'],settings['finish_mode'],FORCES[0],SPEEDS[0])
        print(f'USB write completed: {sent} bytes; this does NOT confirm execution.')
    else:
        print('NO CUT SENT: dry-run output only.')

if __name__=='__main__':
    main()
