"""Create a physical-mm grid of copies of a Smart 3-compatible SVG.

Uses smart3_cut.parse_svg to normalize supported source geometry into mm.
Output contains only untransformed polylines/polygons, no <use> or transforms.
"""
import argparse
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from smart3_cut import parse_svg

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)

def grid_svg(source, destination, nx, ny, gap_x, gap_y, margin, max_paths, preview_stroke):
    if nx < 1 or ny < 1 or nx > 100 or ny > 100:
        raise ValueError('repeat counts must be between 1 and 100')
    if any(not math.isfinite(v) or v < 0 for v in (gap_x, gap_y, margin)):
        raise ValueError('gaps and margin must be finite nonnegative millimeters')
    if not math.isfinite(preview_stroke) or preview_stroke <= 0:
        raise ValueError('preview stroke must be positive and finite')
    if source.resolve() == destination.resolve():
        raise ValueError('Output cannot overwrite input')
    outlines = parse_svg(source)
    if len(outlines) * nx * ny > max_paths:
        raise ValueError(f'Grid exceeds maximum {max_paths} paths; reduce repeats or increase --max-paths')
    coords = [p for outline in outlines for p in outline]
    min_x = min(p[0] for p in coords)
    max_x = max(p[0] for p in coords)
    min_y = min(p[1] for p in coords)
    max_y = max(p[1] for p in coords)
    tile_w, tile_h = max_x-min_x, max_y-min_y
    if tile_w <= 0 or tile_h <= 0:
        raise ValueError('Source cutting geometry must have nonzero X and Y extents')
    total_w = 2*margin + nx*tile_w + (nx-1)*gap_x
    total_h = 2*margin + ny*tile_h + (ny-1)*gap_y
    root = ET.Element(f'{{{NS}}}svg', {
        'version':'1.1', 'width':f'{total_w:.6f}mm', 'height':f'{total_h:.6f}mm',
        'viewBox':f'0 0 {total_w:.6f} {total_h:.6f}'})
    for row in range(ny):
        for col in range(nx):
            dx = margin + col*(tile_w+gap_x)-min_x
            dy = margin + row*(tile_h+gap_y)-min_y
            for idx, outline in enumerate(outlines):
                # Closed polygons must have at least three distinct vertices.
                closed = len(outline) >= 4 and math.dist(outline[0], outline[-1]) < 1e-8
                pts = outline[:-1] if closed else outline
                tag = 'polygon' if closed and len(pts) >= 3 else 'polyline'
                point_text = ' '.join(f'{x+dx:.6f},{y+dy:.6f}' for x,y in pts)
                ET.SubElement(root, f'{{{NS}}}{tag}', {
                    'id':f'cell_{row+1}_{col+1}_path_{idx+1}',
                    'points':point_text, 'fill':'none', 'stroke':'#000000',
                    'stroke-width':f'{preview_stroke:.6f}',
                    'stroke-linecap':'round', 'stroke-linejoin':'round'})
    try: ET.indent(root, space='  ')
    except AttributeError: pass
    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(destination, encoding='utf-8', xml_declaration=True)
    return tile_w, tile_h, total_w, total_h, len(outlines)*nx*ny

def main():
    p=argparse.ArgumentParser(description='Repeat SVG cutting geometry in a physical-mm grid (no transforms)')
    p.add_argument('input', type=Path)
    p.add_argument('--repeat-x', type=int, required=True)
    p.add_argument('--repeat-y', type=int, required=True)
    p.add_argument('--gap-x', type=float, default=0, help='Physical spacing between tile geometry in mm')
    p.add_argument('--gap-y', type=float, default=0)
    p.add_argument('--margin', type=float, default=1.0, help='Outer page margin in mm (default: 1)')
    p.add_argument('--preview-stroke', type=float, default=0.02, help='Visual stroke width in mm (default: 0.02; not cutter geometry)')
    p.add_argument('--output', type=Path)
    p.add_argument('--max-paths', type=int, default=20000)
    args=p.parse_args()
    out=args.output or args.input.with_name(args.input.stem+f'_grid_{args.repeat_x}x{args.repeat_y}.svg')
    try:
        tw,th,w,h,n=grid_svg(args.input,out,args.repeat_x,args.repeat_y,args.gap_x,args.gap_y,args.margin,args.max_paths,args.preview_stroke)
    except (ValueError,ET.ParseError,OSError) as e: p.exit(1,f'Error: {e}\n')
    print(f'Source geometry: {tw:.3f} x {th:.3f} mm')
    print(f'Grid: {args.repeat_x} columns x {args.repeat_y} rows; gaps {args.gap_x} / {args.gap_y} mm')
    print(f'Output: {w:.3f} x {h:.3f} mm, {n} paths: {out.resolve()}')
    print('NOTE: Cutter v0.8 live mode limits calibrated command coordinates to 0..50 mm on both axes.')

if __name__=='__main__': main()
