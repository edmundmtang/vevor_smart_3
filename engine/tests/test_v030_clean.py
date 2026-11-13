import unittest, math, subprocess, sys, tempfile
from pathlib import Path
from blade_tip_clean import CleanConfig, component_audit, compensate
from calibration.legacy_generators.smart3_v029_grid import cases

class CleanModelTests(unittest.TestCase):
    def test_no_competing_terms(self):
        a=component_audit()
        self.assertEqual(a['extra turn-direction bias (mm)'],0)
        self.assertEqual(a['artificial target apex extension (mm)'],0)
        self.assertEqual(a['independent outgoing normal shift (mm)'],0)
        self.assertFalse(a['history based on intended rather than holder path'])
    def test_history_parameter_rejected(self):
        with self.assertRaises(ValueError): CleanConfig(lateral_history_mm=-.41).model()
    def test_finite_holder_and_bounds(self):
        for group in (cases()[3],cases()[5]):
            for path in group:
                out=compensate(path)
                self.assertGreater(len(out),len(path))
                self.assertTrue(all(math.isfinite(v) for p in out for v in p))
                self.assertTrue(all(0<=x<=124 and 0<=y<=111 for x,y in out))
    def test_double_compensation_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/'test.svg'
            src.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="20mm" height="20mm" viewBox="0 0 20 20"><polyline points="3,3 17,3 17,17"/></svg>')
            result=subprocess.run([sys.executable,str(Path(__file__).resolve().parents[1]/'smart3_cut.py'),str(src),'--blade-tip-compensation','--blade-offset-mm','.2','--dry-run'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('cannot be combined',result.stderr)
            self.assertFalse(src.with_suffix('.hpgl').exists())
if __name__=='__main__':unittest.main()
