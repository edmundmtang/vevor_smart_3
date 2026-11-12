import math
import unittest
from loop_closure import add_same_path_overlap
from blade_offset import compensate

class BladeGeometryTests(unittest.TestCase):
    def test_multisegment_overlap_circle(self):
        p=[(20+5*math.cos(2*math.pi*i/100),20+5*math.sin(2*math.pi*i/100)) for i in range(101)]
        out,info=add_same_path_overlap(p,1.0)
        self.assertIn('across',info)
        self.assertGreater(len(out),len(p)+1)
        travelled=sum(math.dist(a,b) for a,b in zip(out[len(p)-1:],out[len(p):]))
        self.assertAlmostEqual(travelled,1.0,places=7)
        self.assertEqual(out[len(p)-1],out[0])
    def test_overlap_exact_vertex(self):
        p=[(0,0),(0.2,0),(0.5,0),(1,0),(1,1),(0,1),(0,0)]
        out,_=add_same_path_overlap(p,0.5)
        self.assertEqual(out[-1],(0.5,0))
    def test_offset_zero_exact(self):
        p=[(1,2),(4,2),(4,4)]
        self.assertEqual(compensate(p,0)[0],p)
    def test_corner_pivot_geometry(self):
        p=[(2,2),(5,2),(5,5)]
        out,info=compensate(p,0.25,10)
        self.assertAlmostEqual(out[0][0],2.25)
        self.assertAlmostEqual(out[0][1],2)
        self.assertAlmostEqual(out[-1][0],5)
        self.assertAlmostEqual(out[-1][1],5.25)
        for pt in out[2:-1]:
            self.assertAlmostEqual(math.dist(pt,(5,2)),0.25,places=6)
        self.assertIn('1 pivot',info)
    def test_invalid_offset(self):
        with self.assertRaises(ValueError): compensate([(0,0),(1,0)],float('nan'))
    def test_perimeter_guard(self):
        p=[(0,0),(1,0),(1,1),(0,1),(0,0)]
        out,msg=add_same_path_overlap(p,4)
        self.assertEqual(out,p)
        self.assertIn('skipped',msg)

if __name__=='__main__': unittest.main()
