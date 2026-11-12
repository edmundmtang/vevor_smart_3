import unittest, math
from pathlib import Path
from xml.etree import ElementTree as ET

class TestHorizontalTravel(unittest.TestCase):
    def test_four_pairs(self):
        root=ET.parse(Path(__file__).with_name('calibration_horizontal_travel_direction.svg')).getroot()
        paths=[e for e in root if e.tag.endswith('polyline')]
        self.assertEqual(len(paths),8)
        self.assertEqual(root.attrib['viewBox'],'0 0 115 100')
        for i in range(0,8,2):
            gap=0 if i<4 else 2
            direction=1 if (i//2)%2==0 else -1
            a,b=[[tuple(map(float,p.split(','))) for p in paths[j].attrib['points'].split()] for j in (i,i+1)]
            for path in (a,b):
                self.assertEqual(len(path),3)
                self.assertAlmostEqual(abs(path[1][1]-path[0][1]),8)
                self.assertAlmostEqual(path[2][0]-path[1][0],direction*22)
                self.assertAlmostEqual(path[2][1],path[1][1])
                for x,y in path: self.assertTrue(0<=x<=115 and 0<=y<=100)
            self.assertAlmostEqual(abs(a[1][1]-b[1][1]),gap)
            self.assertAlmostEqual(a[1][0],b[1][0])
            self.assertAlmostEqual(a[0][1]-a[1][1],-(b[0][1]-b[1][1]))

if __name__=='__main__': unittest.main()
