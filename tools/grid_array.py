"""Generate an SVG grid of repeated, translated Smart3 cut contours.

The margin translates *geometry*, not just the SVG page boundary. This
provides clearance for the holder-path compensation near the origin.
"""
import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
from smart3_cut import parse_svg, get_physical_bounds


def generate(source, output, rows, cols, gap_mm=5.0, margin_mm=5.0):
    if not (1 <= rows <= 100 and 1 <= cols <= 100):
        raise ValueError('Rows/columns must be 1..100')
    if any(not math.isfinite(v) or v < 0 for v in (gap_mm, margin_mm)):
        raise ValueError('Gap and margin must be finite and nonnegative')
    paths = parse_svg(source)
    if not paths:
        raise ValueError('No geometry')
    x0, y0, x1, y1 = get_physical_bounds(paths)
    shape_w, shape_h = x1 - x0, y1 - y0
    if shape_w <= 0 or shape_h <= 0:
        raise ValueError('Zero-size geometry')
    dx, dy = shape_w + gap_mm, shape_h + gap_mm
    content_w = shape_w * cols + gap_mm * (cols - 1)
    content_h = shape_h * rows + gap_mm * (rows - 1)
    page_w, page_h = content_w + 2 * margin_mm, content_h + 2 * margin_mm
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{page_w:.6f}mm" height="{page_h:.6f}mm" viewBox="0 0 {page_w:.6f} {page_h:.6f}">']
    for r in range(rows):
        for c in range(cols):
            for path in paths:
                coords = [(x - x0 + margin_mm + c * dx, y - y0 + margin_mm + r * dy) for x, y in path]
                d = 'M ' + ' '.join(('L ' if i else '') + f'{x:.6f},{y:.6f}' for i, (x, y) in enumerate(coords))
                lines.append(f'<path d="{d}" fill="none" stroke="black" stroke-width="0.05"/>')
    lines.append('</svg>')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return len(paths) * rows * cols, page_w, page_h


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--rows', type=int, required=True)
    p.add_argument('--cols', type=int, required=True)
    p.add_argument('--gap-mm', type=float, default=5.0)
    p.add_argument('--margin-mm', type=float, default=5.0, help='Clearance around actual cut geometry (default: 5 mm)')
    a = p.parse_args()
    try:
        contours, w, h = generate(a.source, a.output, a.rows, a.cols, a.gap_mm, a.margin_mm)
    except (ValueError, OSError) as exc:
        p.error(str(exc))
    print(f'Generated {a.rows*a.cols} copies ({contours} contours), {w:.2f} x {h:.2f} mm, margin {a.margin_mm:.2f} mm')


if __name__ == '__main__':
    main()
