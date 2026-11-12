NOTE (v0.15): Historical v0.13 closure documentation below. Overlap is NOW symmetric, not forward-only. See README.txt and BLADE_GEOMETRY_README.txt for current behavior.

CLOSURE MODES / CALIBRATION — v0.13
==================================

IMPLEMENTED
  --cut-strategy no-waste (default): all blade-down motions stay on the
    input contour. No sacrificial entry or offset correction.
  --cut-strategy keep-inside: material intent = keep the cut-out shape.
  --cut-strategy keep-outside: material intent = keep the surrounding material.
    These two modes currently produce the SAME toolpath as no-waste. They are
    metadata/forward-compatible controls; off-contour lead-ins are not enabled.
  --contour-modes modes.json: per-path overrides; JSON object mapping
    zero-based SVG parsed outline indices to mode strings. E.g.:
       {"0":"keep-inside","1":"keep-outside","2":"no-waste"}
    Indices refer to the cutter's parsed path order, not SVG element IDs.
    Nested geometry is NOT automatically classified as waste or kept material.
  --loop-start auto-straight: relocate seam to midpoint of a straight run.
    Straight-run check rejects accumulated curvature above turn tolerance.
    If no run qualifies, retain the original seam.
  --loop-overlap-mm N: after returning to the seam, continue N mm along the
    first existing contour segment. Default 0. Max 5 mm. If first segment
    shorter than N, SKIP overlap for that path (reported). Open paths unchanged.
    HPGL coordinates are rounded to 40 units/mm after calibration.
  --lead-in-mm 0 only. Nonzero rejected (not implemented).

NOT IMPLEMENTED
  Waste-side curved/tangential lead-ins, collision/clearance checking,
  drag-knife tip offset and corner compensation, true blade orientation sensing.
  Never assume keep-inside/outside currently adds a lead-in.

CALIBRATION PROCEDURE
  1. Run: py -m unittest discover -v
  2. Use calibration_loops.svg (5, 7.5, 10, 15 mm rows; columns square,
     rectangle, circle, octagon). No 1–3 mm standard rows.
  3. Produce separate DRY RUNS for overlap 0, 0.2, 0.4, 0.6, 0.8 mm,
     with --loop-start auto-straight, --loop-overlap-mm VALUE, --output NAME.
  4. Inspect console per-path overlap-skipped messages and generated HPGL.
  5. Cut each setting on separate unused material areas. Verify physical
     origin and bounds before EVERY cut. Compare closure, hooks, double cuts,
     corner quality, and whether shapes peel free.
  6. Test calibration_corners.svg separately; corner compensation is not
     implemented, so this is a baseline only.
  7. Choose the smallest overlap that consistently closes the target sizes
     without visible damage. Values are experimental, not calibrated.

EXAMPLES
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 0.4 --output loops_04.hpgl
  py smart3_cut.py calibration_loops.svg --loop-start auto-straight --loop-overlap-mm 0.4 --force 200 --speed 100 --cut --confirm-live-test I_ACCEPT_MOVEMENT
  py smart3_cut.py calibration_corners.svg --dry-run --cut-strategy no-waste
  py smart3_cut.py calibration_loops.svg --dry-run --contour-modes modes.json

IMPORTANT: each run of calibration_loops.svg has the SAME origin. Reposition
material/origin between runs to avoid cutting on top of an earlier test.
No live USB test of this revision has been performed.
