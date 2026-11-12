import math
import tempfile
import unittest
from pathlib import Path
from blade_tip_model import Parameters, clean, conditioning, predict, steady_compensation_candidate
from smart3_blade_tip_preview import write_preview


class BladeTipModelTests(unittest.TestCase):
    def test_invalid_parameters(self):
        for values in ({'recovery_mm':0},{'recovery_mm':float('nan')},
                       {'signed_bias_mm':3},{'sample_step_mm':0}):
            with self.assertRaises(ValueError): Parameters(**values)

    def test_duplicate_points(self):
        self.assertEqual(clean([(0,0),(0,0),(1,0)]),[(0,0),(1,0)])

    def test_conditioning_direction(self):
        self.assertEqual(conditioning([(1,1),(4,1)],3)[0],(-2,1))

    def test_no_lead(self):
        self.assertEqual(conditioning([(1,1),(4,1)],0),[(1,1),(4,1)])

    def test_straight_bias_is_constant(self):
        path=predict([(0,0),(10,0)],Parameters(signed_bias_mm=0.2))
        self.assertTrue(all(abs(y-.2)<1e-9 for x,y in path))
        self.assertAlmostEqual(path[-1][0],10)

    def test_corner_recovers_to_straight_at_finite_distance(self):
        p=Parameters(recovery_mm=1.4,sample_step_mm=.1)
        path=predict([(0,0),(10,0),(10,10)],p)
        # After corner recovery the path is exactly on x=10, not approaching it asymptotically.
        self.assertTrue(all(abs(x-10)<1e-9 for x,y in path if y>=11.4-1e-8))
        self.assertTrue(any(x<10 and y>0 for x,y in path))

    def test_candidate_is_identity_without_calibrated_bias(self):
        pts=[(0,0),(10,0),(10,10)]
        self.assertEqual(steady_compensation_candidate(pts,Parameters()),pts)

    def test_candidate_straight_offsets_opposite_normal(self):
        p=steady_compensation_candidate([(0,0),(10,0)],Parameters(signed_bias_mm=.2))
        self.assertEqual(p,[(0,-.2),(10,-.2)])

    def test_preview_svg(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'preview.svg'
            a=[[(0,0),(10,0),(10,10)]]
            write_preview(target,a,a,[predict(a[0],Parameters())],a)
            self.assertIn('polyline',target.read_text())

    def test_nonfinite_path_rejected(self):
        with self.assertRaises(ValueError): predict([(0,0),(math.inf,0)],Parameters())


if __name__=='__main__': unittest.main()
