"""Grid layout regression: margin must move the paths, not just the page."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('grid_array', ROOT / 'tools' / 'grid_array.py')
grid = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grid)


class GridMarginTests(unittest.TestCase):
    def test_margin_moves_geometry_and_expands_page(self):
        import xml.etree.ElementTree as ET
        with tempfile.TemporaryDirectory() as tmp:
            source = ROOT / 'examples' / 'square.svg'
            output = Path(tmp) / 'grid.svg'
            n, w, h = grid.generate(source, output, 2, 4, 5.0, 5.0)
            self.assertEqual(n, 8)
            root = ET.parse(output).getroot()
            paths = list(root)
            self.assertEqual(len(paths), 8)
            import re
            coords = [tuple(map(float, xy)) for path in paths for xy in re.findall(r"(-?\d+\.\d+),(-?\d+\.\d+)", path.attrib["d"])]
            x0 = min(x for x, y in coords)
            y0 = min(y for x, y in coords)
            x1 = max(x for x, y in coords)
            y1 = max(y for x, y in coords)
            self.assertAlmostEqual(x0, 5.0, places=4)
            self.assertAlmostEqual(y0, 5.0, places=4)
            self.assertAlmostEqual(w - x1, 5.0, places=4)
            self.assertAlmostEqual(h - y1, 5.0, places=4)

    def test_invalid_margin_rejected(self):
        with self.assertRaises(ValueError):
            grid.generate(ROOT / 'examples' / 'square.svg', Path('unused.svg'), 2, 2, 5, -1)
