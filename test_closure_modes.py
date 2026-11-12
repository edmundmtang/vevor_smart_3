import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from loop_closure import relocate, add_same_path_overlap
from smart3_cut import make_hpgl

ROOT = Path(__file__).resolve().parent
SQUARE = [(10,10),(20,10),(20,20),(10,20),(10,10)]

class ClosureModeTests(unittest.TestCase):
    def test_overlap_exactly_on_first_edge(self):
        seam,_ = relocate(SQUARE,'auto-straight')
        out,msg = add_same_path_overlap(seam,0.4)
        self.assertEqual(out[-2],out[0])
        self.assertAlmostEqual(math.dist(out[-1],out[0]),0.4)
        a,b,c = out[0],out[1],out[-1]
        self.assertAlmostEqual((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]),0)
    def test_too_long_skips(self):
        out,msg = add_same_path_overlap(SQUARE,12)
        self.assertEqual(out,SQUARE)
        self.assertIn('skipped',msg)
    def test_open_untouched(self):
        out,msg = add_same_path_overlap([(1,1),(2,2)],0.4)
        self.assertEqual(out,[(1,1),(2,2)])
    def test_hpgl_overlap_is_not_pen_up(self):
        out,_=add_same_path_overlap(SQUARE,0.5)
        settings=dict(preserve_origin=True,finish_mode='minimal',x_scale=0.74906512,y_scale=3.59950979,x_offset=0,y_offset=0)
        lines=make_hpgl([out],settings)[0].splitlines()
        self.assertEqual(sum(line.startswith('PU') for line in lines),2)
        self.assertEqual(sum(line.startswith('PD') for line in lines),5)
    def test_curved_run_not_accepted(self):
        # A polygon approximating a circle: local turns can be small, but cumulative curvature is large.
        pts=[(20+10*math.cos(2*math.pi*i/100),20+10*math.sin(2*math.pi*i/100)) for i in range(101)]
        out,info=relocate(pts,'auto-straight',0.5,5)
        self.assertEqual(out,pts)
    def test_live_guard_rejects_lead_in(self):
        cmd=[sys.executable,str(ROOT/'smart3_cut.py'),str(ROOT/'calibration_loops.svg'),'--dry-run','--lead-in-mm','0.5']
        result=subprocess.run(cmd,capture_output=True,text=True,cwd=ROOT)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('not implemented',result.stderr)
    def test_modes_map_validation(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'modes.json'
            f.write_text(json.dumps({'999':'keep-inside'}))
            cmd=[sys.executable,str(ROOT/'smart3_cut.py'),str(ROOT/'calibration_loops.svg'),'--dry-run','--contour-modes',str(f)]
            result=subprocess.run(cmd,capture_output=True,text=True,cwd=ROOT)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Invalid contour index',result.stderr)

if __name__=='__main__': unittest.main()
