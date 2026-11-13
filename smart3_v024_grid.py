"""Nine compact test cases in a 3x3 grid; baseline and stateful compensated SVGs.
Offline generator only. No USB activity. Dimensions in mm.
"""
import argparse, math, xml.etree.ElementTree as ET
from pathlib import Path
from blade_tip_stateful import Model,inverse,forward,sample,length,minus
from smart3_cut import parse_svg
NS='http://www.w3.org/2000/svg'

def star(cx,cy,r=8.5,rotation=0):
    # Five pointed convex tips connected through concave notches (star polygon).
    # The requested convex geometry is represented by the five outward tips.
    return [(cx+(r if i%2==0 else r*.48)*math.cos(rotation-math.pi/2+i*math.pi/5),
             cy+(r if i%2==0 else r*.48)*math.sin(rotation-math.pi/2+i*math.pi/5)) for i in range(10)]+[(cx+r*math.cos(rotation-math.pi/2),cy+r*math.sin(rotation-math.pi/2))]

def cases():
    # 3x3 cells: two squares, four opposing corner tests,
    # a circular control, and two rotated five-point stars.
    positions=[(22+36*c,21+35*r) for r in range(3) for c in range(3)]
    result=[]
    for i,(cx,cy) in enumerate(positions):
        if i<2:
            a=8; result.append([[(cx-a,cy-a),(cx+a,cy-a),(cx+a,cy+a),(cx-a,cy+a),(cx-a,cy-a)]])
        elif i==2:
            # Opposing 90-degree turns meeting at one intended vertex.
            result.append([[(cx-10,cy-9),(cx,cy),(cx,cy+9)],
                           [(cx+10,cy+9),(cx,cy),(cx,cy-9)]])
        elif i==3:
            # Same nominal contact, rotated 90 degrees.
            result.append([[(cx-9,cy+10),(cx,cy),(cx+9,cy)],
                           [(cx+9,cy-10),(cx,cy),(cx-9,cy)]])
        elif i==4:
            result.append([[(cx-10,cy-10),(cx-10,cy-2),(cx+10,cy-2)],[(cx-10,cy+10),(cx-10,cy+2),(cx+10,cy+2)]])
        elif i==5:
            result.append([[(cx-10,cy-9),(cx,cy),(cx+10,cy-9)],[(cx-10,cy+9),(cx,cy),(cx+10,cy+9)]])
        elif i==6:
            result.append([[(cx+9*math.cos(2*math.pi*j/120),cy+9*math.sin(2*math.pi*j/120)) for j in range(121)]])
        elif i==7: result.append([star(cx,cy,8.5,0)])
        else: result.append([star(cx,cy,8.5,math.pi/5)])
    return result

def save(path,groups,w=124,h=111):
    root=ET.Element('svg',{'xmlns':NS,'width':f'{w}mm','height':f'{h}mm','viewBox':f'0 0 {w} {h}'})
    for paths in groups:
        for pts in paths:
            ET.SubElement(root,'polyline',{'points':' '.join(f'{x:.5f},{y:.5f}' for x,y in pts),'fill':'none','stroke':'black','stroke-width':'0.1'})
    ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)

def main():
    p=argparse.ArgumentParser(description='v0.24 offline 3x3 test grid')
    p.add_argument('--output-dir',type=Path,default=Path('.'))
    p.add_argument('--recovery-mm',type=float,default=1.39)
    p.add_argument('--blade-offset-mm',type=float,default=.20)
    p.add_argument('--x-rotation',type=float,default=1.)
    p.add_argument('--y-rotation',type=float,default=1.)
    p.add_argument('--min-approach-x-mm',type=float,default=.09)
    p.add_argument('--min-approach-y-mm',type=float,default=0.)
    p.add_argument('--conditioning-mm',type=float,default=3.)
    p.add_argument('--max-correction-mm',type=float,default=.85)
    p.add_argument('--iterations',type=int,default=12)
    p.add_argument('--vertex-weight',type=float,default=3.0)
    p.add_argument('--corner-extra-mm',type=float,default=.10)
    p.add_argument('--y-history-mm',type=float,default=0.0,help='Experimental signed Y-memory amplitude; default 0')
    a=p.parse_args()
    model=Model(recovery_mm=a.recovery_mm,blade_offset_mm=a.blade_offset_mm,
                x_rotation=a.x_rotation,y_rotation=a.y_rotation,
                min_approach_x_mm=a.min_approach_x_mm,min_approach_y_mm=a.min_approach_y_mm,
                conditioning_mm=a.conditioning_mm,max_correction_mm=a.max_correction_mm,
                iterations=a.iterations,vertex_weight=a.vertex_weight,corner_extra_mm=a.corner_extra_mm,y_history_mm=a.y_history_mm)
    original=cases()
    print('Y-history correction:',a.y_history_mm,'mm (0 means disabled)')
    experimental=[[inverse(path,model,closed=(math.dist(path[0],path[-1])<1e-7)) for path in group] for group in original]
    a.output_dir.mkdir(parents=True,exist_ok=True)
    files=[a.output_dir/'v024_grid_baseline.svg',a.output_dir/'v024_grid_experimental.svg']
    for filename,groups in zip(files,(original,experimental)):
        save(filename,groups)
        parsed=parse_svg(filename)
        if len(parsed)!=13: raise ValueError(f'Expected 13 paths, got {len(parsed)}')
        if any(not(0<=x<=124 and 0<=y<=111) for path in parsed for x,y in path): raise ValueError('Out of bounds')
        print(filename,'paths',len(parsed))
    print('Experimental: may cut off-contour. Dry-run both SVGs before live cutting.')
    print('Diagnostics: compensation does not guarantee physical improvement.')
if __name__=='__main__':main()
