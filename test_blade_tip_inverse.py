import unittest
import math
from blade_tip_inverse import Config,compensate
from smart3_v019_compact import shapes

class InverseTests(unittest.TestCase):
    def test_parameters(self):
        for kwargs in ({'per_side_mm':float('nan')},{'overshoot_mm':2},{'conditioning_mm':-1}):
            with self.assertRaises(ValueError):Config(**kwargs)
    def test_open_has_conditioning(self):
        p=compensate([(10,10),(20,10),(20,20)],Config())
        self.assertAlmostEqual(p[0][0],7)
        self.assertEqual(p[0][1],10)
        self.assertGreater(len(p),3)
    def test_corner_overshoot(self):
        p=compensate([(10,10),(20,10),(20,20)],Config())
        self.assertTrue(any(x>20 for x,y in p))
    def test_closed_on_contour_conditioning(self):
        p=compensate(shapes()[0],Config())
        self.assertAlmostEqual(p[0][0],12)
        self.assertAlmostEqual(p[0][1],15)
    def test_all_compensated_shapes_in_bounds(self):
        for path in shapes()[:8]:
            result=compensate(path,Config())
            self.assertTrue(all(math.isfinite(v) and 0<=v<=115 for p in result for v in p))
    def test_short_segments_rejected(self):
        with self.assertRaises(ValueError):
            compensate([(10,10),(10.1,10),(20,20)],Config())
if __name__=='__main__':unittest.main()
