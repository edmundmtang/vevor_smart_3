Smart 3 single-sheet force/speed test (separate script)
======================================================
Run from the project directory on Windows:
  py smart3_force_speed_grid.py --dry-run
  py smart3_force_speed_grid.py --cut --confirm-live-test I_ACCEPT_MOVEMENT

Nine cells in a 3x3 grid, rows: force 150, 175, 200; columns: speed 50, 75, 100.
Each cell is two independent, open, three-vertex mirrored L cuts. Main lines
travel +X and are commanded to coincide (0 mm nominal gap). Approach legs are
6 mm; main lines 16 mm. Physical geometry X 14..100, Y 7..73 mm.

The generated force_speed_grid_measurements.csv maps cell IDs and settings.
Measure the lateral gap several millimeters after each corner. Also note how
far after each turn the blade settles. Record whether the cutter visibly
changes speed between cells: mid-job FS/VS updates have NOT been validated.

SAFETY: Place sufficient vinyl across the whole physical cut area relative to
the manually established cutter origin; check mat position and blade depth.
The 0 mm test retraces the same nominal line twice. The job is one experimental
USB WriteFile without response handshake. No auto-retry. Inspect HPGL first.
The existing cutter and its settings are not modified. No blade compensation,
loop overlap, or extra off-contour movements are used.
