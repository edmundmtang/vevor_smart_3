import unittest, math
from pathlib import Path
from blade_tip_stateful import Model, forward, inverse
from smart3_cut import parse_svg
class SweepTests(unittest.TestCase):
    def test_sweep_amplitudes(self):
        for a in (-.225,-.300,-.375):
            self.assertEqual(Model(y_history_mm=a).y_history_mm,a)
        with self.assertRaises(ValueError): Model(y_history_mm=-.401)
        with self.assertRaises(ValueError): Model(y_history_mm=.300)
    def test_default_disabled(self):
        self.assertEqual(Model().y_history_mm,0.)
    def test_reference_model_still_matches_zero(self):
        from blade_tip_stateful_v025_reference import Model as Ref, forward as ref_forward
        path=[(0,0),(0,1),(0,2),(1,2),(2,2),(3,2)]
        self.assertEqual(forward(path,Model()),ref_forward(path,Ref()))
    def test_paths_finite(self):
        for a in (-.225,-.300,-.375):
            out=inverse([(0,0),(0,3),(5,3)],Model(y_history_mm=a))
            self.assertTrue(all(math.isfinite(v) for p in out for v in p))
    def test_prebuilt_patterns(self):
        for name in ('A_reference_minus_0225','B_minus_0300','C_minus_0375'):
            path=Path(name)/'v027_grid_experimental.svg'
            if not path.exists(): self.skipTest('Prebuilt SVGs not generated')
            paths=parse_svg(path)
            self.assertEqual(len(paths),4)
            self.assertTrue(all(0<=x<=124 and 0<=y<=111 for p in paths for x,y in p))
if __name__=='__main__':unittest.main()
