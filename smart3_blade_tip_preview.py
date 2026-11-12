"""Generate an offline SVG preview of desired/conditioned/predicted/candidate paths.

No HPGL output, USB access, or live cutting code is reachable from this CLI.
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from blade_tip_model import Parameters, clean, conditioning, predict, steady_compensation_candidate, bounds
from smart3_cut import parse_svg


def write_preview(destination, original, conditioned, predicted, candidate):
    paths=[*original,*conditioned,*predicted,*candidate]
    x0,y0,x1,y1=bounds(paths)
    margin=4
    root=ET.Element('svg',{'xmlns':'http://www.w3.org/2000/svg',
        'width':f'{x1-x0+2*margin:.4f}mm','height':f'{y1-y0+2*margin:.4f}mm',
        'viewBox':f'{x0-margin:.4f} {y0-margin:.4f} {x1-x0+2*margin:.4f} {y1-y0+2*margin:.4f}'})
    for group,color,style in ((original,'#222222','4 2'),(conditioned,'#1e78d2','none'),
                              (predicted,'#df6a19','none'),(candidate,'#9a4bba','3 2')):
        for points in group:
            ET.SubElement(root,'polyline',{'points':' '.join(f'{x:.5f},{y:.5f}' for x,y in points),
                'fill':'none','stroke':color,'stroke-width':'0.16',
                'stroke-dasharray':style,'stroke-linecap':'round','stroke-linejoin':'round'})
    ET.ElementTree(root).write(destination,encoding='utf-8',xml_declaration=True)


def main():
    p=argparse.ArgumentParser(description='v0.18 blade-tip OFFLINE diagnostic SVG (NO USB / NO HPGL)')
    p.add_argument('svg',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--recovery-mm',type=float,default=1.40)
    p.add_argument('--steady-gap-mm',type=float,default=0.19,
                   help='Measured relative mirrored-L gap, NOT an absolute correction')
    p.add_argument('--signed-bias-mm',type=float,default=0.0,
                   help='UNMEASURED hypothetical signed tip bias; defaults to zero')
    p.add_argument('--conditioning-mm',type=float,default=3.0)
    p.add_argument('--sample-step-mm',type=float,default=0.10)
    p.add_argument('--allow-off-contour-conditioning',action='store_true',
                   help='Explicitly allow lead-in in diagnostic preview (NOT for live cutting)')
    a=p.parse_args()
    try:
        params=Parameters(a.recovery_mm,a.steady_gap_mm,a.signed_bias_mm,
                          a.conditioning_mm,a.sample_step_mm)
        if params.conditioning_mm and not a.allow_off_contour_conditioning:
            p.error('Off-contour lead-in requires --allow-off-contour-conditioning (preview only); alternatively set --conditioning-mm 0')
        originals=parse_svg(a.svg)
        conditioned=[conditioning(path,params.conditioning_mm) for path in originals]
        predicted=[predict(path,params) for path in conditioned]
        candidates=[steady_compensation_candidate(path,params) for path in originals]
        destination=a.output or a.svg.with_name(a.svg.stem+'_blade_tip_preview.svg')
        if destination.resolve()==a.svg.resolve(): raise ValueError('Output cannot overwrite input')
        write_preview(destination,originals,conditioned,predicted,candidates)
        print(f'OFFLINE ONLY: {destination} ({len(originals)} paths)')
        print('Black dashed: desired; blue: conditioned holder path; orange: predicted surrogate tip; purple dashed: straight-run inverse candidate.')
        print(f'Finite recovery={params.recovery_mm:.2f} mm; relative measured gap={params.steady_gap_mm:.2f} mm; signed bias={params.signed_bias_mm:.2f} mm (NOT calibrated).')
        print('NO HPGL GENERATED; NO USB DATA SENT. Do not cut the candidate path without further validation.')
    except (ValueError,OSError,ET.ParseError) as exc:
        p.exit(1,f'Error: {exc}\n')

if __name__=='__main__': main()
