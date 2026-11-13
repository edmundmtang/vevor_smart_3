"""Export Blender mesh edges to Smart3-compatible SVG (run inside Blender).

The exported geometry is the evaluated world-XY projection, without modifying the
source mesh.  SVG coordinates are in millimetres; each unique mesh edge is cut
exactly once.  Degree != 2 vertices split paths; degree-2 components form loops.

Configure SETTINGS below, then run this file in Blender's Scripting workspace.
The geometry/export helpers can also be tested with ordinary Python (no bpy).
"""
from collections import Counter
from pathlib import Path
import math
import xml.etree.ElementTree as ET

# --- USER SETTINGS ---
OBJECT_NAME = None  # None: active object; otherwise exact Blender object name
OUTPUT_PATH = ""  # Empty: write beside the saved .blend file as smart3_mesh.svg
BLENDER_UNITS_TO_MM = 1.0  # 1 world coordinate unit = 1 mm; adjust explicitly
BORDER_MM = 1.0
STROKE_WIDTH_MM = 0.05  # Display-only stroke; SVG coordinates are mm
BORDER_MODE = "margin"  # "margin" or "cut" (adds a cuttable outer rectangle)
OUTPUT_PRECISION = 6
ZERO_LENGTH_TOLERANCE_MM = 1e-9
USE_EVALUATED_MESH = False  # True: include modifiers; topology may change


def edge_key(a, b):
    return (min(a, b), max(a, b))


def extract_paths(edges):
    """Return (vertex-id sequence, closed) paths, covering every edge once."""
    unique = {edge_key(a, b) for a, b in edges if a != b}
    adjacency = {}
    for a, b in unique:
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    unused = set(unique)
    paths = []
    for start in sorted(v for v, neighbors in adjacency.items() if len(neighbors) != 2):
        for neighbor in sorted(adjacency[start]):
            if edge_key(start, neighbor) not in unused:
                continue
            vertices = [start, neighbor]
            unused.remove(edge_key(start, neighbor))
            previous, current = start, neighbor
            while len(adjacency[current]) == 2:
                nxt = next(n for n in sorted(adjacency[current]) if n != previous)
                k = edge_key(current, nxt)
                if k not in unused:
                    break
                vertices.append(nxt)
                unused.remove(k)
                previous, current = current, nxt
            paths.append((vertices, False))
    while unused:
        start, current = min(unused)
        vertices = [start, current]
        unused.remove(edge_key(start, current))
        previous = start
        while True:
            if len(adjacency[current]) != 2:
                raise RuntimeError("Unexpected residual non-loop edge")
            nxt = next(n for n in sorted(adjacency[current]) if n != previous)
            k = edge_key(current, nxt)
            if k not in unused:
                raise RuntimeError("Loop topology inconsistency")
            unused.remove(k)
            if nxt == start:
                paths.append((vertices, True))
                break
            vertices.append(nxt)
            previous, current = current, nxt
    walked = []
    for vertices, closed in paths:
        walked.extend(edge_key(a, b) for a, b in zip(vertices, vertices[1:]))
        if closed:
            walked.append(edge_key(vertices[-1], vertices[0]))
    if Counter(walked) != Counter(unique):
        raise RuntimeError("Edge coverage validation failed")
    return paths


