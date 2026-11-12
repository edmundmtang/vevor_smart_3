SMART 3 v0.14 — MULTI-SEGMENT OVERLAP & EXPERIMENTAL BLADE OFFSET
=================================================================

1. MULTI-SEGMENT OVERLAP
  --loop-overlap-mm 1.0
  After finishing a closed contour, the commanded path retraces the same
  existing segments for 1 mm total arc length, interpolating the final point.
  This now works on circles with segments shorter than 1 mm. Overlap >= the
  entire perimeter is skipped; open paths are unchanged. Console diagnostics
  show how many segments the overlap traversed. Overlap still cannot guarantee
  physical blade-tip closure because the knife can swivel.

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
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 1.0 --output loops_10.hpgl
  py smart3_cut.py calibration_corners.svg --dry-run --blade-offset-mm 0.2 --output corners_offset_02.hpgl
  py smart3_cut.py calibration_loops.svg --dry-run --loop-start auto-straight --loop-overlap-mm 1.0 --blade-offset-mm 0.2 --output loops_10_offset_02.hpgl

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
