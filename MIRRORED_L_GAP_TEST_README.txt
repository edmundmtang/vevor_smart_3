MIRRORED-L APPROACH-DIRECTION GAP TEST — v0.16

FILE: calibration_mirrored_l_gaps.svg
Six cases, arranged left-to-right by long-edge orientation: X, Y, diagonal 45 degrees.
Top row: 0 mm nominal lateral gap. Bottom row: 2 mm nominal lateral gap.
The SVG intentionally contains no cuttable labels; case positions are:
  top left X/0, top middle Y/0, top right diagonal/0
  bottom left X/2, bottom middle Y/2, bottom right diagonal/2.

Each case contains TWO INDEPENDENT OPEN polylines, each with EXACTLY THREE VERTICES:
  (outer start) -> (90-degree turn) -> (end of 30 mm long leg).
Each short leg is 12 mm long. The Ls are reflections across the axis
parallel to the long legs; both long legs are traversed in the SAME direction.
The nominal gap is the perpendicular distance between the long legs.
At 0 mm, the long legs are geometrically coincident and should ideally
produce one cut track. At 2 mm, they are two separate parallel tracks.

No closed loops, seam relocation, loop overlap, or blade offset are needed.
Use --loop-overlap-mm 0 --blade-offset-mm 0 for a clean baseline.

DRY RUN (recommended first):
  py smart3_cut.py calibration_mirrored_l_gaps.svg --dry-run --loop-overlap-mm 0 --blade-offset-mm 0 --output mirrored_l_gaps.hpgl

PHYSICAL CUT (only after verifying mat/origin/material and dry-run):
  py smart3_cut.py calibration_mirrored_l_gaps.svg --loop-overlap-mm 0 --blade-offset-mm 0 --force 200 --speed 100 --cut --confirm-live-test I_ACCEPT_MOVEMENT

WARNING: The 0 mm cases intentionally retrace the same nominal 30 mm line
with two blade-down passes, which may deepen cuts. Use suitable scrap and
check material, blade depth, mat, and origin before live cutting.

MEASURE: Observe whether the two long-leg tracks coincide at 0 mm and whether
the perpendicular separation is 2 mm at 2 mm. Note deviations near the
corner versus near the far end to distinguish transient rotation from
persistent lateral tracking error. Do not infer blade offset from a single
measurement. See mirrored_l_geometry.csv for exact vertex coordinates.

SVG dimensions: 210 x 160 mm. Intended for 304.8 x 304.8 mm mat;
retain existing bounds and USB safety checks. No software changes to
cutting logic are required for this test.
