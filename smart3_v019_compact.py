"""v0.19 compact experimental cut shapes and inverse compensation generator.
No USB calls; use the existing smart3_cut.py explicitly to dry-run or cut.
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
from blade_tip_inverse import Config,compensate
from smart3_cut import parse_svg

NS='http://www.w3.org/2000/svg'
def write_svg(filename,paths,width=115,height=92):
    root=ET.Element('svg',{'xmlns':NS,'width':f'{width}mm','height':f'{height}mm','viewBox':f'0 0 {width} {height}'})
    for path in paths:
        ET.SubElement(root,'polyline',{'points':' '.join(f'{x:.5f},{y:.5f}' for x,y in path),'fill':'none','stroke':'black','stroke-width':'0.1'})
    ET.ElementTree(root).write(filename,encoding='utf-8',xml_declaration=True)

def shapes():
    # Four isolated 15-mm squares, two horizontal/vertical mirrored-Ls,
    # plus a 12-mm radius circle and a triangular corner comparison.
    import math
    return [
        [(12,12),(27,12),(27,27),(12,27),(12,12)],
        [(43,12),(58,12),(58,27),(43,27),(43,12)],
        [(74,12),(89,12),(89,27),(74,27),(74,12)],
        [(12,44),(27,44),(27,59),(12,59),(12,44)],
        [(43,38),(43,46),(62,46)],
        [(43,62),(43,54),(62,54)],
        [(76,39),(84,46),(92,39)],
        [(76,62),(84,55),(92,62)],
        [(24+10*math.cos(2*math.pi*i/96),77+10*math.sin(2*math.pi*i/96)) for i in range(97)],
    ]

def main():
    p=argparse.ArgumentParser(description='v0.19 offline compact test pattern; generates SVG only')
    p.add_argument('--output-dir',type=Path,default=Path('.'))
    p.add_argument('--recovery-mm',type=float,default=1.39)
    p.add_argument('--per-side-mm',type=float,default=0.09)
    p.add_argument('--overshoot-mm',type=float,default=0.70)
    p.add_argument('--conditioning-mm',type=float,default=3)
    a=p.parse_args()
    cfg=Config(a.recovery_mm,a.per_side_mm,a.overshoot_mm,a.conditioning_mm)
    # Circles are too finely sampled for a corner-by-corner recovery heuristic.
    # Keep them uncompensated as a baseline in both files.
    original=shapes()
    experimental=[compensate(s,cfg) if i<8 else s for i,s in enumerate(original)]
    a.output_dir.mkdir(parents=True,exist_ok=True)
    baseline=a.output_dir/'v019_compact_baseline.svg'
    modified=a.output_dir/'v019_compact_experimental.svg'
    write_svg(baseline,original)
    write_svg(modified,experimental)
    for f in (baseline,modified):
        parsed=parse_svg(f)
        if len(parsed)!=9: raise ValueError('SVG roundtrip lost paths')
        if any(not (0<=x<=115 and 0<=y<=92) for path in parsed for x,y in path):
            raise ValueError('Geometry outside compact test bounds')
    print('Generated:',baseline,modified)
    print('OFFLINE SVG ONLY. Experimental version may cut outside nominal contours.')
    print('Run smart3_cut.py --dry-run on each SVG before choosing to cut.')
if __name__=='__main__':main()
