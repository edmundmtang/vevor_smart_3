VEVOR SMART 3 CUTTER — v0.15 experimental geometry compensation
=============================================================

MAIN PROJECT README (maintained from previous releases).

FILES
  smart3_cut.py             SVG-to-HPGL and guarded Windows USB sender
  loop_closure.py           Straight-run seam selection and symmetric multi-segment overlap
  blade_offset.py           EXPERIMENTAL drag-knife holder trajectory model
  settings.txt              Provisional axis calibration, force/speed and mat settings
  smart3_calibrate.py       Axis calibration regression tool
  smart3_usb_probe.py       USBPRINT open-only probe
  blender_mask_to_svg.py   Blender outline exporter
  svg_grid.py               SVG grid generator
  calibration_loops.svg     5, 7.5, 10, 15 mm loop sheet
  calibration_corners.svg   Mirrored corner-angle test sheet
  *_legacy.svg             Previous small-feature test patterns
  test_*.py                Offline automated geometry and CLI tests
  BLADE_GEOMETRY_README.txt Current v0.15 usage, limitations and safety
  CLOSURE_MODES_README.txt v0.13 historical notes (first-edge overlap is superseded)
  CALIBRATION_*.txt, LOOP_CLOSURE_README.txt historical calibration notes

CURRENT CALIBRATION (provisional)
  x_scale = 0.74906512; y_scale = 3.59950979
  x_offset = 0.0; y_offset = 0.0
  Force 200, speed 100 are device command values; not verified physical units.

QUICK START (PowerShell in project directory)
  py -m unittest discover -v
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 1.0 --output loops_10.hpgl
  py smart3_cut.py calibration_corners.svg --dry-run --blade-offset-mm 0.2 --output corners_offset_02.hpgl

Do not run an offset-compensated physical cut without inspecting the generated
HPGL and understanding that blade-holder pivots can cut outside the nominal SVG.
Blade offset is an unknown mechanical parameter: 0.2 mm above is an example,
NOT a measured or recommended calibrated value.

For guarded physical cutting, the existing --cut --confirm-live-test I_ACCEPT_MOVEMENT
mechanism remains. Secure material, load mat, set displayed Y near -115 and press
physical Origin, inspect bounds and supervise cutter. A successful USB WriteFile
does NOT establish device execution. No USB handshake or buffer-size proof exists.

SAFETY / LIMITATIONS
  Default blade offset 0.0 (disabled); default overlap 0.0 (disabled).
  Closed contours use symmetric overlap: total N mm is split N/2 before and N/2 after the nominal seam, following the original contour across corners and curves. The physical blade-down start shifts backward; the nominal seam stays fixed. Overlap must be less than the perimeter.
  Requested overlap is limited by CLI to 5 mm. It is applied before offset.
  --blade-offset-mm 0..2 mm (experimental); --blade-arc-step-deg 1..45.
  At corners the holder pivots about the theoretical blade-tip vertex.
  These holder motions are not strictly on the nominal SVG path and can
  produce unwanted blade marks, especially at the first engagement.
  Keep-inside / keep-outside remain intent metadata only: NO off-contour
  lead-ins or region/collision planning are implemented.
  --lead-in-mm > 0 is rejected. No physical v0.15 cuts have been validated.
  Physical mat bounds 304.8 x 304.8 mm, warn at >=90% of either axis.
  The check uses planned holder-path samples, not the actual blade-tip track.
  SVG transforms unsupported; flatten first. For SVG <path> install svgpathtools.

V0.15 RECOMMENDED OFFLINE TEST:
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 2.0 --blade-offset-mm 0 --output loops_symmetric_20.hpgl
  py -m unittest discover -v

WARNING: v0.15 changes the meaning of --loop-overlap-mm from forward-only to symmetric TOTAL overlap. Review any existing commands before cutting.


v0.16 calibration addition: calibration_mirrored_l_gaps.svg, MIRRORED_L_GAP_TEST_README.txt, mirrored_l_geometry.csv, and test_mirrored_l_gaps.py. Six mirrored-L open-path approach tests (0/2 mm gaps; X/Y/45-degree diagonal). Cutting algorithm remains v0.15.


v0.17 compact horizontal travel-direction calibration: calibration_horizontal_travel_direction.svg, HORIZONTAL_TRAVEL_TEST_README.txt, horizontal_travel_geometry.csv and test_horizontal_travel.py. Four mirrored-L pairs (+X/-X x 0/2 mm gap), 115x100 mm canvas. Cutting logic unchanged. Future blade-tip tracking/overshoot idea documented but NOT implemented.

