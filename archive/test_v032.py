import unittest, math
from corner_transition_v032 import Transition,transition_holder,ease
class TestTransition(unittest.TestCase):
    def setUp(self):
        self.p=[(0,0),(8,0),(8,8)]
        self.h=[(i*.1,0) for i in range(81)]+[(8,i*.1) for i in range(1,81)]
    def test_zero_identity(self): self.assertEqual(transition_holder(self.h,self.p,Transition(0)),self.h)
    def test_local_and_bounded(self):
        o=transition_holder(self.h,self.p)
        self.assertEqual(o[0],self.h[0]);self.assertEqual(o[-1],self.h[-1])
        self.assertEqual(o[20],self.h[20]);self.assertEqual(o[120],self.h[120])
        self.assertTrue(0<max(math.dist(a,b) for a,b in zip(o,self.h))<=.100000001)
    def test_easing_endpoints(self):
        for k in ('linear','cubic','quintic'):
            self.assertEqual(ease(0,k),0);self.assertEqual(ease(1,k),1)
    def test_reject_bad(self):
        for v in (-.1,.31,float('nan')):
            with self.assertRaises(ValueError): transition_holder(self.h,self.p,Transition(v))
    def test_straight(self):
        h=[(i*.1,0) for i in range(101)]
        self.assertEqual(transition_holder(h,[(0,0),(10,0)]),h)
if __name__=='__main__':unittest.main()
