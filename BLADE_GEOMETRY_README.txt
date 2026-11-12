SMART 3 v0.15 — MULTI-SEGMENT OVERLAP & EXPERIMENTAL BLADE OFFSET
=================================================================

1. SYMMETRIC MULTI-SEGMENT OVERLAP (v0.15)
  --loop-overlap-mm 2.0
  The nominal seam stays at the chosen straight-run midpoint (or original
  seam if no suitable straight run exists). The physical cut starts 1.0 mm
  BEFORE that seam along the existing contour, traverses one full revolution,
  and ends 1.0 mm AFTER the seam. Thus 2.0 mm is the TOTAL duplicated length.
  This replaces forward-only overlap; there is no overlap-mode switch.
  Both halves can traverse multiple segments, corners, and curves. Open paths
  remain unchanged. Requests >= the entire perimeter are skipped.
  The physical start moves, but no new off-contour cutting geometry is added.
  The entry hook and blade-tip lag may still cause incomplete physical cuts.

2. EXPERIMENTAL BLADE OFFSET
  --blade-offset-mm 0.2
  This models holder center H = desired blade-tip P + offset * unit tangent.
  At vertices, the holder moves around a radius-offset pivot arc while the
  theoretical tip remains at the vertex. Angular step is set using
  --blade-arc-step-deg 10 (default). A larger step is coarser.
  This is a geometric approximation, NOT calibrated for the Smart 3. It
  cannot guarantee tip tracking, corner sharpness, or no-waste cutting.
  Pivot arcs and starting holder offsets leave the original SVG boundary.
  The model does not add blade-lift swivel alignment or waste-side lead-ins.
  No reliable mechanical offset has been measured; start with 0.0 (off).

3. CLOSURE MODES
  --cut-strategy no-waste | keep-inside | keep-outside
  All three still produce identical geometry for the same overlap/offset.
  They express preservation intent for future safe lead-ins. Nonzero blade
  offset is NOT strict no-waste, even if mode is named no-waste.

4. RECOMMENDED OFFLINE CHECKS (PowerShell)
  py -m unittest discover -v
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 2.0 --output loops_symmetric_20.hpgl
  py smart3_cut.py calibration_corners.svg --dry-run --blade-offset-mm 0.2 --output corners_offset_02.hpgl
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 2.0 --blade-offset-mm 0.2 --output loops_symmetric_20_offset_02.hpgl

  Compare HPGL and bounds before cutting. In particular inspect corner pivot
  arcs and whether any paths are near other contours or mat edges.
  Keep offset=0 for the first physical multi-segment overlap calibration.
  Only after visual inspection should offset compensation be tried on scrap.

5. HARDWARE SAFETY
  Cutter protocol is experimental, with a single WriteFile and no ACK.
  Live cut requires explicit --cut --confirm-live-test I_ACCEPT_MOVEMENT.
  Mat limits check planned holder coordinates; actual blade-tip deviation,
  collision with neighboring shapes, and material behavior are not guaranteed.
  Keep the blade supervised and stop immediately if unexpected motion occurs.
