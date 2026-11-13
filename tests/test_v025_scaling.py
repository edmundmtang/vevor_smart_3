import math, unittest
from geometry_scaling import scale_group
from calibration.legacy_generators.smart3_v025_grid import cases
from blade_tip_stateful import Model, inverse

class GeometryScaleTests(unittest.TestCase):
    def test_identity_preserves_paths(self):
        self.assertEqual(cases(),[scale_group(g) for g in cases()])
    def test_square_dimensions_and_center(self):
        p=scale_group(cases()[0],16/15.65,16/15.47)[0]
        self.assertAlmostEqual(max(x for x,y in p)-min(x for x,y in p),16*16/15.65)
        self.assertAlmostEqual(max(y for x,y in p)-min(y for x,y in p),16*16/15.47)
        self.assertAlmostEqual((max(x for x,y in p)+min(x for x,y in p))/2,22)
        self.assertEqual(p[0],p[-1])
    def test_opposing_vertices_still_meet(self):
        for i in (2,3,5):
            a,b=scale_group(cases()[i],1.02,1.03)
            self.assertEqual(a[1],b[1])
    def test_reject_invalid_scales(self):
        for sx in [float('nan'),float('inf'),0.8,1.11]:
            with self.assertRaises(ValueError): scale_group(cases()[0],sx,1)
    def test_inverse_with_scaled_closed_path(self):
        p=scale_group(cases()[0],1.02,1.03)[0]
        result=inverse(p,Model(),closed=True)
        self.assertGreater(len(result),len(p))
        self.assertTrue(all(math.isfinite(z) for point in result for z in point))
if __name__=='__main__': unittest.main()
