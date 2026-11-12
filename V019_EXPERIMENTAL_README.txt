Smart 3 v0.19: COMPACT EXPERIMENTAL COMPENSATION TEST
=====================================================

This is a first, bounded, empirical inverse-path HEURISTIC, not a validated
blade-tip inverse kinematics solution. It does NOT prove better accuracy.
Existing cutter code is unchanged. New files: blade_tip_inverse.py,
smart3_v019_compact.py, test_blade_tip_inverse.py, and the two compact SVGs.

Model / assumptions:
- Force 200, speed 100 baseline from your prior tests.
- Symmetry hypothesis: 0.18 mm opposing-cut gap = +/-0.09 mm each.
- Measured recovery ends at 1.39 mm; no further convergence assumed.
- A straight lead-in attempts to condition initial blade orientation.
- At corners the holder intentionally overshoots 0.70 mm by default,
  then traverses toward the outgoing recovery point. THIS CAN SCORE WASTE
  OR THE INSIDE OF A SHAPE. Do not use on valuable workpieces.
- The 0.70 mm overshoot is a tuning hypothesis, NOT inferred from the
  recovery length. We have not measured the true blade tip position.
- The side sign is chosen from the preceding corner turn. It is not
  calibrated for all directions; compare against baseline.
- Squares get an on-contour initial approach, but the outgoing excursions
  may damage the square interior/exterior. Closure is NOT corrected by
  an exact physical inverse; this is a first testable heuristic.
- Circle is intentionally unmodified in both versions as a control.
- Generated geometry is small (nominal 115 x 92 mm page; cut extents roughly
  X 11..92 mm and Y 12..87 mm). The cutter's calibration scales are NOT
  equivalent to physical mat coordinates; inspect both bounds in dry-run.
- Each job contains nine paths, including four 15-mm squares, four open
  corner paths, and a 20-mm-diameter circle. The two files must be cut on
  separate, unused areas; do NOT overcut the same location.

Generate SVGs (offline only):
  py smart3_v019_compact.py

Optional tuning (offline):
  py smart3_v019_compact.py --per-side-mm 0.09 --recovery-mm 1.39 --overshoot-mm 0.70 --conditioning-mm 3

Dry run both:
  py smart3_cut.py v019_compact_baseline.svg --dry-run
  py smart3_cut.py v019_compact_experimental.svg --dry-run

When physically ready, load material, establish origin using your VERIFIED
workflow, confirm the actual placement and bounds, then explicitly run:
  py smart3_cut.py v019_compact_baseline.svg --cut --confirm-live-test I_ACCEPT_MOVEMENT
  py smart3_cut.py v019_compact_experimental.svg --cut --confirm-live-test I_ACCEPT_MOVEMENT

CAUTION: The two jobs share coordinates; REPOSITION to fresh vinyl between
jobs, or deliberately shift origin. Avoid blade-offset-mm and overlap flags
in this comparison so the new algorithm is isolated. A successful USB write
is not an execution acknowledgment. Stay with the cutter.

Measure and report:
1. Square closure: gap, doubled line, gouge, or overshoot (mm).
2. Straight-run alignment of mirrored approach cuts (mm).
3. Corner recovery: distance until settled (mm), and any inward/outward nick.
4. Whether the experimental path improves or worsens each relative to baseline.
5. Whether the circle is unchanged (sanity control).

Do not treat these results as proof of a calibrated physical model. This
prototype does not optimize arbitrary curves, account for all knife swivel
states, or guarantee a clean closed loop. We need physical results before
calling it a final compensation algorithm.
