import unittest,math,tempfile
from pathlib import Path
from blade_tip_stateful import Model,forward,inverse
from smart3_v020_grid import cases,main
class StatefulTests(unittest.TestCase):
 def test_nine_cases(self):
  c=cases(); self.assertEqual(len(c),9); self.assertEqual(sum(map(len,c)),11)
 def test_finite(self):
  m=Model(); p=inverse([(10,10),(25,10),(25,25)],m)
  self.assertTrue(all(math.isfinite(x) and math.isfinite(y) for x,y in p))
 def test_corner_approach_stable(self):
  m=Model(); h=[(i*.1,0) for i in range(31)]+[(3,j*.1) for j in range(1,51)]
  out=forward(h,m); self.assertEqual(len(out),len(h))
  self.assertTrue(all(math.isfinite(x) for pt in out for x in pt))
 def test_inverse_closed(self):
  p=inverse(cases()[0][0],Model(),True); self.assertGreater(len(p),20)
 def test_all_cases(self):
  for group in cases():
   for p in group:
    out=inverse(p,Model(),math.dist(p[0],p[-1])<1e-7)
    self.assertGreater(len(out),len(p))
 def test_invalid(self):
  with self.assertRaises(ValueError): Model(x_rotation=0)
if __name__=='__main__':unittest.main()
