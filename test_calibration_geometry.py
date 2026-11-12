"""Offline regression tests; not a physical cutting validation."""
import unittest
from pathlib import Path
from loop_closure import relocate
from smart3_cut import parse_svg, make_hpgl, load_settings, get_physical_bounds, check_mat_limits
ROOT=Path(__file__).resolve().parent
class CalibrationTests(unittest.TestCase):
    def test_patterns_parse(self):
        self.assertEqual(len(parse_svg(ROOT/'calibration_loops.svg')),16)
        self.assertEqual(len(parse_svg(ROOT/'calibration_corners.svg')),12)
    def test_fallback_short_run(self):
        shape=[(2,2),(2.3,2),(2.3,2.3),(2,2.3),(2,2)]
        pts,reason=relocate(shape,'auto-straight',0.5)
        self.assertEqual(pts,shape)
        self.assertIn('below',reason)
    def test_fallback_circle(self):
        pts=[(10+2*__import__('math').cos(i*2*__import__('math').pi/64),10+2*__import__('math').sin(i*2*__import__('math').pi/64)) for i in range(64)]
        pts.append(pts[0])
        out,reason=relocate(pts,'auto-straight')
        self.assertEqual(out,pts)
        self.assertIn('unchanged',reason)
    def test_open_corners_unchanged(self):
        for p in parse_svg(ROOT/'calibration_corners.svg'):
            self.assertEqual(relocate(p,'auto-straight')[0],p)
    def test_patterns_fit_mat_and_generate_hpgl(self):
        settings=load_settings()
        for name in ('calibration_loops.svg','calibration_corners.svg'):
            outlines=parse_svg(ROOT/name)
            if name=='calibration_loops.svg':
                outlines=[relocate(p,'auto-straight')[0] for p in outlines]
            hpgl,bounds=make_hpgl(outlines,settings)
            check_mat_limits(get_physical_bounds(outlines),bounds,settings)
            self.assertIn('PD',hpgl)
if __name__=='__main__': unittest.main()
