import math
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

SVG = Path(__file__).with_name('calibration_mirrored_l_gaps.svg')

class TestMirroredL(unittest.TestCase):
    def test_six_pairs_three_vertices_and_geometry(self):
        root=ET.parse(SVG).getroot()
        lines=[e for e in root if e.tag.endswith('polyline')]
        self.assertEqual(len(lines),12)
        for i in range(0,12,2):
            gap = 0 if i < 6 else 2
            a,b=[] , []
            for e,out in ((lines[i],a),(lines[i+1],b)):
                out.extend(tuple(map(float,s.split(','))) for s in e.attrib['points'].split())
                self.assertEqual(len(out),3)
                short=(out[1][0]-out[0][0],out[1][1]-out[0][1])
                long=(out[2][0]-out[1][0],out[2][1]-out[1][1])
                self.assertAlmostEqual(math.hypot(*short),12,places=4)
                self.assertAlmostEqual(math.hypot(*long),30,places=4)
                self.assertAlmostEqual(short[0]*long[0]+short[1]*long[1],0,places=4)
            av=(a[2][0]-a[1][0],a[2][1]-a[1][1]);bv=(b[2][0]-b[1][0],b[2][1]-b[1][1])
            self.assertAlmostEqual(av[0],bv[0],places=4)
            self.assertAlmostEqual(av[1],bv[1],places=4)
            sep=(b[1][0]-a[1][0],b[1][1]-a[1][1])
            self.assertAlmostEqual(math.hypot(*sep),gap,places=4)
            sa=(a[1][0]-a[0][0],a[1][1]-a[0][1]);sb=(b[1][0]-b[0][0],b[1][1]-b[0][1])
            self.assertAlmostEqual(sa[0],-sb[0],places=4)
            self.assertAlmostEqual(sa[1],-sb[1],places=4)

if __name__=='__main__':unittest.main()
