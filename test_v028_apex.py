import unittest, math
from blade_tip_stateful import Model,apex_targets,inverse,length,minus
from smart3_v028_grid import cases
class ApexTests(unittest.TestCase):
    def test_default_off(self):
        self.assertEqual(Model().corner_apex_mm,0)
    def test_straight_no_change(self):
        pts=[(0,0),(1,0),(2,0)]
        self.assertEqual(apex_targets(pts,.2),pts)
    def test_open_v_moves_outward_and_keeps_endpoints(self):
        pts=[(-3,3),(0,0),(3,3)]
        out=apex_targets(pts,.2)
        self.assertEqual(out[0],pts[0]);self.assertEqual(out[-1],pts[-1])
        self.assertAlmostEqual(out[1][0],0)
        self.assertAlmostEqual(out[1][1],-.2)
    def test_rotational_covariance(self):
        pts=[(-3,3),(0,0),(3,3)]
        rotate=lambda p:(-p[1],p[0])
        self.assertTrue(all(length(minus(rotate(a),b))<1e-9 for a,b in zip(apex_targets(pts,.2),apex_targets([rotate(p) for p in pts],.2))))
    def test_closed_seam(self):
        pts=[(0,0),(4,0),(4,4),(0,4),(0,0)]
        out=apex_targets(pts,.1,closed=True)
        self.assertEqual(out[0],out[-1])
    def test_bounds(self):
        with self.assertRaises(ValueError):Model(corner_apex_mm=.31)
        with self.assertRaises(ValueError):Model(corner_apex_mm=-.01)
    def test_inverse_finite(self):
        for a in (0,.1,.2):
            for group in (cases()[3],cases()[5]):
                for pts in group:
                    out=inverse(pts,Model(y_history_mm=-.3,corner_apex_mm=a,max_correction_mm=.85))
                    self.assertTrue(all(math.isfinite(v) for p in out for v in p))
if __name__=='__main__':unittest.main()
