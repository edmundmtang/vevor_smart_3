import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_cli',ROOT/'smart3.py')
app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)

class ReleaseTests(unittest.TestCase):
    def test_defaults(self):
        c=app.DEFAULT_TRANSITION
        self.assertEqual((c.overshoot_mm,c.approach_mm,c.recovery_mm,c.easing),(.2,.5,1.5,'quintic'))
    def test_build_verify_tamper(self):
        with tempfile.TemporaryDirectory() as t:
            svg=Path(t)/'test.svg'
            svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40mm" height="40mm" viewBox="0 0 40 40"><rect x="5" y="5" width="16" height="16"/></svg>')
            hp=Path(t)/'test.hpgl'
            app.write(svg,hp)
            app.verify(svg,hp)
            hp.write_bytes(hp.read_bytes()+b'PD0,0;')
            with self.assertRaises(ValueError): app.verify(svg,hp)
    def test_source_change_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            svg=Path(t)/'test.svg'
            svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40mm" height="40mm" viewBox="0 0 40 40"><rect x="5" y="5" width="16" height="16"/></svg>')
            app.write(svg)
            svg.write_text(svg.read_text().replace('width="16"','width="17"'))
            with self.assertRaises(ValueError): app.verify(svg)
    def test_live_confirmation_required(self):
        with tempfile.TemporaryDirectory() as t:
            svg=Path(t)/'test.svg'
            self.assertRaises(SystemExit,app.main,['cut',str(svg)])
if __name__=='__main__':unittest.main()
