import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("blender_export", Path(__file__).resolve().parents[1] / "tools" / "blender_export.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class BlenderStrokeTests(unittest.TestCase):
    def test_thin_visual_stroke_on_paths_and_border(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "test.svg"
            mod.export_geometry({0:(0,0),1:(2,0),2:(2,2),3:(0,2)}, [(0,1),(1,2),(2,3),(3,0)], out, border_mode="cut")
            root=ET.parse(out).getroot()
            for el in root:
                self.assertEqual(el.get("stroke-width"), "0.050000")
