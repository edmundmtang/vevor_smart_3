"""Pure Python Blender exporter checks (Blender itself not required)."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('blender_export', ROOT/'tools'/'blender_export.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class BlenderExportTests(unittest.TestCase):
    def test_square_closed_once_and_parser_compatible(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'square.svg'
            report = exporter.export_geometry({0:(0,0),1:(16,0),2:(16,16),3:(0,16)},
                                               [(0,1),(1,2),(2,3),(3,0)], output)
            self.assertEqual((report['paths'],report['edges']), (1,4))
            root = ET.parse(output).getroot()
            self.assertEqual(root.get('width'), '18.000000mm')
            self.assertEqual(len(root.findall('{*}polygon')),1)
            from smart3_cut import parse_svg
            contours = parse_svg(output)
            self.assertEqual(len(contours),1)
            self.assertEqual(contours[0][0], contours[0][-1])
            self.assertAlmostEqual(max(x for x,y in contours[0])-min(x for x,y in contours[0]),16)

    def test_branch_splits_without_repeated_edges(self):
        paths = exporter.extract_paths([(0,1),(1,2),(1,3)])
        self.assertEqual(len(paths),3)
        self.assertTrue(all(not closed for _,closed in paths))

    def test_units_and_optional_border(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'border.svg'
            report=exporter.export_geometry({0:(0,0),1:(2,0),2:(2,2),3:(0,2)},
                [(0,1),(1,2),(2,3),(3,0)],output,units_to_mm=5,border_mode='cut')
            self.assertAlmostEqual(report['width_mm'],10)
            from smart3_cut import parse_svg
            self.assertEqual(len(parse_svg(output)),2)

    def test_rejects_bad_scale_and_zero_area(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                exporter.export_geometry({0:(0,0),1:(1,1)},[(0,1)],Path(d)/'a.svg',units_to_mm=0)
            with self.assertRaises(ValueError):
                exporter.export_geometry({0:(0,0),1:(1,0)},[(0,1)],Path(d)/'a.svg')


if __name__=='__main__':
    unittest.main()
