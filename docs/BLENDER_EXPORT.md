# Blender mesh-edge SVG export

Open `tools/blender_export.py` in Blender's **Scripting** workspace. Select a mesh
object, switch to **Object Mode**, save the `.blend` file, then click **Run Script**.
The output defaults to `smart3_mesh.svg` beside the `.blend` file. Change
`OBJECT_NAME` to select an object by name, or `OUTPUT_PATH` for a custom location.

## Units and coordinate mapping

`BLENDER_UNITS_TO_MM = 1.0` means **one world-space Blender coordinate unit equals
one millimetre**. This matches the original workflow when Blender scene units are
configured with metric scale length 0.001. If your mesh is modeled with one unit
per metre, use `BLENDER_UNITS_TO_MM = 1000.0`. Do not assume Blender's display
unit settings change the numeric coordinates automatically: verify a known 16 mm
feature in the resulting SVG before cutting.

`STROKE_WIDTH_MM = 0.05` sets the thin, visual-only line width in SVG millimetres; it does not change the cut centerline.

The script uses the object's world transform and projects XY to the SVG plane;
world Y is flipped to SVG Y. Source geometry is **not** flattened, and scene
units are **not** changed. `USE_EVALUATED_MESH` optionally exports modifier output
without modifying the original mesh.

Only mesh edges are exported. Branches split into separate open polylines; loops
are closed polygons. Repeated edges are removed. Duplicate coincident edges with
different vertex IDs are **not** deduplicated geometrically; clean overlapping
mesh geometry before exporting. The order of cut paths is deterministic but is
not optimized for minimum travel. The script does not guarantee cutting order.

`BORDER_MODE = 'margin'` adds blank space only. `'cut'` adds a cuttable rectangle
outside the mesh geometry; it can consume extra material and should be inspected.

## Cutter workflow

From the Smart3 project root, run:

```powershell
python .\smart3.py build "C:\path\to\smart3_mesh.svg"
python .\smart3.py preview "C:\path\to\smart3_mesh.svg"
python .\smart3.py check "C:\path\to\smart3_mesh.svg"
```

Review physical dimensions, contour count, preview, origin and mat bounds before
using the separately guarded `cut` command. The preview is a **holder trajectory**,
not a new source SVG. Do not feed it back into the cutter CLI.

## Compatibility and validation

The exporter emits only `<polyline>`, `<polygon>`, and optional `<rect>` elements
with no SVG transforms; these are supported by the current Smart3 parser. Pure
Python tests validate scale, topology, and parser compatibility. A real Blender export was used for a physically cut 2×4 grid with clean, closed loops.
