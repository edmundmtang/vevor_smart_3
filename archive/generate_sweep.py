"""Offline-only 3x3 intended-tip geometry for v0.31 corner-reach sweep.
Columns are IDENTICAL until a separately validated corner-reach implementation exists.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
import math
NS='http://www.w3.org/2000/svg'
ET.register_namespace('',NS)
root=ET.Element(f'{{{NS}}}svg',{'width':'104mm','height':'90mm','viewBox':'0 0 104 90'})
centers_x=[20,52,84]
centers_y=[18,41,69]

def add(points):
    ET.SubElement(root,f'{{{NS}}}polyline',{'points':' '.join(f'{x:.5f},{y:.5f}' for x,y in points),'fill':'none','stroke':'black','stroke-width':'0.1'})

def rotate45(points,cx,cy):
    angle=math.radians(45)
    co,si=math.cos(angle),math.sin(angle)
    return [(cx+(x-cx)*co-(y-cy)*si,cy+(x-cx)*si+(y-cy)*co) for x,y in points]

for col,cx in enumerate(centers_x):
    cy=centers_y[0]
    add([(cx-8,cy-8),(cx+8,cy-8),(cx+8,cy+8),(cx-8,cy+8),(cx-8,cy-8)])
    for row in (1,2):
        cy=centers_y[row]
        paths=[[(cx-10,cy-9),(cx,cy),(cx+10,cy-9)],[(cx-10,cy+9),(cx,cy),(cx+10,cy+9)]]
        if row==2: paths=[rotate45(p,cx,cy) for p in paths]
        for path in paths: add(path)

out=Path(__file__).with_name('corner_sweep_target.svg')
ET.ElementTree(root).write(out,encoding='utf-8',xml_declaration=True)
print(out)
