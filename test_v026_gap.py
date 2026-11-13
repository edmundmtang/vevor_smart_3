import unittest, math
from blade_tip_stateful import Model, forward, inverse

class GapProbeTests(unittest.TestCase):
    def test_both_signs_are_valid(self):
        for amp in (-.225,0,.225):
            self.assertEqual(Model(y_history_mm=amp).y_history_mm,amp)
    def test_state_is_continuous_at_y_reversal(self):
        # A smooth lateral model must not jump 0.45 mm when the travel sign flips.
        holder=[(0,0),(0,.5),(0,1),(0,1.5),(.1,1.5),(.2,1.5),(.3,1.5),(.4,1.5),(.5,1.5)]
        a=forward(holder,Model(y_history_mm=.225))
        b=forward(holder,Model(y_history_mm=-.225))
        self.assertTrue(all(math.isfinite(v) for p in a+b for v in p))
        z=forward(holder,Model())
        residual=[a[i][1]-z[i][1] for i in range(len(a))]
        self.assertLessEqual(max(abs(residual[i]-residual[i-1]) for i in range(5,len(a))),.225001)
    def test_zero_is_identical_to_reference(self):
        from blade_tip_stateful_v025_reference import Model as OldModel, forward as old_forward
        path=[(0,0),(0,1),(0,2),(1,2),(2,2),(3,2)]
        self.assertEqual(forward(path,Model()),old_forward(path,OldModel()))
    def test_inverse_is_finite_for_both_polarities(self):
        path=[(0,0),(0,3),(5,3)]
        for amp in (-.225,.225):
            out=inverse(path,Model(y_history_mm=amp))
            self.assertTrue(all(math.isfinite(v) for p in out for v in p))
if __name__=='__main__': unittest.main()
