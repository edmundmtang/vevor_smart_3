HISTORICAL DOCUMENT (v0.12). For current v0.13 options, see README.txt and CLOSURE_MODES_README.txt.

Smart 3 physical loop and corner calibration patterns (v0.12 code, suite edition)
=============================================================================

IMPORTANT: This suite does NOT implement blade-tip corner compensation.
It is intended to measure the existing behavior and seam relocation before
introducing new compensation parameters. Cutting remains experimental.

FILES
calibration_loops.svg: 175 x 145 mm, 25 CLOSED contours.
  Rows (top to bottom): nominal sizes 1, 2, 3, 5, 10 mm.
  Columns (left to right): square, 1.5:1 rectangle, triangle, circle, octagon.
  All shapes are at distinct locations. Do not use their spacing as a measure.
  Inspect seam hooks, gap, corner rounding, shape dimensions, and repeat cuts.

calibration_corners.svg: 155 x 145 mm, 12 OPEN two-leg corners.
  Rows (top to bottom): nominal interior turning angles 30, 45, 60, 90, 120, 150 degrees.
  Left/right columns: mirrored turning direction. Each leg nominally 8 mm.
  Note: geometric turning angle conventions can differ; compare paired corners.
  Open paths deliberately bypass seam relocation.

WORKFLOW
  1. Dry-run each pattern with original seam behavior, then with auto-straight.
  2. For a controlled comparison, use the same SVG/material/speed/force and
     compare two separately cut placements; never cut both passes at the same
     location (the second pass changes the result).
  3. Photograph with scale and record: shape, size, direction, seam gap (mm),
     visible hook (mm), corner rounding (mm), and notes.
  4. Avoid changing scale and blade settings while comparing seam strategies.

EXAMPLES (from this folder)
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start original
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight
  py smart3_cut.py calibration_corners.svg --dry-run --loop-start auto-straight
  py -m unittest -v test_loop_closure.py test_calibration_geometry.py

Live cutting requires the existing --cut --confirm-live-test I_ACCEPT_MOVEMENT
guards. Verify dry-run, origin, mat, material, and clearance first.

PARAMETERS NOW
  --min-loop-straight (default 0.5 mm): threshold for moving seam; too short
     => original seam preserved.
  --loop-turn-tolerance (default 5 degrees): turn allowed between adjacent
     edges in a run; not a blade-offset parameter.
  --loop-start original | auto-straight: seam relocation toggle.

FUTURE, NOT IMPLEMENTED
  blade-tip offset (mm), corner swivel compensation, tangent entry/exit,
  optional same-path overlap (mm). These require physical measurement and
  careful mat-bound checks before live use.

LIMITATIONS
  Current run detection considers per-vertex turns and can misclassify
  gradual arcs as straight runs. This is a known algorithm limitation.
  No actual cut validation is claimed. Small segments may merge after HPGL
  rounding; evaluate generated HPGL before cutting.
