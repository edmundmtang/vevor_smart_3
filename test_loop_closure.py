import unittest
from loop_closure import relocate
from smart3_cut import make_hpgl

class LoopTests(unittest.TestCase):
    def test_rectangle_seam_mid_edge_and_direction(self):
        shape=[(1,1),(11,1),(11,4),(1,4),(1,1)]
        out,info=relocate(shape,'auto-straight')
        self.assertEqual(out[0],out[-1])
        self.assertEqual(out[0],(6,1))
        self.assertEqual(out[1],(11,1))
        self.assertIn('relocated',info)
        self.assertEqual(len(out),6)
    def test_open_untouched(self):
        path=[(1,1),(2,1),(3,1)]
        self.assertEqual(relocate(path,'auto-straight')[0],path)
    def test_tiny_fallback(self):
        shape=[(1,1),(1.2,1),(1.2,1.2),(1,1.2),(1,1)]
        self.assertEqual(relocate(shape,'auto-straight',0.5)[0],shape)
    def test_segmented_straight(self):
        shape=[(1,1),(3,1),(5,1),(9,1),(9,4),(1,4),(1,1)]
        out,_=relocate(shape,'auto-straight')
        self.assertEqual(out[0],(5,1))
    def test_hpgl_closed_exact_integer_endpoint(self):
        shape=[(1,1),(11,1),(11,4),(1,4),(1,1)]
        out,_=relocate(shape,'auto-straight')
        settings=dict(preserve_origin=True,finish_mode='minimal',x_scale=0.74906512,y_scale=3.59950979,x_offset=0,y_offset=0)
        hpgl,_=make_hpgl([out],settings)
        lines=hpgl.splitlines()
        self.assertEqual(lines[1][2:],lines[-2][2:])

if __name__=='__main__': unittest.main()
