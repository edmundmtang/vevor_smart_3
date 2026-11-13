import unittest
from blade_tip_stateful import Model,forward

class HysteresisTests(unittest.TestCase):
    def test_y_history_persists_on_horizontal(self):
        m=Model(blade_offset_mm=0,min_approach_y_mm=.225)
        up=[(0.,-5.+i*.15) for i in range(41)]+[(i*.15,1.) for i in range(1,81)]
        down=[(0.,7.-i*.15) for i in range(41)]+[(i*.15,1.) for i in range(1,81)]
        a=forward(up,m);b=forward(down,m)
        self.assertGreater(a[-1][1]-b[-1][1],.35)
        self.assertAlmostEqual(a[-1][1]-b[-1][1],a[-21][1]-b[-21][1],delta=.01)
    def test_no_bias_on_straight_y(self):
        m=Model(blade_offset_mm=0,min_approach_y_mm=.225)
        path=[(0.,i*.15) for i in range(41)]
        self.assertAlmostEqual(forward(path,m)[-1][0],0,places=6)

if __name__=='__main__':unittest.main()
