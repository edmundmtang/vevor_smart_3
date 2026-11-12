HISTORICAL DOCUMENT (v0.12). For current v0.13 options, see README.txt and CLOSURE_MODES_README.txt.

Smart 3 v0.12 - Intelligent loop seam placement
=================================================

Changes from v0.11
- Adds --loop-start auto-straight to smart3_cut.py (opt-in).
- For explicitly closed paths, groups adjacent edges with turns <= 5 degrees
  (configurable) into straight runs, then places the seam at the midpoint of
  the longest run meeting the minimum length (default 0.5 mm).
- Keeps original winding and shape; no automatic overcut, no extra cutting
  outside the original contour. Open paths are unchanged.
- Reports relocation and fallback counts on the console.
- Includes the previously agreed provisional calibration scales in settings.txt:
  X 0.74906512, Y 3.59950979. Original settings preserved in v0.11 archive.
- Retains 90% mat-travel warning, >100% rejection, and experimental USB guards.

Dry run:
  py smart3_cut.py calibration_details.svg --dry-run --loop-start auto-straight

Live (ONLY after verifying material placement and origin, and reviewing HPGL):
  py smart3_cut.py calibration_details.svg --loop-start auto-straight --force 200 --speed 100 --cut --confirm-live-test I_ACCEPT_MOVEMENT

Options:
  --loop-start original                 (default; no changes)
  --loop-start auto-straight            (opt-in)
  --min-loop-straight 0.5               (minimum qualifying run, mm)
  --loop-turn-tolerance 5               (max turn between run edges, degrees)

Important limits:
- This is seam relocation, not actual drag-knife offset compensation.
- No new USB protocol or flow control. Physical cutter execution is untested.
- The algorithm treats a path as closed only if first and last points coincide.
- Short contours may fall back to the original start; read diagnostics.
- Longest nearly straight run does not guarantee blade orientation; test on
  sacrificial material and inspect actual start/end cuts.
- All compensation is geometric; the actual blade tip can still hook.
- Calibrated command quantization can merge extremely short edges.
- Keep the physical origin setup (manual Y about -115, press Origin).
- The 12-inch mat limit is nominal; configure smaller usable dimensions if needed.

Offline tests:
  py -m unittest -v test_loop_closure.py