def export_geometry(vertices_xy, edges, output_path, *, units_to_mm=1.0,
                    border_mm=1.0, border_mode="margin", precision=6,
                    tolerance_mm=1e-9, stroke_width_mm=0.05):
    """Write SVG from {index:(world_x,world_y)} and iterable of edge pairs."""
    if border_mode not in ("margin", "cut"):
        raise ValueError("border_mode must be 'margin' or 'cut'")
    if not math.isfinite(units_to_mm) or units_to_mm <= 0:
        raise ValueError("units_to_mm must be positive and finite")
    if not math.isfinite(border_mm) or border_mm < 0:
        raise ValueError("border_mm must be nonnegative and finite")
    if not math.isfinite(tolerance_mm) or tolerance_mm < 0:
        raise ValueError("tolerance_mm must be nonnegative and finite")
    if not math.isfinite(stroke_width_mm) or stroke_width_mm <= 0:
        raise ValueError("stroke_width_mm must be positive and finite")
    if not isinstance(precision, int) or not 0 <= precision <= 12:
        raise ValueError("precision must be an integer between 0 and 12")
    coords = {}
    for vid, (x, y) in vertices_xy.items():
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError("Non-finite vertex coordinate")
        coords[vid] = (x * units_to_mm, y * units_to_mm)
    unique = set()
    skipped = 0
    for a, b in edges:
        if a not in coords or b not in coords:
            raise ValueError("Edge references a missing vertex")
        if a == b or math.dist(coords[a], coords[b]) <= tolerance_mm:
            skipped += 1
            continue
        unique.add(edge_key(a, b))
    if not unique:
        raise ValueError("No usable mesh edges")
    paths = extract_paths(unique)
    used = {v for a, b in unique for v in (a, b)}
    x0 = min(coords[v][0] for v in used)
    x1 = max(coords[v][0] for v in used)
    y0 = min(coords[v][1] for v in used)
    y1 = max(coords[v][1] for v in used)
    width, height = x1 - x0, y1 - y0
    if width <= 0 or height <= 0:
        raise ValueError("Projected geometry must have positive width and height")
    page_w, page_h = width + 2 * border_mm, height + 2 * border_mm
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}svg", {
        "version": "1.1", "width": f"{page_w:.{precision}f}mm",
        "height": f"{page_h:.{precision}f}mm",
        "viewBox": f"0 0 {page_w:.{precision}f} {page_h:.{precision}f}",
    })
    for index, (vertex_ids, closed) in enumerate(paths):
        points = []
        for vid in vertex_ids:
            x, y = coords[vid]
            points.append(f"{x-x0+border_mm:.{precision}f},{y1-y+border_mm:.{precision}f}")
        ET.SubElement(root, f"{{{ns}}}{'polygon' if closed else 'polyline'}", {
            "id": f"cut_path_{index:04d}", "points": " ".join(points),
            "fill": "none", "stroke": "#000000",
            "stroke-width": f"{stroke_width_mm:.{precision}f}",
        })
    if border_mode == "cut":
        # Border sits halfway through the blank margin, never at the page edge.
        ET.SubElement(root, f"{{{ns}}}rect", {
            "id": "optional_border_cut",
            "x": f"{border_mm/2:.{precision}f}",
            "y": f"{border_mm/2:.{precision}f}",
            "width": f"{width+border_mm:.{precision}f}",
            "height": f"{height+border_mm:.{precision}f}",
            "fill": "none", "stroke": "#000000",
            "stroke-width": f"{stroke_width_mm:.{precision}f}",
        })
    if hasattr(ET, "indent"):
        ET.indent(root, space="  ")
    dest = Path(output_path).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(dest, encoding="utf-8", xml_declaration=True)
    return {"path": str(dest), "paths": len(paths), "edges": len(unique),
            "skipped": skipped, "width_mm": width, "height_mm": height,
            "page_width_mm": page_w, "page_height_mm": page_h}


def main():
    try:
        import bpy
    except ImportError as exc:
        raise RuntimeError("Run main() inside Blender's Python environment") from exc
    obj = bpy.data.objects.get(OBJECT_NAME) if OBJECT_NAME else bpy.context.active_object
    if obj is None or obj.type != "MESH":
        raise RuntimeError("Select a mesh object or configure OBJECT_NAME")
    if obj.mode != "OBJECT":
        raise RuntimeError("Switch the mesh to Object Mode before exporting")
    if not OUTPUT_PATH:
        if not bpy.data.filepath:
            raise RuntimeError("Save the .blend file or set OUTPUT_PATH explicitly")
        output = str(Path(bpy.data.filepath).with_name("smart3_mesh.svg"))
    else:
        output = bpy.path.abspath(OUTPUT_PATH)
    evaluated = None
    mesh = obj.data
    try:
        if USE_EVALUATED_MESH:
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
        matrix = obj.matrix_world
        vertices = {v.index: tuple((matrix @ v.co)[:2]) for v in mesh.vertices}
        edges = [tuple(e.vertices) for e in mesh.edges]
        report = export_geometry(vertices, edges, output,
                                 units_to_mm=BLENDER_UNITS_TO_MM,
                                 border_mm=BORDER_MM,
                                 border_mode=BORDER_MODE,
                                 precision=OUTPUT_PRECISION,
                                 tolerance_mm=ZERO_LENGTH_TOLERANCE_MM,
                                 stroke_width_mm=STROKE_WIDTH_MM)
    finally:
        if evaluated is not None:
            evaluated.to_mesh_clear()
    print("Smart3 SVG exported:", report)
    print("No Blender mesh data or scene unit settings were modified.")
    print("Check scale and preview using smart3.py before any live cut.")


if __name__ == "__main__":
    main()
