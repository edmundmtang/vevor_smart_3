import unittest
from blade_tip_stateful import Model, forward, inverse, length, minus
from calibration.legacy_generators.smart3_v029_grid import cases

class V029Tests(unittest.TestCase):
    def test_history_reference_changes_only_history_term(self):
        holder=[(0,0),(0,2),(1,2),(2,2),(3,2)]
        reference=[(0,0),(0,-2),(1,-2),(2,-2),(3,-2)]
        m=Model(y_history_mm=-.3)
        a=forward(holder,m)
        b=forward(holder,m,history_reference=reference)
        self.assertGreater(abs(a[-1][1]-b[-1][1]),.1)
        self.assertEqual(a[0],b[0])
    def test_reference_count_checked(self):
        with self.assertRaises(ValueError):forward([(0,0),(1,0)],Model(),[(0,0)])
    def test_no_history_no_effect_of_reference(self):
        holder=[(0,0),(0,2),(2,2)]
        ref=[(0,0),(0,-2),(2,-2)]
        self.assertEqual(forward(holder,Model(),ref),forward(holder,Model()))
    def test_finite_gap_patterns(self):
        for isolate,taper in [(False,0),(True,0),(True,.5)]:
            m=Model(y_history_mm=-.3,corner_apex_mm=.2,max_correction_mm=.85,
                    isolate_history=isolate,apex_taper_mm=taper)
            for group in (cases()[3],cases()[5]):
                for path in group:
                    holder=inverse(path,m)
                    self.assertGreater(len(holder),10)
                    self.assertLess(max(length(minus(a,b)) for a,b in zip(holder,holder[1:])),2)
    def test_taper_bound(self):
        with self.assertRaises(ValueError):Model(apex_taper_mm=1.01)

if __name__=='__main__':unittest.main()