v0.18 OFFLINE BLADE-TIP ALGORITHM PROTOTYPE
==========================================
See BLADE_TIP_V018_README.txt. New: blade_tip_model.py,
smart3_blade_tip_preview.py, test_blade_tip_model.py. The existing
smart3_cut.py live-cutting path and v0.17 behavior are UNCHANGED.
This prototype does NOT generate HPGL or send USB data.

v0.19 EXPERIMENTAL COMPACT TEST (offline generator; existing cutter unchanged)
--------------------------------------------------------------------------
See V019_EXPERIMENTAL_README.txt. Run py smart3_v019_compact.py to generate
baseline and experimental SVGs. Compare on scrap vinyl, dry-run first.
This is a bounded empirical inverse-path prototype, NOT calibrated compensation.


V0.20 STATEFUL BLADE-TIP GRID (EXPERIMENTAL)
----------------------------------------
Run: py smart3_v020_grid.py
Creates v020_grid_baseline.svg and v020_grid_experimental.svg.
Nine cells (row-major): 1-4 squares; 5 opposing horizontal Ls;
6 opposing diagonal corners; 7 circle; 8 star 0 degrees;
9 star 36 degrees. Two paths in cells 5 and 6.
Grid 124 x 111 mm, three rows x three columns.

Model: finite-recovery orientation response, X/Y rotation parameters,
and signed persistent approach offset (default 0.09 mm X, 0 mm Y).
Iterative sampled inverse estimates holder commands from desired blade cuts.
No per-corner lookup table. Rotation parameters and physical offset are
UNIDENTIFIED experimental guesses, not calibrated physical measurements.
The model is phenomenological and the inverse is not validated on hardware.
Closed polygons start with a same-edge conditioning segment; finely sampled
closed curves start without a lead-in to avoid a tangent excursion. Open shapes
use off-contour lead-ins. Curves are also compensated, unlike v0.19.
The SVG generator never sends USB data. Off-contour cuts can damage artwork.

First run: py smart3_v020_grid.py
Then: py smart3_cut.py v020_grid_baseline.svg --dry-run
      py smart3_cut.py v020_grid_experimental.svg --dry-run
Only on sacrificial material, with origin and mat placement checked, use:
      py smart3_cut.py v020_grid_baseline.svg --cut --confirm-live-test I_ACCEPT_MOVEMENT
      py smart3_cut.py v020_grid_experimental.svg --cut --confirm-live-test I_ACCEPT_MOVEMENT
Use separate material for each pattern; never cut both on same patch.
Force 200, speed 100 unless your settings.txt differs.
Keep additional blade-offset compensation disabled (0) to avoid double correction.
Numbers are assigned by grid position; they are NOT cut into the material.

======================================================================
v0.21 CLEAN STATEFUL BLADE-TIP EXPERIMENT (2026-11-12)
======================================================================
The cutter above remains the guarded existing SVG-to-HPGL engine. The new
experimental algorithm is in blade_tip_stateful.py and smart3_v021_grid.py.
This is an offline experimental model, NOT a validated physical inverse.

Generate the nine-case grid (four squares, opposing Ls, opposing diagonal Vs,
circle, and two five-point stars rotated by 36 degrees):
    py smart3_v021_grid.py

Generate HPGL without sending any cutting data:
    py smart3_cut.py v021_grid_experimental.svg --dry-run

ONLY AFTER confirming origin, vinyl coverage and intended blade travel on
scrap material, a guarded live run is possible:
    py smart3_cut.py v021_grid_experimental.svg --cut --confirm-live-test I_ACCEPT_MOVEMENT

Default model: blade offset .20 mm (unverified), X/Y rotation response 1/1,
minimum approach X/Y .09/0 mm, recovery 1.39 mm, conditioning 3 mm,
max correction .85 mm, vertex weight 2.5, 12 iterations.

Parameter exploration without touching the main cutter:
    py smart3_v021_grid.py --x-rotation 1.1 --y-rotation 1.0 --vertex-weight 3.0

Important cautions:
* The empirical parameters are NOT uniquely identified by existing test cuts.
* The persistent lateral offset is an assumed symmetric split of the measured
  opposing-path gap, not a directly measured absolute blade position.
* Open paths may contain off-contour conditioning cuts. Use scrap vinyl.
* The windowed direction model and inverse are heuristics; an accurate sharp
  corner is not guaranteed. Watch for undercut, hooks and overcuts.
