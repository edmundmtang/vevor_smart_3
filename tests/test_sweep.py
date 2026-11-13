import unittest
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sweep import build,validate,write_job,parameters,main,HPGL_NAME

class SweepTests(unittest.TestCase):
    def test_build_and_validate(self):
        hpgl,report=build()
        self.assertEqual(report['contours'],15)
        self.assertEqual(report['overshoot_mm_by_column'],{'A':0.,'B':.1,'C':.2})
        self.assertEqual((ROOT/HPGL_NAME).read_bytes(),hpgl.encode('ascii'))
        self.assertEqual(validate()[1],report)
    def test_zero_control(self):
        hpgl,report=build((0,0,0))
        self.assertTrue(all(d['max_holder_delta_mm']==0 for d in report['diagnostics']))
    def test_reach_bounded(self):
        _,report=build()
        for d in report['diagnostics']:
            self.assertLessEqual(d['max_holder_delta_mm'],report['overshoot_mm_by_column'][d['column']]+1e-6)
    def test_bad_inputs(self):
        for v in (-.1,.31,float('nan')):
            with self.assertRaises(ValueError): parameters((0,v,.2),.5,1.5,'quintic')
    def test_live_confirmation_required(self):
        with self.assertRaises(SystemExit) as caught:
            main(['cut'])
        self.assertEqual(caught.exception.code,1)
    def test_bad_report_blocked(self):
        f=ROOT/HPGL_NAME.replace('.hpgl','.json')
        original=f.read_bytes()
        try:
            data=json.loads(original)
            data['settings']['x_scale']=42
            f.write_text(json.dumps(data))
            with self.assertRaises(ValueError):validate()
        finally:
            f.write_bytes(original)
if __name__=='__main__':unittest.main()
