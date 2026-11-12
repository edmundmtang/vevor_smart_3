import math, unittest
from blade_tip_stateful import Model, forward, inverse
from smart3_v021_grid import cases
class StatefulV021Tests(unittest.TestCase):
 def test_nine_cells(self):
  self.assertEqual(len(cases()),9)
  self.assertEqual(sum(len(x) for x in cases()),11)
 def test_all_inverse_paths_finite(self):
  for group in cases():
   for p in group:
    out=inverse(p,Model(),math.dist(p[0],p[-1])<1e-8)
    self.assertTrue(len(out)>len(p))
    self.assertTrue(all(math.isfinite(v) for q in out for v in q))
 def test_persistent_gap_does_not_decay(self):
  h=[(i*.1,0) for i in range(61)]+[(6,j*.1) for j in range(1,101)]
  p=forward(h,Model())
  self.assertAlmostEqual(p[-1][0],p[-6][0],delta=.02)
 def test_bounds(self):
  with self.assertRaises(ValueError): Model(vertex_weight=0)
  with self.assertRaises(ValueError): Model(max_correction_mm=2)
 def test_repeatable(self):
  p=cases()[0][0]
  self.assertEqual(inverse(p,Model(),True),inverse(p,Model(),True))
if __name__=='__main__': unittest.main()
