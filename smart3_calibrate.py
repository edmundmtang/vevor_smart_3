"""Smart 3 offline calibration pattern generator and axis-scale fitter.

No USB access. Pattern lines are open so blade corner behavior does not bias
axis-scale measurements. Measure center-to-center distances between end marks.
"""
import argparse
import csv
import math
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def generate(out, mode='axes'):
    root = ET.Element(f'{{{NS}}}svg', {'width':'200mm','height':'190mm',
             'viewBox':'0 0 200 190', 'version':'1.1'})
    def line(x1,y1,x2,y2,ident):
        ET.SubElement(root,f'{{{NS}}}line',{'id':ident,'x1':str(x1),'y1':str(y1),
          'x2':str(x2),'y2':str(y2),'stroke':'black','fill':'none'})
    def polygon(points,ident):
        ET.SubElement(root,f'{{{NS}}}polygon',{'id':ident,
          'points':' '.join(f'{x:.5f},{y:.5f}' for x,y in points),
          'stroke':'black','fill':'none'})
    if mode == 'axes':
        # Independent open lines. Each distance can be measured directly.
        for i,length in enumerate((20,40,80,120,160)):
            y=10+12*i
            line(10,y,10+length,y,f'X_{length}')
        for i,length in enumerate((20,40,80,120,160)):
            x=180+4*i
            line(x,10,x,10+length,f'Y_{length}')
    else:
        # Paired loops: direction reversed; deliberately no overcut.
        sizes=(1,2,3,5,10)
        for i,s in enumerate(sizes):
            for j,clockwise in enumerate((True,False)):
                x=12+i*34; y=12+j*24
                pts=[(x,y),(x+s,y),(x+s,y+s),(x,y+s)]
                if not clockwise: pts=[pts[0]]+list(reversed(pts[1:]))
                polygon(pts,f'square_{s}mm_{"cw" if clockwise else "ccw"}')
        # Rounded shape comparison with same sizes, discretized to simple polygons.
        for i,s in enumerate(sizes):
            cx=12+i*34+s/2; cy=84+s/2
            pts=[(cx+s/2*math.cos(2*math.pi*k/64),cy+s/2*math.sin(2*math.pi*k/64)) for k in range(64)]
            polygon(pts,f'circle_{s}mm')
    out.parent.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(root).write(out,encoding='utf-8',xml_declaration=True)
    print(f'Wrote {mode} pattern: {out} (200 x 190 mm page; no USB commands sent)')


def fit(path, old_x, old_y):
    data={'X':[],'Y':[]}
    with path.open(newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        if not {'axis','target_mm','measured_mm'}.issubset(reader.fieldnames or []):
            raise ValueError('CSV requires axis,target_mm,measured_mm columns')
        for row in reader:
            axis=row['axis'].strip().upper()
            if axis not in data: raise ValueError(f'Invalid axis: {axis}')
            t,m=float(row['target_mm']),float(row['measured_mm'])
            if not (math.isfinite(t) and math.isfinite(m) and t>0 and m>0):
                raise ValueError('Lengths must be positive finite numbers')
            data[axis].append((t,m))
    for axis,old in (('X',old_x),('Y',old_y)):
        rows=data[axis]
        if len(rows)<3 or len(set(t for t,m in rows))<3:
            raise ValueError(f'{axis}: need at least 3 distinct target lengths')
        xs=[t for t,m in rows]; ys=[m for t,m in rows]
        xm=statistics.mean(xs); ym=statistics.mean(ys)
        slope=sum((x-xm)*(y-ym) for x,y in rows)/sum((x-xm)**2 for x in xs)
        intercept=ym-slope*xm
        if slope<=0: raise ValueError(f'{axis}: nonpositive fitted slope')
        residuals=[y-(slope*x+intercept) for x,y in rows]
        rmse=math.sqrt(sum(r*r for r in residuals)/len(rows))
        print(f'{axis}: measured = {slope:.8f} * target + {intercept:.5f} mm')
        print(f'   RMSE={rmse:.5f} mm; old_scale={old:.8f}; suggested_scale={old/slope:.8f}')
        print('   Inspect intercept and residuals before applying any suggested scale.')


def main():
    p=argparse.ArgumentParser(description='Offline Smart 3 calibration pattern and regression tool')
    sub=p.add_subparsers(dest='command',required=True)
    g=sub.add_parser('generate'); g.add_argument('--mode',choices=('axes','details'),default='axes');g.add_argument('--output',type=Path)
    f=sub.add_parser('fit');f.add_argument('csv',type=Path);f.add_argument('--x-scale',type=float,default=.74772);f.add_argument('--y-scale',type=float,default=3.63376)
    args=p.parse_args()
    if args.command=='generate':generate(args.output or Path('calibration_'+args.mode+'.svg'),args.mode)
    else:fit(args.csv,args.x_scale,args.y_scale)
if __name__=='__main__':main()
