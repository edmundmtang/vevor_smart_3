HORIZONTAL TRAVEL-DIRECTION GAP TEST — v0.17

File: calibration_horizontal_travel_direction.svg
Compact SVG canvas: 115 x 100 mm; actual geometry X 22..91 mm, Y 19..78 mm.

Layout (not cuttable labels):
  top left: +X, 0 mm gap      top right: -X, 0 mm gap
  bottom left: +X, 2 mm gap   bottom right: -X, 2 mm gap

Each pair contains two separate OPEN polylines of exactly 3 vertices.
The two 8 mm approach legs turn 90 degrees from opposite sides into
22 mm parallel main legs that travel in the SAME direction for each pair.
The gap is the perpendicular distance between main legs, NOT an end gap.
The 0 mm pairs deliberately retrace a nominally identical main line.

For a clean baseline keep overlap and experimental blade offset disabled.
DRY RUN:
  py smart3_cut.py calibration_horizontal_travel_direction.svg --dry-run --loop-overlap-mm 0 --blade-offset-mm 0 --output horizontal_direction.hpgl

GUARDED LIVE TEST (only after confirming physical mat, origin and material):
  py smart3_cut.py calibration_horizontal_travel_direction.svg --loop-overlap-mm 0 --blade-offset-mm 0 --force 200 --speed 100 --cut --confirm-live-test I_ACCEPT_MOVEMENT

Use a scrap piece with enough coverage and margin for the entire pattern.
Check material location relative to the cutter origin: smaller geometry does
not by itself guarantee that the cutter will remain on the material.
At 0 mm, two passes on the same line can cut more deeply.
Measure near the corners and after 2-5 mm along each main line.
Compare +X and -X at both nominal gaps. See horizontal_travel_geometry.csv.

FUTURE DESIGN NOTE (NOT IMPLEMENTED): Model the actual blade tip position
through turns, potentially allowing controlled holder overshoot and gradual
re-entry onto the true contour as the blade rotates. Requires validation
against measurements and safety/retained-material constraints.

No changes to cutting algorithms, axis scales, USB code, or guards.