* Keep --blade-offset-mm 0 and --loop-overlap-mm 0 on the cutter for this test
  to avoid stacking independent compensation algorithms.
* The generator uses the same nine-case geometry as v0.20. The generated
  baseline is optional; it is not necessary to consume vinyl repeating it.
* Existing settings.txt, USB guard, mat limits, and README history retained.

Active files are deliberately lean: historical one-off geometry experiments,
old blade-tip preview models, prior versions' generated SVGs and duplicated
readmes have been omitted from this package. The previous ZIPs remain the
historical archive. Existing loop_closure.py and blade_offset.py are retained
because smart3_cut.py still imports/uses them for optional legacy behavior.

Tests:
    py -m unittest discover -p "test_*.py" -q


V0.22 CORNER-CONTACT DIAGNOSTICS (CURRENT)
-----------------------------------------
Run py smart3_v022_grid.py then dry-run v022_grid_experimental.svg.
Cells 1-2: identical squares retained as repeatability/placement controls.
Cells 3-4: opposing 90-degree corners, second rotated 90 degrees.
Cell 5: opposing Ls (unchanged); cell 6: opposing 45-degree corners
(unchanged and nominally touching at the center); cell 7: circle;
cells 8-9: five-point stars at 0 and 36 degrees.

The inverse model now permits a small ADDITIONAL bounded correction around
actual geometric vertices, scaled by turn angle. It does not add a hard-coded
corner overshoot or promise closure. Default corner-extra 0.25 mm; maximum
correction at a 90-degree vertex is 0.85+0.25=1.10 mm. The actual blade-tip
model is still phenomenological and unvalidated. Off-contour cuts possible.

Run baseline only if desired; do not use the cutter's separate --blade-offset-mm
or --loop-overlap-mm on these generated compensated SVGs.


v0.24 experimental blade-tip grid
--------------------------------
Run `py smart3_v024_grid.py` then `py smart3_cut.py v024_grid_experimental.svg --dry-run`.
See V024_TEST_GUIDE.txt. The regression-inducing v0.23 Y-history amplitude
is disabled by default. Optional --y-history-mm is experimental only.
The inverse retains the best simulated fit across iterations.
This is NOT physically validated and may cut outside the desired contour.


v0.25 — geometry scale stage before blade-tip compensation
---------------------------------------------------------
Run `py smart3_v025_grid.py --trial-square-dimension-factors` to test optional
X/Y geometry factors based on one measured 16 mm square (15.65 X, 15.47 Y).
The generator scales each cell's intended paths about their shared center, then
uses the unchanged v0.24 inverse model. Defaults are X=Y=1.0.
`settings.txt` and the main cutter's machine calibration are unchanged.
See V025_TEST_GUIDE.txt for dry-run, guarded cutting, and cautions.

V0.26 GAP PROBE
---------------
See V026_TEST_GUIDE.txt. Default history correction remains zero. The signed
approach-history term is experimental; compare +/- polarity on separate scrap.
No dimensional correction is applied in the supplied test SVGs.

V0.27 NEGATIVE Y-HISTORY MAGNITUDE SWEEP
---------------------------------------
See V027_TEST_GUIDE.txt. Physical v0.26 results favor negative polarity:
-0.225 mm reduced case 4 gap to 0.20 mm and case 6 gap to 0.38 mm,
versus approximately 0.45 mm in the v0.24 baseline. This is not yet a
validated general-purpose blade compensation algorithm.

v0.27 changes ONLY the permitted negative history-amplitude range (to
-0.400 mm), and supplies three precomputed four-path SVGs at -0.225,
-0.300, and -0.375 mm. The continuous state, angular gate, inverse solver,
corner behavior, X/Y machine calibration, and geometry scale=1.0 remain
unchanged. No extra compensation should be applied to the precomputed SVGs.
The correction remains off by default. Stop testing if cuts collide or
become distorted. These patterns have overlapping placement; use fresh vinyl.

V0.28 CORNER-APEX TEST (EXPERIMENTAL)
-----------------------------------
See V028_TEST_GUIDE.txt. Added optional corner_apex_mm to the stateful
inverse model (default 0). Outward vertex targets are capped at 0.30 mm
and 15% of adjacent edge lengths. The v0.27 -0.300 mm Y-history setting
is held fixed in three gap-only SVG variants. No general cutter-side
blade-tip compensation or machine calibration changes are made.
