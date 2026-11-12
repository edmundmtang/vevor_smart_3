"""Blender: export edges of object 'mask' as Smart 3-compatible SVG.

World XY -> SVG, 1 Blender Unit = 1 mm with the configured scene units.
Only mesh edges generate cuts; branches split; no edge is repeated.
"""
import bpy
import math
import os
import xml.etree.ElementTree as ET
from collections import Counter

# === USER SETTINGS ===
OUTPUT_PATH = r'D:\3D\prints\dice\iroha_dice\masking_cuts_mesh.svg'
EXPORT_MESH_NAME = 'mask'
SVG_DPI = 72.0  # physical size is independently specified in mm
OUTPUT_PRECISION = 6
BORDER_MM = 1.0
BORDER_MODE = 'margin'  # 'margin' (blank 1 mm) or 'cut' (also cut outer rectangle)
FLATTEN_SOURCE_MESH = True  # destructive: move mesh vertices to world Z=0
ZERO_LENGTH_TOLERANCE = 1e-9


def mm_to_svg(v):
    return v*SVG_DPI/25.4


def edge_key(a,b):
    return (min(a,b),max(a,b))


def extract_paths(edges):
    adjacency={}
    for a,b in edges:
        adjacency.setdefault(a,set()).add(b)
        adjacency.setdefault(b,set()).add(a)
    unused={edge_key(a,b) for a,b in edges}
    paths=[]
    # Deterministic traversal from endpoints and branches.
    for start in sorted(v for v,n in adjacency.items() if len(n)!=2):
        for neighbor in sorted(adjacency[start]):
            if edge_key(start,neighbor) not in unused: continue
            vertices=[start,neighbor]
            unused.remove(edge_key(start,neighbor))
            previous,current=start,neighbor
            while len(adjacency[current])==2:
                nxt=next(n for n in sorted(adjacency[current]) if n!=previous)
                k=edge_key(current,nxt)
                if k not in unused: break
                vertices.append(nxt)
                unused.remove(k)
                previous,current=current,nxt
            paths.append((vertices,False))
    # Remaining degree-2 components are loops.
    while unused:
        start,current=min(unused)
        vertices=[start,current]
        unused.remove(edge_key(start,current))
        previous=start
        while True:
            if len(adjacency[current])!=2:
                raise RuntimeError('Unexpected non-loop residual edge')
            nxt=next(n for n in sorted(adjacency[current]) if n!=previous)
            k=edge_key(current,nxt)
            if nxt==start:
                if k not in unused: raise RuntimeError('Missing loop closing edge')
                unused.remove(k)
                paths.append((vertices,True))
                break
            if k not in unused: raise RuntimeError('Unexpected loop topology')
            unused.remove(k)
            vertices.append(nxt)
            previous,current=current,nxt
    expected=set(edges)
    walked=[]
    for vertices,closed in paths:
        walked.extend(edge_key(a,b) for a,b in zip(vertices,vertices[1:]))
        if closed: walked.append(edge_key(vertices[-1],vertices[0]))
    counts=Counter(walked)
    if set(counts)!=expected or any(n!=1 for n in counts.values()):
        raise RuntimeError('Edge coverage validation failed')
    return paths


def main():
    if BORDER_MODE not in ('margin','cut'):
        raise ValueError('BORDER_MODE must be margin or cut')
    if not math.isfinite(BORDER_MM) or BORDER_MM < 0:
        raise ValueError('BORDER_MM must be nonnegative and finite')
    scene=bpy.context.scene
    scene.unit_settings.system='METRIC'
    scene.unit_settings.scale_length=0.001
    scene.unit_settings.length_unit='MILLIMETERS'
    obj=bpy.data.objects.get(EXPORT_MESH_NAME)
    if obj is None or obj.type!='MESH':
        raise RuntimeError(f'Expected a mesh object named {EXPORT_MESH_NAME!r}')
    if obj.mode!='OBJECT':
        bpy.context.view_layer.objects.active=obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='OBJECT')
    matrix=obj.matrix_world.copy()
    if FLATTEN_SOURCE_MESH:
        inv=matrix.inverted()
        for v in obj.data.vertices:
            world=matrix@v.co
            world.z=0.0
            v.co=inv@world
        obj.data.update()
        bpy.context.view_layer.update()
    world={v.index:matrix@v.co for v in obj.data.vertices}
    unique=set()
    skipped=0
    for e in obj.data.edges:
        a,b=e.vertices
        if a==b or (world[a]-world[b]).length <= ZERO_LENGTH_TOLERANCE:
            skipped+=1
            continue
        unique.add(edge_key(a,b))
    if not unique: raise RuntimeError('No usable mesh edges')
    paths=extract_paths(unique)
    used={v for edge in unique for v in edge}
    min_x=min(world[v].x for v in used)
    max_x=max(world[v].x for v in used)
    min_y=min(world[v].y for v in used)
    max_y=max(world[v].y for v in used)
    width=max_x-min_x
    height=max_y-min_y
    if width<=0 or height<=0: raise RuntimeError('Zero width or height geometry')
    page_w=width+2*BORDER_MM
    page_h=height+2*BORDER_MM
    ns='http://www.w3.org/2000/svg'
    ET.register_namespace('',ns)
    root=ET.Element(f'{{{ns}}}svg',{
        'version':'1.1', 'width':f'{page_w:.6f}mm', 'height':f'{page_h:.6f}mm',
        'viewBox':f'0 0 {mm_to_svg(page_w):.6f} {mm_to_svg(page_h):.6f}'})
    for index,(vertices,closed) in enumerate(paths):
        points=[]
        for vid in vertices:
            w=world[vid]
            x=mm_to_svg(w.x-min_x+BORDER_MM)
            y=mm_to_svg(max_y-w.y+BORDER_MM)
            points.append(f'{x:.{OUTPUT_PRECISION}f},{y:.{OUTPUT_PRECISION}f}')
        tag='polygon' if closed else 'polyline'
        ET.SubElement(root,f'{{{ns}}}{tag}',{
            'id':f'cut_path_{index:04d}', 'points':' '.join(points),
            'fill':'none','stroke':'#000000'})
    if BORDER_MODE=='cut':
        # A rectangle 1 mm outside geometry, not on the page boundary.
        x=mm_to_svg(BORDER_MM/2)
        y=mm_to_svg(BORDER_MM/2)
        w=mm_to_svg(width+BORDER_MM)
        h=mm_to_svg(height+BORDER_MM)
        ET.SubElement(root,f'{{{ns}}}rect',{
            'id':'optional_border_cut', 'x':f'{x:.6f}', 'y':f'{y:.6f}',
            'width':f'{w:.6f}', 'height':f'{h:.6f}',
            'fill':'none','stroke':'#000000'})
    try: ET.indent(root,space='  ')
    except AttributeError: pass
    folder=os.path.dirname(os.path.abspath(OUTPUT_PATH))
    os.makedirs(folder,exist_ok=True)
    ET.ElementTree(root).write(OUTPUT_PATH,encoding='utf-8',xml_declaration=True)
    print(f'Exported {len(paths)} mesh paths ({len(unique)} unique edges, {skipped} zero-length skipped)')
    print(f'Geometry {width:.3f} x {height:.3f} mm; page {page_w:.3f} x {page_h:.3f} mm')
    print(f'Border: {BORDER_MM} mm; mode: {BORDER_MODE}')
    print(f'Output: {OUTPUT_PATH}')
    print('Warning: Smart 3 v0.8 has a 50 mm live corrected-coordinate limit per axis.')

if __name__=='__main__': main()
