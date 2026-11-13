import unittest, math
from blade_tip_stateful import Model,forward,inverse
from smart3_v025_grid import cases
class SafetyTests(unittest.TestCase):
 def test_history_off_by_default(self):
  self.assertEqual(Model().y_history_mm,0.)
 def test_bounded_history(self):
  with self.assertRaises(ValueError): Model(y_history_mm=.3)
 def test_no_history_baseline_invariance(self):
  h=[(0.,-5.),(0.,0.)]+[(i*.2,0.) for i in range(1,51)]
  self.assertEqual(forward(h,Model()),forward(h,Model(y_history_mm=0.)))
 def test_history_continuity(self):
  h=[(0.,-5+i*.1) for i in range(51)]+[(i*.1,0.) for i in range(1,51)]
  a=forward(h,Model(blade_offset_mm=0,min_approach_x_mm=0,y_history_mm=.08))
  self.assertLess(max(math.dist(x,y) for x,y in zip(a,a[1:])),.25)
 def test_inverse_finite(self):
  for group in cases():
   for pts in group:
    out=inverse(pts,Model(),closed=(math.dist(pts[0],pts[-1])<1e-7))
    self.assertTrue(all(math.isfinite(v) for p in out for v in p))
if __name__=='__main__': unittest.main()
